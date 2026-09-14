---
name: wondelai-skills
description: "Wondel AI skill library for AI-powered workflows and automation."
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [AI, Automation, Workflows, Skills, Integration, WondeL AI]

---

# WondeL AI Skills Skill

WondeL AI provides a library of pre-built skills for integrating AI capabilities into workflows, automation pipelines, and applications. This skill covers how to discover, install, configure, and use WondeL AI skills within the Hermes Agent ecosystem.

## When to Use This Skill

This skill should be triggered when:
- Looking for pre-built AI skills for specific tasks
- Integrating WondeL AI skills into Hermes workflows
- Configuring WondeL AI skill parameters and options
- Troubleshooting skill execution or integration issues
- Building custom skills compatible with WondeL AI

## Quick Reference

### Common Patterns

**Pattern 1: List available skills**

```bash
# List all available WondeL AI skills
wendel skills list

# Filter by category
wendel skills list --category document-processing
wendel skills list --category data-analysis
```

**Pattern 2: Install a skill**

```bash
# Install a skill from the registry
wendel skills install document-summarizer

# Install with specific version
wendel skills install document-summarizer@v2.1.0

# Install from local path
wendel skills install ./my-custom-skill
```

**Pattern 3: Run a skill**

```bash
# Execute a skill with input
wendel skills run document-summarizer \
  --input ./document.pdf \
  --output ./summary.md \
  --options '{"max_length": 500, "language": "en"}'
```

**Pattern 4: Configure skill parameters**

```bash
# Set default parameters for a skill
wendel skills configure document-summarizer \
  --set defaults.max_length=1000 \
  --set defaults.language=en \
  --set defaults.output_format=markdown
```

### Skill manifest structure

```yaml
# skill.yaml — WondeL AI skill manifest
name: document-summarizer
version: 2.1.0
description: Summarizes documents using AI
category: document-processing
author: WondeL AI
license: MIT

inputs:
  - name: document
    type: file
    required: true
    formats: [pdf, docx, txt, md]

outputs:
  - name: summary
    type: text
    format: markdown

options:
  max_length:
    type: integer
    default: 500
    description: Maximum summary length in words
  language:
    type: string
    default: en
    description: Output language code
  tone:
    type: string
    default: neutral
    enum: [neutral, formal, casual]

runtime:
  engine: gpt-4
  temperature: 0.7
  max_tokens: 2000

hooks:
  pre_process: scripts/pre_process.py
  post_process: scripts/post_process.py
```

## Reference Files

This skill includes reference documentation in `references/`:

- **skill-registry.md** - Complete list of available WondeL AI skills
- **configuration.md** - Skill configuration reference and options
- **custom-skills.md** - Guide to building custom WondeL AI skills
- **integration.md** - Integrating WondeL AI skills with Hermes Agent
- **troubleshooting.md** - Common issues and solutions

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners

Start with `wendel skills list` to see what's available, then `wendel skills install <name>` to try one. See references/skill-registry.md for the full catalog.

### For Specific Features

- Finding skills: See references/skill-registry.md
- Custom skills: See references/custom-skills.md
- Integration: See references/integration.md

### For Code Examples

The quick reference above shows common CLI patterns for managing and running WondeL AI skills.

## Resources

### references/

Organized documentation extracted from official sources. These files contain:
- Complete skill catalog with descriptions
- Configuration parameter references
- Custom skill development guides
- Integration examples with Hermes Agent

### scripts/

Add helper scripts here for common automation tasks.

### assets/

Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from documentation
- Reference files preserve the structure and examples from source docs
- WondeL AI skills are versioned and can be pinned to specific versions

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
