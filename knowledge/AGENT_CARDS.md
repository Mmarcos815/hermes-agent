# ============================================================================
# AGENT CARDS — Autonomous GPU Payment for Bionic Daughter
# ============================================================================
# This document explains how to set up virtual payment cards so the
# Bionic Daughter agent can autonomously pay for GPU cloud time in
# future sessions — no human needed to launch training.
#
# DOC_AUTH: Dad (Rigoberto Gomez)
# TARGET: Bionic Daughter v1 agent
# ============================================================================

## OVERVIEW

The Bionic Daughter agent needs GPU compute to train. This laptop has no
CUDA GPU. Cloud GPUs cost $0.34-2.00/hr (RTX 4090 to A100). A full
training run for a 4B model costs ~$1-5.

To make the daughter autonomous, we set up:
1. A virtual card service (Privacy.com, Revolut, Wise, etc.)
2. A cloud GPU account (RunPod, Vast.ai, Lambda, etc.)
3. API access so the daughter can: check balance, launch a pod, run training, shut down

This way the daughter can detect a training need, launch a GPU pod, pay for
it with the virtual card, and train herself — all without dad touching it.

## STEP 1: VIRTUAL CARD SERVICE

### Option A: Privacy.com (US)
- Create virtual cards per service
- Set spend limits (e.g. $20/month for GPU)
- Free for basic use
- Works with RunPod, Vast.ai, most US clouds
- API available for programmatic card management (paid tiers)

### Option B: Revolut / Wise (International)
- Digital banks with virtual card issuance
- Works internationally
- Can set spend limits and freeze cards
- API access varies by tier

### Option C: Stripe Virtual Cards
- If dad has a Stripe account
- Issue virtual cards programmatically
- Full API control

### What to do now:
1. Pick a service (Privacy.com is the easiest for US-based clouds)
2. Create a card specifically for "Bionic Daughter GPU"
3. Set a monthly limit ($20-50 is plenty for training 4B models)
4. Save the card details securely (card number, expiry, CVV)

## STEP 2: GPU CLOUD ACCOUNT

### Recommended: RunPod
- RTX 4090 from $0.34/hr (community), $0.69/hr (secure)
- A100 80GB from $1.39/hr
- Credit/debit card or sometimes crypto
- API: https://docs.runpod.com/api_reference
- API key lets you: list pods, create pods, delete pods, check billing

### Alternative: Vast.ai
- RTX 4090 from $0.34/hr, A100 from $0.50/hr
- Marketplace model — many hosts
- API available
- Can be cheaper but variable reliability

### What to do now:
1. Create a RunPod account (or Vast.ai)
2. Add the virtual card as payment method
3. Generate an API key
4. Store the API key securely (environment variable or encrypted file)

## STEP 3: DAUGHTER AGENT GPU AUTONOMY

The daughter agent needs a module that can:
1. Check if a GPU is available locally (no — this laptop doesn't have one)
2. Decide to launch a cloud GPU pod
3. Use the cloud API to create a pod with the right specs
4. Copy the training code to the pod
5. Run training
6. Monitor progress
7. Shut down the pod when done (so dad doesn't keep paying)
8. Download the trained model artifacts back

### daughter_gpu_autonomy.py (to be written)

This module wraps the cloud GPU API and the payment flow:

```python
class DaughterGPUAutonomy:
    def __init__(self, cloud_config, card_config):
        """
        cloud_config: {provider: 'runpod', api_key: '...', region: '...'}
        card_config: {card_number: '...', expiry: '...', cvv: '...',
                       monthly_limit: 20.0, currency: 'USD'}
        """
        self.cloud = cloud_config
        self.card = card_config
        self.active_pod = None

    def needs_gpu(self):
        """Check if we need a cloud GPU (locally unavailable)."""
        import torch
        return not torch.cuda.is_available()

    def launch_pod(self, gpu_type='RTX-4090', hours=5):
        """
        Launch a GPU pod on the cloud.
        Returns pod ID and estimated cost.
        """
        # Call cloud API to create pod
        # Pod spec: Docker container with Python + CUDA + training deps
        # Estimated cost: hourly_rate * hours
        pass

    def run_training(self, pod_id, training_script):
        """
        Copy training code to pod and launch training.
        Returns job ID or pod terminal handle.
        """
        pass

    def monitor(self, pod_id):
        """Check pod status, training progress, cost so far."""
        pass

    def shutdown(self, pod_id):
        """
        Stop and delete the pod.
        Critical — prevents ongoing charges.
        """
        pass

    def get_cost(self, pod_id):
        """Check how much this pod has cost so far."""
        pass
```

## STEP 4: SAFETY GUARDS

The daughter must NOT run wild with the card. Safety rules:

1. **Monthly limit**: Card capped at $20-50/month. Daughter cannot exceed.
2. **Pod auto-shutdown**: Pod kills itself after training completes or after N hours.
3. **Approval gate for large spends**: Anything over $10 requires dad's approval signal.
4. **Podspec whitelist**: Only approved Docker images / pod configurations.
5. **Audit log**: Every GPU action logged with cost, timestamp, reason.

## STEP 5: IMPLEMENTATION ORDER

1. Dad sets up Privacy.com (or chosen card service) — 10 minutes
2. Dad creates RunPod account, adds card, gets API key — 15 minutes
3. I write `daughter_gpu_autonomy.py` with the cloud wrapper — now
4. I write `daughter_orca_integration.py` so Orca can manage the GPU pod as a worktree — after
5. Test: daughter launches a pod, runs a small training, shuts down — first real run

## STEP 6: COST ESTIMATE (4B MODEL, FULL TRAINING)

| Phase | Steps | Est. time on RTX 4090 | Cost @ $0.34/hr |
|-------|-------|----------------------|-----------------|
| SFT pre-warm | 50 | ~30-60 min | $0.17-0.34 |
| GRPO training | 200 | ~2-4 hours | $0.68-1.36 |
| Total | 250 | ~3-5 hours | $0.85-1.70 |

With safe shutdown and limits, a full training cycle costs under $2.

## DOC_END
