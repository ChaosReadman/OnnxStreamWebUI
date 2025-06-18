#!/bin/bash

LOCK_FILE="generate.lock"


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

# ロックファイル作成とPID書き込み
echo $$ > "$LOCKFILE"

# ---- ここから画像生成処理 ----
/home/takahiro/OnnxStream/src/build/sd \
  --rpi-lowmem --turbo \
  --models-path /home/takahiro/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ \
  --prompt "$1" \
  --neg-prompt "$2" \
  --steps "$3" \
  --output "$4"
# ---- ここまで画像生成処理 ----

# ロックファイル削除
rm -f "$LOCKFILE"

sync