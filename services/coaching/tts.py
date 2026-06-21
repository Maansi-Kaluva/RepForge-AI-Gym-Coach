from io import BytesIO
from gtts import gTTS

ORPHEUS_MODEL = "canopylabs/orpheus-v1-english"
ORPHEUS_VOICE = "troy"
MAX_ORPHEUS_CHARS = 200  # Orpheus hard limit per call

class TextToSpeech:
    def __init__(self, groq_client):
        self.client = groq_client

    def speak(self, text, lang="en"):
        cleaned_text = (text or "").strip()

        if not cleaned_text:
            return None

        try:
            response = self.client.audio.speech.create(
                model=ORPHEUS_MODEL,
                voice=ORPHEUS_VOICE,
                input=cleaned_text[:MAX_ORPHEUS_CHARS],
                response_format="wav"
            )
            return response.read()
        except Exception as e:
            print(f"Orpheus TTS Error: {e} — falling back to gTTS")
            return self._gtts_fallback(cleaned_text, lang)

    def _gtts_fallback(self, text, lang):
        try:
            buffer = BytesIO()
            gTTS(text=text, lang=lang, slow=False, tld="co.in").write_to_fp(buffer)
            buffer.seek(0)
            return buffer.read()
        except Exception as e:
            print(f"gTTS fallback Error: {e}")
            return None