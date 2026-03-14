from __future__ import annotations

import json
import logging
import os
import re
import requests, base64, os

import urllib.request
import urllib.error

from dotenv import load_dotenv
load_dotenv()

GOOGLE_TTS_KEY = os.getenv("GOOGLE_TTS_API_KEY")

class TTSService:
    def synthesize(self, text: str, language: str = "en") -> str:
        lang_map = {
            "en": ("en-US", "en-US-Neural2-F"),
            "bn": ("bn-BD", "bn-BD-Standard-A"),
            "hi": ("hi-IN", "hi-IN-Neural2-A"),
            "ur": ("ur-PK", "ur-PK-Standard-A"),
            "ar": ("ar-XA", "ar-XA-Neural2-A"),
        }
        lang_code, voice_name = lang_map.get(language, lang_map["en"])

        resp = requests.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_KEY}",
            json={
                "input": {"text": text},
                "voice": {"languageCode": lang_code, "name": voice_name},
                "audioConfig": {"audioEncoding": "MP3"},
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["audioContent"]  # already base64