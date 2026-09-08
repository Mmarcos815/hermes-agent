#!/usr/bin/env python3
"""
Minimal Transformer from Scratch — Phase 1A Learning Project

Pure Python, pure math. No PyTorch, no frameworks. Every step of the
forward pass is labeled, documented, and executable.

What this demonstrates (every step between "here's a prompt" and "here's
a response"):

1. Tokenization — text → integer token IDs
2. Embedding — token IDs → dense vectors (token embedding + position embedding)
3. Multi-head attention — Q, K, V projections → split heads → scaled dot-product
   attention per head → concatenate → output projection
4. Residual connection + layer normalization
5. Feed-forward network — two linear layers with GELU activation
6. Residual connection + layer normalization
7. Output projection — back to vocabulary size → logits → softmax → probabilities
8. Top-k sampling — pick the most likely next tokens
"""

import math
import random
import json
from typing import List

# ============================================================================
# CONFIGURATION
# ============================================================================
# Small dimensions for an educational demo. A real model uses much larger
# values (GPT-2 Small: d_model=768, d_ff=3072, n_heads=12).

D_MODEL = 64        # Model dimension (hidden size)
D_FF = 256          # Feed-forward hidden dimension (typically 4x D_MODEL)
N_HEADS = 4         # Number of attention heads
D_HEAD = D_MODEL // N_HEADS  # Dimension per head (= 16)
VOCAB_SIZE = 36     # Tiny character-level vocabulary
MAX_POS = 128       # Maximum sequence length for position embeddings

# ============================================================================
# STEP 0: VOCABULARY AND TOKENIZATION
# ============================================================================
# A tokenizer maps text to integer IDs. Real models use BPE or similar;
# we use character-level for clarity.

VOCAB = {
    "<PAD>": 0, "<BOS>": 1, "<EOS>": 2, "<UNK>": 3,
    "a": 4, "b": 5, "c": 6, "d": 7, "e": 8, "f": 9, "g": 10,
    "h": 11, "i": 12, "j": 13, "k": 14, "l": 15, "m": 16, "n": 17,
    "o": 18, "p": 19, "q": 20, "r": 21, "s": 22, "t": 23, "u": 24,
    "v": 25, "w": 26, "x": 27, "y": 28, "z": 29,
    " ": 30, ".": 31, ",": 32, "!": 33, "?": 34, "\n": 35,
}
INV_VOCAB = {v: k for k, v in VOCAB.items()}

def tokenize(text: str) -> List[int]:
    """Convert text to token IDs (character-level)."""
    return [VOCAB.get(ch, VOCAB["<UNK>"]) for ch in text.lower()]

def decode(tokens: List[int]) -> str:
    """Convert token IDs back to text."""
    return "".join(INV_VOCAB.get(t, "<UNK>") for t in tokens)

# ============================================================================
# RANDOM WEIGHT INITIALIZATION
# ============================================================================
# Real models learn these. Here we use small random values for demo.

random.seed(42)

def rand_matrix(rows: int, cols: int) -> List[List[float]]:
    """Create a rows x cols matrix with small Gaussian values."""
    return [[random.gauss(0, 0.02) for _ in range(cols)] for _ in range(rows)]

def rand_vec(n: int) -> List[float]:
    """Create a vector of n small Gaussian values."""
    return [random.gauss(0, 0.02) for _ in range(n)]

# ============================================================================
# STEP 1: EMBEDDING
# ============================================================================
# Each token ID is looked up in an embedding table to produce a dense vector
# of size D_MODEL. We also add a learned position embedding so the model
# knows where each token is in the sequence.

# Token embedding: (vocab_size x d_model)
token_emb = rand_matrix(VOCAB_SIZE, D_MODEL)
# Position embedding: (max_positions x d_model)
pos_emb = rand_matrix(MAX_POS, D_MODEL)

def embed(tokens: List[int]) -> List[List[float]]:
    """
    Convert token IDs to embeddings.
    Output: list of len(tokens) vectors, each of size D_MODEL.
    Each vector = token_embedding[token_id] + position_embedding[position]
    """
    result = []
    for pos, tok_id in enumerate(tokens):
        # Start with token embedding
        vec = token_emb[tok_id][:]  # copy
        # Add position embedding
        for i in range(D_MODEL):
            vec[i] += pos_emb[min(pos, MAX_POS - 1)][i]
        result.append(vec)
    return result

# ============================================================================
# STEP 2: LINEAR PROJECTION (fully-connected layer)
# ============================================================================
# y = xW^T + b  (PyTorch convention: W is out_features x in_features)

