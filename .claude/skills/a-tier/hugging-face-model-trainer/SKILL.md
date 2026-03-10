---
name: hugging-face-model-trainer
description: Use when training or fine-tuning language models using TRL (Transformer Reinforcement Learning) on Hugging Face Jobs infrastructure. Covers SFT, DPO, GRPO and reward modeling training methods, plus GGUF conversion for local deployment. Includes guidance on the TRL Jobs package, UV scripts with PEP 723 format, dataset preparation and validation, hardware selection, cost estimation, Trackio monitoring, Hub authentication, and model persistence.
license: Complete terms in LICENSE.txt
---

# TRL Training on Hugging Face Jobs

## Overview

Train language models using TRL on fully managed Hugging Face infrastructure. No local GPU required -- models train on cloud GPUs with results auto-saved to the Hub.

**Training methods:** SFT (instruction tuning), DPO (preference optimization), GRPO (online RL), Reward Modeling (RLHF).

**For TRL docs:** `hf_doc_search("query", product="trl")` or `hf_doc_fetch("https://huggingface.co/docs/trl/sft_trainer")`. See also `references/training_methods.md`.

## Key Directives

1. **ALWAYS use `hf_jobs()` MCP tool** -- Submit via `hf_jobs("uv", {...})`, NOT bash `trl-jobs`. Pass script content inline as a string. When user asks to train/fine-tune, create the script AND submit immediately.
2. **Always include Trackio** -- Every training script must include Trackio for real-time monitoring. Use `scripts/train_sft_example.py` as template.
3. **Provide job details after submission** -- Job ID, monitoring URL, estimated time, and note user can check status later.
4. **Use example scripts as templates** -- `scripts/train_sft_example.py`, `scripts/train_dpo_example.py`, `scripts/train_grpo_example.py`.

## Prerequisites Checklist

- **Account**: HF Pro/Team/Enterprise plan required; check auth with `hf_whoami()`
- **HF_TOKEN**: Must have write permissions; MUST pass `secrets={"HF_TOKEN": "$HF_TOKEN"}` in job config
- **Dataset**: Must exist on Hub or be loadable via `datasets.load_dataset()`; format must match training method
- **ALWAYS validate unknown datasets** before GPU training (see Dataset Validation section)
- **Timeout must exceed training time** -- Default 30min is too short; minimum 1-2 hours recommended
- **Hub push must be enabled** -- `push_to_hub=True`, `hub_model_id="username/model-name"`

## Asynchronous Job Guidelines

Jobs run asynchronously and can take hours:
1. Create the training script with Trackio
2. Submit immediately using `hf_jobs()`
3. Report submission with job ID, monitoring URL, estimated time
4. Wait for user to request status checks -- don't poll automatically

## Quick Start: UV Scripts (Recommended)

UV scripts use PEP 723 inline dependencies. This is the primary approach for Claude Code.

```python
hf_jobs("uv", {
    "script": """
# /// script
# dependencies = ["trl>=0.12.0", "peft>=0.7.0", "trackio"]
# ///

from datasets import load_dataset
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig
import trackio

dataset = load_dataset("trl-lib/Capybara", split="train")
dataset_split = dataset.train_test_split(test_size=0.1, seed=42)

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    train_dataset=dataset_split["train"],
    eval_dataset=dataset_split["test"],
    peft_config=LoraConfig(r=16, lora_alpha=32),
    args=SFTConfig(
        output_dir="my-model",
        push_to_hub=True,
        hub_model_id="username/my-model",
        num_train_epochs=3,
        eval_strategy="steps",
        eval_steps=50,
        report_to="trackio",
        project="meaningful_project_name",
        run_name="meaningful_run_name",
    )
)
trainer.train()
trainer.push_to_hub()
""",
    "flavor": "a10g-large",
    "timeout": "2h",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"}
})
```

### Sequence Length

