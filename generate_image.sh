#!/bin/bash

LOCK_FILE="generate.lock"

# 二重起動防止
if [ -f "$LOCK_FILE" ]; then
    echo "すでに画像生成中です。"
    exit 1
fi

# ロック作成
touch "$LOCK_FILE"

# 終了時にロック解除するためのtrap
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT INT TERM

# 引数取得
OUTFILE=$1
PROMPT=$2
NEGATIVE_PROMPT=$3
STEPS=$4

# デバッグ出力（必要なら削除OK）
echo "出力ファイル: $OUTFILE"
echo "プロンプト: $PROMPT"
echo "ネガティブプロンプト: $NEGATIVE_PROMPT"
echo "ステップ数: $STEPS"

# 画像生成コマンド実行
/home/takahiro/OnnxStream/src/build/sd --rpi-lowmem --turbo --models-path /home/takahiro/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ --prompt "$PROMPT" --neg-prompt "$NEGATIVE_PROMPT" --steps "$STEPS" --output "$OUTFILE"

# 画像生成完了メッセージ
echo "画像生成完了: $OUTFILE"

sync