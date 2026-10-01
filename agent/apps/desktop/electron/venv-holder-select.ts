/**
 * venv-holder-select.ts
 *
 * Pure Windows venv-holder selection logic (testable without Electron).
 *
 * The pre-update handoff kills Iris-OWNED venv daemons (the memory plugin's
 * hindsight daemon) so the updater never races a mapped shim. External
 * holders (a user terminal running `iris`, unrelated scripts) must NOT be
 * killed — current design reports them via scanVenvBlockers and ABORTS the
 * handoff instead (main.ts releaseBackendLock / applyUpdates).
 */

/** Ordinal case-insensitive prefix check for Windows paths. */
export function hasWindowsPathPrefix(exePath: string, venvScriptsDir: string): boolean {
  const prefix = `${venvScriptsDir}\\`

  return exePath.length >= prefix.length && exePath.slice(0, prefix.length).toLowerCase() === prefix.toLowerCase()
}

/**
 * True when a process is a Iris-owned venv daemon: its exe lives under
 * `<venv>\Scripts\` (ordinal case-insensitive prefix) AND its cmdline
 * references `hindsight_api.main` (the memory daemon the memory plugin
 * spawns DETACHED — it outlives Iris and holds venv shims mapped).
 */
export function isIrisOwnedVenvDaemon(
  exePath: string | null | undefined,
  cmdline: string | null | undefined,
  venvScriptsDir: string
): boolean {
  if (!exePath || !cmdline) {
    return false
  }

  return hasWindowsPathPrefix(exePath, venvScriptsDir) && /hindsight_api\.main/i.test(cmdline)
}
