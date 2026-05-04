# Dataset Deployment Guide (for Ada-MSS Repair Pipeline)

## Recommended Datasets

为贴合 proposal 的“Buggy Code + Tests -> Repair -> Validation”流程，建议：

1. **主评测：SWE-bench Lite（Python）**
2. **开发回归：QuixBugs（Python）**

---

## Ada-MSS Task Format

每条任务统一转成 JSONL：

```json
{"task_id":"repo__issue_x","buggy_code":"...","tests":"..."}
```

字段说明：
- `task_id`: 唯一 ID
- `buggy_code`: 有缺陷的源代码（字符串）
- `tests`: 可执行测试代码（至少包含一个 `test_*` 函数）

---

## End-to-end Commands

### 0) 先跑内置 demo 数据集（无需下载）

```bash
PYTHONPATH=src python scripts/run_benchmark.py
```

### 1) 准备目录

```bash
mkdir -p data/raw data/processed
```

### 2) 下载数据（示例）

```bash
mkdir -p data/raw data/processed

export HF_DATASETS_CACHE="$PWD/data/raw/hf_cache"

python - <<'PY'
from datasets import load_dataset

ds = load_dataset(
    "princeton-nlp/SWE-bench_Lite",
    split="test",
    cache_dir="data/raw/hf_cache",
)

print("rows:", len(ds))
print("columns:", ds.column_names)
print(ds[0])

# 额外导出一份 jsonl，方便后面自己处理
ds.to_json("data/raw/swebench_lite_test.jsonl", orient="records", lines=True)
print("saved to data/raw/swebench_lite_test.jsonl")
PY
```

### 3) 转换成 Ada-MSS 格式

如果你已经有中间 JSONL（字段含 `id`/`task_id`, `buggy_code`, `tests`），可直接：

```bash
python scripts/prepare_dataset.py \
  --input data/raw/debugbench.jsonl \
  --output data/processed/repair_tasks.jsonl
```
python scripts/prepare_dataset.py \
  --input data/processed/debugbench.jsonl \
  --output data/processed/repair_tasks.jsonl

### 4) 运行批量评测

```bash
PYTHONPATH=src python - <<'PY'
from ada_mss.benchmark import run_benchmark

summary = run_benchmark("configs/local_awq.json", "data/processed/repair_tasks_demo.jsonl")
print(summary)
PY
```


mkdir -p logs
ADA_MSS_LLM_LOG=logs/llm_debug.jsonl PYTHONPATH=src python scripts/run_benchmark.py --config configs/local_awq.json


---

## Notes

- 本仓库内置 `data/processed/repair_tasks_demo.jsonl` 用于快速验证流程。
- 真实修复能力取决于 LLM 服务是否可用（本地 vLLM 或远端 API）。
- 当 LLM 不可用时，会走 template fallback，主要用于流程联调而非最终效果评估。
