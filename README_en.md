## Dify Plugin for Google Gemini 2.5 Flash TTS

**Author:** tomy-kyu
**Version:** 0.1.0
**Type:** tool

### Description

This plugin generates conversational audio data similar to Notebook LM using the Gemini 2.5 TTS model. It was created quickly, so the design is somewhat rough.

* Created processing to output Gemini 2.5 TTS dialogue WAV files using Dify.
* The output format is limited to WAV files. This aligns with the Gemini API output specifications.
* The API used is intended for the Gemini API. VertexAI is not supported.
* There are still some limitations when expanding prompts, such as unclear constraints, which may result in longer processing times or data generation with 10-minute silent intervals even for short dialogues. Please be aware of these limitations.

* Input values
* API-KEY Enter your Gemini API key. We recommend defining it as an ENV-Secret type variable.
* senario-data Enter the dialogue data for Speaker 1 and Speaker 2 in the specified format.
* In my case, I run this dialogue data output using Gemini 2.5 Pro Preview 05-06.
* static_prompt Enter scene settings and settings for each speaker. Provide instructions on the tone in which they should speak.
* This will be set at the beginning of the message sent to Gemini.
* temperature Temperature sampling value. 1.0 seems adequate. Please set to Constant.
* model Select the TTS model to use. Choose from two options.
* speaker-1 Specifies the voice for Speaker 1 (the moderator). Choose from 30 voices.
* speaker-2 Specifies the voice for speaker 2 (the person answering). The list is the same as for Speaker-1.

* Output values
* text string Error messages will be output here if an error occurs.
* files array/(file) WAV files will be output. The same specifications as those output by Google AI Studio.

### Estimated processing time

* For Gemini 2.5 Flash, it takes approximately 2.5 minutes to output a 5-minute WAV file. For a 10-minute audio file, it took approximately 6 minutes.

### License

I would like to create a more feature-rich plugin based on this, so I am releasing it under the MIT license.
