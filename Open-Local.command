#!/bin/zsh
# Double-click this file to run the LOCAL version (your own Postgres, no internet needed).
cd "$(dirname "$0")"

PG_BIN="/Applications/Postgres.app/Contents/Versions/latest/bin"
STREAMLIT="$HOME/.venvs/comp9120-baggage/bin/streamlit"

if [ ! -x "$STREAMLIT" ]; then
  echo "找不到 Streamlit 環境，請先看 README 的 Run locally 步驟安裝。"
  echo "按任意鍵關閉視窗..."
  read -k 1
  exit 1
fi

if ! "$PG_BIN/pg_isready" >/dev/null 2>&1; then
  echo "正在啟動 Postgres.app..."
  open "/Applications/Postgres.app"
  for i in {1..30}; do
    "$PG_BIN/pg_isready" >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "本機版啟動中，瀏覽器會自動打開 http://localhost:8501"
echo "要停止：回到這個視窗按 Control + C"
exec "$STREAMLIT" run app.py --server.port 8501 --browser.gatherUsageStats false
