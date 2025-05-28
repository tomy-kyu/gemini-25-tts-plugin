from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from typing import Generator, Any, Dict
import base64
import mimetypes
import os
import re
import io
import struct
from google import genai
from google.genai import types

class Gemini25TtsPluginTool(Tool):
    def _invoke(self, tool_parameters: Dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:

        api_key = tool_parameters.get("api_key")
        if not api_key:
            yield self.create_text_message("エラー: GEMINI_API_KEY が設定されていません。Difyの設定を確認してください。")
            return

        tts_model = tool_parameters.get("model")
        if not tts_model:
            yield self.create_text_message("エラー: GEMINI_MODEL が設定されていません。Difyの設定を確認してください。")
            return

        speaker_1 = tool_parameters.get("speaker-1")
        if not speaker_1:
            yield self.create_text_message("エラー: 話者1 が設定されていません。")
            return
        speaker_2 = tool_parameters.get("speaker-2")
        if not speaker_2:
            yield self.create_text_message("エラー: 話者2 が設定されていません。")
            return

        scenario_data = tool_parameters.get("scenario_data")
        if not scenario_data:
            yield self.create_text_message("エラー: パラメータ 'scenario_data' (対話データ) が必要です。")
            return

        static_prompt = tool_parameters.get("static_prompt")
        if not scenario_data:
            yield self.create_text_message("エラー: パラメータ 'static_prompt' (場面設定、話者設定文) が必要です。")
            return

        # Ensure temperature is float, default to 1.0 if not provided or invalid
        try:
            temperature = float(tool_parameters.get("temperature", 1.0))
        except (ValueError, TypeError):
            temperature = 1.0


        full_text_input = f"{static_prompt}\n{scenario_data}"

        try:
            audio_data_bytes, mime_type_from_api = self._generate_gemini_tts(
                api_key=api_key,
                text_input=full_text_input,
                tts_model=tts_model,
                speaker_1=speaker_1,
                speaker_2=speaker_2,
                temperature=temperature
            )

            if audio_data_bytes and mime_type_from_api:
                # The requirement is to output .wav
                # The original script's save_binary_file would save with an extension based on
                # mime_type or convert to .wav if it's raw PCM.
                if mime_type_from_api.lower() == "audio/wav":
                    final_audio_data = audio_data_bytes
                elif mime_type_from_api.lower().startswith("audio/l") or "pcm" in mime_type_from_api.lower():
                    # If it's raw PCM (e.g., audio/L16;rate=24000), convert to WAV
                    final_audio_data = self._convert_to_wav(audio_data_bytes, mime_type_from_api)
                else:
                    # If the API returns something else (e.g. audio/mpeg for MP3)
                    # and we must output WAV, this is an issue.
                    # The original script's convert_to_wav only handles raw PCM to WAV.
                    yield self.create_text_message(
                        f"エラー: APIから予期しないMIMEタイプ ({mime_type_from_api}) を受信しました。 "
                        f"audio/wav または raw PCM (例: audio/L16) を期待しています。この形式はWAVに変換できません。"
                    )
                    return
                yield self.create_blob_message(blob=final_audio_data, meta={"mime_type": "audio/wav"})
     
            elif audio_data_bytes is None and mime_type_from_api is None: # Explicitly no data
                 yield self.create_text_message("エラー: APIから音声データが返されませんでした。")

            else: # Should not happen if the helper returns consistent tuples
                yield self.create_text_message("エラー: 音声データの生成中に予期せぬ状態になりました。")

        except AttributeError as e_attr:
            yield self.create_text_message(
                f"エラー: Gemini SDKの型またはメソッドが見つかりません: {e_attr}。 "
                "元のスクリプトと互換性のあるSDKバージョンがDify環境にインストールされているか確認してください。"
                )
            
        except RuntimeError as e_runtime: # Catch custom runtime errors from helper
            yield self.create_text_message(f"ランタイムエラー: {e_runtime}")
        except Exception as e:
            # Catching other potential errors from the genai library or other issues.
            # For genai specific errors like BlockedPromptException, they would need to be
            # imported from genai.types.generation_types if that path exists.
            # e.g. except genai.types.generation_types.BlockedPromptException as bpe:
            yield self.create_text_message(f"エラー: Gemini TTS サービスで予期せぬ問題が発生しました: {str(e)}")

    def _generate_gemini_tts(
            self, api_key: str, text_input: str, temperature: float, tts_model: str, speaker_1: str, speaker_2: str
    ) -> tuple[bytes | None, str | None]:
        """
        Generates speech using the Gemini API, strictly following the structure
        of the user-provided original script.
        Returns a tuple: (audio_bytes, mime_type_from_api) or (None, None) on failure.
        """

        # 1. Initialize Client (as per original script)
        # The original script uses: client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        # We adapt this to use the passed api_key.
        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            raise RuntimeError(f"Geminiクライアントの初期化に失敗しました ({type(e).__name__}: {e})。"
                               "SDKが正しくインストールされ、`genai.Client(api_key=...)` が有効か確認してください。")

        # 2. Define Model Name
        #model_name = "gemini-2.5-pro-preview-tts" # As specified in the original script
        model_name = tts_model
        #print(text_input)
        # 3. Prepare Contents (as per original script)
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=text_input),
                    ],
                ),
            ]
            #print (types.Part.from_text(text=text_input))
        except AttributeError as e:
            raise AttributeError(f"genai.types.Content または genai.types.Part.from_text の定義エラー: {e}。"
                                 "SDKの型定義を確認してください。")

        # 4. Prepare GenerateContentConfig (as per original script)
        try:
            speech_config_payload = types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker="Speaker 1",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=speaker_1)
                            )
                        ),
                        types.SpeakerVoiceConfig(
                            speaker="Speaker 2",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=speaker_2)
                            )
                        ),
                    ]
                )
            )

            generate_content_config_payload = types.GenerateContentConfig(
                temperature=temperature,
                response_modalities=["audio"],
                speech_config=speech_config_payload,
            )
        except AttributeError as e:
            raise AttributeError(f"types の設定クラス (GenerateContentConfig, SpeechConfig等) の定義エラー: {e}。"
                                 "SDKの型定義を確認してください。")

        # 5. Call API and Stream Response (as per original script)
        audio_buffer_chunks = []
        mime_type_from_api = None

        try:
            # The original script uses client.models.generate_content_stream(...)
            stream = client.models.generate_content_stream(
                model=model_name, # Passing the model name string directly
                contents=contents,
                config=generate_content_config_payload, # Using the variable from original script
            )

            for chunk in stream:
                if (
                    chunk.candidates is None
                    or not chunk.candidates  # Check if list is empty
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                    or not chunk.candidates[0].content.parts  # Check if list is empty
                ):
                    continue # Skip malformed chunks

                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and hasattr(part.inline_data, 'data') and hasattr(part.inline_data, 'mime_type'):
                    if mime_type_from_api is None: # Capture MIME type from the first relevant chunk
                        mime_type_from_api = part.inline_data.mime_type
                    audio_buffer_chunks.append(part.inline_data.data)
                # else:
                    # Original script had: print(chunk.text)
                    # This could be useful for debugging or if non-audio parts are expected.
                    # For this TTS tool, we primarily focus on audio.
                    # if chunk.text:
                    #   print(f"Debug: Received text part: {chunk.text}")
        except Exception as e: # Catch other API call errors
            raise RuntimeError(f"Gemini APIの呼び出し中にエラーが発生しました ({type(e).__name__}: {e})。")


        if not audio_buffer_chunks or mime_type_from_api is None:
            return None, None # No valid audio data extracted

        return b"".join(audio_buffer_chunks), mime_type_from_api


    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """
        Converts raw PCM audio data to WAV format bytes.
        Estimates sample rate and bit depth from the MIME type.
        (This function is based on the user's original script's helper functions)
        """
        parameters = self._parse_audio_mime_type(mime_type)
        # Use parsed values, or fallback to defaults similar to original script's context
        bits_per_sample = parameters.get("bits_per_sample", 16)
        sample_rate = parameters.get("rate", 24000)

        num_channels = 1  # Mono, as per original script's implicit assumption for WAV header
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        if bytes_per_sample == 0: # Avoid division by zero if bits_per_sample is < 8 (e.g. L4, L1)
            raise ValueError("Bits per sample must be 8 or higher for this WAV conversion.")
            
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize (total file size - 8 bytes)
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (16 for PCM)
            1,                # AudioFormat (1 for PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size (size of audio data)
        )
        return header + audio_data

    def _parse_audio_mime_type(self, mime_type: str) -> Dict[str, int | None]:
        """
        Parses bits per sample and rate from an audio MIME type string.
        (This function is based on the user's original script's helper functions)
        Example: "audio/L16;rate=24000" -> {"bits_per_sample": 16, "rate": 24000}
        Uses defaults from original script (16 bits, 24000 Hz) if parsing fails.
        """
        parsed_bits_per_sample = None
        parsed_rate = None

        # Defaults from the original script's context
        default_bits_per_sample = 16
        default_rate = 24000

        # Normalize and split MIME type
        mime_type_lower = mime_type.lower()
        parts = [p.strip() for p in mime_type_lower.split(';')]

        # Parse the main type for bits (e.g., "audio/l16")
        main_type = parts[0]
        if main_type.startswith("audio/l"):
            try:
                bits_str = main_type.split('l', 1)[1]
                parsed_bits_per_sample = int(bits_str)
            except (ValueError, IndexError, TypeError):
                pass # Keep as None, will use default

        # Parse parameters for rate (e.g., "rate=24000")
        for param in parts[1:]:
            if param.startswith("rate="):
                try:
                    rate_str = param.split('=', 1)[1]
                    parsed_rate = int(rate_str)
                except (ValueError, IndexError, TypeError):
                    pass # Keep as None, will use default
                break # Rate found

        return {
            "bits_per_sample": parsed_bits_per_sample if parsed_bits_per_sample is not None else default_bits_per_sample,
            "rate": parsed_rate if parsed_rate is not None else default_rate,
        }
