---
name: hugging-face-evaluation
description: Use when adding or managing evaluation results in Hugging Face model cards. Supports extracting eval tables from README content, importing scores from Artificial Analysis API, and running custom model evaluations with vLLM/lighteval. Works with the model-index metadata format.
---

# Overview

Add structured evaluation results to Hugging Face model cards via multiple methods:
- Extract existing evaluation tables from README content
- Import benchmark scores from Artificial Analysis API
- Run custom model evaluations with vLLM or accelerate backends (lighteval/inspect-ai)

**Ecosystem integration:** Model Cards (model-index metadata), Artificial Analysis API, Papers with Code (model-index spec), HF Jobs (`uv` integration), vLLM (GPU inference), lighteval, inspect-ai.

# Version
1.3.0

# Dependencies

**Core:** huggingface_hub>=0.26.0, markdown-it-py>=3.0.0, python-dotenv>=1.2.1, pyyaml>=6.0.3, requests>=2.32.5

**Inference Provider Evaluation:** inspect-ai>=0.3.0, inspect-evals, openai

**vLLM Custom Evaluation (GPU required):** lighteval[accelerate,vllm]>=0.6.0, vllm>=0.4.0, torch>=2.0.0, transformers>=4.40.0, accelerate>=0.30.0

Note: vLLM dependencies are installed automatically via PEP 723 script headers when using `uv run`.

# IMPORTANT: Check for Existing PRs Before Creating New Ones

**Before creating ANY pull request with `--create-pr`, you MUST check:**

```bash
uv run scripts/evaluation_manager.py get-prs --repo-id "username/model-name"
```

If open PRs exist: warn the user, show PR URLs, do NOT create a new PR unless user explicitly confirms. This prevents spamming model repositories with duplicate evaluation PRs.

# Usage Instructions

**Use `--help` for the latest workflow guidance:**
```bash
uv run scripts/evaluation_manager.py --help
```

### Prerequisites
- Preferred: use `uv run` (PEP 723 header auto-installs deps)
- Set `HF_TOKEN` environment variable with Write-access token
- For Artificial Analysis: Set `AA_API_KEY` environment variable
- `.env` is loaded automatically if `python-dotenv` is installed

## Core Workflow

### Method 1: Extract from README

```bash
# 1) Inspect tables to get table numbers and column hints
uv run scripts/evaluation_manager.py inspect-tables --repo-id "username/model"

# 2) Extract a specific table (prints YAML by default)
uv run scripts/evaluation_manager.py extract-readme \
  --repo-id "username/model" \
  --table 1 \
  [--model-column-index <column index>] \
  [--model-name-override "<exact column header>"]

# 3) Apply changes (push or PR)
uv run scripts/evaluation_manager.py extract-readme \
  --repo-id "username/model" --table 1 --apply       # push directly
# or
uv run scripts/evaluation_manager.py extract-readme \
  --repo-id "username/model" --table 1 --create-pr   # open a PR
```

**Validation:** YAML is printed by default; compare against the README table before applying. Prefer `--model-column-index`; `--model-name-override` requires exact column header text.

### Method 2: Import from Artificial Analysis

```bash
AA_API_KEY="your-api-key" uv run scripts/evaluation_manager.py import-aa \
  --creator-slug "anthropic" \
  --model-name "claude-sonnet-4" \
  --repo-id "username/model-name" \
  [--create-pr]
```

### Method 3: Run Evaluation Job (Inference Providers)

```bash
HF_TOKEN=$HF_TOKEN hf jobs uv run hf-evaluation/scripts/inspect_eval_uv.py \
  --flavor cpu-basic \
  --secret HF_TOKEN=$HF_TOKEN \
  -- --model "meta-llama/Llama-2-7b-hf" --task "mmlu"
```

Python helper (optional):
```bash
python scripts/run_eval_job.py --model "meta-llama/Llama-2-7b-hf" --task "mmlu" --hardware "t4-small"
```

### Method 4: Custom Model Evaluation with vLLM

Evaluate HuggingFace models directly on GPU. Requires `uv` and sufficient GPU memory. Check GPU with `nvidia-smi` before running.

| Feature | vLLM Scripts | Inference Provider Scripts |
|---------|-------------|---------------------------|
| Model access | Any HF model | Models with API endpoints |
| Hardware | Your GPU / HF Jobs GPU | Provider infrastructure |
| Speed | vLLM optimized | Depends on provider |

#### Option A: lighteval with vLLM Backend

```bash
# Local GPU
python scripts/lighteval_vllm_uv.py \
  --model meta-llama/Llama-3.2-1B \
  --tasks "leaderboard|mmlu|5"

# Via HF Jobs
hf jobs uv run scripts/lighteval_vllm_uv.py \
  --flavor a10g-small --secrets HF_TOKEN=$HF_TOKEN \
  -- --model meta-llama/Llama-3.2-1B --tasks "leaderboard|mmlu|5"
```

