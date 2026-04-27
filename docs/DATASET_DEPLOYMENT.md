# Dataset Deployment Guide (for Ada-MSS Repair Pipeline)

## Recommended Datasets

为贴合你 proposal 的“Buggy Code + Tests -> Repair -> Validation”流程，我建议分两层：

1. **首选：SWE-bench Lite（Python）**
   - 优点：真实仓库 issue + 测试驱动修复任务，和图里的验证闭环最一致。
   - 用途：主评测集（端到端修复成功率）。

2. **补充：QuixBugs（Python 子集）**
   - 优点：轻量、上手快，适合快速验证 pruning / escalation 策略。
   - 用途：开发期 smoke benchmark。

> Defects4J 也很经典，但主要是 Java，若你这版先走 Python 管线，SWE-bench Lite + QuixBugs 更顺手。

---

## Directory Layout

```text
data/
├── raw/
│   ├── swe_bench_lite/
│   └── quixbugs/
└── processed/
    └── repair_tasks.jsonl
```

`repair_tasks.jsonl` target schema:

```json
{"task_id":"repo__issue_x","buggy_code":"...","tests":"..."}
```

---

## Minimal Deployment Steps

### 1) Prepare folders

```bash
mkdir -p data/raw/swe_bench_lite data/raw/quixbugs data/processed
```

### 2) Download datasets (example)

```bash
# SWE-bench Lite (from Hugging Face datasets)
python - <<'PY'
from datasets import load_dataset

ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
print(ds[0].keys())
print("rows:", len(ds))
PY
```

```bash
# QuixBugs (Python)
git clone https://github.com/jkoppel/QuixBugs.git data/raw/quixbugs
```

### 3) Convert to Ada-MSS task format

把每条样本转为：
- `task_id`
- `buggy_code`
- `tests`

输出到 `data/processed/repair_tasks.jsonl`，供 `TaskDataset.from_jsonl(...)` 读取。

---

## Notes

- 由于体积和许可证原因，本仓库不直接提交完整数据集。
- 建议先用 QuixBugs 做 20~50 条小规模回归，再上 SWE-bench Lite 全量评测。
