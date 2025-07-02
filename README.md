+ OnnxStream用にブラウザから操作できるUIを作りました（Flask製）

    + トップ画面  
!["トップページ"](images/top.png)

    + 画像生成中は、ロック状態となります（負荷かけたくないので一度に１枚ずつ）  
!["画像生成中"](images/generating.png)

+ 公式を見ればわかりますが、OnnxStreamをRaspberryPiに仕込む説明

Python等が必要らしいのでインストール
```
sudo apt-get update
sudo apt-get install -y cmake python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
```

XnnPack の特定バージョンが必要らしいので、クローンして、チェックアウトしてビルドする
```
cd ~
git clone https://github.com/google/XNNPACK.git
cd XNNPACK
git checkout 1c8ee1b68f3a3e0847ec3c53c186c5909fa3fbd3
mkdir build
cd build
cmake -DXNNPACK_BUILD_TESTS=OFF -DXNNPACK_BUILD_BENCHMARKS=OFF ..
cmake --build . --config Release
```

OnnxStreamをビルド

```
cd ~
git clone https://github.com/vitoplantamura/OnnxStream.git
cd OnnxStream
cd src
mkdir build
cd build
cmake -DMAX_SPEED=ON -DOS_LLM=OFF -DOS_CUDA=OFF -DXNNPACK_DIR=~/XNNPACK ..
cmake --build . --config Release
```

最近のバージョンでは自動的に選択したモデルをダウンロードするらしいですが、時間がかかりまくるようなので、modelsフォルダを作りそこに各モデルをマニュアルインストールします。
```
mkdir ~/models
```

+ StableDiffusion1.5（使わないので入れる必要なし）
```
cd ~/models
git lfs install
git clone --depth=1 https://huggingface.co/vitoplantamura/stable-diffusion-1.5-onnxstream
```

+ Stable Diffusion XL 1.0 Base（使わないので入れる必要なし）
```
cd ~/models
git lfs install
git clone --depth=1 https://huggingface.co/vitoplantamura/stable-diffusion-xl-base-1.0-onnxstream
```

+ Stable Diffusion XL Turbo 1.0（これだけ必要、インストール必須）
```
cd ~/models
git lfs install
git clone --depth=1 https://huggingface.co/vitoplantamura/stable-diffusion-xl-turbo-1.0-anyshape-onnxstream

cd ~
cd OnnxStream/src/build/
./sd --rpi-lowmem --turbo --models-path ../../../stable-diffusion-xl-turbo-1.0-anyshape-onnxstream/ --prompt "An astronaut riding a horse on Mars" --steps 1 --output astronaut.png

```
これで、astronaut.pngが出来上がると思うのでここまで確認してください。実は他のモデルも試してみたのですが、時間がかかるわ、クオリティ低いわで使えないと判断しました。今回は、turboだけ使うことにします。ただし、turboだとネガティブプロンプトが使えません。この辺り少し残念に感じますが仕方ありません。




+ ここから本Gitの説明です。cd ~してから、本 git を cloneしてください。（多分これで立ち上がると思います）

```
chmod +x launch.sh
./launch.sh

```
+ 最後に  
今回のWebUIでは、turboモデルのみ対応しています。他のモデルをつかってみたところ、使い物にならなかったので、turboだけでいいやという判断をしました。異論があれば受け入れますので、どうぞご連絡ください。

