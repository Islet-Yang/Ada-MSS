# #!/usr/bin/env bash
# set -euo pipefail

# CONFIG="${CONFIG:-configs/default.json}"
# DATASET="${DATASET:-data/processed/debugbench.jsonl}"
# SAMPLES="${SAMPLES:-150}"
# BASE_URL="${BASE_URL:-http://127.0.0.1:8030/v1}"
# MODEL="${MODEL:-local_qwen}"
# MAX_TOKENS="${MAX_TOKENS:-2048}"
# RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
# OUT_DIR="${OUT_DIR:-logs/experiments_${RUN_ID}}"

# mkdir -p "${OUT_DIR}"

# echo "Ada-MSS 150-case experiment"
# echo "OUT_DIR=${OUT_DIR}"
# echo "CONFIG=${CONFIG}"
# echo "DATASET=${DATASET}"
# echo "SAMPLES=${SAMPLES}"
# echo "BASE_URL=${BASE_URL}"
# echo "MODEL=${MODEL}"
# echo "MAX_TOKENS=${MAX_TOKENS}"

# HEALTH_ROOT="${BASE_URL%/v1}"
# curl --noproxy '*' -fsS "${HEALTH_ROOT}/health" >/dev/null
# curl --noproxy '*' -fsS "${BASE_URL}/models" > "${OUT_DIR}/models.json"

# cat > "${OUT_DIR}/params.json" <<EOF
# {
#   "run_id": "${RUN_ID}",
#   "config": "${CONFIG}",
#   "dataset": "${DATASET}",
#   "samples": ${SAMPLES},
#   "base_url": "${BASE_URL}",
#   "model": "${MODEL}",
#   "max_tokens": ${MAX_TOKENS}
# }
# EOF

# for MODE in ada_mss tac_only highest_context; do
#   echo
#   echo "=== Running ${MODE} ==="
#   NO_PROXY=127.0.0.1,localhost \
#   ADA_MSS_MAX_TOKENS="${MAX_TOKENS}" \
#   ADA_MSS_LLM_LOG="${OUT_DIR}/${MODE}_llm_debug.jsonl" \
#   PYTHONPATH=src python scripts/run_benchmark.py \
#     --config "${CONFIG}" \
#     --dataset "${DATASET}" \
#     --test-samples "${SAMPLES}" \
#     --provider-base-url "${BASE_URL}" \
#     --provider-model "${MODEL}" \
#     --experiment-mode "${MODE}" \
#     --output-json "${OUT_DIR}/${MODE}.json" \
#     --output-csv "${OUT_DIR}/${MODE}.csv" \
#     --verbose-log-file "${OUT_DIR}/${MODE}_benchmark.txt" \
#     --patch-preview-lines 40
# done

PYTHONPATH=src python scripts/summarize_experiments.py \
  --ada "${OUT_DIR}/ada_mss.json" \
  --tac "${OUT_DIR}/tac_only.json" \
  --highest "${OUT_DIR}/highest_context.json" \
  --out-dir "${OUT_DIR}"

echo
echo "Done. Key outputs:"
echo "- ${OUT_DIR}/summary.md"
echo "- ${OUT_DIR}/case_studies.json"
echo "- ${OUT_DIR}/*_benchmark.txt"
echo "- ${OUT_DIR}/*_llm_debug.jsonl"
