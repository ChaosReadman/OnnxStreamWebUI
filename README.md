+ OnnxStream用にブラウザから操作できるUIを作りました（Flask製）

    + トップ画面  
!["トップページ"](images/top.png)

    + 画像生成中は、ロック状態となります（負荷かけたくないので一度に１枚ずつ）  
!["画像生成中"](images/generating.png)

+ 公式を見ればわかりますが、OnnxStreamをRaspberryPiに仕込む説明

    ところどころにtakahiroというパス名がありますが、これはわたしの名前なので広く世界に広めてください！ではなくて、各自変えるように！

```
sudo apt-get update
sudo apt-get install -y cmake python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
sudo -H pip3 install setuptools==58.3.0
sudo -H pip3 install Cython
sudo -H pip3 install gdown


cd ~
git clone https://github.com/google/XNNPACK.git
cd XNNPACK
git checkout 1c8ee1b68f3a3e0847ec3c53c186c5909fa3fbd3
mkdir build
cd build
cmake -DXNNPACK_BUILD_TESTS=OFF -DXNNPACK_BUILD_BENCHMARKS=OFF ..
cmake --build . --config Release

cd ~
git clone https://github.com/vitoplantamura/OnnxStream.git
cd OnnxStream
cd src
mkdir build
cd build
cmake -DMAX_SPEED=ON -DOS_LLM=OFF -DOS_CUDA=OFF -DXNNPACK_DIR=/home/takahiro/XNNPACK ..
cmake --build . --config Release


cd ~
git lfs install
git clone --depth=1 https://huggingface.co/vitoplantamura/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream

cd ~
cd OnnxStream/src/build/
./sd --rpi-lowmem --turbo --models-path ../../../stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ --prompt "An astronaut riding a horse on Mars" --steps 1 --output astronaut.png

sudo apt install python3-tk
sudo apt install python3.13-full
sudo apt install python3-guizero
sudo apt install python3-pillow
sudo apt install python3-flask

```

+ ようやく、ここから本Gitの説明です。といっても、クローンして実行するだけです。

    generate_image.shがすべてなので、ここを編集して自分の環境に合わせてください。たとえば、/home/takahiro/OnnxStream/src/build/sd の takahiroはわたしのユーザー名なので、そこは自分の環境に変えてください。

    次に、Flaskを実行
```
python3 app.py

```
+ 以上で立ち上がります。あとはご自分でサービス化するなどやってみてください。だとわからないと思いますので・・・サービス化をする説明を追加します。

```
sudo apt install gunicorn
cd ~/クローンしたところに移動

gunicorn --bind 0.0.0.0:5000 app:app
```
+ これで動くことを確認したら、Ctrl+Cで止め、/etc/systemd/system/onnxstream.serviceを作ってください。
```
sudo vi /etc/systemd/system/onnxstream.service
```

+ 中身は以下の通り、ここもtakahiroがあるので各自の環境に合わせること
```
[Unit]
Description=OnnxStream Web UI via Gunicorn
After=network.target

[Service]
User=takahiro
Group=www-data
WorkingDirectory=/home/takahiro/sd_web_app
ExecStart=/usr/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

Restart=always

[Install]
WantedBy=multi-user.target
```
+ 上記の通りエディット出来たら起動
```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable onnxstream
sudo systemctl start onnxstream
```

+ これで、再起動しても自動的にgunicornでFlaskアプリが立ち上がります。外に出したい場合は、Apacheなりnginxなり使ってください。
この説明はすごく面倒なのでご自分で調べてください。
なお、外に出して攻撃されても、こちらにはなんの責任もありません。
