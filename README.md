# Ada-MSS

> Figure-aligned automatic program repair scaffold.

## 中文（与 proposal/figure 对齐）

当前主流程严格贴近你给的 system figure：
1. Input: Buggy Code + Tests
2. Semantic Pruning Engine（TAC/PSS/CDS）
3. LLM Repair Agent（默认本地 Qwen）
4. Validation Sandbox
5. Pass Tests? -> Success；否则 Escalation Policy 提升粒度并重试
6. 达到最大上下文级别后 Repair Fail

默认本地模型：`Qwen/Qwen3-4B-Thinking-2507`（OpenAI-compatible endpoint）。

### 快速运行

```bash
PYTHONPATH=src python scripts/run_demo.py
```

### 本地模型服务示例（vLLM）

```bash
vllm serve Qwen/Qwen3-4B-Thinking-2507 --served-model-name Qwen/Qwen3-4B-Thinking-2507 --port 8000
```

### 数据集建议与部署

请看：`docs/DATASET_DEPLOYMENT.md`

---

## English

This repo now follows the figure-aligned repair loop:
- Buggy code + tests input
- Semantic pruning (TAC/PSS/CDS)
- LLM repair agent
- Validation sandbox
- Escalation policy until success or max context reached

Default local model: `Qwen/Qwen3-4B-Thinking-2507`.

Dataset recommendation and setup guide: `docs/DATASET_DEPLOYMENT.md`.
