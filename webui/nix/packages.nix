{ pkgs, version ? "unstable" }:

let
  pythonEnv = pkgs.python3.withPackages (
    ps: with ps; [
      pyyaml
      cryptography
    ]
  );

  runtimeDir = "iris-webui";
in
pkgs.stdenv.mkDerivation {
  pname = "iris-webui";
  inherit version;

  dontUnpack = true;
  dontBuild = true;
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/${runtimeDir}" "$out/bin"

    cp "${./../bootstrap.py}" "$out/${runtimeDir}/bootstrap.py"
    cp "${./../server.py}" "$out/${runtimeDir}/server.py"
    cp "${./../mcp_server.py}" "$out/${runtimeDir}/mcp_server.py"
    cp "${./../requirements.txt}" "$out/${runtimeDir}/requirements.txt"
    cp -r "${./../api}" "$out/${runtimeDir}/api"
    chmod u+w "$out/${runtimeDir}/api"
    cp -r "${./../static}" "$out/${runtimeDir}/static"
    printf "__version__ = '%s'\n" "$version" > "$out/${runtimeDir}/api/_version.py"

    makeWrapper ${pythonEnv}/bin/python3 "$out/bin/iris-webui" \
      --set IRIS_WEBUI_DISABLE_LOCAL_VENV 1 \
      --add-flags "$out/${runtimeDir}/bootstrap.py --foreground --no-browser --skip-agent-install"

    runHook postInstall
  '';

  meta = {
    description = "Iris WebUI package";
    mainProgram = "iris-webui";
  };
}
