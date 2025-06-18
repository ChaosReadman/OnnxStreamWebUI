#!/bin/bash

LOCKFILE="generate.lock"


# 古いロックがある場合、そのPIDを調べてプロセスの生死を確認
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "別の生成プロセス (PID=$OLD_PID) が実行中です"
        exit 1
    else
        echo "ロックファイルが残っていましたが、プロセスは死んでいます。削除します。"
        rm -f "$LOCKFILE"
    fi
fi

OUTFILE=$1
PROMPT=$2
NEGATIVE_PROMPT=$3
STEPS=$4

# ---- ここから画像生成処理 ----
/home/takahiro/OnnxStream/src/build/sd \
  --rpi-lowmem --turbo \
  --models-path /home/takahiro/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ \
  --prompt "$PROMPT" \
  --neg-prompt "$NEGATIVE_PROMPT" \
  --steps "$STEPS" \
  --output "$OUTFILE" &
# ---- ここまで画像生成処理 ----

# ロックファイル作成とPID書き込み
SD_PID=$!
echo "$SD_PID" > "$LOCKFILE"

wait $SD_PID
rm -f "$LOCKFILE"

sync