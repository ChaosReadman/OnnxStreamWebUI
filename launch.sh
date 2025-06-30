#!/bin/bash

APP_NAME="onnxstream"
APP_DIR="$(cd "$(dirname "$0")"; pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

# 仮想環境の作成
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# 仮想環境に入って依存をインストール
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# systemd サービスファイルを作成
if [ ! -f "$SERVICE_FILE" ]; then
  echo "Creating systemd service: $SERVICE_FILE"
  sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=OnnxStream Web UI via Gunicorn
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/gunicorn -b 0.0.0.0:5000 app:app
Restart=always
Environment=FLASK_ENV=production
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
fi

# systemd サービスのリロード・有効化・起動
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable "$APP_NAME"
sudo systemctl restart "$APP_NAME"

echo "✅ サービスが起動しました: systemctl status $APP_NAME"
