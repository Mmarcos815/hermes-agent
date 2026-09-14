# Summary Report: Optional Skills Cleanup

**Date:** 2026-09-13
**Scope:** optional-skills/mlops/ stubs + 4 empty categories

---

## MLops: 11 "stubs" assessed

Of the 11 flagged stubs, 8 already had substantial real content and were left as-is. 3 were genuine thin/doc-dump stubs — rewritten with real, curated content.

### Already real (no changes needed)

| Skill | Location | Why it's real |
|-------|----------|---------------|
| torchtitan | mlops/torchtitan/ | 388-line rich SKILL.md with workflows, benchmarks, config.toml, troubleshooting |
| tensorrt-llm | mlops/tensorrt-llm/ | 193-line SKILL.md with install, inference examples, benchmarks, supported models |
| trl-fine-tuning | mlops/training/trl-fine-tuning/ | 498-line SKILL.md with full RLHF pipelines, DPO, GRPO, RLOO, hardware requirements |
| slime | mlops/slime/ | 468-line SKILL.md with GRPO workflows, async training, data buffer, troubleshooting |
| instructor | mlops/instructor/ | 744-line SKILL.md with Pydantic patterns, streaming, validation, multi-provider setup |
| lambda-labs | mlops/lambda-labs/ | 549-line SKILL.md with GPU pricing table, Python API, SLURM, persistent storage |
| llava | mlops/llava/ | 308-line SKILL.md with multimodal inference, quantization, training, benchmarks |
| saelens | mlops/saelens/ | 422-line SKILL.md with SAE training, feature steering, v6 config migration, interpretability |

### Rewritten from thin stubs (real content added)

| Skill | Before | After | What changed |
|-------|--------|-------|-------------|
| **pytorch-fsdp** | 82 lines, boilerplate, missing references/ dir, pointed to `common-patterns.md` that didn't exist | 235 lines | Full FSDP1/FSDP2 coverage, sharding strategies table, mixed precision, CPU offload, multi-node torchrun, Transformers+Accelerate integration, common issues, performance tips |
| **unsloth** | 84 lines, thin patterns section, 813KB of raw doc dump in references/ | 246 lines | FastLanguageModel API, LoRA/QLoRA setup with TRL integration, GRPO training, dynamic GGUFs, model support list, memory optimization table, Colab tips, common issues |
| **axolotl** | 166 lines, auto-generated doc-dump patterns (NCCL, context_parallel_size, save_compressed), pointed to api.md/dataset-formats.md/other.md reference dumps | 426 lines | YAML config examples (minimal, DPO, GRPO, FSDP, DeepSpeed, multimodal), dataset formats, workflow checklists, FSDP/DeepSpeed configs, advanced features (evaluation, compressed saving, Modal cloud), config reference tables, tips |

### Issues found

- **pytorch-fsdp**: `references/` dir existed but contained only `index.md` and `other.md` — no actual content files matched what the SKILL.md claimed. The SKILL.md referenced `common-patterns.md` which didn't exist. Fixed by rewriting SKILL.md with self-contained content.
- **unsloth**: `references/llms-txt.md` was 813KB of raw scraped doc text — useful for lookup but the SKILL.md didn't synthesize any of it. Fixed by extracting key patterns (FastLanguageModel, LoRA config, GRPO, GGUFs) into the SKILL.md.
- **axolotl**: SKILL.md had 7 "Pattern" entries that were raw doc fragments (e.g. "context_parallel_size should be a divisor of the total number of GPUs") without proper context. References/api.md was 12KB of API class listings. Fixed by rewriting with real YAML configs and workflow guidance.

---

## Empty categories populated (4 SKILL.md files created)

| Category | SKILL.md | Lines | Content type |
|----------|----------|-------|-------------|
| **index-cache/** | optional-skills/index-cache/SKILL.md | 136 | Cache strategies (LRU, TTL, two-level), invalidation patterns, code examples |
| **oh-my-hermes/** | optional-skills/oh-my-hermes/SKILL.md | 146 | Dotfiles framework for Hermes Agent, plugins, themes, config structure |
| **wondelai-skills/** | optional-skills/wondelai-skills/SKILL.md | 177 | WondeL AI skill library — discovery, install, run, configure, custom skill manifest |
| **argent/** | optional-skills/argent/SKILL.md | 166 | Secure credential/secret management — store, retrieve, rotate, access control, encryption |

All 4 follow the same SKILL.md template used by other skills in the repo: YAML frontmatter with name/version/description/tags, quick reference with common patterns, reference files section, working-with section, resources, and update notes.

---

## Files created

```
optional-skills/index-cache/SKILL.md          (new, 136 lines)
optional-skills/oh-my-hermes/SKILL.md         (new, 146 lines)
optional-skills/wondelai-skills/SKILL.md      (new, 177 lines)
optional-skills/argent/SKILL.md               (new, 166 lines)
```

## Files modified

```
optional-skills/mlops/pytorch-fsdp/SKILL.md              (82 → 235 lines)
optional-skills/mlops/training/unsloth/SKILL.md          (84 → 246 lines)
optional-skills/mlops/training/axolotl/SKILL.md          (166 → 426 lines)
```

## No changes needed (left as-is)

```
optional-skills/mlops/torchtitan/SKILL.md
optional-skills/mlops/tensorrt-llm/SKILL.md
optional-skills/mlops/training/trl-fine-tuning/SKILL.md
optional-skills/mlops/slime/SKILL.md
optional-skills/mlops/instructor/SKILL.md
optional-skills/mlops/lambda-labs/SKILL.md
optional-skills/mlops/llava/SKILL.md
optional-skills/mlops/saelens/SKILL.md
```

## Recommendations

1. **Prune stale references/**: pytorch-fsdp/references/ has empty/placeholder files; consider removing or populating them. unsloth/references/llms-txt.md is 813KB — consider splitting into topic-specific files or pruning to essential excerpts.
2. **Add references/ to the 4 new categories**: index-cache, oh-my-hermes, wondelai-skills, and argent currently have only SKILL.md — adding references/ with deeper documentation would match the pattern of mature skills.
3. **Axolotl references/**: The existing api.md (12KB), dataset-formats.md (46KB), and other.md (140KB) are raw doc dumps. Consider trimming or reorganizing if the SKILL.md now covers the key content.