TRL uses `max_length` (NOT `max_seq_length`). Default is 1024. Override for longer context (`max_length=2048`), memory constraints (`max_length=512`), or vision models (`max_length=None`). Usually the default is fine.

### Script Parameter Rules

The `script` parameter accepts inline code or URLs. **Local file paths do NOT work** (jobs run in isolated containers).

```python
# Correct
hf_jobs("uv", {"script": "# /// script\n# dependencies = [...]\n# ///\n\n<code>"})
hf_jobs("uv", {"script": "https://huggingface.co/user/repo/resolve/main/train.py"})

# Wrong -- these all fail
hf_jobs("uv", {"script": "train.py"})
hf_jobs("uv", {"script": "./scripts/train.py"})
```

## Alternative Approaches

### TRL Maintained Scripts

Battle-tested scripts for all methods, run from URLs:
```python
hf_jobs("uv", {
    "script": "https://raw.githubusercontent.com/huggingface/trl/main/trl/scripts/sft.py",
    "script_args": ["--model_name_or_path", "Qwen/Qwen2.5-0.5B", "--dataset_name", "trl-lib/Capybara",
                    "--output_dir", "my-model", "--push_to_hub", "--hub_model_id", "username/my-model"],
    "flavor": "a10g-large", "timeout": "2h", "secrets": {"HF_TOKEN": "$HF_TOKEN"}
})
```

Available at https://github.com/huggingface/trl/tree/main/examples/scripts. Discover UV script collections: `dataset_search({"author": "uv-scripts", "sort": "downloads", "limit": 20})`.

### HF Jobs CLI (when MCP unavailable)

```bash
# Correct syntax: flags BEFORE script URL, use "uv run" (not "run uv"), --secrets (plural)
hf jobs uv run --flavor a10g-large --timeout 2h --secrets HF_TOKEN "https://example.com/train.py"

# Status commands
hf jobs ps                        # List all jobs
hf jobs logs <job-id>             # View logs
hf jobs cancel <job-id>           # Cancel a job
```

### TRL Jobs Package (terminal use only)

```bash
pip install trl-jobs
trl-jobs sft --model_name Qwen/Qwen2.5-0.5B --dataset_name trl-lib/Capybara
```

In Claude Code context, prefer `hf_jobs()` MCP tool.

## Hardware Selection

| Model Size | Hardware | Cost (approx/hr) |
|------------|---------|------------------|
| <1B params | `t4-small` | ~$0.75 |
| 1-3B params | `t4-medium`, `l4x1` | ~$1.50-2.50 |
| 3-7B params | `a10g-small/large` | ~$3.50-5.00 |
| 7-13B params | `a10g-large`, `a100-large` | ~$5-10 |
| 13B+ params | `a100-large`, `a10g-largex2` | ~$10-20 |

**All flavors:** cpu-basic/upgrade/performance/xl, t4-small/medium, l4x1/x4, a10g-small/large/largex2/largex4, a100-large, h100/h100x8

Use **LoRA/PEFT** for models >7B. Multi-GPU handled automatically by TRL/Accelerate. See `references/hardware_guide.md`.

## Critical: Saving Results to Hub

The Jobs environment is ephemeral. All files deleted when job ends. Without Hub push, **ALL TRAINING IS LOST**.

```python
# In training config
SFTConfig(push_to_hub=True, hub_model_id="username/model-name")
# In job submission
{"secrets": {"HF_TOKEN": "$HF_TOKEN"}}
```

Verify before submitting: `push_to_hub=True`, `hub_model_id` set, `secrets` includes HF_TOKEN, user has write access.

## Timeout Management

Default 30 minutes is too short. Always add 20-30% buffer.

| Scenario | Recommended |
|----------|-------------|
| Quick demo (50-100 examples) | 10-30 min |
| Development training | 1-2 hours |
| Production (3-7B model) | 4-6 hours |
| Large model with LoRA | 3-6 hours |

