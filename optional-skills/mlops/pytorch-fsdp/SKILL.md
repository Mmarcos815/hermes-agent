---
name: pytorch-fsdp
description: Fully Sharded Data Parallel training for large models with PyTorch.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [torch>=2.4, transformers>=4.40, accelerate>=0.34]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Distributed Training, PyTorch, FSDP, FSDP2, ZeRO, Sharding, Mixed Precision, CPU Offloading, Large-Scale Training, Memory Optimization]

---

# PyTorch FSDP — Fully Sharded Data Parallel

FSDP shards model parameters, gradients, and optimizer states across data-parallel ranks, letting you train models that wouldn't fit on a single GPU. FSDP2 (PyTorch 2.4+) is the current generation; FSDP1 is legacy.

## When to Use FSDP

**Use FSDP when:**
- Model doesn't fit on one GPU even with activation checkpointing
- You need data parallelism at scale (multi-GPU, multi-node)
- You want full control over sharding strategy
- Working directly with PyTorch (not via higher-level trainers)

**Use alternatives when:**
- **DeepSpeed ZeRO**: Need stage 1-3 optimization with offload; broader ecosystem
- **Accelerate's `Trainer`**: Want a one-line API wrapping FSDP
- **Megatron-LM**: Need tensor/pipeline parallelism in addition to data parallelism
- **FSDP2 specific**: Already on PyTorch 2.4+ and want simplified API

## Quick start

### FSDP2 (PyTorch 2.4+, recommended)

```python
import torch
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.fully_sharded_data_parallel import ShardingStrategy

# Wrap model — shards params, gradients, optimizer states
model = FSDP(
    model,
    sharding_strategy=ShardingStrategy.FULL_SHARD,  # default: shard all
    device_id=torch.cuda.current_device(),
    mixed_precision=torch.autocast,  # optional BF16
)

# Standard training loop — FSDP handles sharding transparently
output = model(inputs)
loss = criterion(output, targets)
loss.backward()
# Optionally: model.optim_step(optimizer)  # FSDP-optimized step
optimizer.step()
optimizer.zero_grad()
```

### FSDP1 (legacy, PyTorch <2.4)

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import ShardingStrategy, MixedPrecision, CPUOffload

model = FSDP(
    model,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    device_id=torch.cuda.current_device(),
    mixed_precision=MixedPrecision(param_dtype=torch.bfloat16),
    cpu_offload=CPUOffload(offload_params=True),  # offload params to CPU
)
```

### with Transformers + Accelerate

```python
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments
from accelerate import Accelerator

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")

training_args = TrainingArguments(
    output_dir="./outputs",
    per_device_train_batch_size=4,
    fsdp="full_shard auto_wrap",
    fsdp_config={
        "fsdp_min_num_params": 1e8,
        "fsdp_transformer_layer_cls_to_wrap": "LlamaDecoderLayer",
        "fsdp_grad_cache": True,  # reduce memory at cost of recompute
    },
    bf16=True,
    gradient_checkpointing=True,
)

trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
trainer.train()
```

## Sharding strategies

| Strategy | What's sharded | VRAM per GPU | Communication |
|----------|---------------|--------------|---------------|
| `FULL_SHARD` | Params + grads + optimizer | Lowest | Highest |
| `SHARD_GRAD_OP` | Gradients + optimizer (params replicated) | Medium | Medium |
| `NO_SHARD` | Nothing (DDP-equivalent) | Highest | Lowest |

**Rule of thumb**: Use `FULL_SHARD` unless you have a specific reason (e.g. small model where communication overhead dominates).

### Auto-wrap policy

Control which modules are wrapped as FSDP units. Smaller units = more fine-grained sharding but more communication.

```python
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy
from transformers.models.llama.modeling_llama import LlamaDecoderLayer

auto_wrap_policy = functools.partial(
    transformer_auto_wrap_policy,
    transformer_layer_cls={LlamaDecoderLayer},
)

