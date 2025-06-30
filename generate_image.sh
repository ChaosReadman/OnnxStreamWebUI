#!/bin/bash

LOCKFILE="/tmp/generate.lock"
LOGFILE="/tmp/generate.log"

# 古いロックがある場合、そのPIDを調べてプロセスの生死を確認
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "別の生成プロセス (PID=$OLD_PID) が実行中です" >> "$LOGFILE"
        exit 1
    else
        echo "ロックファイルが残っていましたが、プロセスは死んでいます。削除します。" >> "$LOGFILE"
        rm -f "$LOCKFILE"
    fi
fi

OUTFILE=$1
PROMPT=$2
NEGATIVE_PROMPT=$3
STEPS=$4
WIDTH=$5
HEIGHT=$6
# JSONファイル名を決定（.png.json）
JSONFILE="${OUTFILE}.json"

# バックグラウンドで画像生成 + trapでロック削除
(
  trap "rm -f $LOCKFILE" EXIT
  /home/takahiro/OnnxStream/src/build/sd \
    --rpi-lowmem --turbo \
    --models-path /home/takahiro/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ \
    --prompt "$PROMPT" \
    --neg-prompt "$NEGATIVE_PROMPT" \
    --steps "$STEPS" \
    --res "${WIDTH}x${HEIGHT}" \
    --output "$OUTFILE" >> "$LOGFILE" 2>&1

    # 画像生成成功後のみ
    if [ $? -eq 0 ] && [ -f "$OUTFILE" ]; then
        echo "画像生成成功。メタデータを書き出します。" >> "$LOGFILE" 2>&1
        echo "{" > "$JSONFILE"
        echo "  \"prompt\": \"$PROMPT\"," >> "$JSONFILE"
        echo "  \"negative_prompt\": \"$NEGATIVE_PROMPT\"," >> "$JSONFILE"
        echo "  \"steps\": \"$STEPS\"," >> "$JSONFILE"
        echo "  \"width\": \"$WIDTH\"," >> "$JSONFILE"
        echo "  \"height\": \"$HEIGHT\"," >> "$JSONFILE"
        echo "  \"created_at\": \"$(date --iso-8601=seconds)\"" >> "$JSONFILE"
        echo "}" >> "$JSONFILE"
    else
        echo "画像生成に失敗。JSONは出力しません。" >>"$LOGFILE"
    fi

    rm -f "$LOCKFILE"
) &

SD_PID=$!

echo "生成開始: PID=$SD_PID PROMPT=$PROMPT STEPS=$STEPS WIDTH=$WIDTH HEIGHT=$HEIGHT"  >> "$LOGFILE"
echo "$SD_PID" > "$LOCKFILE"

