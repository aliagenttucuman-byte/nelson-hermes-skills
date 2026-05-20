# Headless Vault Setup

When Obsidian needs to run against a vault on a headless Linux server (no X11/Wayland), prepare the vault filesystem-first and let the user open it from their local machine.

## Steps

1. Ensure the target directory exists and contains a `.obsidian/` config folder.
2. Write `app.json`, `appearance.json`, `core-plugins.json` with sensible defaults.
3. Create an index/root note with wikilinks (`[[...]]`) to connect existing notes.
4. Organize subfolders: `notas/`, `assets/`, etc.
5. Instruct the user to:
   - Install Obsidian on their local machine (Windows/macOS/Linux with GUI).
   - Open the remote vault via Tailscale/network mount, **or**
   - Sync the directory to their local machine.

## Pitfalls

- **Do NOT try to run the Obsidian AppImage on a headless server.** It requires a display server.
- **Do NOT use `xvfb-run` as a workaround** for a GUI the user needs to interact with. It adds complexity without value.
- Prefer filesystem tools (`write_file`, `patch`, `search_files`) over shell text rewriting when building vault content.
- The vault path may contain spaces; always resolve to an absolute concrete path before passing to file tools.

## Minimal config files

`app.json`:
```json
{
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "notas",
  "attachmentFolderPath": "assets",
  "promptDelete": false
}
```

`appearance.json`:
```json
{
  "accentColor": "#7c3aed",
  "cssTheme": "",
  "theme": "obsidian",
  "baseFontSize": 16
}
```

`core-plugins.json`:
```json
[
  "graph", "backlink", "page-preview", "note-composer",
  "command-palette", "editor-status", "starred", "outline",
  "word-count", "file-recovery"
]
```
