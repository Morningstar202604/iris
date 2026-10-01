{
  description = "Iris Web UI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      linuxSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      irisModule = import ./nix/nixosModules.nix { inherit self; };
      packageVersion = self.shortRev or (self.dirtyShortRev or "unstable");
      perSystem = forAllSystems (system: let
        pkgs = import nixpkgs { inherit system; };
        package = import ./nix/packages.nix {
          inherit pkgs;
          version = packageVersion;
        };
        moduleChecks = if builtins.elem system linuxSystems then
          let
            moduleConfig = nixpkgs.lib.nixosSystem {
              inherit system;
              modules = [
                irisModule
                {
                  services.iris-webui = {
                    enable = true;
                    package = package;
                    host = "127.0.0.1";
                    port = 8787;
                    stateDir = "/var/lib/iris-webui";
                    agent.dir = "/var/lib/iris-agent";
                  };
                }
              ];
            };
            packageOnlyAgentVenv = pkgs.runCommand "iris-agent-package-only-venv-${system}" { } ''
              mkdir -p "$out/bin"
              touch "$out/bin/python3"
            '';
            packageOnlyAgentPackage = pkgs.runCommand "iris-agent-package-only-${system}" {
              passthru.irisVenv = packageOnlyAgentVenv;
            } ''
              touch "$out"
            '';
            packageOnlyModuleConfig = nixpkgs.lib.nixosSystem {
              inherit system;
              modules = [
                irisModule
                {
                  services.iris-webui = {
                    enable = true;
                    package = package;
                    agent.package = packageOnlyAgentPackage;
                  };
                }
              ];
            };
            moduleServiceEnvironment = nixpkgs.lib.concatStringsSep "\n" moduleConfig.config.systemd.services.iris-webui.serviceConfig.Environment;
            envProbe = pkgs.writeText "iris-webui-nixos-env-${system}.txt" moduleServiceEnvironment;
            packageOnlyServiceEnvironment = nixpkgs.lib.concatStringsSep "\n" packageOnlyModuleConfig.config.systemd.services.iris-webui.serviceConfig.Environment;
            packageOnlyEnvProbe = pkgs.writeText "iris-webui-nixos-package-only-env-${system}.txt" packageOnlyServiceEnvironment;
          in
          {
            module-env-mapping = pkgs.runCommand "iris-webui-nixos-module-${system}" {
              nativeBuildInputs = [ pkgs.coreutils ];
            } ''
              grep -q 'IRIS_WEBUI_HOST=127.0.0.1' ${envProbe}
              grep -q 'IRIS_WEBUI_PORT=8787' ${envProbe}
              grep -q 'IRIS_WEBUI_STATE_DIR=/var/lib/iris-webui' ${envProbe}
              grep -q 'IRIS_WEBUI_AGENT_DIR=/var/lib/iris-agent' ${envProbe}
              grep -q 'IRIS_WEBUI_PYTHON=${packageOnlyAgentVenv}/bin/python3' ${packageOnlyEnvProbe}
              ! grep -q 'IRIS_WEBUI_AGENT_DIR=' ${packageOnlyEnvProbe}
              touch "$out"
            '';
            runtime-layout = pkgs.runCommand "iris-webui-runtime-layout-${system}" {
              nativeBuildInputs = [ pkgs.coreutils ];
            } ''
              test -f ${package}/iris-webui/bootstrap.py
              test -f ${package}/iris-webui/server.py
              test -d ${package}/iris-webui/api
              test -d ${package}/iris-webui/static
              cd ${package}/iris-webui
              ${package}/bin/iris-webui --help >/dev/null
              ${package}/bin/iris-webui --help 2>&1 | grep -q -- '--foreground'
              PYTHONPATH=${package}/iris-webui ${pkgs.python3.withPackages (ps: with ps; [ pyyaml cryptography ])}/bin/python3 -c 'import api.config, server; print("runtime imports ok")'
              touch "$out"
            '';
          }
        else
          { };
      in
      {
        packages = {
          iris-webui = package;
          default = package;
        };

        apps = {
          default = {
            type = "app";
            program = "${package}/bin/iris-webui";
          };
        };

        checks = moduleChecks // {
          package = package;
        };
      });
    in
    {
      packages = forAllSystems (system: perSystem.${system}.packages);
      apps = forAllSystems (system: perSystem.${system}.apps);
      checks = nixpkgs.lib.genAttrs linuxSystems (system: perSystem.${system}.checks);

      nixosModules = {
        default = irisModule;
        iris-webui = irisModule;
      };
    };
}
