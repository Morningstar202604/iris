# Usage Guide

**English** · [简体中文](usage.zh-CN.md)

Iris is a complete personal AI workbench. This guide walks through the core features
by everyday scenario.

## Chat & tasks

- **Ask directly**: type in the bottom composer and send. Iris calls tools on its own
  (terminal, files, web, image generation, …) whenever a task needs them.
- **Complex tasks**: describe the goal in plain language, e.g.
  - “Create a directory `demo` in the workspace, write a complete single-page site and
    tell me the path and size”
  - “Write a Python program for the Fibonacci sequence, run it and verify the output”
  - “Generate a brand logo with the image tool and save it to the workspace”
- **Composer selectors** (left to right):
  1. **Profile** (default) — switch persona / identity config
  2. **Workspace** (Home) — switch the task working directory
  3. **Model** (Agnes 3.0 Flash) — switch the conversation model
- **Preset prompts**: the preset dropdown above the composer saves frequent commands.

### Self-healing during long tasks

Iris handles common environment problems automatically, with no manual intervention:

| Situation | Auto handling |
|---|---|
| Stream response truncated | Continues writing, resumes unfinished work |
| Oversized file write | Automatically switches to batched writes |
| Model rate limit (429) | Exponential backoff retry (3 attempts) |
| Tool permission denied | Records the reason and uses an equivalent alternative |
| Context too long | Compacts history automatically and continues |

## Sessions

- Left **Chat** panel: search, filter by source (WebUI / CLI), start new sessions.
- Every session keeps its own history, model and workspace.
- Export: Settings → Conversations → record / JSON / share / HTML.

## Skills

- **Skills hub** (left rail): view, create, enable/disable skills. Skills are reusable
  instruction templates that make Iris follow a fixed workflow.
- Keep skill descriptions short (trigger words first, one line); oversized ones are
  rejected.

## Memory

- Personal memory has four sections: **My Notes**, **User Profile**, **Agent Soul**,
  **Project Context**.
- Iris accumulates profile and long-term memory during conversation; you can also
  edit entries manually.

## Scheduled tasks (Cron)

- **Tasks** panel: create scheduled jobs (one-off / recurring / complex calendar rules).
- Jobs can pick a model and workspace, and expose run history.

## Kanban & todos

- **Kanban**: multi-column task board, good for project management.
- **Todos**: personal task list.

## Workspace

- **Workspace** panel: manage working directories (Home is the default).
- Sessions can bind a workspace; all file operations happen inside that directory.

## Usage analytics

- **Insights** panel: system health (CPU/RAM/Disk), skill usage, session / message /
  token / cost statistics.
- **Providers → quota**: per-provider usage. Free quotas may return 429 once exhausted;
  wait for the window to reset.

## Mobile

The mobile browser works too: drawer navigation, responsive layout, mobile config
buttons (workspace / model / quota).

## Keyboard shortcuts

- `Ctrl+Shift+P` command palette
- `↑` / `↓` scroll through history while editing
- `Esc` close dialogs / dropdowns

## Voice

- 🎤 voice input, 🔖 presets, 📝 attachments beside the composer.
- Settings → Appearance / Preferences adjusts voice and TTS options.
