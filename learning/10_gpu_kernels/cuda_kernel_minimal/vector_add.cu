/*
 * Minimal CUDA Vector Add Kernel
 * 
 * Computes C = A + B for three float vectors of length N.
 * Each thread computes one element of the output.
 * 
 * Build: nvcc -O2 -shared -Xcompiler -fPIC -o vector_add.so vector_add.cu
 */

#include <cuda_runtime.h>
#include <stdio.h>

/* The kernel: one thread per element */
__global__ void vector_add_kernel(const float* __restrict__ a,
                                  const float* __restrict__ b,
                                  float* __restrict__ c,
                                  int n)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

/* Host wrapper exposed for ctypes / Python integration.
 * Allocates device memory, copies input, launches kernel, copies result back.
 * Returns 0 on success, non-zero on CUDA error.
 */
extern "C" int vector_add(const float* h_a, const float* h_b, float* h_c, int n)
{
    if (n <= 0) return -1;

    size_t bytes = (size_t)n * sizeof(float);

    float *d_a = nullptr, *d_b = nullptr, *d_c = nullptr;

    cudaError_t err;
    err = cudaMalloc(&d_a, bytes);
    if (err != cudaSuccess) return -2;
    err = cudaMalloc(&d_b, bytes);
    if (err != cudaSuccess) { cudaFree(d_a); return -3; }
    err = cudaMalloc(&d_c, bytes);
    if (err != cudaSuccess) { cudaFree(d_a); cudaFree(d_b); return -4; }

    err = cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice);
    if (err != cudaSuccess) goto cleanup;
    err = cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice);
    if (err != cudaSuccess) goto cleanup;

    /* Launch configuration: 256 threads per block, enough blocks to cover n */
    int block_size = 256;
    int grid_size  = (n + block_size - 1) / block_size;
    vector_add_kernel<<<grid_size, block_size>>>(d_a, d_b, d_c, n);

    err = cudaGetLastError();          /* catch launch errors */
    if (err != cudaSuccess) goto cleanup;

    err = cudaMemcpy(h_c, d_c, bytes, cudaMemcpyDeviceToHost);

cleanup:
    cudaFree(d_a);
    cudaFree(d_b);
    cudaFree(d_c);

    return (err == cudaSuccess) ? 0 : -5;
}
