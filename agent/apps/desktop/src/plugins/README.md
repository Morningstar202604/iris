# Bundled plugins

Drop a `<name>/plugin.{ts,tsx}` here that default-exports a `IrisPlugin` and
it registers automatically at boot (vite glob in `../contrib/plugins.ts`), with
the same inventory + live enable/disable contract as runtime plugins.

Keep this tree for real shipped plugins (and the small authoring fixtures that
dogfood the SDK). One-off demos that rebuild a core chrome piece 1:1 do not
belong here — they double the UI and confuse Capabilities ▸ Plugins; ship them
through the plugin catalog instead.

User- and agent-authored plugins load at runtime from
`$IRIS_HOME/desktop-plugins/<name>/plugin.js` (the disk door) — see the
`iris-desktop-plugins` skill.
