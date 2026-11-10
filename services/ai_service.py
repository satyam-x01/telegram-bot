import os
import sys
import json
import re
import asyncio
import mimetypes
import warnings
from pathlib import Path
from typing import Dict, Optional

# Ensure parent directory is in sys.path when script is executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import requests

# Working Gemini model names (updated Sept 2026)
# Use fastest models first for instant sub-3-second responses
GEMINI_MODELS = ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-2.5-flash', 'gemini-2.0-flash']


class _GeminiResponse:
    def __init__(self, payload: dict):
        self.payload = payload
        parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        self.text = "".join(part.get("text", "") for part in parts)


class _GeminiFile:
    def __init__(self, payload: dict, mime_type: str):
        file_info = payload.get("file", {})
        self.uri = file_info.get("uri", "")
        self.mime_type = file_info.get("mime_type") or mime_type


class _GeminiRESTModels:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_content(self, model: str, contents):
        if not isinstance(contents, list):
            contents = [contents]
        parts = []
        for item in contents:
            if isinstance(item, _GeminiFile):
                parts.append({"file_data": {"mime_type": item.mime_type, "file_uri": item.uri}})
            else:
                parts.append({"text": str(item)})
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": self.api_key},
            json={"contents": [{"parts": parts}]},
            timeout=45,
        )
        response.raise_for_status()
        return _GeminiResponse(response.json())


class _GeminiRESTFiles:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def upload(self, file):
        path = Path(file)
        mime_type = mimetypes.guess_type(path.name)[0] or "audio/ogg"
        size = path.stat().st_size
        start = requests.post(
            "https://generativelanguage.googleapis.com/upload/v1beta/files",
            params={"key": self.api_key},
            headers={
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Header-Content-Length": str(size),
                "X-Goog-Upload-Header-Content-Type": mime_type,
                "Content-Type": "application/json",
            },
            json={"file": {"display_name": path.name}},
            timeout=45,
        )
        start.raise_for_status()
        upload_url = start.headers.get("X-Goog-Upload-URL")
        if not upload_url:
            raise RuntimeError("Gemini upload URL was not returned")
        with path.open("rb") as stream:
            uploaded = requests.post(
                upload_url,
                headers={
                    "Content-Length": str(size), "X-Goog-Upload-Offset": "0",
                    "X-Goog-Upload-Command": "upload, finalize",
                },
                data=stream,
                timeout=90,
            )
        uploaded.raise_for_status()
        return _GeminiFile(uploaded.json(), mime_type)


class _GeminiRESTClient:
    """Small SDK-compatible Gemini REST adapter; works on Termux without Rust wheels."""
    def __init__(self, api_key: str):
        self.models = _GeminiRESTModels(api_key)
        self.files = _GeminiRESTFiles(api_key)

