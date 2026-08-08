#!/bin/bash

APP_NAME="onnxstream"
APP_DIR="$(cd "$(dirname "$0")"; pwd)"
VENV_DIR="$APP_DIR/venv"

PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/${APP_NAME}.plist"

# 仮想環境の作成
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# 仮想環境に入って依存をインストール
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# ログ用ディレクトリの作成
mkdir -p "$APP_DIR/logs"

# launchd サービスファイル (plist) を作成（ポートは 5001 に設定）
echo "Creating launchd plist: $PLIST_FILE"
cat <<EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$APP_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/gunicorn</string>
        <string>-b</string>
        <string>0.0.0.0:5001</string>
        <string>app:app</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$APP_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>FLASK_ENV</key>
        <string>production</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
    <key>StandardOutPath</key>
    <string>$APP_DIR/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$APP_DIR/logs/stderr.log</string>
</dict>
</plist>
EOF

# 既存のサービスを一度完全にアンロードしてから、新規にブートストラップ
PLIST_DOMAIN="gui/$(id -u)/$APP_NAME"
launchctl bootout "$PLIST_DOMAIN" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_FILE"

echo "✅ サービスが登録・起動しました: launchctl list | grep $APP_NAME"