# Ada-MSS

> CS527 Team Project scaffold (based on the proposal in `proposal.pdf`).

## 中文说明（Chinese）

### 项目简介
这是一个根据当前 proposal 搭建的**可扩展代码框架**，目标是先把工程结构、配置入口、数据流与训练/推理接口统一起来，后续再按 proposal 的具体实验方法替换模块实现。

### 当前目录结构

```text
Ada-MSS/
├── proposal.pdf
├── configs/
│   └── default.json
├── scripts/
│   └── run_demo.py
└── src/
    └── ada_mss/
        ├── __init__.py
        ├── config.py
        ├── data.py
        ├── infer.py
        ├── models.py
        ├── pipeline.py
        └── train.py
```

### 模块说明
- `config.py`：统一配置数据结构与加载逻辑。
- `data.py`：数据样本与读取器（占位实现）。
- `models.py`：基线模型（占位实现，便于后续替换为 proposal 的核心模型）。
- `pipeline.py`：串联数据读取与模型预测。
- `train.py`：训练入口脚手架。
- `infer.py`：推理入口。
- `scripts/run_demo.py`：最小可运行示例。

### 快速开始
```bash
PYTHONPATH=src python scripts/run_demo.py
```

---

## English

### Overview
This repository now contains an **extensible project scaffold** aligned with the proposal in `proposal.pdf`. The goal is to establish a clean engineering skeleton first (config, data flow, train/infer entry points), then plug in proposal-specific algorithms.

### Structure

```text
Ada-MSS/
├── proposal.pdf
├── configs/
│   └── default.json
├── scripts/
│   └── run_demo.py
└── src/
    └── ada_mss/
        ├── __init__.py
        ├── config.py
        ├── data.py
        ├── infer.py
        ├── models.py
        ├── pipeline.py
        └── train.py
```

### Module Guide
- `config.py`: typed config definitions + loader.
- `data.py`: sample schema and dataset reader placeholder.
- `models.py`: baseline model placeholder (to be replaced with proposal model).
- `pipeline.py`: orchestrates reading + prediction flow.
- `train.py`: training entry scaffold.
- `infer.py`: inference entry scaffold.
- `scripts/run_demo.py`: minimal runnable demo.

### Quick Run
```bash
PYTHONPATH=src python scripts/run_demo.py
```

## Next Suggested Steps
1. Replace `BaselineModel` with the proposal model implementation.
2. Implement actual dataset loader and preprocessing in `data.py`.
3. Add evaluation metrics and experiment scripts.
4. Add tests under `tests/` for data/model/pipeline.
