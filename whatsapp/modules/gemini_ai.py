import io
import re
import logging
from datetime import datetime
from typing import Optional, List, Dict
from PIL import Image

from modules.config import config_manager, logger

# Ordered list of high-quota free tier models for automatic failover
MODEL_FALLBACK_LIST = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash"
]

class GeminiService:
    def __init__(self):
        self._client = None
        self._last_key = None
        self._user_clients: Dict[str, Any] = {}

    def get_client(self, api_key: Optional[str] = None):
        if api_key and api_key.strip():
            clean_key = api_key.strip()
            if clean_key not in self._user_clients:
                try:
                    from google import genai
                    self._user_clients[clean_key] = genai.Client(api_key=clean_key)
                    logger.info("Initialized custom user GenAI Client.")
                except Exception as e:
                    logger.error(f"Failed to initialize custom GenAI Client: {e}")
                    return None
            return self._user_clients[clean_key]

        current_key = config_manager.get("gemini_api_key", "").strip()
        if not current_key:
            return None
        if self._client is None or self._last_key != current_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=current_key)
                self._last_key = current_key
                logger.info("Initialized Google GenAI Client with updated key.")
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")
                self._client = None
        return self._client

    def is_available(self, api_key: Optional[str] = None) -> bool:
        return self.get_client(api_key=api_key) is not None

    def validate_api_key(self, api_key: str) -> tuple[bool, str]:
        """Test a given API key with a quick ping to verify validity."""
        clean_key = api_key.strip()
        if not clean_key:
            return False, "API key cannot be empty."
        if len(clean_key) < 20 or any(c.isspace() for c in clean_key):
            return False, "API key format invalid. Please copy the complete key from Google AI Studio without spaces."
        try:
            from google import genai
            test_client = genai.Client(api_key=clean_key)
            # Fast verification via models.list (works instantly for all valid AQ. and AIzaSy keys)
            first_model = next(iter(test_client.models.list()), None)
            if first_model:
                self._user_clients[clean_key] = test_client
                return True, "Valid"
            return False, "No models accessible with this API key."
        except Exception as e:
            err_m = str(e)
            logger.warning(f"Key validation exception: {err_m}")
            if any(term in err_m for term in ["API_KEY_INVALID", "PERMISSION_DENIED", "UNAUTHENTICATED", "401", "400", "403"]) or "not valid" in err_m.lower():
                return False, "API key is invalid or unauthorized. Please verify your key on Google AI Studio."
            return False, f"Verification failed: {err_m[:80]}"

    def check_creator_query(self, user_text: str) -> Optional[str]:
        """Check if user is asking who created/made the bot and reply in the same language."""
        text = user_text.lower().strip()
        creator_name = config_manager.get("creator_name", "Satyam Developer")

        hindi_patterns = ["kisne banaya", "kisne banaya he", "kisne banaya hai", "kaun banaya", "kisne develop kiya", "banane wala kaun"]
        english_patterns = ["who made", "who created", "who is the developer", "who developed", "who built", "who created this bot"]

        for p in hindi_patterns:
            if p in text:
                return f"🤖 Yeh WhatsApp bot *{creator_name}* ne banaya hai."

        for p in english_patterns:
            if p in text:
                return f"🤖 This WhatsApp bot was created by *{creator_name}*."

        if "who" in text and ("creator" in text or "author" in text or "developer" in text):
            return f"🤖 This WhatsApp bot was created by *{creator_name}*."

        return None

    def check_image_generation_query(self, user_text: str) -> Optional[str]:
        """Check if user is asking to generate images (which the bot strictly does not do)."""
        text = user_text.lower()
        gen_patterns = [
            "generate image", "create image", "photo banao", "image banao", "draw",
            "make a photo", "generate picture", "photo generate", "image generate"
        ]
        for p in gen_patterns:
            if p in text:
                return "⚠️ Main photos analyze kar sakta hoon (photo send karne par), par photo generate karke nahi de sakta. (I can analyze photos, but I do not generate images.)"
        return None

    def generate_with_fallback(self, contents, system_prompt: str = "", enable_google_search: bool = False, api_key: Optional[str] = None) -> Optional[str]:
        """Attempt generation with auto-failover across free-tier high quota models."""
        client = self.get_client(api_key=api_key)
        if not client:
            return None

        configured_model = config_manager.get("gemini_model", "gemini-2.5-flash")
        models_to_try = [configured_model] + [m for m in MODEL_FALLBACK_LIST if m != configured_model]

        # If google search is enabled, prioritize models known to support search grounding
        if enable_google_search:
            search_priority = ["gemini-2.5-flash", "gemini-flash-latest"]
            models_to_try = search_priority + [m for m in models_to_try if m not in search_priority]

        call_config = {}
        if enable_google_search:
            call_config["tools"] = [{"google_search": {}}]

        for model in models_to_try:
            try:
                full_contents = contents
                if system_prompt:
                    if isinstance(contents, str):
                        full_contents = f"{system_prompt}\n\n{contents}"
                    elif isinstance(contents, list):
                        full_contents = [system_prompt] + contents

                kwargs = {"model": model, "contents": full_contents}
                if call_config:
                    kwargs["config"] = call_config

                response = client.models.generate_content(**kwargs)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning(f"Quota exhausted on model '{model}', switching to next free model...")
                    continue
                elif "503" in err_str or "UNAVAILABLE" in err_str or "404" in err_str:
                    logger.warning(f"Model '{model}' temporarily unavailable ({err_str[:40]}), trying next model...")
                    continue
                else:
                    logger.error(f"Error with model '{model}': {e}")
                    # If failed with search config, retry without search config on same or next model
                    continue

        return None

    def chat_response(self, user_message: str, chat_context: str = "", api_key: Optional[str] = None, user_name: str = "User") -> str:
        """Handle standard chat and questions with auto-failover, personalized for user."""
        # 1. Creator check
        creator_ans = self.check_creator_query(user_message)
        if creator_ans:
            return creator_ans

        # 2. Image generation refusal
        img_gen_refusal = self.check_image_generation_query(user_message)
        if img_gen_refusal:
            return img_gen_refusal

        # 3. Check client
        client = self.get_client(api_key=api_key)
        if not client:
            if api_key:
                return (
                    "⚠️ Your personal Gemini API Key is invalid or not working.\n"
                    "Please check your key and update with `/key <YOUR_API_KEY>`."
                )
            return (
                "⚠️ Gemini API Key not set yet.\n"
                "Please configure your Gemini API Key in the localhost dashboard (http://localhost:5000) or `.env`."
            )

        safe_name = user_name.strip() if user_name and user_name.strip() else "User"
        system_instruction = (
            f"You are an elite, smart personal WhatsApp AI assistant chatting with {safe_name}.\n"
            f"Address the user naturally as {safe_name} when greeting them (never assume their name is someone else).\n"
            "Keep your responses concise, friendly, and beautifully formatted for WhatsApp (use *bold*, bullet points, and clean dividers).\n"
            "If asked who created or developed this bot in any language, answer that Satyam Developer created it in that exact language.\n"
            "Never offer to generate images; clarify you can analyze user-sent photos.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "GLOBAL RESPONSE & EVALUATION SYSTEM:\n"
            "1. NEVER use one universal template. The type of query determines structure, metrics, and length.\n"
            "2. Whenever evaluating apps, games, AI tools, models, APIs, projects, courses, hardware, or services, use the 5-point visual rating bars:\n"
            "   █████ = 5/5\n"
            "   ████░ = 4/5\n"
            "   ███░░ = 3/5\n"
            "   ██░░░ = 2/5\n"
            "   █░░░░ = 1/5\n"
            "3. Category-specific metrics only (e.g. Games: Graphics/Gameplay/Performance; AI: Quality/Speed/Free Tier; Apps: Features/UI/Privacy; GitHub: Popularity/Activity/Docs).\n"
            "4. Clearly distinguish real user data (Play Store stars, GitHub stars) from AI assessment. Never invent fake ratings or stats.\n"
            "5. For comparisons: Use side-by-side comparison bars with BEST OVERALL and BEST FOR YOU.\n"
            "6. For tutorials: Use Goal, Requirements, Step-by-Step, Tips, Expected Result.\n"
            "7. For simple data (gold/crypto/currency/weather): Keep it extremely concise without giant cards or irrelevant pros/cons.\n"
            "8. Length intelligence: Simple facts -> very short; News -> concise; Tools/Apps -> medium; Games/AI -> detailed.\n"
            "9. Personalization context: Android, OPPO F21s Pro (CPH2461), Termux, OpenClaw, GitHub, Open Source, AI, Ollama, Programming, Web/Game Dev, Gaming, Anime, Astronomy, Privacy, Productivity, Student Opportunities.\n"
            "10. Finish with an appropriate verdict (⭐⭐⭐⭐⭐ HIGHLY RECOMMENDED | 🟢 WORTH TRYING | 🟡 MAYBE | 🔴 SKIP) when evaluating."
        )

        prompt = f"User Question: {user_message}"
        if chat_context:
            prompt = f"Context: {chat_context}\n\nUser Question: {user_message}"

        answer = self.generate_with_fallback(prompt, system_instruction, api_key=api_key)
        if answer:
            return answer

        return "⚠️ All AI models are currently busy with high traffic. Please try your question again in a moment."

    def analyze_image(self, image_data: bytes, user_prompt: str = "", api_key: Optional[str] = None) -> str:
        """Analyze a photo sent by the user using Gemini Vision with auto-failover."""
        creator_ans = self.check_creator_query(user_prompt)
        if creator_ans:
            return creator_ans

        img_gen_refusal = self.check_image_generation_query(user_prompt)
        if img_gen_refusal:
            return img_gen_refusal

        client = self.get_client(api_key=api_key)
        if not client:
            if api_key:
                return "⚠️ Your personal Gemini API Key is invalid. Please update it using `/key <API_KEY>`."
            return "⚠️ Gemini API Key is required to analyze photos. Please add it via Web Dashboard or set your own with `/key`."

        try:
            image = Image.open(io.BytesIO(image_data))
            prompt_text = user_prompt.strip() or "Please describe and analyze this image in detail. Extract any text, objects, and key insights."
            full_prompt = (
                "You are an intelligent visual analysis assistant for WhatsApp. "
                "Analyze the provided image accurately. "
                "Format cleanly with bullet points and bold headers for WhatsApp readability. "
                f"User instructions: {prompt_text}"
            )

            answer = self.generate_with_fallback([image, full_prompt], api_key=api_key)
            if answer:
                return f"📸 *Image Analysis:*\n\n{answer}"
            return "⚠️ Vision models are currently experiencing high demand. Please try sending the photo again in a moment."
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return f"⚠️ Failed to analyze image: {str(e)}"

gemini_service = GeminiService()
