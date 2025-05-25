## Dify Plugin for Google Gemini 2.5 Flash TTS 

**Author:** tomy-kyu
**Version:** 0.1.0
**Type:** tool

### Description

* DifyでGemini 2.5 TTSの対話Wavファイルを出力するための処理を作成しました。
  * 使用するモデルはGemini 2.5 Flash TTSで固定しています。
  * 出力形式はwavファイル形式一択です。これはGemini APIで出力する仕様に合わせています。
  * 使用するAPIはGemini APIを想定しています。VertexAIは想定していません。
  * まだプロンプトとして展開する際の制約等がハッキリわかっておらず、場合によっては時間がかかったり、短時間の対話なのに10分無音区間が設定された状態でデータ生成されるなど弱点がありますのでご注意ください。

### License

原作のプラグインと同様に、MITライセンスにて公開します。


