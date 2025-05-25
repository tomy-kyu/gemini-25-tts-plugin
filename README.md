## Dify Plugin for Google Gemini 2.5 Flash TTS 

**Author:** tomy-kyu
**Version:** 0.0.1
**Type:** tool

### Description

Gemini 2.5 TTSモデルを使ってNotebook LMっぽい感じの対話音声データを生成するプラグインです。やっつけで作ったのでだいぶ作りは微妙です。

* DifyでGemini 2.5 TTSの対話Wavファイルを出力するための処理を作成しました。
  * 使用するモデルはGemini 2.5 Flash TTSで固定しています。
  * 出力形式はwavファイル形式一択です。これはGemini APIで出力する仕様に合わせています。
  * 使用するAPIはGemini APIを想定しています。VertexAIは想定していません。
  * まだプロンプトとして展開する際の制約等がハッキリわかっておらず、場合によっては時間がかかったり、短時間の対話なのに10分無音区間が設定された状態でデータ生成されるなど弱点がありますのでご注意ください。
 
* 入力値
  * API-KEY Gemini APIのキーを入力してください。ENV-Secret型変数を定義することをお勧めします。
  * senario-data 所定フォーマットに沿ったSpeaker 1 とSpeaker 2のセリフデータを入力してください。
    * 私の場合、このセリフデータの出力はGemini 2.5 Pro Preview 05-06に実行させていたりします。
  * temperature 温度サンプリング値です。1.0でもよさげな気がします。Constantで設定をお願いします。

* 出力
 * text string 不具合が起きた時、エラーメッセージはこちらに出力されます。
 * files array/(file) wavファイルが出力されます。Google AI Studioで出力されるものと同じ仕様です。

### 処理時間の目安

* Gemini 2.5 Flashの場合、5分程度のwav出力に凡そ2.5分程度かかるようです。10分の音声データであれば、凡そ6分前後ぐらいでした。

### License

これをベースにもっと多機能なプラグインがあるといいなと思っておりまして、MITライセンスにて公開します。

