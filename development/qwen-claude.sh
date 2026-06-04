#!/usr/bin/env bash
#
# qwen-claude.sh — launch Claude Code against a local Ollama model.
#
# Usage:
#   ./qwen-claude.sh                  # uses the default model below
#   ./qwen-claude.sh qwen3-coder:14b  # override the model for this run
#   ./qwen-claude.sh qwen3-coder:30b /path/to/project   # extra args pass through to claude
#
# First time only:  chmod +x qwen-claude.sh
#
# NOTE: the CLAUDE_CODE_ATTRIBUTION_HEADER fix is NOT set here on purpose —
# it has to live in ~/.claude/settings.json (a shell export is ignored).

set -euo pipefail

# --- model selection -------------------------------------------------------
# First argument overrides the model; everything after it is passed to claude.
MODEL="${1:-qwen3-coder:30b}"
[ "$#" -gt 0 ] && shift   # drop the model arg so "$@" holds only pass-through args

# --- point Claude Code at the local Ollama endpoint ------------------------
export ANTHROPIC_BASE_URL="http://localhost:11434"
export ANTHROPIC_AUTH_TOKEN="ollama"
export ANTHROPIC_API_KEY=""

# --- context window --------------------------------------------------------
# 32K is the practical floor for agentic coding. On a 24GB Mac running a ~19GB
# model, going much higher may not fit in memory — raise cautiously.
export OLLAMA_CONTEXT_LENGTH="32768"

# --- sanity check: is Ollama actually up? ----------------------------------
if ! curl -s "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  echo "⚠️  Ollama doesn't seem to be running on localhost:11434."
  echo "    Start it (open the app, or 'brew services start ollama') and try again."
  exit 1
fi

echo "▶  Launching Claude Code with local model: $MODEL"
echo "   (context: ${OLLAMA_CONTEXT_LENGTH} tokens)"
echo

# --- launch ----------------------------------------------------------------
exec claude --model "$MODEL" "$@"

### Notes: Start/Stop Ollama
# brew services start ollama
# brew services stop ollama
