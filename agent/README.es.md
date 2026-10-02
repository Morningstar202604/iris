<p align="center">
  <img src="assets/banner.png" alt="Iris Agent" width="100%">
</p>

# Iris Agent ✦
<p align="center">
  <a href="https://gitcode.com/badhope/iris">Iris Agent</a> | <a href="https://gitcode.com/badhope/iris/releases">Iris Releases</a>
</p>
<p align="center">
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/X33834/iris/blob/main/LICENSE"><img src="https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge" alt="Licencia: MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
</p>

**Iris — el núcleo del agente de tu asistente personal de IA**, un fork comunitario de Hermes, el marco de agente de código abierto originalmente de [Nous Research](https://nousresearch.com) (versión 0.21.4 al momento del fork; totalmente autocontenido, sin dependencia en tiempo de ejecución del paquete ascendente). Es el único agente con un bucle de aprendizaje integrado: crea habilidades a partir de la experiencia, las mejora durante el uso, se impulsa a sí mismo a persistir el conocimiento, busca en sus propias conversaciones pasadas y construye un modelo cada vez más profundo de quién eres a lo largo de las sesiones. Ejecútalo en un VPS de $5, un clúster de GPUs o infraestructura sin servidor que cuesta casi nada cuando está inactivo. No está atado a tu laptop — habla con él desde Telegram mientras trabaja en una VM en la nube.

Usa cualquier modelo que quieras — [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai) (más de 200 modelos), [NovitaAI](https://novita.ai), [NVIDIA NIM](https://build.nvidia.com) (Nemotron), [Xiaomi MiMo](https://platform.xiaomimimo.com), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), [Hugging Face](https://huggingface.co), OpenAI, o tu propio endpoint. Cambia con `iris model` — sin cambios de código, sin dependencias.

<table>
<tr><td><b>Una interfaz de terminal real</b></td><td>TUI completa con edición multilínea, autocompletado de comandos, historial de conversaciones, interrupción y redirección, y salida de herramientas en streaming.</td></tr>
<tr><td><b>Vive donde tú vives</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal y CLI — todo desde un único proceso gateway. Transcripción de notas de voz, continuidad de conversación entre plataformas.</td></tr>
<tr><td><b>Un bucle de aprendizaje cerrado</b></td><td>Memoria curada por el agente con recordatorios periódicos. Creación autónoma de habilidades tras tareas complejas. Las habilidades mejoran solas durante el uso. Búsqueda FTS5 de sesiones con resumención por LLM para recuperación entre sesiones. Modelado de usuario dialéctico <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Compatible con el estándar abierto de <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Automatizaciones programadas</b></td><td>Planificador cron integrado con entrega a cualquier plataforma. Informes diarios, copias de seguridad nocturnas, auditorías semanales — todo en lenguaje natural, ejecutándose de forma autónoma.</td></tr>
<tr><td><b>Delega y paraleliza</b></td><td>Lanza subagentes aislados para flujos de trabajo paralelos. Escribe scripts de Python que llaman a herramientas vía RPC, convirtiendo pipelines de múltiples pasos en turnos de coste cero de contexto.</td></tr>
<tr><td><b>Funciona en cualquier lugar, no solo en tu laptop</b></td><td>Seis backends de terminal — local, Docker, SSH, Singularity, Modal y Daytona. Daytona y Modal ofrecen persistencia sin servidor — el entorno de tu agente hiberna cuando está inactivo y se activa bajo demanda, costando casi nada entre sesiones. Ejecútalo en un VPS de $5 o un clúster de GPUs.</td></tr>
<tr><td><b>Listo para investigación</b></td><td>Generación de trayectorias en lote, compresión de trayectorias para entrenar la próxima generación de modelos de llamadas a herramientas.</td></tr>
</table>

---

## Instalación rápida

### Linux, macOS, WSL2, Termux

```bash
git clone https://gitcode.com/badhope/iris.git && cd iris/agent && ./setup-iris.sh
```

### Windows (nativo, PowerShell)

> **Nota:** En Windows nativo, Iris funciona sin WSL — la CLI, el gateway, la TUI y las herramientas funcionan de forma nativa. Si prefieres usar WSL2, el comando de Linux/macOS de arriba también funciona allí. ¿Encontraste un error? Por favor [crea un issue](https://gitcode.com/badhope/iris/issues).

Ejecuta esto en PowerShell:

```powershell
git clone https://gitcode.com/badhope/iris.git; Set-Location iris\agent; .\setup-iris.sh
```

El instalador se encarga de todo: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **y un Git Bash portátil** (MinGit, descomprimido en `%LOCALAPPDATA%\iris\git` — no requiere administrador, completamente aislado de cualquier instalación de Git del sistema). Iris usa este Git Bash incluido para ejecutar comandos de shell.

Si ya tienes Git instalado, el instalador lo detecta y lo usa en su lugar. De lo contrario, una descarga de ~45MB de MinGit es todo lo que necesitas — no tocará ni interferirá con ningún Git del sistema.

> **Android / Termux:** La ruta manual probada está documentada en la [guía de Termux](../docs/quickstart.md). En Termux, Iris instala el extra `.[termux]` curado porque el extra completo `.[all]` actualmente incluye dependencias de voz incompatibles con Android.
>
> **Windows:** Windows nativo es totalmente compatible — el comando de PowerShell de arriba instala todo. Si prefieres usar WSL2, el comando de Linux también funciona allí. La instalación nativa de Windows se encuentra en `%LOCALAPPDATA%\iris`; WSL2 instala en `~/.iris` como en Linux.

Después de la instalación:

```bash
source ~/.bashrc    # recargar shell (o: source ~/.zshrc)
iris              # ¡empieza a chatear!
```

---

## Primeros pasos

```bash
iris              # CLI interactiva — inicia una conversación
iris model        # Elige tu proveedor y modelo LLM
iris tools        # Configura qué herramientas están habilitadas
iris config set   # Establece valores de configuración individuales
iris gateway      # Inicia el gateway de mensajería (Telegram, Discord, etc.)
iris setup        # Ejecuta el asistente de configuración completo
iris claw migrate # Migra desde OpenClaw (si vienes de OpenClaw)
iris update       # Actualiza a la última versión
iris doctor       # Diagnostica cualquier problema
```

📖 **[Documentación completa →](https://gitcode.com/badhope/iris/tree/main/docs)**

---

## Evita la colección de claves API — Nous Portal

Iris funciona con cualquier proveedor que quieras — eso no cambiará. Pero si prefieres no recopilar cinco claves API separadas para el modelo, búsqueda web, generación de imágenes, TTS y un navegador en la nube, **[Nous Portal](https://portal.nousresearch.com)** las cubre todas bajo una sola suscripción:

- **Más de 300 modelos** — elige cualquiera con `/model <nombre>`
- **Tool Gateway** — búsqueda web (Firecrawl), generación de imágenes (FAL), texto a voz (OpenAI), navegador en la nube (Browser Use), todo enrutado a través de tu suscripción. Sin cuentas adicionales.

Un comando desde una instalación nueva:

```bash
iris setup --portal
```

Esto te autentica vía OAuth, establece Nous como tu proveedor y activa el Tool Gateway. Comprueba qué está conectado en cualquier momento con `iris portal info`. Detalles completos en la [página de documentación del Tool Gateway](../docs/usage.md).

Puedes seguir usando tus propias claves por herramienta cuando quieras — el gateway es por backend, no todo o nada.

---

## Referencia rápida: CLI vs Mensajería

Iris tiene dos puntos de entrada: inicia la interfaz de terminal con `iris`, o ejecuta el gateway y habla con él desde Telegram, Discord, Slack, WhatsApp, Signal o Email. Una vez en una conversación, muchos comandos de barra son compartidos entre ambas interfaces.

| Acción                              | CLI                                           | Plataformas de mensajería                                                         |
| ----------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------- |
| Empezar a chatear                   | `iris`                                      | Ejecuta `iris gateway setup` + `iris gateway start`, luego envía un mensaje al bot |
| Nueva conversación                  | `/new` o `/reset`                             | `/new` o `/reset`                                                                 |
| Cambiar modelo                      | `/model [proveedor:modelo]`                   | `/model [proveedor:modelo]`                                                       |
| Establecer personalidad             | `/personality [nombre]`                       | `/personality [nombre]`                                                           |
| Reintentar o deshacer último turno  | `/retry`, `/undo`                             | `/retry`, `/undo`                                                                 |
| Comprimir contexto / ver uso        | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                         |
| Explorar habilidades                | `/skills` o `/<nombre-habilidad>`             | `/<nombre-habilidad>`                                                             |
| Interrumpir trabajo actual          | `Ctrl+C` o enviar un nuevo mensaje            | `/stop` o enviar un nuevo mensaje                                                 |
| Estado específico de plataforma     | `/platforms`                                  | `/status`, `/sethome`                                                             |

Para las listas de comandos completas, consulta la [guía de CLI](../docs/usage.md) y la [guía del Gateway de Mensajería](../docs/usage.md).

---

## Documentación

Toda la documentación está en **[docs/](../docs/)**:

| Sección                                                                                             | Contenido                                                    |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [Inicio rápido](../docs/quickstart.md)              | Instalar → configurar → primera conversación en 2 minutos   |
| [Uso de CLI](../docs/usage.md)                             | Comandos, atajos de teclado, personalidades, sesiones        |
| [Configuración](../docs/configuration.md)               | Archivo de configuración, proveedores, modelos, todas las opciones |
| [Gateway de Mensajería](../docs/usage.md)           | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant   |
| [Seguridad](../docs/usage.md)                        | Aprobación de comandos, emparejamiento por DM, aislamiento en contenedor |
| [Herramientas y Toolsets](../docs/usage.md)   | Más de 40 herramientas, sistema de toolsets, backends de terminal |
| [Sistema de Habilidades](../docs/usage.md)   | Memoria procedimental, Skills Hub, creación de habilidades   |
| [Memoria](https://gitcode.com/badhope/iris/tree/main/docs)                   | Memoria persistente, perfiles de usuario, mejores prácticas  |
| [Integración MCP](https://gitcode.com/badhope/iris/tree/main/docs)              | Conecta cualquier servidor MCP para capacidades extendidas   |
| [Programación Cron](https://gitcode.com/badhope/iris/tree/main/docs)           | Tareas programadas con entrega a plataforma                  |
| [Archivos de Contexto](https://gitcode.com/badhope/iris/tree/main/docs) | Contexto de proyecto que da forma a cada conversación      |
| [Arquitectura](https://gitcode.com/badhope/iris/tree/main/docs)            | Estructura del proyecto, bucle del agente, clases principales |
| [Contribuir](https://gitcode.com/badhope/iris/tree/main/docs)              | Configuración de desarrollo, proceso de PR, estilo de código |
| [Referencia de CLI](https://gitcode.com/badhope/iris/tree/main/docs)             | Todos los comandos y flags                                   |
| [Variables de Entorno](https://gitcode.com/badhope/iris/tree/main/docs) | Referencia completa de variables de entorno                  |

---

## Migración desde OpenClaw

Si vienes de OpenClaw, Iris puede importar automáticamente tu configuración, memorias, habilidades y claves API.

**Durante la configuración inicial:** El asistente de configuración (`iris setup`) detecta automáticamente `~/.openclaw` y ofrece migrar antes de que comience la configuración.

**En cualquier momento después de instalar:**

```bash
iris claw migrate              # Migración interactiva (preset completo)
iris claw migrate --dry-run    # Vista previa de qué se migraría
iris claw migrate --preset user-data   # Migrar sin secretos
iris claw migrate --overwrite  # Sobreescribir conflictos existentes
```

Qué se importa:

- **SOUL.md** — archivo de personalidad
- **Memorias** — entradas de MEMORY.md y USER.md
- **Habilidades** — habilidades creadas por el usuario → `~/.iris/skills/openclaw-imports/`
- **Lista de comandos permitidos** — patrones de aprobación
- **Configuración de mensajería** — configuración de plataformas, usuarios permitidos, directorio de trabajo
- **Claves API** — secretos en lista de permitidos (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **Assets de TTS** — archivos de audio del espacio de trabajo
- **Instrucciones del espacio de trabajo** — AGENTS.md (con `--workspace-target`)

Consulta `iris claw migrate --help` para todas las opciones, o usa la habilidad `openclaw-migration` para una migración guiada interactiva por el agente con vistas previas de dry-run.

---

## Contribuir

¡Las contribuciones son bienvenidas! Consulta la [Guía de Contribución](CONTRIBUTING.es.md) para la configuración del desarrollo, el estilo de código y el proceso de PR.

Inicio rápido para colaboradores — clona y comienza con `setup-iris.sh`:

```bash
git clone https://gitcode.com/badhope/iris.git
cd iris-agent
./setup-iris.sh     # instala uv, crea venv, instala .[all], enlaza ~/.local/bin/iris
./iris              # detecta automáticamente el venv, no necesitas hacer `source` primero
```

Ruta manual (equivalente a lo anterior):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Comunidad

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://gitcode.com/badhope/iris/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Servidor MCP de control de escritorio Linux para Iris y otros hosts MCP, con árboles de accesibilidad AT-SPI, entrada Wayland/X11, capturas de pantalla y targeting de ventanas del compositor.
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Puente WeChat comunitario: Ejecuta Iris Agent y OpenClaw en la misma cuenta de WeChat.

---

## Licencia

MIT — ver [LICENSE](LICENSE).

El marco ascendente Hermes fue creado por [Nous Research](https://nousresearch.com); Iris es un fork comunitario.
