#!/bin/bash

LOCKFILE="/tmp/generate.lock"

# 古いロックがある場合、そのPIDを調べてプロセスの生死を確認
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "別の生成プロセス (PID=$OLD_PID) が実行中です" >> /tmp/generate.log
        exit 1
    else
        echo "ロックファイルが残っていましたが、プロセスは死んでいます。削除します。" >> /tmp/generate.log
        rm -f "$LOCKFILE"
    fi
fi

OUTFILE=$1
PROMPT=$2
NEGATIVE_PROMPT=$3
STEPS=$4

# バックグラウンドで画像生成 + trapでロック削除
(
  trap "rm -f $LOCKFILE" EXIT
  /home/takahiro/OnnxStream/src/build/sd \
    --rpi-lowmem --turbo \
    --models-path /home/takahiro/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ \
    --prompt "$PROMPT" \
    --neg-prompt "$NEGATIVE_PROMPT" \
    --steps "$STEPS" \
    --output "$OUTFILE"
) &

SD_PID=$!

echo "生成開始: PID=$SD_PID PROMPT=$PROMPT" >> /tmp/generate.log
echo "SD_PID = $SD_PID" >> /tmp/generate.log
echo "$SD_PID" > "$LOCKFILE"

