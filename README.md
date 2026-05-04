# Ada-MSS

> Figure-aligned automatic program repair scaffold.

## 中文（与 proposal/figure 对齐）

主流程：
1. Input: Buggy Code + Tests
2. Semantic Pruning Engine（TAC/PSS/CDS）
3. LLM Repair Agent（默认本地 Qwen）
4. Validation Sandbox（执行 candidate code + tests）
5. Pass Tests? -> Success；否则 Escalation Policy 重试

默认本地模型：`Qwen/Qwen3-4B-Thinking-2507`。

### 一次性跑通整个流程

```bash
# 1) 单任务 demo
PYTHONPATH=src python scripts/run_demo.py

# 2) 批量评测 demo 数据集
PYTHONPATH=src python scripts/run_benchmark.py
```

### 本地模型服务（vLLM）

```bash
vllm serve Qwen/Qwen3-4B-Thinking-2507 --served-model-name Qwen/Qwen3-4B-Thinking-2507 --port 8000
```

vllm serve Qwen/Qwen3-4B-AWQ \
  --served-model-name qwen3-4b-awq \
  --host 127.0.0.1 \
  --port 8001 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.60 \
  --max-num-seqs 1 \
  --enforce-eager

### 部署数据集并跑测试

详见：`docs/DATASET_DEPLOYMENT.md`

---

## English

Pipeline:
- Buggy code + tests
- Semantic pruning (TAC/PSS/CDS)
- LLM repair agent
- Validation sandbox
- Escalation until success/fail

Run end-to-end:

```bash
PYTHONPATH=src python scripts/run_demo.py
PYTHONPATH=src python scripts/run_benchmark.py
```

Dataset deployment and benchmark steps:
- `docs/DATASET_DEPLOYMENT.md`
