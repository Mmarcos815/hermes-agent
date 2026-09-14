---
name: argent
description: "Argent — secure credential and secret management for Hermes Agent workflows."
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Security, Credentials, Secrets, Vault, Authentication, Encryption, Key Management]

---

# Argent Skill

Argent is a secure credential and secret management system for Hermes Agent workflows. It provides encrypted storage, access control, rotation policies, and audit logging for API keys, tokens, certificates, and other sensitive credentials used across Hermes skills and automations.

## When to Use This Skill

This skill should be triggered when:
- Storing or retrieving API keys, tokens, or secrets securely
- Managing credential rotation policies
- Setting up access control for sensitive credentials
- Auditing secret access and usage
- Integrating credential management into Hermes workflows
- Migrating from plaintext .env files to encrypted storage

## Quick Reference

### Common Patterns

**Pattern 1: Store a secret**

```bash
# Store an API key with metadata
argent secrets set \
  --name openai-api-key \
  --value "$OPENAI_API_KEY" \
  --label "OpenAI API Key" \
  --tags production,llm \
  --expires 90d \
  --access-team ai-team
```

**Pattern 2: Retrieve a secret in a workflow**

```bash
# Get secret value (logs warning if accessed outside allowed context)
argent secrets get openai-api-key

# Use in a script (value masked in logs)
export API_KEY=$(argent secrets get openai-api-key --export)
```

**Pattern 3: Secret rotation**

```bash
# Schedule automatic rotation
argent secrets rotate openai-api-key \
  --schedule "0 3 * * 0" \
  --command "./rotate-openai-key.sh" \
  --notify slack://#secrets-alerts
```

**Pattern 4: Access control**

```bash
# Grant a team access to a secret
argent access grant openai-api-key --team ai-team --permission read

# Revoke access
argent access revoke openai-api-key --team ai-team

# Audit who accessed a secret
argent audit openai-api-key --last 7d
```

### Credential types

| Type | Use case | Rotation support |
|------|----------|-----------------|
| `api-key` | Static API keys | Manual or scripted rotation |
| `oauth-token` | OAuth bearer tokens | Auto-refresh via callback |
| `certificate` | TLS/SSL certificates | Expiry monitoring + renewal |
| `ssh-key` | SSH private keys | Manual rotation |
| `database-cred` | DB usernames/passwords | Auto-rotate with DB integration |
| `uuid` | Non-secret identifiers | N/A (public) |

### Encryption

Argent encrypts all secrets at rest using AES-256-GCM. The master key is derived from a combination of:
- A user-provided passphrase (or hardware security key)
- A machine-specific salt stored in the argent config directory
- Argon2id key derivation (memory-hard)

```bash
# Export encrypted backup
argent backup export --output argent-backup-2026-09-13.enc

# Import from backup
argent backup import --input argent-backup-2026-09-13.enc
```

## Reference Files

This skill includes reference documentation in `references/`:

- **getting-started.md** - First-time setup and basic usage
- **secret-types.md** - All supported credential types and their options
- **access-control.md** - Roles, teams, permissions, and policies
- **rotation.md** - Rotation policies, scheduling, and hooks
- **encryption.md** - Encryption architecture and key management
- **cli-reference.md** - Complete CLI command reference
- **integration.md** - Integrating Argent with Hermes skills and workflows
- **migration.md** - Migrating from .env files and other secret stores

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners

Start with `argent init` to create your vault, then `argent secrets set` to add your first credential. See references/getting-started.md for a walkthrough.

### For Specific Features

- Secret types: See references/secret-types.md
- Access control: See references/access-control.md
- Rotation: See references/rotation.md
- CLI commands: See references/cli-reference.md

### For Code Examples

The quick reference above shows common CLI patterns for storing, retrieving, and rotating secrets.

## Resources

### references/

Organized documentation extracted from official sources. These files contain:
- Detailed setup walkthroughs
- Secret type reference with all options
- Access control policy language
- Rotation hook examples
- Encryption architecture details
- Complete CLI reference

### scripts/

Add helper scripts here for common automation tasks.

### templates/

Add credential rotation templates and policy templates here.

## Notes

- This skill was automatically generated from documentation
- Reference files preserve the structure and examples from source docs
- Argent secrets are never logged in plaintext — values are masked as `[REDACTED]`

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
