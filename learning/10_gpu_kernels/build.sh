#!/usr/bin/env bash
# Build script for the minimal CUDA vector add kernel.
# Produces a shared library (vector_add.so / vector_add.dll) that can be
# loaded from Python via ctypes.
#
# Usage: ./build.sh
# Requirements: nvcc on PATH, a CUDA-capable GPU (not needed to compile).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Compiling vector_add.cu ..."
nvcc -O2 \
     -shared \
     -Xcompiler -fPIC \
     -o vector_add.so \
     vector_add.cu

echo "==> Build complete: $SCRIPT_DIR/vector_add.so"
