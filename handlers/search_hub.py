"""Public search hub with 20 focused search modes."""
import asyncio
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import requests
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


SEARCH_MODES = {
    "web": ("🌐 Web Search", ""),
    "tgbot": ("🤖 Telegram Bot Search", 'site:t.me bot'),
    "tgchannel": ("📢 Telegram Channel Search", "site:t.me channel"),
    "tggroup": ("👥 Telegram Group Search", "site:t.me group"),
    "youtube": ("▶️ YouTube Search", "site:youtube.com"),
    "github": ("🐙 GitHub Search", "site:github.com"),
    "wiki": ("📚 Wikipedia Search", "site:wikipedia.org"),
    "stackoverflow": ("💻 Stack Overflow", "site:stackoverflow.com"),
    "images": ("🖼️ Image Search", "images"),
    "news": ("📰 News Search", "news"),
    "pdf": ("📄 PDF Finder", "filetype:pdf"),
    "books": ("📖 Book Finder", "books"),
    "courses": ("🎓 Course Finder", "courses tutorial"),
    "jobs": ("💼 Job Search", "jobs"),
    "maps": ("📍 Place Search", "maps location"),
    "apps": ("📱 App Search", "app download"),
    "movies": ("🎬 Movie Search", "movie"),
    "music": ("🎧 Music Search", "song music"),
    "prompts": ("✨ AI Prompt Finder", "AI prompt"),
    "code": ("🧩 Code Search", "programming code example"),
}


class _ResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._href = None
        self._collect = False
        self._parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "result__a" in attrs.get("class", ""):
            self._href = attrs.get("href", "")
            self._collect = True
            self._parts = []

    def handle_data(self, data):
        if self._collect:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._collect:
            title = "".join(self._parts).strip()
            href = self._href or ""
            if href.startswith("//duckduckgo.com/l/"):
                href = "https:" + href
            if "duckduckgo.com/l/?" in href:
                href = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
            if title and href.startswith(("http://", "https://")):
                self.results.append((title, href))
            self._collect = False


def _fetch_results(query: str):
    """Use Bing's public RSS response; it is stable and does not require an API key."""
    response = requests.get(
        "https://www.bing.com/search",
        params={"format": "rss", "q": query},
        headers={"User-Agent": "Mozilla/5.0 (compatible; SHIBHSearchBot/1.0)"},
        timeout=15,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    results = []
    for item in root.findall("./channel/item")[:5]:
        title = (item.findtext("title") or "Result").strip()
        url = (item.findtext("link") or "").strip()
        if url.startswith(("http://", "https://")):
            results.append((title, url))
    return results


def _full_query(mode: str, query: str) -> str:
    suffix = SEARCH_MODES[mode][1]
    return f"{query} {suffix}".strip()


def _search_url(query: str) -> str:
    return "https://duckduckgo.com/?q=" + urllib.parse.quote_plus(query)


async def search_hub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    mode_keys = list(SEARCH_MODES)
    for index in range(0, len(mode_keys), 2):
        keyboard.append([
            InlineKeyboardButton(SEARCH_MODES[key][0], callback_data=f"search_mode_{key}")
            for key in mode_keys[index:index + 2]
        ])
    text = (
        "🔎 <b>SHIBH SUPER SEARCH HUB</b>\n\n"
        "Choose one of 20 search modes. Results are from public web sources and open with one tap.\n\n"
        "ℹ️ Telegram Bot/Channel/Group search finds only public, indexed accounts—private Telegram content is never searchable."
    )
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def choose_search_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.callback_query.data.removeprefix("search_mode_")
    if mode not in SEARCH_MODES:
        await update.callback_query.answer("Unknown search mode.", show_alert=True)
        return
    context.user_data["search_hub_mode"] = mode
    await update.callback_query.message.reply_text(
        f"{SEARCH_MODES[mode][0]}\n\nSend what you want to search for:",
        reply_markup=ForceReply(selective=True),
    )


async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str, query: str):
    query = query.strip()
    if not query:
        await update.effective_message.reply_text("Please enter a search term.")
        return
    full_query = _full_query(mode, query)
    status = await update.effective_message.reply_text("🔍 Searching public sources…")
    try:
        results = await asyncio.to_thread(_fetch_results, full_query)
    except Exception:
        results = []

    lines = [f"🔎 <b>{html.escape(SEARCH_MODES[mode][0])}</b>", f"Query: <code>{html.escape(query)}</code>", ""]
    if results:
        for number, (title, url) in enumerate(results, 1):
            lines.append(f"{number}. <a href=\"{html.escape(url, quote=True)}\">{html.escape(title)}</a>")
    else:
        lines.append("No indexed result was returned right now. Use the search button below to open the live search page.")
    keyboard = [[InlineKeyboardButton("🌐 Open Live Search", url=_search_url(full_query))], [InlineKeyboardButton("🔎 Search Again", callback_data=f"search_mode_{mode}")]]
    await status.edit_text("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_search_hub_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    mode = context.user_data.pop("search_hub_mode", None)
    if not mode:
        return False
    await perform_search(update, context, mode, update.effective_message.text)
    return True


async def quick_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    query = " ".join(context.args)
    if not query:
        context.user_data["search_hub_mode"] = mode
        await update.effective_message.reply_text(f"Send a query for {SEARCH_MODES[mode][0]}.", reply_markup=ForceReply(selective=True))
        return
    await perform_search(update, context, mode, query)
