from io import BytesIO
from gtts import gTTS

class TextToSpeech:
    def speak(self, text, lang="en"):
        cleaned_text = (text or "").strip()

        if not cleaned_text:
            return None

        try:
            buffer = BytesIO()

            gTTS(
                text=cleaned_text,
                lang=lang,
                slow=False
            ).write_to_fp(buffer)

            buffer.seek(0)
            return buffer.read()

        except Exception as e:
            print(f"TTS Error: {e}")
            return None