Format: `"90m"`, `"2h"`, `"1.5h"`, or integer seconds. On timeout: job killed, all unsaved progress lost.

## Cost Estimation

Offer to estimate cost when planning jobs:
```bash
python scripts/estimate_cost.py --model meta-llama/Llama-2-7b-hf --dataset trl-lib/Capybara \
  --hardware a10g-large --dataset-size 16000 --epochs 3
```

## Monitoring with Trackio

Add `trackio` to dependencies and configure with `report_to="trackio"`, `run_name="meaningful_name"`. Default space: `{username}/trackio`. See `references/trackio_guide.md`.

```python
# Check job status
hf_jobs("ps")
hf_jobs("inspect", {"job_id": "your-job-id"})
hf_jobs("logs", {"job_id": "your-job-id"})
```

## Dataset Validation

Validate format BEFORE GPU training -- 50%+ of failures are format mismatches. DPO is especially strict (`prompt`, `chosen`, `rejected` required).

```python
hf_jobs("uv", {
    "script": "https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py",
    "script_args": ["--dataset", "username/dataset-name", "--split", "train"]
})
```

Output markers: `READY` (use directly), `NEEDS MAPPING` (mapping code provided), `INCOMPATIBLE` (cannot use). Skip validation for known TRL datasets (trl-lib/Capybara, trl-lib/ultrachat_200k, etc.).

## GGUF Conversion

Convert trained models for use with Ollama, LM Studio, llama.cpp. See `references/gguf_conversion.md` for the complete guide and production script.

```python
hf_jobs("uv", {
    "script": "<see references/gguf_conversion.md>",
    "flavor": "a10g-large", "timeout": "45m",
    "secrets": {"HF_TOKEN": "$HF_TOKEN"},
    "env": {"ADAPTER_MODEL": "username/my-model", "BASE_MODEL": "Qwen/Qwen2.5-0.5B",
            "OUTPUT_REPO": "username/my-model-gguf"}
})
```

## Common Failure Modes

| Issue | Fix |
|-------|-----|
| OOM | Reduce `per_device_train_batch_size=1`, increase `gradient_accumulation_steps=8`, enable `gradient_checkpointing=True`, upgrade hardware, use LoRA |
| Dataset format error | Validate with dataset inspector first; apply mapping code from output |
| Job timeout | Increase timeout with 30% buffer, reduce epochs/dataset, enable `max_steps`, save checkpoints with `hub_strategy="every_save"` |
| Hub push failure | Add `secrets={"HF_TOKEN": "$HF_TOKEN"}`, set `push_to_hub=True` and `hub_model_id`, verify write permissions |
| Missing dependencies | Add to PEP 723 header: `# dependencies = ["trl>=0.12.0", "peft>=0.7.0", "missing-package"]` |

## Resources

**Reference docs (in this skill):** training_methods.md, training_patterns.md, gguf_conversion.md, trackio_guide.md, hardware_guide.md, hub_saving.md, troubleshooting.md

**Scripts (in this skill):** train_sft_example.py, train_dpo_example.py, train_grpo_example.py, estimate_cost.py, convert_to_gguf.py

**External:** [TRL Docs](https://huggingface.co/docs/trl), [TRL Jobs Guide](https://huggingface.co/docs/trl/en/jobs_training), [HF Jobs Docs](https://huggingface.co/docs/huggingface_hub/guides/jobs), [Dataset Inspector](https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py)

## Key Takeaways

1. **Submit scripts inline** via `hf_jobs("uv", {...})` -- no file saving required
2. **Jobs are asynchronous** -- don't wait/poll; let user check when ready
3. **Always set timeout** -- minimum 1-2 hours; default 30min is insufficient
4. **Always enable Hub push** -- environment is ephemeral
5. **Include Trackio** for real-time monitoring
6. **Validate datasets** before GPU training with dataset inspector
7. **Use LoRA** for models >7B to reduce memory
