---
name: oh-my-hermes
description: "Oh My Hermes — community-customizable dotfiles and configuration for Hermes Agent."
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Configuration, Dotfiles, Customization, Setup, Hermes Agent, CLI]

---

# Oh My Hermes Skill

Oh My Hermes is a community-driven framework for customizing and configuring Hermes Agent environments. Inspired by frameworks like Oh My Zsh, it provides a modular way to manage Hermes settings, plugins, aliases, and environment-specific configurations.

## When to Use This Skill

This skill should be triggered when:
- Setting up a new Hermes Agent environment
- Customizing Hermes behavior, themes, or plugins
- Managing multiple Hermes configurations across machines
- Troubleshooting configuration issues
- Sharing or importing community configurations

## Quick Reference

### Common Patterns

**Pattern 1: Initialize Oh My Hermes**

```bash
# First-time setup
oh-my-hermes init

# This creates:
# ~/.oh-my-hermes/
# ├── config/
# ├── plugins/
# ├── themes/
# └── aliases/
```

**Pattern 2: Enable a plugin**

```bash
# In ~/.oh-my-hermes/config/plugins.conf
plugins=(git python docker kubernetes)
```

**Pattern 3: Switch themes**

```bash
# In ~/.oh-my-hermes/config/theme.conf
theme="dark-auto"

# Available themes:
# - dark-auto    (auto-detect terminal background)
# - light        (light terminal)
# - dark         (dark terminal)
# - minimal      (no colors, plain text)
# - rainbow      (colorful output)
```

### Configuration structure

```
~/.oh-my-hermes/
├── config/
│   ├── plugins.conf      # Enabled plugins
│   ├── theme.conf        # Theme selection
│   └── settings.conf     # General settings
├── plugins/
│   ├── git/
│   │   └── plugin.sh
│   ├── python/
│   │   └── plugin.sh
│   └── ...
├── themes/
│   ├── dark-auto.sh
│   ├── light.sh
│   └── ...
├── aliases/
│   └── custom.sh
└── custom/
    └── (user overrides)
```

## Reference Files

This skill includes reference documentation in `references/`:

- **installation.md** - Installation and first-time setup
- **plugins.md** - Available plugins and how to enable them
- **themes.md** - Theme gallery and customization
- **configuration.md** - Full configuration reference
- **migration.md** - Migrating from manual config to Oh My Hermes

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners

Start with `oh-my-hermes init` and enable one plugin at a time. See references/installation.md for step-by-step setup.

### For Specific Features

- Plugins: See references/plugins.md
- Themes: See references/themes.md
- Advanced config: See references/configuration.md

### For Code Examples

The quick reference above shows common setup and configuration patterns.

## Resources

### references/

Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Plugin and theme listings
- Configuration reference tables

### scripts/

Add helper scripts here for common automation tasks.

### assets/

Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from documentation
- Reference files preserve the structure and examples from source docs
- Community plugins can be installed from the Oh My Hermes plugin registry

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