class AIService:
    def __init__(self):
        raw_keys = config.GEMINI_API_KEY
        self.api_keys = [k.strip() for k in raw_keys.split(",") if k.strip() and k.strip() != "your_gemini_api_key_here"]
        self.current_key_idx = 0
        self.enabled = len(self.api_keys) > 0

    def _get_client(self):
        if not self.enabled:
            return None
        current_key = self.api_keys[self.current_key_idx]
        return _GeminiRESTClient(current_key)

    def _rotate_key(self):
        if len(self.api_keys) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
            print(f"🔄 Rotated to Gemini API key index {self.current_key_idx+1}/{len(self.api_keys)}")

    def identify_song_from_description(self, user_description: str) -> Optional[Dict]:
        """Analyze song tune, lyrics fragment, vibe, or description using Gemini AI with key rotation."""
        if not self.enabled:
            return None

        prompt = f"""
You are the world's best music identifier AI for a Telegram Music Bot.
A user is describing a song tune, hummed lyrics, background music vibe, or description:

User Query: "{user_description}"

Task:
Identify the best real song title and artist matching this description.
Respond in EXACT JSON format ONLY:
{{
  "found": true,
  "song_title": "Song Title",
  "artist": "Artist Name",
  "search_query": "Full song title and artist for Youtube search",
  "reason": "Brief 1-sentence explanation why this song matches"
}}
"""
        MODELS = GEMINI_MODELS
        attempts = len(self.api_keys) if self.api_keys else 1
        for _ in range(attempts):
            client = self._get_client()
            if not client:
                return None
            for model_name in MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        text = response.text.strip()
                        match = re.search(r"\{.*\}", text, re.DOTALL)
                        if match:
                            return json.loads(match.group(0))
                except Exception as e:
                    print(f"AI song identification error with model {model_name} (key {self.current_key_idx+1}): {e}")
                    continue
            self._rotate_key()

        return None

    def identify_song_from_audio(self, audio_file_path: str) -> Optional[Dict]:
        """Identify song tune/lyrics from a voice note or audio clip with key rotation."""
        if not self.enabled:
            return None

        prompt = """
Listen carefully to this voice note / hummed tune / audio recording.
Identify the song being hummed, sung, or played in the background.
Respond in EXACT JSON format ONLY:
{
  "found": true,
  "song_title": "Exact Title",
  "artist": "Artist Name",
  "search_query": "Song Title Artist Name",
  "reason": "Brief explanation"
}
"""
        MODELS = GEMINI_MODELS
        attempts = len(self.api_keys) if self.api_keys else 1
        for _ in range(attempts):
            client = self._get_client()
            if not client:
                return None
            try:
                uploaded_file = client.files.upload(file=Path(audio_file_path))
                for model_name in MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[uploaded_file, prompt]
                        )
                        if response and response.text:
                            text = response.text.strip()
                            match = re.search(r"\{.*\}", text, re.DOTALL)
                            if match:
                                return json.loads(match.group(0))
                    except Exception as e:
                        print(f"AI audio identification error with model {model_name} (key {self.current_key_idx+1}): {e}")
                        continue
            except Exception as e:
                print(f"AI audio upload error with key {self.current_key_idx+1}: {e}")
                self._rotate_key()

        return None

    async def search_astronomy_or_code(self, query: str, user_lang: str = "en") -> str:
        """Search astronomy, NASA missions, exoplanet discoveries OR answer code/error troubleshooting queries."""
        if not self.enabled:
            return "❌ AI search is currently disabled. Please check your GEMINI_API_KEY."

        prompt = f"""
You are the AI Space & Astrophysics Expert and Tech Advisor for an Astronomy Telegram Bot.
The user is asking a query via /search: "{query}"

Instructions:
1. If the query is about Astronomy, NASA, Planets, Black Holes, Space Missions, or Cosmology:
   Provide an engaging, scientifically accurate answer with emojis, key facts, and clear structure.
2. If the user is asking about an Error, Bug, Python code, or "why showing error":
   Analyze the error/bug carefully, explain WHY the error happens step-by-step, and provide the exact fix code/solution!
3. Language format: Respond naturally in clear, easy-to-understand Hinglish or English based on user's language choice ("{user_lang}").

Keep response clean, beautiful, formatted for Telegram MarkdownV2 or plain text with emojis.
Keep the answer concise (under 500 words).
"""
        MODELS = GEMINI_MODELS
        attempts = len(self.api_keys) if self.api_keys else 1
        for _ in range(attempts):
            client = self._get_client()
            if not client:
                return "❌ Unable to connect to Gemini AI."
            for model_name in MODELS:
                try:
                    # Run the blocking API call in a thread with a 15-second timeout
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.models.generate_content,
                            model=model_name,
                            contents=prompt
                        ),
                        timeout=15.0
                    )
                    if response and response.text:
                        return response.text.strip()
                except asyncio.TimeoutError:
                    print(f"AI search TIMEOUT with model {model_name} (15s limit)")
                    continue
                except Exception as e:
                    print(f"AI search error with model {model_name}: {e}")
                    continue
            self._rotate_key()

        return "❌ Search request failed due to API limit or network error. Please try again in a few moments."

    def generate_hourly_funfact(self) -> Dict[str, str]:
        """Generate a fascinating hourly astronomy fun fact and exoplanet update."""
        default_facts = [
            {
                "title": "🌌 Neutron Stars are Mind-Bogglingly Dense!",
                "fact": "A single teaspoon of a neutron star would weigh about 6 billion tons on Earth — equivalent to the weight of Mount Everest!",
                "topic": "Neutron Stars"
            },
            {
                "title": "🪐 Sunset on Mars is Blue!",
                "fact": "Sunsets on Mars appear blue to human eyes because fine dust particles in the thin Martian atmosphere scatter red light and let blue light pass through.",
                "topic": "Mars Atmosphere"
            },
            {
                "title": "💎 Diamond Rain on Saturn & Jupiter!",
                "fact": "High pressure and lightning in the upper atmospheres of Saturn and Jupiter crush methane gas into diamond hail falling thousands of miles down!",
                "topic": "Gas Giants"
            },
            {
                "title": "🔭 One Space Year in Venus!",
                "fact": "Venus rotates so slowly that a day on Venus (243 Earth days) is actually LONGER than its year (225 Earth days)!",
                "topic": "Venus Rotation"
            }
        ]

        if not self.enabled:
            return random.choice(default_facts)

        prompt = """
Generate ONE exciting, surprising, mind-blowing Astronomy Fun Fact or New Exoplanet Discovery snippet for our 24/7 Telegram Astronomy Bot.
Format as JSON:
{
  "title": "Catchy Title with Emoji",
  "fact": "Detailed 2-3 sentence mind-blowing space fact written in engaging style.",
  "topic": "Topic Name"
}
"""
        MODELS = GEMINI_MODELS
        attempts = len(self.api_keys) if self.api_keys else 1
        for _ in range(attempts):
            client = self._get_client()
            if not client:
                return random.choice(default_facts)
            for model_name in MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        match = re.search(r"\{.*\}", response.text.strip(), re.DOTALL)
                        if match:
                            return json.loads(match.group(0))
                except Exception as e:
                    print(f"Funfact AI generation error with model {model_name}: {e}")
                    continue
            self._rotate_key()

        return random.choice(default_facts)

    def generate_study_content(self, context_dict: Dict) -> str:
        """Generate high-yield notes, textbook solutions, exam cheatsheets, or research via Gemini AI."""
        mode = context_dict.get("mode", "notes")
        topic = context_dict.get("topic", "")
        subject = context_dict.get("subject", "")
        board = context_dict.get("board", "")
        standard = context_dict.get("standard", "")
        exam = context_dict.get("exam", "")
        query = context_dict.get("query", "")

        if mode == "notes":
            prompt = f"""
You are an expert Indian education mentor and textbook author for {board} ({standard}).
Generate comprehensive, high-scoring STUDY NOTES & SUMMARY for:
Subject: {subject}
Lesson / Chapter: "{topic}"

Please format your response cleanly in Telegram Markdown:
1. 📖 **Overview & Central Theme** (Clear, engaging summary)
2. 🔑 **Key Concepts & Important Points** (Bullet points, definitions, formulas or poem meaning)
3. 💡 **Character Analysis / Scientific Principles** (Key elements explained simply)
4. 🎯 **High-Yield Exam Takeaways** (What examiners frequently ask)
5. 🌐 **Recommended Free Websites & Resources** (e.g. Shaalaa.com, Balbharati, LearnCBSE, Khan Academy, PW)
Keep it structured, thorough, easy to read for a student, and strictly under 3500 characters.
"""
        elif mode == "solutions":
            prompt = f"""
You are an expert textbook solution guide for {board} ({standard}).
Provide detailed TEXTBOOK QUESTIONS & STEP-BY-STEP SOLUTIONS for:
Subject: {subject}
Lesson / Chapter: "{topic}"

Please format your response cleanly in Telegram Markdown:
1. ❓ **Major Textbook Questions & Model Answers** (Provide 4-5 core exercise questions with complete high-scoring answers)
2. 📝 **Grammar / Working Steps / Numericals / Extracts** (Explain key working steps or language study)
3. ⚠️ **Common Mistakes to Avoid in Board Exams**
4. 🌐 **Where to find full PDF solutions:** (Mention Shaalaa.com, Target Publications, LearnCBSE, etc.)
Keep the answers clear, formatted with bullet points, and under 3500 characters.
"""
        elif mode == "exam_cheatsheet":
            prompt = f"""
You are India's top competitive exam mentor for {exam}.
Generate an intensive, high-yield FORMULA CHEATSHEET & REVISION GUIDE for {exam}.
Specific subject or focus: {subject or 'Full Syllabus'}

Format in Telegram Markdown:
1. ⚡ **Top Formulas & Must-Know Equations**
2. 📌 **Shortcuts, Tricks & Dimensional Analysis tips**
3. 🎯 **High-Weightage Chapters (80/20 Rule)**
4. 🧠 **Quick Memory Hacks & Mnemonics**
Keep it ultra-high-yield, precise, and under 3500 characters.
"""
        elif mode == "exam_pyq":
            prompt = f"""
You are a competitive exam analyst for {exam}.
Provide a deep-dive PAST YEAR QUESTIONS (PYQ) TREND ANALYSIS & SAMPLE SOLVED PROBLEMS for {exam}.
Subject: {subject or 'Key Subjects'}

Format in Telegram Markdown:
1. 📊 **Past 5-Year Question Distribution & Weightage Trends**
2. 📝 **Sample Solved PYQs with Step-by-Step Logic**
3. ⚠️ **Trickiest Traps set by Examiners**
4. 🏆 **Recommended PYQ Books & Apps** (e.g. Marks App, MTG 36 Years, Disha, PW)
Keep it practical, motivating, and under 3500 characters.
"""
        elif mode == "exam_research":
            prompt = f"""
You are an expert educational researcher and tech reviewer.
Conduct a detailed research analysis on:
"Best websites, mobile apps, YouTube channels, and study materials for {exam or topic}."

Format in Telegram Markdown:
1. 🌐 **Top 5 Free & Best Websites** (Official portals, free mock test sites, notes archives with links)
2. 📱 **Top 4 Mobile Apps** (For mock tests, revision, formula flashcards, PYQ practice)
3. 🎥 **Best YouTube Teachers / Channels** (For concept building & one-shot revisions)
4. 📚 **Standard Reference Books Recommended by Toppers**
5. ⏱ **Winning Daily Study Routine & Strategy**
Keep it comprehensive, honest, and under 3500 characters.
"""
        else:
            prompt = f"""
You are an expert tutor in Indian curriculum ({board}, {standard}, {exam}).
User study inquiry: "{query or topic}"

Provide a detailed, clear, high-scoring explanation with examples, formulas, or study guidance.
Format cleanly in Telegram Markdown under 3500 characters.
"""

        MODELS = GEMINI_MODELS
        attempts = len(self.api_keys) if self.api_keys else 1
        for _ in range(attempts):
            client = self._get_client()
            if not client:
                break
            for model_name in MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    print(f"Study AI error with model {model_name}: {e}")
                    continue
            self._rotate_key()

        return f"""
📚 *{topic or exam}* — Study Guide & Resources

📌 *Subject / Focus:* {subject or 'General'}
🏫 *Curriculum:* {board or exam} {standard}

💡 *Key Revision Points:*
• Review core definitions, fundamental laws, and textbook diagrams.
• Solve all end-of-chapter textbook exercise questions twice.
• Practice past 5 years' board/exam question papers with a timer.

🌐 *Recommended Top Free Websites:*
• [Shaalaa.com](https://www.shaalaa.com) — Free Maharashtra Board & CBSE Solutions
• [LearnCBSE.in](https://www.learncbse.in) — NCERT Textbook Solutions & Notes
• [Khan Academy](https://www.khanacademy.org) — Interactive Concept Videos
• [Physics Wallah](https://www.pw.live) — Top Free Lecture Notes & Question Banks
"""

ai_service = AIService()
