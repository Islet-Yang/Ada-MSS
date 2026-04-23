# Ada-MSS

> CS527 Team Project implementation scaffold, now filled according to the proposal + system figure (as far as can be landed in code).

## 中文说明（Chinese）

### 这次补充了什么
这版不再只是空壳，而是按 proposal/system figure 映射成可运行流程：
1. **Query Intake**：接收用户问题。
2. **Retrieval**：用关键字检索从知识库取 Top-K。
3. **Context Assembly**：拼接上下文，限制长度。
4. **Cost-aware LLM Routing**：在可用供应商里优先选便宜模型。
5. **Answer Generation / Fallback**：生成答案；若无可用 API Key 则走模板兜底。

### 目录结构

```text
Ada-MSS/
├── proposal.pdf
├── configs/
│   └── default.json
├── data/
│   └── sample_kb.jsonl
├── scripts/
│   └── run_demo.py
└── src/
    └── ada_mss/
        ├── __init__.py
        ├── config.py
        ├── data.py
        ├── infer.py
        ├── llm.py
        ├── pipeline.py
        ├── provider_router.py
        ├── retrieval.py
        └── train.py
```

### API 模型选择（按“便宜优先”）
`configs/default.json` 里预置了 3 家（不多但够用）：
- Groq（通常便宜、速度快）
- DeepSeek
- OpenRouter（可聚合更多模型）

> 你可以直接在配置里改成本参数和启用状态；路由器会选**当前已配置 API Key 且总价最低**的供应商。

### 目前明确不复现（proposal 里较难直接落地的部分）
- 检索器 + 生成器联合训练（需要专门训练数据和 GPU 训练流程）。
- 在线持续学习（需要稳定反馈闭环和线上基础设施）。

### 运行
```bash
PYTHONPATH=src python scripts/run_demo.py
```

如果要启用真实 API，请先设置至少一个环境变量（示例）：
```bash
export GROQ_API_KEY=xxx
# 或 DEEPSEEK_API_KEY / OPENROUTER_API_KEY
```

---

## English

### What is implemented now
This version maps the proposal/system figure into a runnable flow:
1. Query intake
2. Top-K retrieval from a knowledge base
3. Context assembly with length cap
4. Cost-aware LLM provider routing
5. Answer generation with template fallback when no provider is available

### API providers (cheap-first)
`configs/default.json` includes three provider presets:
- Groq
- DeepSeek
- OpenRouter

The router selects the **cheapest currently available provider** (enabled + API key present).

### Explicitly not reproduced yet (hard-to-land proposal ideas)
- End-to-end joint retriever-generator training
- Continual online adaptation with feedback loops

### Quick run
```bash
PYTHONPATH=src python scripts/run_demo.py
```

Set at least one key for real API calls:
```bash
export GROQ_API_KEY=xxx
# or DEEPSEEK_API_KEY / OPENROUTER_API_KEY
```
