#!/usr/bin/env python3
"""
PyTorch Integration for CUDA Vector Add Kernel
Loads the compiled .so via ctypes, benchmarks vs pure PyTorch

Usage:
    python pytorch_integration.py              # Run benchmarks
    python pytorch_integration.py --info       # Show CUDA device info
    python pytorch_integration.py --test       # Verify correctness
"""

import argparse
import ctypes
import os
import platform
import sys
import time
from pathlib import Path


def load_cuda_kernel():
    """Load the compiled CUDA shared library."""
    so_path = Path(__file__).parent / "vector_add.so"
    if not so_path.exists():
        print(f"[ERROR] {so_path} not found. Build first: bash build.sh")
        return None

    lib = ctypes.CDLL(str(so_path))

    # Setup function signatures
    lib.vector_add.restype = ctypes.c_int
    lib.vector_add.argtypes = [
        ctypes.POINTER(ctypes.c_float),  # a
        ctypes.POINTER(ctypes.c_float),  # b
        ctypes.POINTER(ctypes.c_float),  # c
        ctypes.c_int,                     # n
    ]

    lib.get_device_count.restype = ctypes.c_int
    lib.get_device_count.argtypes = []

    lib.get_device_name.restype = ctypes.c_int
    lib.get_device_name.argtypes = [ctypes.c_char_p, ctypes.c_int]

    return lib


def cuda_vector_add(lib, a, b):
    """Call the CUDA kernel via ctypes."""
    import numpy as np

    n = len(a)
    a_flat = np.ascontiguousarray(a.flatten(), dtype=np.float32)
    b_flat = np.ascontiguousarray(b.flatten(), dtype=np.float32)
    c_flat = np.zeros_like(a_flat)

    a_ptr = a_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    b_ptr = b_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    c_ptr = c_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    ret = lib.vector_add(a_ptr, b_ptr, c_ptr, ctypes.c_int(n))
    if ret != 0:
        raise RuntimeError(f"CUDA kernel failed with code {ret}")

    return c_flat.reshape(a.shape)


def pytorch_vector_add(a, b):
    """Pure PyTorch implementation."""
    import torch

    if isinstance(a, list):
        a = torch.tensor(a, dtype=torch.float32)
    if isinstance(b, list):
        b = torch.tensor(b, dtype=torch.float32)

    return a + b


def benchmark_cuda(lib, sizes=None):
    """Benchmark CUDA kernel vs PyTorch at various sizes."""
    import numpy as np

    if sizes is None:
        sizes = [100, 1000, 10000, 100000, 1000000]

    print(f"\n{'Size':>12} | {'CUDA (ms)':>12} | {'PyTorch (ms)':>14} | {'Speedup':>8}")
    print("-" * 60)

    for size in sizes:
        a = np.random.randn(size).astype(np.float32)
        b = np.random.randn(size).astype(np.float32)

        # CUDA benchmark
        start = time.perf_counter()
        for _ in range(10):
            result_cuda = cuda_vector_add(lib, a, b)
        cuda_time = (time.perf_counter() - start) / 10 * 1000

        # PyTorch benchmark
        start = time.perf_counter()
        for _ in range(10):
            result_torch = pytorch_vector_add(a, b)
        torch_time = (time.perf_counter() - start) / 10 * 1000

        speedup = torch_time / cuda_time if cuda_time > 0 else float('inf')
        print(f"{size:>12} | {cuda_time:>10.3f}ms | {torch_time:>12.3f}ms | {speedup:>6.2f}x")


def verify_correctness(lib):
    """Verify CUDA kernel produces correct results."""
    import numpy as np

    print("\n=== Correctness Verification ===")
    sizes = [1, 10, 100, 1000, 10000]
    all_pass = True

    for size in sizes:
        a = np.random.randn(size).astype(np.float32)
        b = np.random.randn(size).astype(np.float32)

        result_cuda = cuda_vector_add(lib, a, b)
        result_numpy = a + b

        # Check with tolerance
        if np.allclose(result_cuda, result_numpy, atol=1e-5):
            print(f"  Size {size:>6}: PASS")
        else:
            max_diff = np.max(np.abs(result_cuda - result_numpy))
            print(f"  Size {size:>6}: FAIL (max diff: {max_diff})")
            all_pass = False

    print()
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")

    return all_pass


def print_device_info(lib):
    """Print CUDA device information."""
    print("\n=== CUDA Device Info ===")
    count = lib.get_device_count()
    print(f"  Device count: {count}")

    if count > 0:
        name_buf = ctypes.create_string_buffer(256)
        lib.get_device_name(name_buf, 256)
        print(f"  Device 0: {name_buf.value.decode()}")


def main():
    parser = argparse.ArgumentParser(description="PyTorch CUDA Integration")
    parser.add_argument("--info", action="store_true", help="Show CUDA device info")
    parser.add_argument("--test", action="store_true", help="Verify correctness")
    parser.add_argument("--bench", action="store_true", help="Run benchmarks")
    args = parser.parse_args()

    lib = load_cuda_kernel()
    if lib is None:
        sys.exit(1)

    if args.info:
        print_device_info(lib)
        return

    if args.test:
        verify_correctness(lib)
        return

    if args.bench:
        benchmark_cuda(lib)
        return

    # Default: info + correctness + benchmark
    print_device_info(lib)
    verify_correctness(lib)
    benchmark_cuda(lib)


if __name__ == "__main__":
    main()
