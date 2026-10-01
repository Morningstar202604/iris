import { contextBridge, ipcRenderer, webFrame, webUtils } from 'electron'

import type { DesktopProfileRoute } from './desktop-profile'
import type { HudModifierApi, HudModifierStatus } from './hud-modifier-types'
import { customWindowControlsEnabled } from './window-controls'

// Which translucency the OS can back. Asked synchronously because the renderer
// needs it before its first paint, and answered by main because deciding it
// needs `os.release()` — a sandboxed preload may only require electron, events,
// timers and url, so importing node:os here throws before contextBridge runs
// and takes the ENTIRE bridge down with it (window.irisDesktop undefined =>
// "Desktop IPC bridge is unavailable"). No reply means no glass, which degrades
// to an ordinary opaque window rather than a page thinned over nothing.
const translucencySupport = ipcRenderer.sendSync('iris:translucency:support')
const hudWindowing = ipcRenderer.sendSync('iris:hud:windowing')
const hudNativeDrag = hudWindowing?.nativeDrag === true
const launchFlags = ipcRenderer.sendSync('iris:launch-flags')

contextBridge.exposeInMainWorld('irisDesktop', {
  glassSupported: translucencySupport?.glass === true,
  translucencySupported: translucencySupport?.translucency === true,
  // Launch-flag fact: the app was started with --local, so the renderer may
  // show the local-models surfaces. Static for the window's lifetime.
  localModelsEnabled: launchFlags?.localModels === true,
  // Launch-flag fact: the Nous free tier is on for this launch
  // (IRIS_GUEST_ONBOARDING=1 or --guest-onboarding). Read-only; the same
  // decision is stamped onto every backend the app spawns.
  guestOnboardingEnabled: launchFlags?.guestOnboarding === true,
  // Launch-flag fact: skip the first-run film (IRIS_SKIP_INTRO=1 or
  // --skip-intro). Rehearsal aid for the guided chat behind it.
  skipIntro: launchFlags?.skipIntro === true,
  getConnection: (profile, opts) => ipcRenderer.invoke('iris:connection', profile, opts),
  // Registry-scoped backend resolution: { connectionId, profile } → descriptor.
  getConnectionFor: payload => ipcRenderer.invoke('iris:connection:for', payload),
  getProfileRoutes: profiles => ipcRenderer.invoke('iris:plugin-profile-routes', profiles),
  revalidateConnection: () => ipcRenderer.invoke('iris:connection:revalidate'),
  touchBackend: (profile, options) => ipcRenderer.invoke('iris:backend:touch', profile, options),
  getPoolLimits: () => ipcRenderer.invoke('iris:pool-limits:get'),
  setPoolLimits: limits => ipcRenderer.invoke('iris:pool-limits:set', limits),
  getGatewayWsUrl: profile => ipcRenderer.invoke('iris:gateway:ws-url', profile),
  // Registry-scoped fresh WS URL: { connectionId, profile } → result shape of
  // getGatewayWsUrl, minted against that connection's backend.
  getGatewayWsUrlFor: payload => ipcRenderer.invoke('iris:gateway:ws-url-for', payload),
  // Union agent roster across every registered connection.
  getAgentRoster: () => ipcRenderer.invoke('iris:agents:roster'),
  openSessionWindow: (sessionId, opts) => ipcRenderer.invoke('iris:window:openSession', sessionId, opts),
  openSessionInTerminal: (sessionId, opts) => ipcRenderer.invoke('iris:window:openInTerminal', sessionId, opts),
  openWindow: (options?: DesktopProfileRoute) => ipcRenderer.invoke('iris:window:openInstance', options),
  openBrowserWindow: tabId => ipcRenderer.invoke('iris:window:openBrowser', tabId),
  onBrowserPopoutClosed: callback => {
    const listener = (_event, tabId) => callback(tabId)
    ipcRenderer.on('iris:browser-popout:closed', listener)

    return () => ipcRenderer.removeListener('iris:browser-popout:closed', listener)
  },
  claimAmbientCue: key => ipcRenderer.invoke('iris:ambient:claim', key),
  windowControls: {
    custom: customWindowControlsEnabled(),
    minimize: () => ipcRenderer.send('iris:window-control', 'minimize'),
    toggleMaximize: () => ipcRenderer.send('iris:window-control', 'toggle-maximize'),
    close: () => ipcRenderer.send('iris:window-control', 'close')
  },
  wakeIndicator: {
    getState: () => ipcRenderer.invoke('iris:wake-indicator:get'),
    setState: state => ipcRenderer.send('iris:wake-indicator:set', state),
    onState: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('iris:wake-indicator:state', listener)

      return () => ipcRenderer.removeListener('iris:wake-indicator:state', listener)
    }
  },
  chatOnboarding: {
    grow: request => ipcRenderer.send('iris:chat-onboarding:grow', request),
    soloBoot: () => ipcRenderer.send('iris:chat-onboarding:solo-boot')
  },
  introReveal: {
    open: (payload?: { hideMain?: boolean }) => ipcRenderer.invoke('iris:intro-reveal:open', payload),
    close: (payload?: { showMain?: boolean }) => ipcRenderer.invoke('iris:intro-reveal:close', payload),
    skip: () => ipcRenderer.send('iris:intro-reveal:skip'),
    ready: () => ipcRenderer.send('iris:intro-reveal:ready'),
    onSkip: callback => {
      const listener = () => callback()

      ipcRenderer.on('iris:intro-reveal:skip', listener)

      return () => ipcRenderer.removeListener('iris:intro-reveal:skip', listener)
    },
    onClosed: callback => {
      const listener = () => callback()

      ipcRenderer.on('iris:intro-reveal:closed', listener)

      return () => ipcRenderer.removeListener('iris:intro-reveal:closed', listener)
    }
  },
  petOverlay: {
    // Main renderer → main process: window lifecycle + drag. `request` is
    // `{ bounds, screen }`; resolves with the screen bounds it actually used.
    open: request => ipcRenderer.invoke('iris:pet-overlay:open', request),
    close: () => ipcRenderer.invoke('iris:pet-overlay:close'),
    setBounds: bounds => ipcRenderer.send('iris:pet-overlay:set-bounds', bounds),
    setIgnoreMouse: ignore => ipcRenderer.send('iris:pet-overlay:ignore-mouse', ignore),
    // Flip the overlay focusable (and focus it) while the composer needs keys.
    setFocusable: focusable => ipcRenderer.send('iris:pet-overlay:set-focusable', focusable),
    // Main renderer → overlay (forwarded by main): push the latest pet state.
    pushState: payload => ipcRenderer.send('iris:pet-overlay:state', payload),
    // Overlay → main renderer (forwarded by main): pop back in / composer submit.
    control: payload => ipcRenderer.send('iris:pet-overlay:control', payload),
    // Overlay subscribes to state pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:pet-overlay:state', listener)

      return () => ipcRenderer.removeListener('iris:pet-overlay:state', listener)
    },
    // Main renderer subscribes to overlay control messages.
    onControl: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:pet-overlay:control', listener)

      return () => ipcRenderer.removeListener('iris:pet-overlay:control', listener)
    }
  },
  // HUD mode: the chrome-free floating chat. A full app renderer (own gateway)
  // sized as a floating bar, so it mounts the real composer. Main owns the
  // window; `onChanged` keeps every window's toggle truthful.
  hud: {
    nativeDrag: hudNativeDrag,
    windowing: {
      clientPlacement: hudWindowing?.clientPlacement !== false,
      controlDrag: hudWindowing?.controlDrag === true,
      nativeDrag: hudNativeDrag,
      solid: hudWindowing?.solid === true,
      workspaceTransfer: hudWindowing?.workspaceTransfer === true
    },
    open: request => ipcRenderer.invoke('iris:hud:open', request),
    close: () => ipcRenderer.invoke('iris:hud:close'),
    setIgnoreMouse: ignore => ipcRenderer.send('iris:hud:ignore-mouse', ignore),
    beginMove: () => ipcRenderer.send('iris:hud:begin-move'),
    endMove: () => ipcRenderer.send('iris:hud:end-move'),
    moveBy: delta => ipcRenderer.send('iris:hud:move-by', delta),
    setWorkspaceTransfer: transferring => ipcRenderer.send('iris:hud:workspace-transfer', transferring),
    setBounds: bounds => ipcRenderer.send('iris:hud:set-bounds', bounds),
    resetLayout: () => ipcRenderer.invoke('iris:hud:reset-layout'),
    // Whether the band covers the window below the bar. Main pairs it with the
    // user's translucency setting to decide the native frost (macOS vibrancy /
    // Windows 11 DWM backdrop) — see hudFrostFor.
    setFrost: showing => ipcRenderer.invoke('iris:hud:frost', showing),
    // The HUD tells main which session it is on; main hands that back to the
    // app window when the HUD closes, so the app can re-home onto it.
    setSession: sessionId => ipcRenderer.send('iris:hud:session', sessionId),
    onGoto: callback => {
      const listener = (_event, sessionId) => callback(sessionId)
      ipcRenderer.on('iris:hud:goto', listener)

      return () => ipcRenderer.removeListener('iris:hud:goto', listener)
    },
    onChanged: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('iris:hud:changed', listener)

      return () => ipcRenderer.removeListener('iris:hud:changed', listener)
    },
    // Linux only, and silent elsewhere: where the cursor is, in page
    // coordinates, or null when it has left the window. Stands in for the
    // mousemove that `setIgnoreMouseEvents(true, { forward: true })` delivers on
    // macOS and Windows but not here.
    onCursor: callback => {
      const listener = (_event, point) => callback(point)
      ipcRenderer.on('iris:hud:cursor', listener)

      return () => ipcRenderer.removeListener('iris:hud:cursor', listener)
    },
    // Main's game-overlay watch: whether a fullscreen app (a game) is under
    // the HUD, so the renderer can step back to the low-opacity overlay
    // treatment while one owns the screen.
    onGameOverlay: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('iris:hud:game-overlay', listener)

      return () => ipcRenderer.removeListener('iris:hud:game-overlay', listener)
    }
  },
  hudModifier: {
    getSettings: () => ipcRenderer.invoke('iris:hud-modifier:settings:get'),
    setEnabled: enabled => ipcRenderer.invoke('iris:hud-modifier:settings:set', enabled),
    openPermissionSettings: () => ipcRenderer.invoke('iris:hud-modifier:permission'),
    onStatus: callback => {
      const listener = (_event: Electron.IpcRendererEvent, status: HudModifierStatus) => callback(status)
      ipcRenderer.on('iris:hud-modifier:status', listener)

      return () => ipcRenderer.removeListener('iris:hud-modifier:status', listener)
    }
  } satisfies HudModifierApi,
  // macOS native screenshot gesture; captures require a main-issued request.
  screenshot:
    process.platform === 'darwin'
      ? {
          getSettings: () => ipcRenderer.invoke('iris:screenshot:settings:get'),
          setEnabled: enabled => ipcRenderer.invoke('iris:screenshot:settings:set', enabled),
          openPermissionSettings: kind => ipcRenderer.invoke('iris:screenshot:permission', kind),
          capture: requestId => ipcRenderer.invoke('iris:screenshot:capture', requestId),
          onStatus: callback => {
            const listener = (_event, status) => callback(status)
            ipcRenderer.on('iris:screenshot:status', listener)

            return () => ipcRenderer.removeListener('iris:screenshot:status', listener)
          },
          onRequest: callback => {
            const channel = 'iris:screenshot:request'
            const listener = (_event, requestId) => callback(requestId)

            if (ipcRenderer.listenerCount(channel) === 0) {
              ipcRenderer.send('iris:screenshot:subscribe', true)
            }

            ipcRenderer.on(channel, listener)

            return () => {
              ipcRenderer.removeListener(channel, listener)

              if (ipcRenderer.listenerCount(channel) === 0) {
                ipcRenderer.send('iris:screenshot:subscribe', false)
              }
            }
          }
        }
      : undefined,
  // Quick Entry: the global-hotkey mini composer window. Main owns the OS
  // shortcut + the persisted preference; the quick window only captures text
  // and hands it back, and the primary renderer submits it through the normal
  // prompt path.
  quickEntry: {
    getSettings: () => ipcRenderer.invoke('iris:quick-entry:settings:get'),
    setSettings: patch => ipcRenderer.invoke('iris:quick-entry:settings:set', patch),
    submit: payload => ipcRenderer.send('iris:quick-entry:submit', payload),
    dismiss: () => ipcRenderer.send('iris:quick-entry:dismiss'),
    // Primary renderer → main → quick window: gateway connection state + the
    // recent-session options the target picker offers. Main caches the latest
    // payload so a freshly spawned quick window starts from truth.
    pushState: payload => ipcRenderer.send('iris:quick-entry:state', payload),
    // Quick window subscribes to those pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:quick-entry:state', listener)

      return () => ipcRenderer.removeListener('iris:quick-entry:state', listener)
    },
    // Main → primary renderer: a submit captured by the quick window.
    onSubmit: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:quick-entry:submit', listener)

      return () => ipcRenderer.removeListener('iris:quick-entry:submit', listener)
    },
    // Main → quick window: you were just summoned (reset draft + refocus).
    onShown: callback => {
      const listener = () => callback()
      ipcRenderer.on('iris:quick-entry:shown', listener)

      return () => ipcRenderer.removeListener('iris:quick-entry:shown', listener)
    }
  },
  getBootProgress: () => ipcRenderer.invoke('iris:boot-progress:get'),
  getConnectionConfig: profile => ipcRenderer.invoke('iris:connection-config:get', profile),
  saveConnectionConfig: payload => ipcRenderer.invoke('iris:connection-config:save', payload),
  applyConnectionConfig: payload => ipcRenderer.invoke('iris:connection-config:apply', payload),
  testConnectionConfig: payload => ipcRenderer.invoke('iris:connection-config:test', payload),
  // Opt-in OS-keychain encryption for stored gateway secrets (default off —
  // see secret-storage-policy.ts). get never touches the OS keychain.
  getSecretStorageEncryption: () => ipcRenderer.invoke('iris:secret-storage:get'),
  setSecretStorageEncryption: (on: boolean) => ipcRenderer.invoke('iris:secret-storage:set', on),
  // v2 multi-connection registry: named agent sources (local / remote / cloud / ssh).
  connections: {
    list: () => ipcRenderer.invoke('iris:connections:list'),
    save: payload => ipcRenderer.invoke('iris:connections:save', payload),
    remove: id => ipcRenderer.invoke('iris:connections:remove', id),
    setPrimary: id => ipcRenderer.invoke('iris:connections:set-primary', id),
    setLaunchMode: mode => ipcRenderer.invoke('iris:connections:set-launch-mode', mode),
    setLastUsed: id => ipcRenderer.invoke('iris:connections:set-last-used', id),
    test: id => ipcRenderer.invoke('iris:connections:test', id),
    updateManaged: id => ipcRenderer.invoke('iris:connections:update-managed', id),
    // Fan out `iris update` to every eligible registered connection.
    // Optional excludeIds skips rows the caller updates through another path.
    updateAll: options => ipcRenderer.invoke('iris:connections:update-all', options),
    // Registry lifecycle push (main → renderer): a connection was removed or
    // materially edited, so secondaries scoped to it must be disposed (and,
    // for edits, re-dialed at the new target).
    onChanged: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:connections:changed', listener)

      return () => ipcRenderer.removeListener('iris:connections:changed', listener)
    }
  },
  sshConfigHosts: () => ipcRenderer.invoke('iris:ssh-config:hosts'),
  sshResolveHost: host => ipcRenderer.invoke('iris:ssh-config:resolve', host),
  probeConnectionConfig: remoteUrl => ipcRenderer.invoke('iris:connection-config:probe', remoteUrl),
  oauthLoginConnectionConfig: remoteUrl => ipcRenderer.invoke('iris:connection-config:oauth-login', remoteUrl),
  oauthLogoutConnectionConfig: remoteUrl => ipcRenderer.invoke('iris:connection-config:oauth-logout', remoteUrl),
  // Iris Cloud: one portal login powers discovery + silent per-agent sign-in
  // (cloud-auto-discovery Phase 3).
  cloud: {
    status: () => ipcRenderer.invoke('iris:cloud:status'),
    login: () => ipcRenderer.invoke('iris:cloud:login'),
    logout: () => ipcRenderer.invoke('iris:cloud:logout'),
    discover: org => ipcRenderer.invoke('iris:cloud:discover', org),
    agentSignIn: dashboardUrl => ipcRenderer.invoke('iris:cloud:agent-sign-in', dashboardUrl)
  },
  profile: {
    getDefault: () => ipcRenderer.invoke('iris:profile:default:get'),
    setDefault: (route: DesktopProfileRoute) => ipcRenderer.invoke('iris:profile:default:set', route),
    onDefaultChanged: (callback: (route: DesktopProfileRoute | null) => void) => {
      const listener = (_event: Electron.IpcRendererEvent, route: DesktopProfileRoute | null) => callback(route)
      ipcRenderer.on('iris:profile:default:changed', listener)

      return () => ipcRenderer.removeListener('iris:profile:default:changed', listener)
    },
    get: () => ipcRenderer.invoke('iris:profile:get'),
    remember: name => ipcRenderer.invoke('iris:profile:remember', name),
    set: name => ipcRenderer.invoke('iris:profile:set', name)
  },
  api: request => ipcRenderer.invoke('iris:api', request),
  notify: payload => ipcRenderer.invoke('iris:notify', payload),
  requestMicrophoneAccess: () => ipcRenderer.invoke('iris:requestMicrophoneAccess'),
  readWindowBelow: () => ipcRenderer.invoke('iris:window:readBelow'),
  readFileDataUrl: filePath => ipcRenderer.invoke('iris:readFileDataUrl', filePath),
  readFileDataUrlForAttach: filePath => ipcRenderer.invoke('iris:readFileDataUrlForAttach', filePath),
  dataUrlReadMax: {
    get: () => ipcRenderer.invoke('iris:data-url-read-max:get'),
    set: maxMb => ipcRenderer.invoke('iris:data-url-read-max:set', maxMb)
  },
  readFileText: filePath => ipcRenderer.invoke('iris:readFileText', filePath),
  readPluginSource: (filePath: string) => ipcRenderer.invoke('iris:readPluginSource', filePath),
  selectPaths: options => ipcRenderer.invoke('iris:selectPaths', options),
  selectSavePath: options => ipcRenderer.invoke('iris:selectSavePath', options),
  writeClipboard: text => ipcRenderer.invoke('iris:writeClipboard', text),
  readClipboard: () => ipcRenderer.invoke('iris:readClipboard'),
  saveGatewayFile: payload => ipcRenderer.invoke('iris:saveGatewayFile', payload),
  saveImageFromUrl: url => ipcRenderer.invoke('iris:saveImageFromUrl', url),
  contextMenuEdit: command => ipcRenderer.invoke('iris:context-menu:edit', command),
  contextMenuCopyImage: () => ipcRenderer.invoke('iris:context-menu:copy-image'),
  contextMenuSpellcheck: action => ipcRenderer.invoke('iris:context-menu:spellcheck', action),
  contextMenuGuestAddWord: payload => ipcRenderer.invoke('iris:context-menu:guest-add-word', payload),
  onContextMenuSpellcheck: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:context-menu-spellcheck', listener)

    return () => ipcRenderer.removeListener('iris:context-menu-spellcheck', listener)
  },
  saveImageBuffer: (data, ext, name) => ipcRenderer.invoke('iris:saveImageBuffer', { data, ext, name }),
  capturePreview: payload => ipcRenderer.invoke('iris:capturePreview', payload),
  savePastedText: text => ipcRenderer.invoke('iris:savePastedText', { text }),
  saveClipboardImage: () => ipcRenderer.invoke('iris:saveClipboardImage'),
  getPathForFile: file => {
    try {
      return webUtils.getPathForFile(file) || ''
    } catch {
      return ''
    }
  },
  normalizePreviewTarget: (target, baseDir) => ipcRenderer.invoke('iris:normalizePreviewTarget', target, baseDir),
  watchPreviewFile: url => ipcRenderer.invoke('iris:watchPreviewFile', url),
  watchDirectory: dir => ipcRenderer.invoke('iris:watchDirectory', dir),
  stopPreviewFileWatch: id => ipcRenderer.invoke('iris:stopPreviewFileWatch', id),
  setActiveWork: payload => ipcRenderer.send('iris:active-work', payload),
  setTitleBarTheme: payload => ipcRenderer.send('iris:titlebar-theme', payload),
  setNativeTheme: mode => ipcRenderer.send('iris:native-theme', mode),
  setTranslucency: payload => ipcRenderer.send('iris:translucency', payload),
  setKeepAwake: on => ipcRenderer.send('iris:keep-awake', on),
  minimizeToTray: {
    get: () => ipcRenderer.invoke('iris:minimize-to-tray:get'),
    set: on => ipcRenderer.invoke('iris:minimize-to-tray:set', on),
    onChanged: callback => {
      const listener = (_event, status) => callback(status)
      ipcRenderer.on('iris:minimize-to-tray:changed', listener)

      return () => ipcRenderer.removeListener('iris:minimize-to-tray:changed', listener)
    }
  },
  setDisableF12: blocked => ipcRenderer.send('iris:devtools:disable-f12', blocked),
  setPreviewShortcutActive: active => ipcRenderer.send('iris:previewShortcutActive', Boolean(active)),
  openExternal: url => ipcRenderer.invoke('iris:openExternal', url),
  mcpOauth: {
    // One-shot loopback listener for MCP OAuth against remote backends: bind
    // on this machine, hand redirectUri to mcp.servers.oauth.start, then wait
    // for the provider redirect and relay code/state via oauth.callback.
    listen: () => ipcRenderer.invoke('iris:mcp-oauth:listen'),
    wait: (id, timeoutMs) => ipcRenderer.invoke('iris:mcp-oauth:wait', id, timeoutMs),
    cancel: id => ipcRenderer.invoke('iris:mcp-oauth:cancel', id)
  },
  openPreviewInBrowser: url => ipcRenderer.invoke('iris:openPreviewInBrowser', url),
  reachPreviewUrl: url => ipcRenderer.invoke('iris:preview:reach', url),
  setActiveConnectionRoute: route => ipcRenderer.send('iris:connection:active-route', route),
  fetchLinkTitle: url => ipcRenderer.invoke('iris:fetchLinkTitle', url),
  resolveFavicon: url => ipcRenderer.invoke('iris:resolveFavicon', url),
  sanitizeWorkspaceCwd: cwd => ipcRenderer.invoke('iris:workspace:sanitize', cwd),
  settings: {
    getDefaultProjectDir: () => ipcRenderer.invoke('iris:setting:defaultProjectDir:get'),
    setDefaultProjectDir: dir => ipcRenderer.invoke('iris:setting:defaultProjectDir:set', dir),
    pickDefaultProjectDir: () => ipcRenderer.invoke('iris:setting:defaultProjectDir:pick')
  },
  zoom: {
    // Current zoom of this window, as { level, percent }.
    get: () => ipcRenderer.invoke('iris:zoom:get'),
    // Synchronous zoom factor (1 = 100%). Coordinate math needs it in the
    // same tick as the event it converts, so no IPC round-trip here.
    factor: () => webFrame.getZoomFactor(),
    setPercent: percent => ipcRenderer.send('iris:zoom:set-percent', percent),
    // Fires on every zoom change, including the Ctrl/Cmd +/-/0 shortcuts,
    // so the settings UI can stay in sync with the keyboard.
    onChanged: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:zoom:changed', listener)

      return () => ipcRenderer.removeListener('iris:zoom:changed', listener)
    }
  },
  revealLogs: () => ipcRenderer.invoke('iris:logs:reveal'),
  getRecentLogs: () => ipcRenderer.invoke('iris:logs:recent'),
  // Fire-and-forget: persists a renderer error-boundary catch (with component
  // stack) to desktop.log so crashes survive the window (#79428).
  reportRendererError: report => ipcRenderer.send('iris:logs:renderer-error', report),
  readDir: dirPath => ipcRenderer.invoke('iris:fs:readDir', dirPath),
  gitRoot: startPath => ipcRenderer.invoke('iris:fs:gitRoot', startPath),
  revealPath: targetPath => ipcRenderer.invoke('iris:fs:reveal', targetPath),
  openDir: dirPath => ipcRenderer.invoke('iris:fs:openDir', dirPath),
  desktopPluginsRoot: () => ipcRenderer.invoke('iris:fs:desktopPluginsRoot'),
  reconcileDesktopPlugins: () => ipcRenderer.invoke('iris:fs:reconcileDesktopPlugins'),
  logsRoot: () => ipcRenderer.invoke('iris:fs:logsRoot'),
  renamePath: (targetPath, newName) => ipcRenderer.invoke('iris:fs:rename', targetPath, newName),
  writeTextFile: (filePath, content) => ipcRenderer.invoke('iris:fs:writeText', filePath, content),
  trashPath: targetPath => ipcRenderer.invoke('iris:fs:trash', targetPath),
  git: {
    worktreeList: repoPath => ipcRenderer.invoke('iris:git:worktreeList', repoPath),
    worktreeAdd: (repoPath, options) => ipcRenderer.invoke('iris:git:worktreeAdd', repoPath, options),
    worktreeRemove: (repoPath, worktreePath, options) =>
      ipcRenderer.invoke('iris:git:worktreeRemove', repoPath, worktreePath, options),
    branchSwitch: (repoPath, branch) => ipcRenderer.invoke('iris:git:branchSwitch', repoPath, branch),
    branchList: repoPath => ipcRenderer.invoke('iris:git:branchList', repoPath),
    baseBranchList: repoPath => ipcRenderer.invoke('iris:git:baseBranchList', repoPath),
    repoStatus: repoPath => ipcRenderer.invoke('iris:git:repoStatus', repoPath),
    fileDiff: (repoPath, filePath) => ipcRenderer.invoke('iris:git:fileDiff', repoPath, filePath),
    scanRepos: (roots, options) => ipcRenderer.invoke('iris:git:scanRepos', roots, options),
    review: {
      list: (repoPath, scope, baseRef) => ipcRenderer.invoke('iris:git:review:list', repoPath, scope, baseRef),
      diff: (repoPath, filePath, scope, baseRef, staged) =>
        ipcRenderer.invoke('iris:git:review:diff', repoPath, filePath, scope, baseRef, staged),
      stage: (repoPath, filePath) => ipcRenderer.invoke('iris:git:review:stage', repoPath, filePath),
      unstage: (repoPath, filePath) => ipcRenderer.invoke('iris:git:review:unstage', repoPath, filePath),
      revert: (repoPath, filePath) => ipcRenderer.invoke('iris:git:review:revert', repoPath, filePath),
      revParse: (repoPath, ref) => ipcRenderer.invoke('iris:git:review:revParse', repoPath, ref),
      commit: (repoPath, message, push) => ipcRenderer.invoke('iris:git:review:commit', repoPath, message, push),
      commitContext: repoPath => ipcRenderer.invoke('iris:git:review:commitContext', repoPath),
      push: repoPath => ipcRenderer.invoke('iris:git:review:push', repoPath),
      shipInfo: repoPath => ipcRenderer.invoke('iris:git:review:shipInfo', repoPath),
      prList: (repoPath, branches, numbers) =>
        ipcRenderer.invoke('iris:git:review:prList', repoPath, branches, numbers),
      createPr: repoPath => ipcRenderer.invoke('iris:git:review:createPr', repoPath)
    }
  },
  terminal: {
    attach: id => ipcRenderer.invoke('iris:terminal:attach', id),
    cwd: id => ipcRenderer.invoke('iris:terminal:cwd', id),
    dispose: id => ipcRenderer.invoke('iris:terminal:dispose', id),
    resize: (id, size) => ipcRenderer.invoke('iris:terminal:resize', id, size),
    start: options => ipcRenderer.invoke('iris:terminal:start', options),
    write: (id, data) => ipcRenderer.invoke('iris:terminal:write', id, data),
    onData: (id, callback) => {
      const channel = `iris:terminal:${id}:data`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)

      return () => ipcRenderer.removeListener(channel, listener)
    },
    onExit: (id, callback) => {
      const channel = `iris:terminal:${id}:exit`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)

      return () => ipcRenderer.removeListener(channel, listener)
    }
  },
  onClosePreviewRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('iris:close-preview-requested', listener)

    return () => ipcRenderer.removeListener('iris:close-preview-requested', listener)
  },
  onPreviewNav: callback => {
    const listener = (_event, command) => callback(command)
    ipcRenderer.on('iris:preview-nav', listener)

    return () => ipcRenderer.removeListener('iris:preview-nav', listener)
  },
  onOpenFolderRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('iris:open-folder-requested', listener)

    return () => ipcRenderer.removeListener('iris:open-folder-requested', listener)
  },
  onOpenUpdatesRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('iris:open-updates', listener)

    return () => ipcRenderer.removeListener('iris:open-updates', listener)
  },
  onDeepLink: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:deep-link', listener)

    return () => ipcRenderer.removeListener('iris:deep-link', listener)
  },
  signalDeepLinkReady: () => ipcRenderer.invoke('iris:deep-link-ready'),
  probePluginRepo: payload => ipcRenderer.invoke('iris:plugin:probe', payload),
  installDesktopPlugin: payload => ipcRenderer.invoke('iris:plugin:installDesktop', payload),
  removeDesktopPlugin: payload => ipcRenderer.invoke('iris:plugin:removeDesktop', payload),
  onWindowStateChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:window-state-changed', listener)

    return () => ipcRenderer.removeListener('iris:window-state-changed', listener)
  },
  onFocusSession: callback => {
    const listener = (_event, sessionId) => callback(sessionId)
    ipcRenderer.on('iris:focus-session', listener)

    return () => ipcRenderer.removeListener('iris:focus-session', listener)
  },
  onNotificationAction: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:notification-action', listener)

    return () => ipcRenderer.removeListener('iris:notification-action', listener)
  },
  onNotificationActivate: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:notification-activate', listener)

    return () => ipcRenderer.removeListener('iris:notification-activate', listener)
  },
  onPreviewFileChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:preview-file-changed', listener)

    return () => ipcRenderer.removeListener('iris:preview-file-changed', listener)
  },
  onBackendExit: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:backend-exit', listener)

    return () => ipcRenderer.removeListener('iris:backend-exit', listener)
  },
  // Cooperative pool retirement (main → renderer): the pooled backend under
  // `poolKey` is being stopped for a foreground open. Park that scope; do not
  // redial into the slot it vacated.
  onPoolBackendRetiring: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:pool:retiring', listener)

    return () => ipcRenderer.removeListener('iris:pool:retiring', listener)
  },
  // Soft gateway-mode apply finished tearing down the primary backend. Renderer
  // should wipe session lists + re-dial without a window reload.
  onConnectionApplied: callback => {
    const listener = () => callback()
    ipcRenderer.on('iris:connection:applied', listener)

    return () => ipcRenderer.removeListener('iris:connection:applied', listener)
  },
  onPowerResume: callback => {
    const listener = () => callback()
    ipcRenderer.on('iris:power-resume', listener)

    return () => ipcRenderer.removeListener('iris:power-resume', listener)
  },
  // AC ↔ battery transitions; renderers slow their backstop polls on battery.
  getOnBattery: () => ipcRenderer.invoke('iris:power-battery:get'),
  onBatteryChanged: callback => {
    const listener = (_event, onBattery) => callback(Boolean(onBattery))
    ipcRenderer.on('iris:power-battery', listener)

    return () => ipcRenderer.removeListener('iris:power-battery', listener)
  },
  onBootProgress: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:boot-progress', listener)

    return () => ipcRenderer.removeListener('iris:boot-progress', listener)
  },
  // First-launch bootstrap progress -- emitted by the install.ps1 stage
  // runner in main.ts (apps/desktop/electron/bootstrap-runner.ts).
  // Renderer's install overlay subscribes to live events and queries the
  // current snapshot via getBootstrapState() to recover after a devtools
  // reload mid-bootstrap.
  getBootstrapState: () => ipcRenderer.invoke('iris:bootstrap:get'),
  continueBootstrapLocal: () => ipcRenderer.invoke('iris:bootstrap:continue-local'),
  recycleBackend: profile => ipcRenderer.invoke('iris:backend:recycle', profile),
  resetBootstrap: () => ipcRenderer.invoke('iris:bootstrap:reset'),
  repairBootstrap: () => ipcRenderer.invoke('iris:bootstrap:repair'),
  cancelBootstrap: () => ipcRenderer.invoke('iris:bootstrap:cancel'),
  onBootstrapEvent: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('iris:bootstrap:event', listener)

    return () => ipcRenderer.removeListener('iris:bootstrap:event', listener)
  },
  getVersion: () => ipcRenderer.invoke('iris:version'),
  relaunchApp: () => ipcRenderer.invoke('iris:app:relaunch'),
  getMachineProfile: () => ipcRenderer.invoke('iris:machine:profile'),
  getRemoteDisplayReason: () => ipcRenderer.invoke('iris:get-remote-display-reason'),
  uninstall: {
    summary: () => ipcRenderer.invoke('iris:uninstall:summary'),
    run: mode => ipcRenderer.invoke('iris:uninstall:run', { mode })
  },
  updates: {
    check: opts => ipcRenderer.invoke('iris:updates:check', opts),
    apply: opts => ipcRenderer.invoke('iris:updates:apply', opts),
    getBranch: () => ipcRenderer.invoke('iris:updates:branch:get'),
    setBranch: name => ipcRenderer.invoke('iris:updates:branch:set', name),
    onProgress: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('iris:updates:progress', listener)

      return () => ipcRenderer.removeListener('iris:updates:progress', listener)
    }
  },
  themes: {
    fetchMarketplace: id => ipcRenderer.invoke('iris:vscode-theme:fetch', id),
    searchMarketplace: query => ipcRenderer.invoke('iris:vscode-theme:search', query)
  },
  // Find-in-page (Ctrl/Cmd+F): delegates to Electron's
  // webContents.findInPage on the IPC sender's window so a Cmd+F pressed
  // in a secondary session window searches THAT window, not the primary.
  // `onFoundInPage` returns the unsubscribe fn; the renderer wires it via
  // `initFindInPageListener` in store/find-in-page.ts and tears it down
  // when the FindBar unmounts.
  findInPage: (query, options) => ipcRenderer.invoke('iris:find-in-page', query, options),
  stopFindInPage: () => ipcRenderer.invoke('iris:stop-find-in-page'),
  onFoundInPage: callback => {
    const listener = (_event, result) => callback(result)
    ipcRenderer.on('iris:found-in-page', listener)

    return () => ipcRenderer.removeListener('iris:found-in-page', listener)
  },
  // Main-process `before-input-event` forwards Ctrl/Cmd+F here so renderer
  // can open the FindBar even when the GTK compositor has already grabbed
  // the chord at the windowing layer (#81727).
  onOpenFindBarRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('iris:open-find-bar', listener)

    return () => ipcRenderer.removeListener('iris:open-find-bar', listener)
  }
})
