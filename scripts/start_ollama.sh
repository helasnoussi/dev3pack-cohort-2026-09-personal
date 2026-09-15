#!/usr/bin/env bash
# Start the local model lane, from nothing to a green doctor.
#
#   bash scripts/start_ollama.sh        # start it, pull the model if missing
#   make ollama                         # the same thing, shorter
#
# WHY A SCRIPT AND NOT AN INSTRUCTION. "Run `ollama serve` in another terminal"
# is three things a learner has to get right at once: a second terminal, a
# process they must not close, and knowing whether the model is already pulled.
# Each one produced a support question on day one.
#
# It is safe to run twice. Every step checks before it acts, and a server that
# is already up is left alone rather than restarted.

set -euo pipefail

MODEL="${BOOTCAMP_MODEL:-qwen2.5:7b-instruct}"
BASE="${OLLAMA_BASE_URL:-http://localhost:11434}"
HOST="${BASE%/v1}"

say() { printf '%s\n' "$*"; }

if ! command -v ollama >/dev/null 2>&1; then
  say "❌ Ollama is not installed."
  say ""
  say "   Download it:  https://ollama.com/download"
  say "   macOS: a .dmg · Windows: an .exe · Linux: one shell line"
  say ""
  say "   Then run this again. Or stay offline: BOOTCAMP_PROVIDER=fake in .env"
  exit 2
fi
# `ollama --version` prints a "could not connect" warning FIRST when no server
# is up, so take the line that carries the version rather than the first one.
version=$(ollama --version 2>/dev/null | grep -m1 -i version || echo "version unknown")
say "✅ ollama is installed ($version)"

# A server that is already answering is left exactly as it is. Starting a second
# one does not fail loudly -- it fails by binding nothing and looking fine.
if curl -fsS -m 3 "$HOST/api/tags" >/dev/null 2>&1; then
  say "✅ server already running at $HOST"
else
  say "·  starting the server…"
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  for _ in $(seq 1 30); do
    if curl -fsS -m 2 "$HOST/api/tags" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  if ! curl -fsS -m 3 "$HOST/api/tags" >/dev/null 2>&1; then
    say "❌ it did not come up. The log is at /tmp/ollama-serve.log"
    exit 1
  fi
  say "✅ server running at $HOST"
  say "   (it keeps running in the background; /tmp/ollama-serve.log has its output)"
fi

if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$MODEL"; then
  say "✅ model $MODEL already pulled"
else
  say "·  pulling $MODEL — about 4.7 GB the first time, so give it a while…"
  ollama pull "$MODEL"
  say "✅ model $MODEL pulled"
fi

say ""
say "Point the course at it: set BOOTCAMP_PROVIDER=ollama in .env, then"
say ""
say "    uv run bootcamp doctor"
say ""
say "Going back is the same line with fake. Every scored exercise passes there."
