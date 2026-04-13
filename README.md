# Origami

A dotfile and rice manager for Linux, macOS, and Termux. Origami installs
configuration files by symlinking or hard-linking them from a central theme
directory to their expected locations on the system.

> **This project is in early alpha. Expect bugs, missing features, and breaking changes.**

---

## Concepts

- **Rice**: a named collection of components (e.g. `monokai`, `gruvbox`,
  `system9`)
- **Component**: a single program's config (e.g. `nvim`, `waybar`), described by an `origami.json` file
- **Install entry**: a source → target mapping, installed as a symlink or hard link

---

## Directory structure

```
~/.config/origami/
  config.toml              # global config
  themes/
    <rice-name>/
      <component-name>/
        origami.json       # component build file
        ...                # your actual config files
  installations/           # install receipts (auto-generated)
  backups/                 # pre-install backups (auto-generated)
  scripts/                 # optional helper scripts
```

---

## config.toml

```toml
theme = "my-rice"
config_dir = "~/.config/origami"
scripts_dir = "~/.config/origami/scripts"
themes_dir  = "~/.config/origami/themes"

[defaults]
os = "linux"
```

---

## origami.json

```json
{
  "name": "nvim",
  "version": "1.0.0",
  "install": {
    "linux": [
      {
        "type": "symlink",
        "source": "~/.config/origami/themes/my-rice/nvim/nvim",
        "target": "~/.config/nvim"
      }
    ]
  },
  "deps": {
    "programs": [{ "name": "nvim", "required": true }]
  },
  "hooks": {
    "post_install": ["nvim --headless +PlugInstall +qa"]
  }
}
```

**Install types:** `symlink`, `hardlink`, `auto`

---

## CLI

```
origami apply <theme>       # install a rice
origami remove <theme>      # remove a rice
origami list                # list available rices
origami status <theme>      # check install status (not yet implemented)
origami update <theme>      # update from upstream (not yet implemented)
origami theme set <theme>   # set active theme (not yet implemented)
origami theme list          # list themes (not yet implemented)
```

---

## Requirements

- Python 3.11+
- See `requirements.txt` for dependencies

```
pip install -r requirements.txt
```

---

## Status

| Feature                   | Status              |
| ------------------------- | ------------------- |
| Symlink installation      | working             |
| Hard link installation    | working             |
| Dependency checking       | working             |
| Font installation         | working             |
| Conflict detection        | working             |
| Install receipts          | working             |
| Pre/post hooks            | working             |
| Upstream git sync         | not yet implemented |
| CLI (apply/remove/list)   | partial             |
| CLI (status/update/theme) | not yet implemented |

---

## License

[WTFPL](./LICENSE)