**Task format:** `suite|task|num_fewshot` (e.g., `leaderboard|mmlu|5`, `leaderboard|gsm8k|5`, `lighteval|hellaswag|0`). Multiple tasks: comma-separated. Full list: https://github.com/huggingface/lighteval/blob/main/examples/tasks/all_tasks.txt

**Additional flags:** `--backend accelerate` (use HF Transformers), `--use-chat-template` (instruction-tuned models).

#### Option B: inspect-ai with vLLM Backend

```bash
python scripts/inspect_vllm_uv.py \
  --model meta-llama/Llama-3.2-1B --task mmlu
```

Available tasks: mmlu, gsm8k, hellaswag, arc_challenge, truthfulqa, winogrande, humaneval. Additional flags: `--backend hf`, `--tensor-parallel-size N`.

#### Hardware Recommendations

| Model Size | Hardware |
|------------|---------|
| < 3B params | `t4-small` |
| 3B - 13B | `a10g-small` |
| 13B - 34B | `a10g-large` |
| 34B+ | `a100-large` |

## Commands Reference

```bash
# Top-level
uv run scripts/evaluation_manager.py --help
uv run scripts/evaluation_manager.py --version

# Inspect tables
uv run scripts/evaluation_manager.py inspect-tables --repo-id "username/model-name"

# Extract from README
uv run scripts/evaluation_manager.py extract-readme \
  --repo-id "username/model-name" --table N \
  [--model-column-index N] [--model-name-override "Name"] \
  [--task-type "text-generation"] [--dataset-name "Custom Benchmarks"] \
  [--apply | --create-pr]

# Import from Artificial Analysis
AA_API_KEY=... uv run scripts/evaluation_manager.py import-aa \
  --creator-slug "creator" --model-name "model" --repo-id "username/model" [--create-pr]

# View / Validate
uv run scripts/evaluation_manager.py show --repo-id "username/model-name"
uv run scripts/evaluation_manager.py validate --repo-id "username/model-name"

# Check open PRs (ALWAYS run before --create-pr)
uv run scripts/evaluation_manager.py get-prs --repo-id "username/model-name"
```

## Model-Index Format

```yaml
model-index:
  - name: Model Name
    results:
      - task:
          type: text-generation
        dataset:
          name: Benchmark Dataset
          type: benchmark_type
        metrics:
          - name: MMLU
            type: mmlu
            value: 85.2
        source:
          name: Source Name
          url: https://source-url.com
```

WARNING: Do not use markdown formatting in the model name. Use plain text. Only use urls in the source.url field.

## Model Name Matching

The script uses **exact normalized token matching** for multi-model tables:
- Removes markdown formatting (bold, links), normalizes to lowercase, replaces `-`/`_` with spaces
- Compares token sets: `"OLMo-3-32B"` matches `"**Olmo 3 32B**"` or `"[Olmo-3-32B](...)`
- For column-based tables: finds matching column header, extracts that column only
- For transposed tables (models as rows): finds matching row, extracts benchmark scores from that row

## Best Practices

1. **Check for existing PRs first** with `get-prs` before creating any new PR
2. **Start with `inspect-tables`** to see table structure and get correct extraction command
3. **Preview first**: default prints YAML; review before `--apply` or `--create-pr`
4. **Verify extracted values** against the README table manually
5. **Use `--table N`** when multiple evaluation tables exist
6. **Use `--model-name-override`** for comparison tables with exact column header text
7. **Create PRs for others** with `--create-pr`; push directly only to your own models
8. **One model per repo**: only add the main model's results

## Common Patterns

**Update your own model:**
```bash
uv run scripts/evaluation_manager.py extract-readme \
  --repo-id "your-username/your-model" --task-type "text-generation"
```

**Update someone else's model:**
```bash
# Step 1: Check for existing PRs
uv run scripts/evaluation_manager.py get-prs --repo-id "other-user/their-model"
# Step 2: If NO open PRs, create one
uv run scripts/evaluation_manager.py extract-readme \
  --repo-id "other-user/their-model" --create-pr
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No evaluation tables found | Check if README contains markdown tables with numeric scores |
| Could not find model in table | Use `--model-name-override` with exact name from available models list |
| AA_API_KEY not set | Set environment variable or add to .env file |
| Token lacks write access | Ensure HF_TOKEN has write permissions |
| Model not found in AA | Verify creator-slug and model-name match API values |
| vLLM out of memory | Use larger hardware, reduce `--gpu-memory-utilization`, or use `--tensor-parallel-size` |
| Architecture not supported by vLLM | Use `--backend hf` (inspect-ai) or `--backend accelerate` (lighteval) |
| Trust remote code required | Add `--trust-remote-code` flag for models with custom code |
| Chat template not found | Only use `--use-chat-template` for instruction-tuned models |

## Error Handling
- **Table Not Found**: Reports if no evaluation tables detected
- **Invalid Format**: Clear error messages for malformed tables
- **API Errors**: Retry logic for transient Artificial Analysis API failures
- **Merge Conflicts**: Preserves existing model-index entries when adding new ones
