{ self }:
{ config, lib, pkgs, ... }:

let
  cfg = config.services.iris-webui;
  defaultPackage = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
  defaultStateDir = "/var/lib/iris-webui";

  protectedEnvironment = [
    "IRIS_WEBUI_HOST"
    "IRIS_WEBUI_PORT"
    "IRIS_WEBUI_STATE_DIR"
    "IRIS_HOME"
    "IRIS_WEBUI_AGENT_DIR"
    "IRIS_WEBUI_PYTHON"
  ];

  defaultUser = "iris-webui";
  defaultGroup = "iris-webui";

  protectedEnvironmentFileCheck = pkgs.writeShellScript "iris-webui-protected-envfile-check" ''
    set -eu
    for env_file in "$@"; do
      [ -f "$env_file" ] || continue
      while IFS= read -r raw_line || [ -n "$raw_line" ]; do
        line=$(printf '%s' "$raw_line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        case "$line" in
          ""|\#*) continue ;;
          export\ *) line=''${line#export } ;;
        esac
        key=''${line%%=*}
        case "$key" in
          IRIS_WEBUI_HOST|IRIS_WEBUI_PORT|IRIS_WEBUI_STATE_DIR|IRIS_HOME|IRIS_WEBUI_AGENT_DIR|IRIS_WEBUI_PYTHON)
            echo "environmentFiles must not set protected WebUI runtime key $key; use module options or extraEnvironment for supported keys." >&2
            exit 1
            ;;
        esac
      done < "$env_file"
    done
  '';

  inferredAgentPython =
    if cfg.agent.package == null then
      null
    else if (cfg.agent.package ? passthru) && (cfg.agent.package.passthru ? irisVenv) then
      "${cfg.agent.package.passthru.irisVenv}/bin/python3"
    else
      null;

  inferredAgentDir =
    if cfg.agent.package == null then
      null
    else if (cfg.agent.package ? passthru) && (cfg.agent.package.passthru ? irisAgentDir) then
      "${cfg.agent.package.passthru.irisAgentDir}"
    else
      null;

  configuredAgentPython =
    if cfg.agent.python != null then
      cfg.agent.python
    else
      inferredAgentPython;

  mappedEnvironment = (lib.mapAttrsToList
    (name: value: "${name}=${value}")
    ({
      IRIS_WEBUI_HOST = cfg.host;
      IRIS_WEBUI_PORT = toString cfg.port;
      IRIS_WEBUI_STATE_DIR = cfg.stateDir;
    }
    // lib.optionalAttrs (cfg.irisHome != null) {
      IRIS_HOME = cfg.irisHome;
    }
    // lib.optionalAttrs (cfg.agent.dir != null) {
      IRIS_WEBUI_AGENT_DIR = cfg.agent.dir;
    }
    // lib.optionalAttrs (cfg.agent.dir == null && inferredAgentDir != null) {
      IRIS_WEBUI_AGENT_DIR = inferredAgentDir;
    }
    // lib.optionalAttrs (configuredAgentPython != null) {
      IRIS_WEBUI_PYTHON = configuredAgentPython;
    }
    // lib.filterAttrs
      (name: _: !(lib.elem name protectedEnvironment))
      cfg.extraEnvironment));

  needsWritableStateDir = cfg.stateDir != defaultStateDir;
  tmpfilesRules = lib.optionals needsWritableStateDir [
    "d ${cfg.stateDir} 0700 ${cfg.user} ${cfg.group} - -"
  ];
in
{
  options.services.iris-webui = {
    enable = lib.mkEnableOption "Iris WebUI service";

    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      defaultText = lib.literalExpression "self.packages.${pkgs.stdenv.hostPlatform.system}.default";
      description = "Package that provides the `bin/iris-webui` executable.";
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = defaultUser;
      description = "User that runs the Iris WebUI service.";
    };

    group = lib.mkOption {
      type = lib.types.str;
      default = defaultGroup;
      description = "Group that runs the Iris WebUI service.";
    };

    host = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1";
      description = "Value for IRIS_WEBUI_HOST.";
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 8787;
      description = "Value for IRIS_WEBUI_PORT.";
    };

    openFirewall = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Open the configured TCP port in the NixOS firewall.";
    };

    stateDir = lib.mkOption {
      type = lib.types.strMatching "^/.+";
      default = defaultStateDir;
      defaultText = lib.literalExpression ''"/var/lib/iris-webui"'';
      description = "Value for IRIS_WEBUI_STATE_DIR.";
    };

    irisHome = lib.mkOption {
      type = lib.types.nullOr (lib.types.strMatching "^/.+");
      default = null;
      description = "Optional value for IRIS_HOME.";
    };

    agent = {
      package = lib.mkOption {
        type = lib.types.nullOr lib.types.package;
        default = null;
        description = "Package to derive IRIS_WEBUI_PYTHON from passthru.irisVenv and optionally IRIS_WEBUI_AGENT_DIR from passthru.irisAgentDir.";
      };

      dir = lib.mkOption {
        type = lib.types.nullOr (lib.types.strMatching "^/.+");
        default = null;
        description = "Explicit path for IRIS_WEBUI_AGENT_DIR.";
      };

      python = lib.mkOption {
        type = lib.types.nullOr (lib.types.strMatching "^/.+");
        default = null;
        description = "Explicit path for IRIS_WEBUI_PYTHON when the service must run with agent dependencies from a separately managed environment.";
      };
    };

    environmentFiles = lib.mkOption {
      type = lib.types.listOf (lib.types.strMatching "^/.+");
      default = [ ];
      description = "Paths with extra environment variables for the service, including API keys. Protected WebUI runtime keys from module options are rejected here.";
    };

    extraEnvironment = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = { };
      description = "Additional environment entries for the service. Required WebUI variables remain enforced.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.iris-webui = {
      description = "Iris Web UI service";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig =
        {
          Type = "simple";
          User = cfg.user;
          Group = cfg.group;
          ExecStartPre = lib.optional (cfg.environmentFiles != [ ]) "+${protectedEnvironmentFileCheck} ${lib.escapeShellArgs (map builtins.toString cfg.environmentFiles)}";
          ExecStart = "${cfg.package}/bin/iris-webui";
          Restart = "on-failure";
          Environment = mappedEnvironment;
          EnvironmentFile = map builtins.toString cfg.environmentFiles;
          StateDirectoryMode = "0700";
          UMask = "0077";
        }
        // lib.optionalAttrs (cfg.stateDir == defaultStateDir) {
          StateDirectory = "iris-webui";
        };
    };

    networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];

    users.groups = lib.mkIf (cfg.group == defaultGroup) {
      ${cfg.group} = { };
    };

    users.users = lib.mkIf (cfg.user == defaultUser) {
      ${cfg.user} = {
        isSystemUser = true;
        group = cfg.group;
        home = cfg.stateDir;
      };
    };

    systemd.tmpfiles.rules = tmpfilesRules;
  };
}
