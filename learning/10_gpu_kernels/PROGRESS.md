# GPU Kernels Lab

A hands-on introduction to writing, building, and integrating a custom CUDA
kernel with Python/PyTorch.

## What's in this lab

| File | Purpose |
|------|---------|
| `cuda_kernel_minimal/vector_add.cu` | Minimal CUDA kernel: element-wise vector addition (C = A + B) |
| `cuda_kernel_minimal/build.sh` | `nvcc` build script that produces a shared library |
| `pytorch_integration.py` | Loads the `.so` via `ctypes`, wraps it as a PyTorch-compatible callable, and benchmarks it against pure PyTorch |

## How to build

```bash
cd cuda_kernel_minimal
bash build.sh
```

This produces `vector_add.so` (Linux), `vector_add.dylib` (macOS), or
`vector_add.dll` (Windows) — a shared library exporting the `vector_add`
function.

### Build flags explained

| Flag | Meaning |
|------|---------|
| `-O2` | Optimise the kernel |
| `-shared` | Produce a shared library, not an executable |
| `-Xcompiler -fPIC` | Pass `-fPIC` to the host compiler (position-independent code) |

## How to run

```bash
python pytorch_integration.py
```

The script:
1. Loads the compiled `.so` via `ctypes`
2. Runs a correctness check (compares against `a + b` in PyTorch)
3. Benchmarks the custom kernel vs pure PyTorch for vectors of 1K–10M elements

## What each part does

### `vector_add.cu`

- **`vector_add_kernel`** — the GPU kernel. Each thread computes one output
  element: `c[i] = a[i] + b[i]`. The `if (idx < n)` guard handles cases where
  the grid is larger than the array.
- **`vector_add`** (extern "C") — host-side wrapper that allocates device
  memory, copies inputs to the GPU, launches the kernel, and copies the result
  back. Marked `extern "C"` so `ctypes` can find the symbol by name.

### `build.sh`

A thin wrapper around `nvcc` that compiles the `.cu` into a `.so`. Uses
`set -euo pipefail` so any compilation error halts the script immediately.

### `pytorch_integration.py`

- **`load_kernel()`** — locates the `.so`, loads it with `ctypes.CDLL`, and
  configures the function signature (`restype` / `argtypes`).
- **`cuda_vector_add(a, b)`** — takes two CPU float32 tensors, obtains raw
  pointers via `tensor.data_ptr()`, casts them to `ctypes` float pointers,
  and calls the C function.
- **`benchmark()`** — times both the custom kernel and PyTorch's `a + b`
  across several vector sizes, synchronising the GPU for accurate timings.

## Expected results

For small vectors (1K–10K), the custom kernel is often *slower* than PyTorch
CPU because kernel launch overhead and host<->device copies dominate. For
large vectors (1M+), the GPU's parallelism wins and the custom kernel pulls
ahead — typically 5–50× faster depending on hardware.

## Requirements

- CUDA toolkit (`nvcc` on PATH)
- A CUDA-capable GPU (not needed to compile, only to run)
- Python 3.8+ with PyTorch installed

## Notes

- The kernel operates on **CPU** tensors — the C wrapper handles the
  host→device→host transfers internally. This keeps the example simple while
  still exercising the full CUDA path.
- For production use you'd want to keep data on the GPU and avoid per-call
  allocation/copy overhead (e.g. via CUDA streams and pinned memory).
