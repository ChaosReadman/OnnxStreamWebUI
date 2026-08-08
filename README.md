+ OnnxStream用にブラウザから操作できるUIを作りました（Flask製）

    + トップ画面  
!["トップページ"](images/top.png)

    + 画像生成中は、ロック状態となります（負荷かけたくないので一度に１枚ずつ）  
!["画像生成中"](images/generating.png)

+ OnnxStreamはビルドの仕方が随分簡単になった模様

```
git clone https://github.com/vitoplantamura/OnnxStream.git
cd OnnxStream/src
mkdir build
cd build
cmake ..
cmake --build . --config Release
```



最近のバージョンでは自動的に選択したモデルをダウンロードするらしい
さきほどbuildしたフォルダにsdが出来上がっていると思うので、
以下コマンドを入力すると、画像が生成される。
ここで --downloadオプションを付けることによってモデルがダウンロードされる
モデルのダウンロードを行わないと、この先のOnnxSreamWebUIでの画像生成ができないので、
このステップは必ず行ってください。
ただの画像生成のお試しではなく、モデルのダウンロードを兼ねたステップです。

```
./sd --rpi-lowmem --turbo  --prompt "An astronaut riding a horse on Mars" --steps 1 --output astronaut.png --download
```
これで、astronaut.pngが出来上がります。モデルのダウンロードにはやただ時間がかかります。

実は他のモデルも試してみたのですが、時間がかかるわ、クオリティ低いわで使えないと判断しました。今回は、turboだけ使うことにします。ただし、turboだとネガティブプロンプトが使えません。この辺り少し残念に感じますが仕方ありません。


+ ここから本Git(OnnxStreamWebUI)の説明です。cd ~してから、本 git を cloneしてください。
以下を行う前に、上記テストでモデルのダウンロードも完了している必要がありますう。

```
chmod +x launch.sh
./launch.sh
```
Macの場合はlaunch4Mac.shを実行してください

+ 起動確認  
    http://RaspberryPiのURL:5000 を開き
    プロンプトに以下を注入
    ```
    anime stye, a beautiful anime girl in a flower field, detailed illustration, soft sunlight, variant colors, rules of thirds, long flowing hair, big eyes, cute expression, detailed facial features, realistic skin texture, shiny white hair, flowing fabric
    ```
    Stepは1、サイズは512 x 512でのままでOKです

    時間は少しかかりますが、なにやら画像が生成されることでしょう。

+ 最後に  
今回のWebUIでは、turboモデルのみ対応しています。他のモデルをつかってみたところ、使い物にならなかったので、turboだけでいいやという判断をしました。異論があれば受け入れますので、どうぞご連絡ください。