def matmul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiply A (m x n) x B (n x p) = (m x p)."""
    m, n, p = len(A), len(A[0]), len(B[0])
    C = [[0.0] * p for _ in range(m)]
    for i in range(m):
        for j in range(p):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C

def transpose(M: List[List[float]]) -> List[List[float]]:
    """Matrix transpose."""
    r, c = len(M), len(M[0])
    return [[M[i][j] for i in range(r)] for j in range(c)]

def linear(X: List[List[float]], W: List[List[float]], b: List[float] = None) -> List[List[float]]:
    """
    Linear transformation: y = X @ W^T + b
    X: (seq_len x in_features), W: (out_features x in_features)
    Output: (seq_len x out_features)
    """
    out = matmul(X, transpose(W))
    if b:
        for i in range(len(out)):
            for j in range(len(out[0])):
                out[i][j] += b[j]
    return out

# ============================================================================
# STEP 3: SCALED DOT-PRODUCT ATTENTION
# ============================================================================
# The core attention operation:
#   Attention(Q, K, V) = softmax(Q @ K^T / sqrt(d_k)) @ V

def softmax_rows(X: List[List[float]]) -> List[List[float]]:
    """Row-wise softmax (stable: subtract max)."""
    out = []
    for row in X:
        mx = max(row)
        exps = [math.exp(x - mx) for x in row]
        s = sum(exps)
        out.append([e / s for e in exps])
    return out

def attention(Q: List[List[float]], K: List[List[float]], V: List[List[float]],
              mask: List[List[float]] = None) -> tuple:
    """
    Scaled dot-product attention.
    Q, K: (seq_len x d_k), V: (seq_len x d_v)
    Returns: (output, attention_weights)
    """
    d_k = len(Q[0])
    scores = matmul(Q, transpose(K))           # (seq_len x seq_len)
    scale = math.sqrt(d_k)
    for i in range(len(scores)):
        for j in range(len(scores[0])):
            scores[i][j] /= scale
    if mask:
        for i in range(len(mask)):
            for j in range(len(mask[0])):
                scores[i][j] += mask[i][j]      # -inf for masked positions
    weights = softmax_rows(scores)              # (seq_len x seq_len)
    output = matmul(weights, V)                # (seq_len x d_v)
    return output, weights

# ============================================================================
# STEP 4: MULTI-HEAD ATTENTION
# ============================================================================
# Split D_MODEL into N_HEADS heads, run attention independently per head,
# then concatenate and project.

def split_heads(X: List[List[float]], n_heads: int) -> List[List[List[float]]]:
    """
    Split hidden dim into n_heads separate tensors.
    Input: (seq_len x d_model)
    Return: n_heads x (seq_len x d_head)
    """
    seq_len = len(X)
    d_head = D_MODEL // n_heads
    heads = []
    for h in range(n_heads):
        head = []
        for pos in range(seq_len):
            start = h * d_head
            head.append(X[pos][start:start + d_head])
        heads.append(head)
    return heads

def concat_heads(heads: List[List[List[float]]]) -> List[List[float]]:
    """Concatenate n_heads x (seq_len x d_head) -> (seq_len x d_model)."""
    seq_len = len(heads[0])
    n_heads = len(heads)
    d_head = len(heads[0][0])
    result = []
    for pos in range(seq_len):
        vec = []
        for h in range(n_heads):
            vec.extend(heads[h][pos])
        result.append(vec)
    return result

def multi_head_attention(X: List[List[float]],
                         W_q: List[List[float]], W_k: List[List[float]],
                         W_v: List[List[float]], W_o: List[List[float]],
                         mask: List[List[float]] = None) -> tuple:
    """
    Multi-head attention with residual projection.
    X: (seq_len x d_model)
    W_q, W_k, W_v: (d_model x d_model) — project to Q, K, V
    W_o: (d_model x d_model) — output projection after concat
    Returns: (output, all_head_attention_weights)
    """
    seq_len = len(X)

    # Linear projections
    Q = linear(X, W_q)   # (seq_len x d_model)
    K = linear(X, W_k)
    V = linear(X, W_v)

    # Split into heads
    q_heads = split_heads(Q, N_HEADS)
    k_heads = split_heads(K, N_HEADS)
    v_heads = split_heads(V, N_HEADS)

    # Attention per head
    head_outputs = []
    all_weights = []
    for h in range(N_HEADS):
        out, weights = attention(q_heads[h], k_heads[h], v_heads[h], mask)
        head_outputs.append(out)
        all_weights.append(weights)

    # Concatenate
    concat = concat_heads(head_outputs)

    # Output projection
    output = linear(concat, W_o)

    return output, all_weights

# ============================================================================
# STEP 5: FEED-FORWARD NETWORK
# ============================================================================
# FFN(x) = GELU(x @ W1^T + b1) @ W2^T + b2
# Two linear layers with GELU activation in between.

def gelu(x: float) -> float:
    """GELU activation (Gaussian Error Linear Unit)."""
    return 0.5 * x * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x**3)))

def ff(x: List[List[float]],
       W1: List[List[float]], b1: List[float],
       W2: List[List[float]], b2: List[float]) -> List[List[float]]:
    """
    Feed-forward network.
    W1: (d_ff x d_model), b1: (d_ff,)
    W2: (d_model x d_ff), b2: (d_model,)
    """
    h = linear(x, W1, b1)           # (seq_len x d_ff)
    h = [[gelu(v) for v in row] for row in h]  # GELU activation
    out = linear(h, W2, b2)         # (seq_len x d_model)
    return out

# ============================================================================
# STEP 6: LAYER NORMALIZATION
# ============================================================================
# Normalize each position (row) independently across features.

def layernorm(X: List[List[float]], gamma: List[float], beta: List[float],
              eps: float = 1e-5) -> List[List[float]]:
    """
    LayerNorm: y = gamma * (x - mean) / sqrt(var + eps) + beta
    Applied independently to each position (row).
    gamma, beta: vectors of size D_MODEL (learned scale and shift).
    """
    result = []
    for row in X:
        mean = sum(row) / len(row)
        var = sum((v - mean)**2 for v in row) / len(row)
        std = math.sqrt(var + eps)
        normalized = [(v - mean) / std for v in row]
        result.append([g * n + b for g, n, b in zip(gamma, normalized, beta)])
    return result

# ============================================================================
# STEP 7: RESIDUAL CONNECTION + LAYER NORM
# ============================================================================
# Every sub-layer (attention, FFN) is wrapped:
#   output = LayerNorm(x + SubLayer(x))

def residual_norm(x: List[List[float]], sub_out: List[List[float]],
                  gamma: List[float], beta: List[float]) -> List[List[float]]:
    """Residual connection + layer norm."""
    added = []
    for i in range(len(x)):
        added.append([x[i][j] + sub_out[i][j] for j in range(len(x[0]))])
    return layernorm(added, gamma, beta)

# ============================================================================
# STEP 8: ONE TRANSFORMER BLOCK
# ============================================================================
# A single transformer block = MHA -> Residual+Norm -> FFN -> Residual+Norm

def transformer_block(x: List[List[float]],
                      W_q, W_k, W_v, W_o,
                      W1, b1, W2, b2,
                      ln1_g, ln1_b, ln2_g, ln2_b,
                      mask: List[List[float]] = None) -> List[List[float]]:
    """
    One transformer decoder block (causal/self-attention).
    """
    # Sub-layer 1: Multi-head attention
    mha_out, _ = multi_head_attention(x, W_q, W_k, W_v, W_o, mask)
    x = residual_norm(x, mha_out, ln1_g, ln1_b)

    # Sub-layer 2: Feed-forward network
    ff_out = ff(x, W1, b1, W2, b2)
    x = residual_norm(x, ff_out, ln2_g, ln2_b)

    return x

# ============================================================================
# STEP 9: CAUSAL MASK (for autoregressive generation)
# ============================================================================
# A causal mask prevents each position from attending to future positions.
# mask[i][j] = -inf when j > i, 0 otherwise.

def causal_mask(seq_len: int) -> List[List[float]]:
    """Create a lower-triangular mask (prevents attending to future)."""
    mask = []
    for i in range(seq_len):
        row = []
        for j in range(seq_len):
            row.append(float('-inf') if j > i else 0.0)
        mask.append(row)
    return mask

# ============================================================================
# STEP 10: LANGUAGE MODEL HEAD (output projection to vocab)
# ============================================================================
# After the transformer blocks, project back to vocabulary size to get
# logits for each position. Apply softmax to get probabilities.

def lm_head(x: List[List[float]], W: List[List[float]]) -> List[List[float]]:
    """Project hidden states to vocabulary logits."""
    return linear(x, W)

# ============================================================================
# FULL FORWARD PASS DEMO
# ============================================================================

def demo():
    print("=" * 60)
    print("MINIMAL TRANSFORMER - FULL FORWARD PASS DEMO")
    print("=" * 60)

    # --- Create all weight matrices ---
    # These are random for demo. A real model has learned weights.

    # Attention projections (one block)
    W_q = rand_matrix(D_MODEL, D_MODEL)
    W_k = rand_matrix(D_MODEL, D_MODEL)
    W_v = rand_matrix(D_MODEL, D_MODEL)
    W_o = rand_matrix(D_MODEL, D_MODEL)

    # FFN projections
    W1 = rand_matrix(D_FF, D_MODEL)            # expands: d_model -> d_ff
    b1 = rand_vec(D_FF)
    W2 = rand_matrix(D_MODEL, D_FF)            # projects back: d_ff -> d_model
    b2 = rand_vec(D_MODEL)

    # Layer norm parameters (gamma=1, beta=0 initially)
    ln1_g = [1.0] * D_MODEL
    ln1_b = [0.0] * D_MODEL
    ln2_g = [1.0] * D_MODEL
    ln2_b = [0.0] * D_MODEL

    # LM head (project to vocab)
    lm_w = rand_matrix(VOCAB_SIZE, D_MODEL)

    # --- Input ---
    prompt = "hello"
    tokens = tokenize(prompt)
    print(f"\nInput prompt: '{prompt}'")
    print(f"Tokenized: {tokens}")
    print(f"  '{prompt}' = {[INV_VOCAB.get(t, '?') for t in tokens]}")
    print(f"Sequence length: {len(tokens)}")

    # --- Embed ---
    x = embed(tokens)
    print(f"\n[1] Embedding: {len(x)} positions x {len(x[0])} dims")
    print(f"  (token embedding + position embedding)")

    # --- Causal mask ---
    mask = causal_mask(len(tokens))
    print(f"\n[2] Causal mask: {len(mask)}x{len(mask[0])} (lower triangular)")

    # --- Transformer block ---
    x = transformer_block(
        x,
        W_q, W_k, W_v, W_o,
        W1, b1, W2, b2,
        ln1_g, ln1_b, ln2_g, ln2_b,
        mask=mask,
    )
    print(f"\n[3] After 1 transformer block: {len(x)} positions x {len(x[0])} dims")
    print(f"  MHA (4 heads x 16 dims) -> Residual+Norm -> FFN (64->256->64) -> Residual+Norm")

    # --- Language model head ---
    logits = lm_head(x, lm_w)
    print(f"\n[4] LM head: {len(logits)} positions x {len(logits[0])} vocab entries")
    print(f"  (project from {D_MODEL} -> {VOCAB_SIZE} dimensions)")

    # --- Softmax -> probabilities for last position ---
    last_logits = logits[-1]
    probs = softmax_rows([last_logits])[0]
    print(f"\n[5] Softmax over vocab for last position")
    print(f"  Sum of probabilities: {sum(probs):.6f} (should be 1.0)")

    # --- Top-5 predictions ---
    top5 = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:5]
    print(f"\n[6] Top-5 next-token predictions:")
    for rank, idx in enumerate(top5, 1):
        ch = INV_VOCAB.get(idx, "<UNK>")
        print(f"  #{rank}: '{ch}' (id={idx:2d}, prob={probs[idx]:.4f})")

    # --- Parameter count ---
    params = 0
    params += VOCAB_SIZE * D_MODEL        # token embedding
    params += MAX_POS * D_MODEL           # position embedding
    params += D_MODEL * D_MODEL * 4      # Q, K, V, O (attention)
    params += D_FF * D_MODEL + D_FF      # W1 + b1
    params += D_MODEL * D_FF + D_MODEL   # W2 + b2
    params += D_MODEL * 2 * 2            # 2 layer norms x (gamma + beta)
    params += VOCAB_SIZE * D_MODEL       # LM head
    print(f"\n[7] Parameter count (1 block): {params:,} ({params / 1_000_000:.2f}M)")
    print(f"  GPT-2 Small (124M):       124,000,000")
    print(f"  Llama 2 7B:               7,000,000,000")
    print(f"  This demo (1 block):      {params:,}")

    print(f"\n{'=' * 60}")
    print("FULLY WORKING FORWARD PASS - EVERY STEP EXECUTED")
    print(f"{'=' * 60}")
    print("""
WHAT THIS DEMONSTRATES (every step between prompt and prediction):

  TOKENIZATION -> EMBEDDING -> MULTI-HEAD ATTENTION (with causal mask)
  -> RESIDUAL CONNECTION + LAYER NORM -> FEED-FORWARD NETWORK
  -> RESIDUAL CONNECTION + LAYER NORM -> LM HEAD -> SOFTMAX -> TOP-K

This is ONE block. Real models stack many blocks (GPT-2: 12, Llama: 32-40).
Also missing from this demo for brevity: training, RoPE, KV caching,
and proper weight initialization. But the core computation is correct.

To go deeper from here:
  1. Stack multiple blocks (loop the transformer_block call)
  2. Add RoPE positional encoding (rotate Q and K by position)
  3. Add KV caching for efficient autoregressive generation
  4. Train on real text (minimally: one batch, one step, watch loss drop)
  5. Read "Attention Is All You Need" (Vaswani et al. 2017) end-to-end
""")

if __name__ == "__main__":
    demo()