model = FSDP(model, auto_wrap_policy=auto_wrap_policy, ...)
```

## Key configuration

### Mixed precision

```python
# BF16 (recommended on A100/H100/B200)
MixedPrecision(param_dtype=torch.bfloat16, reduce_dtype=torch.bfloat16, output_dtype=torch.bfloat16)

# FP16 (older hardware)
MixedPrecision(param_dtype=torch.float16, reduce_dtype=torch.float16, output_dtype=torch.float16)
```

### CPU offload (when GPU memory is tight)

```python
CPUOffload(offload_params=True,  # params stay on CPU, loaded on demand
           offload_grads=True,   # gradients offloaded after backward
           pin_memory=True)      # faster transfer
```

⚠️ Offloading slows training ~2-5x. Use only when you can't fit on GPU.

### Activation checkpointing

Combine with FSDP for large models:

```python
model.gradient_checkpointing_enable()
# or per-module
from torch.utils.checkpoint import checkpoint
output = checkpoint(module, input)
```

## Multi-node training

```bash
# torchrun (PyTorch native)
torchrun --nnodes=4 --nproc_per_node=8 --rdzv_backend=c10d \
  --rdzv_endpoint=$MASTER_ADDR:29500 train_fsdp.py
```

```python
# train_fsdp.py
import torch.distributed as dist
dist.init_process_group("nccl")
# ... FSDP setup ...
```

### Resuming from checkpoint

```python
# Save
torch.save(model.state_dict(), "fsdp_checkpoint.pt")

# Load (must be same sharding strategy)
model.load_state_dict(torch.load("fsdp_checkpoint.pt"))
```

### Converting FSDP checkpoint to full model

```python
from torch.distributed.checkpoint import FileSystemWriter, load
from torch.distributed.checkpoint.state_dict import get_state_dict

# FSDP shards are reassembled by load() when rank=0
state_dict = get_state_dict(model, ...
```

## Common issues

### OOM despite FSDP

1. Enable activation checkpointing: `model.gradient_checkpointing_enable()`
2. Reduce micro-batch size, increase gradient accumulation
3. Use `SHARD_GRAD_OP` instead of `FULL_SHARD` (trades VRAM for communication)
4. Enable CPU offload as last resort: `CPUOffload(offload_params=True)`
5. Mixed precision: BF16 cuts activation memory ~50% vs FP32

### Slow training (communication bottleneck)

- Increase `fsdp_min_num_params` to wrap larger modules (fewer all-reduce calls)
- Use `fsdp_grad_cache=True` to reduce communication at cost of recompute
- Check network: NCCL tests with `torch.distributed.all_reduce` benchmark
- Ensure GPUs are on same node (NVLink/PCIe) before multi-node

### Checkpoints not loading after config change

- FSDP checkpoints are sharded; they must be loaded with the **same** FSDP config
- To get a consolidated checkpoint: save with `FSDP(..., state_dict_type="full"` or use `torch.distributed.checkpoint` consolidation APIs

### CUDA OOM on backward pass

- FSDP shards parameters but activations are still per-GPU
- Enable activation checkpointing
- Reduce sequence length or batch size
- Use `fsdp_grad_cache=True` (stores activations in a compressed form)

## Performance tips

1. **BF16 over FP32**: 2x memory, often faster on modern GPUs
2. **Larger wrap policy**: Fewer FSDP units → less communication overhead
3. **Gradient accumulation**: Effective large batch without large per-GPU memory
4. **Benchmark sharding strategies**: `FULL_SHARD` isn't always fastest
5. **NCCL tuning**: `NCCL_SOCKET_IFNAME`, `NCCL_P2P_DISABLE` for debugging

## References

- PyTorch FSDP docs: https://pytorch.org/docs/stable/fsdp.html
- FSDP2 migration guide: https://pytorch.org/docs/stable/fsdp.html#fsdp2
- HuggingFace FSDP guide: https://huggingface.co/docs/transformers/perf_train_gpu_parallelism
- DeepSpeed ZeRO comparison: https://www.deepspeed.com/tutorials/zero/
