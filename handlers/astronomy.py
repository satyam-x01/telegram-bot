import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from services.nasa_service import nasa_service
from services.ai_service import ai_service
import config

async def apod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /apod command - Astronomy Picture of the Day."""
    msg = update.effective_message
    chat_id = update.effective_chat.id

    wait_msg = await msg.reply_text("🚀 *Fetching latest Astronomy Picture of the Day from NASA...*", parse_mode="Markdown")

    apod_data = await asyncio.to_thread(nasa_service.get_apod)
    if not apod_data:
        await wait_msg.edit_text("❌ *Failed to fetch NASA APOD data.* Please try again later.", parse_mode="Markdown")
        return

    title = apod_data.get("title", "Astronomy Picture of the Day")
    date = apod_data.get("date", "")
    explanation = apod_data.get("explanation", "")
    url = apod_data.get("url", "")
    hdurl = apod_data.get("hdurl", url)
    media_type = apod_data.get("media_type", "image")
    copyright_info = apod_data.get("copyright", "NASA")

    # Limit explanation length for Telegram photo caption limit (1024 chars)
    short_explanation = explanation[:700] + "..." if len(explanation) > 700 else explanation

    caption = (
        f"🌌 *NASA Astronomy Picture of the Day*\n"
        f"📅 *Date:* `{date}`\n"
        f"📌 *Title:* {title}\n"
        f"👤 *Credit:* {copyright_info}\n\n"
        f"📝 *Description:*\n{short_explanation}\n\n"
        f"🔗 [View High Definition Image]({hdurl})"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔄 Next Recent Photo", callback_data="astro_next_apod"),
            InlineKeyboardButton("🔭 Latest JWST Photo", callback_data="astro_jwst")
        ],
        [
            InlineKeyboardButton("✨ HD Full Image", url=hdurl) if hdurl else InlineKeyboardButton("🪐 Exoplanets", callback_data="astro_planet"),
            InlineKeyboardButton("🔴 Mars Rover", callback_data="astro_mars")
        ],
        [
            InlineKeyboardButton("☄️ Near-Earth Asteroids", callback_data="astro_asteroids"),
            InlineKeyboardButton("🔔 24/7 Updates", callback_data="astro_sub")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await wait_msg.delete()
    except Exception:
        pass

    if media_type == "image" and url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            print(f"Error sending photo, falling back to message: {e}")

    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="Markdown",
        disable_web_page_preview=False,
        reply_markup=reply_markup
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /search command - Space research or error diagnostic via Gemini AI."""
    msg = update.effective_message
    query = " ".join(context.args).strip() if context.args else ""

    if not query:
        text = (
            "🔭 *Space & Tech AI Search*\n\n"
            "Search any space topic, NASA mission, black hole, new exoplanet, or paste any code/error message!\n\n"
            "📌 *Examples:*\n"
            "• `/search black hole event horizon`\n"
            "• `/search newly discovered exoplanet james webb`\n"
            "• `/search why showing error ValueError: invalid literal for int()`\n"
            "• `/search how does Kepler telescope detect planets?`"
        )
        await msg.reply_text(text, parse_mode="Markdown")
        return

    wait_msg = await msg.reply_text("🔍 *Searching NASA research & analyzing with Gemini AI...*", parse_mode="Markdown")

    user_lang = db.get_user(update.effective_user.id).get("language", "en") if update.effective_user else "en"

    # Run AI search and NASA image search concurrently for faster response
    ai_task = ai_service.search_astronomy_or_code(query, user_lang=user_lang)
    nasa_task = asyncio.to_thread(nasa_service.get_nasa_images, query)
    ai_response, nasa_images = await asyncio.gather(ai_task, nasa_task)
    image_url = nasa_images[0]["img_url"] if nasa_images else None

    formatted_text = f"🌌 *Search Query:* `{query}`\n\n{ai_response}"

    try:
        await wait_msg.delete()
    except Exception:
        pass

    keyboard = [[InlineKeyboardButton("🔍 New Search", switch_inline_query_current_chat="/search ")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if image_url and len(formatted_text) < 1000:
        try:
            await msg.reply_photo(
                photo=image_url,
                caption=formatted_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass

    await msg.reply_text(formatted_text, parse_mode="Markdown", reply_markup=reply_markup)

async def planet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /planet or /exoplanets command - New Planet & Exoplanet discoveries."""
    msg = update.effective_message
    exoplanets = nasa_service.get_exoplanet_catalog()
    planet = random.choice(exoplanets)

    caption = (
        f"🔭 *NASA Exoplanet Discovery Spotlight*\n\n"
        f"🪐 *Planet Name:* `{planet['name']}`\n"
        f"📏 *Distance from Earth:* {planet['distance']}\n"
        f"⭐ *Host Star:* {planet['star']}\n"
        f"🧪 *Classification:* {planet['type']}\n"
        f"🚀 *Discovery:* {planet['discovered']}\n\n"
        f"💡 *Key Fact:* {planet['fact']}"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎲 Next Exoplanet", callback_data="astro_planet"),
            InlineKeyboardButton("🌌 Today's APOD", callback_data="astro_apod")
        ],
        [
            InlineKeyboardButton("🔔 Subscribe 24/7 Updates", callback_data="astro_sub")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if planet.get("image"):
        try:
            await msg.reply_photo(
                photo=planet["image"],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            print(f"Error sending exoplanet photo: {e}")

    await msg.reply_text(caption, parse_mode="Markdown", reply_markup=reply_markup)

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /funfact command - Dynamic Space & Astronomy Fun Fact."""
    msg = update.effective_message
    fact_data = await asyncio.to_thread(ai_service.generate_hourly_funfact)

    title = fact_data.get("title", "🌌 Mind-Blowing Astronomy Fact")
    fact = fact_data.get("fact", "")
    topic = fact_data.get("topic", "Astronomy")

    text = (
        f"{title}\n\n"
        f"📌 *Topic:* `{topic}`\n\n"
        f"✨ {fact}\n\n"
        f"_Powered by NASA APIs & Gemini AI_"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎲 Another Fact", callback_data="astro_fact"),
            InlineKeyboardButton("🪐 New Planets", callback_data="astro_planet")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def asteroids_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /asteroids or /neo command - Near Earth Objects tracking."""
    msg = update.effective_message
    data = await asyncio.to_thread(nasa_service.get_asteroids)

    if not data:
        await msg.reply_text("❌ Could not fetch Asteroids data right now.")
        return

    date_str = data["date"]
    total = data["total_count"]
    asteroids_list = data["asteroids"]

    text = (
        f"☄️ *Near-Earth Asteroids & Hazard Tracking*\n"
        f"📅 *Date:* `{date_str}`\n"
        f"📊 *Total Near-Earth Asteroids Detected Today:* `{total}`\n\n"
        f"🔭 *Closest & Notable Asteroids Passing Earth:*\n\n"
    )

    for item in asteroids_list:
        hazard_emoji = "⚠️ HAZARDOUS" if item["hazardous"] else "✅ SAFE PASS"
        text += (
            f"• *Asteroid:* `{item['name']}` ({hazard_emoji})\n"
            f"  📏 Diameter: `{item['diameter_m']} meters`\n"
            f"  ⚡ Speed: `{item['velocity_kph']} km/h`\n"
            f"  📍 Distance from Earth: `{item['miss_distance_km']} km`\n\n"
        )

    keyboard = [
        [
            InlineKeyboardButton("🔴 Mars Rover", callback_data="astro_mars"),
            InlineKeyboardButton("🌌 APOD Photo", callback_data="astro_apod")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def mars_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /mars command - Latest Mars Rover Photo."""
    msg = update.effective_message
    mars_data = await asyncio.to_thread(nasa_service.get_mars_photos)

    if not mars_data:
        await msg.reply_text("❌ Failed to fetch latest Mars Rover photo.")
        return

    caption = (
        f"🔴 *Latest Mars Rover View*\n\n"
        f"🤖 *Rover:* `{mars_data['rover']}`\n"
        f"📷 *Camera:* `{mars_data['camera_full_name']}`\n"
        f"📅 *Earth Date:* `{mars_data['earth_date']}`\n"
        f"⚙️ *Mission Status:* `{mars_data['status'].capitalize()}`\n\n"
        f"🔴 _Direct imagery transmitted from the surface of Mars by NASA!_"
    )

    keyboard = [[InlineKeyboardButton("🎲 Another Mars View", callback_data="astro_mars")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await msg.reply_photo(
            photo=mars_data["img_url"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception:
        await msg.reply_text(caption, parse_mode="Markdown", reply_markup=reply_markup)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /subscribe - Enable 24/7 hourly space updates."""
    chat = update.effective_chat
    db.add_subscription(chat.id, chat.type)

    text = (
        "🔔 *Subscribed to 24/7 Hourly Astronomy Updates!*\n\n"
        "🌌 You will now receive automatic space posts every 1 hour containing:\n"
        "• NASA Astronomy Picture of the Day\n"
        "• Mind-Blowing Astronomy Fun Facts\n"
        "• Newly Discovered Exoplanets & Space Discoveries\n\n"
        "Use `/unsubscribe` anytime to stop updates."
    )
    await update.effective_message.reply_text(text, parse_mode="Markdown")

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /unsubscribe - Disable 24/7 hourly space updates."""
    chat = update.effective_chat
    db.remove_subscription(chat.id)

    text = (
        "🔕 *Unsubscribed from 24/7 Hourly Astronomy Updates.*\n\n"
        "You will no longer receive hourly automatic space posts. Use `/subscribe` to turn them back on!"
    )
    await update.effective_message.reply_text(text, parse_mode="Markdown")

async def latest_astronomy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /latest, /spacephoto, /astrophoto - Newest deep-space telescope imagery."""
    msg = update.effective_message
    chat_id = update.effective_chat.id

    wait_msg = await msg.reply_text("🔭 *Fetching newest astronomy photos from James Webb & NASA Telescopes...*", parse_mode="Markdown")

    photos = await asyncio.to_thread(nasa_service.get_latest_astronomy_photos, query="James Webb Space Telescope", limit=25)
    if not photos:
        recent_apods = await asyncio.to_thread(nasa_service.get_recent_apods, limit=10)
        if recent_apods:
            item = random.choice(recent_apods)
            photos = [{
                "title": item["title"],
                "description": item["explanation"],
                "img_url": item["hdurl"] or item["url"],
                "date": item["date"],
                "source": "NASA Astronomy Picture of the Day"
            }]

    if not photos:
        await wait_msg.edit_text("❌ *Failed to fetch latest space photos.* Please try again in a moment.", parse_mode="Markdown")
        return

    photo = random.choice(photos)
    title = photo.get("title", "NASA Deep Space Discovery")
    date = photo.get("date", "")
    desc = photo.get("description", "")
    img_url = photo.get("img_url", "")
    source = photo.get("source", "NASA Deep Space Observatories")

    short_desc = desc[:650] + "..." if len(desc) > 650 else desc

    caption = (
        f"🔭 *NEW ASTRONOMY OBSERVATION SPOTLIGHT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *Subject:* {title}\n"
        f"📅 *Observation Date:* `{date}`\n"
        f"🛰 *Observatory:* {source}\n\n"
        f"📝 *Details:*\n{short_desc}\n\n"
        f"✨ [View High-Resolution Image]({img_url})"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎲 Next Space Photo", callback_data="astro_latest"),
            InlineKeyboardButton("🔭 James Webb (JWST)", callback_data="astro_jwst")
        ],
        [
            InlineKeyboardButton("🌌 Today's APOD", callback_data="astro_apod"),
            InlineKeyboardButton("🔄 Recent APODs", callback_data="astro_next_apod")
        ],
        [
            InlineKeyboardButton("🪐 Exoplanets", callback_data="astro_planet"),
            InlineKeyboardButton("🔴 Mars Rover", callback_data="astro_mars")
        ],
        [
            InlineKeyboardButton("🔔 24/7 Updates", callback_data="astro_sub")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await wait_msg.delete()
    except Exception:
        pass

    if img_url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=img_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            print(f"Error sending latest astronomy photo: {e}")

    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def jwst_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /jwst command - Dedicated James Webb Space Telescope discoveries."""
    msg = update.effective_message
    chat_id = update.effective_chat.id

    wait_msg = await msg.reply_text("🛰 *Accessing James Webb Space Telescope (JWST) Data...*", parse_mode="Markdown")

    photos = await asyncio.to_thread(nasa_service.get_latest_astronomy_photos, query="James Webb", limit=20)
    if not photos:
        await wait_msg.edit_text("❌ *Failed to fetch JWST photos.* Please try again later.", parse_mode="Markdown")
        return

    photo = random.choice(photos)
    title = photo.get("title", "JWST Deep Field Discovery")
    date = photo.get("date", "")
    desc = photo.get("description", "")
    img_url = photo.get("img_url", "")

    short_desc = desc[:650] + "..." if len(desc) > 650 else desc

    caption = (
        f"🛰 *James Webb Space Telescope (JWST) Discovery*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *Title:* {title}\n"
        f"📅 *Date:* `{date}`\n\n"
        f"🔬 *Scientific Description:*\n{short_desc}\n\n"
        f"✨ [High-Definition JWST Image]({img_url})"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎲 Next JWST View", callback_data="astro_jwst"),
            InlineKeyboardButton("✨ All Space Photos", callback_data="astro_latest")
        ],
        [
            InlineKeyboardButton("🌌 Today's APOD", callback_data="astro_apod"),
            InlineKeyboardButton("🪐 Discover Exoplanets", callback_data="astro_planet")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await wait_msg.delete()
    except Exception:
        pass

    if img_url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=img_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            print(f"Error sending JWST photo: {e}")

    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def recent_apod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for cycling through recent APOD photos."""
    query = update.callback_query
    msg = update.effective_message
    chat_id = update.effective_chat.id

    recent = await asyncio.to_thread(nasa_service.get_recent_apods, limit=15)
    if not recent:
        await apod_command(update, context)
        return

    photo = random.choice(recent)
    title = photo.get("title", "Astronomy Picture of the Day")
    date = photo.get("date", "")
    explanation = photo.get("explanation", "")
    url = photo.get("url", "")
    hdurl = photo.get("hdurl", url)
    copyright_info = photo.get("copyright", "NASA / Public Domain")

    short_explanation = explanation[:650] + "..." if len(explanation) > 650 else explanation

    caption = (
        f"🌌 *NASA Astronomy Picture of the Day*\n"
        f"📅 *Date:* `{date}`\n"
        f"📌 *Title:* {title}\n"
        f"👤 *Credit:* {copyright_info}\n\n"
        f"📝 *Description:*\n{short_explanation}\n\n"
        f"🔗 [View High Definition Image]({hdurl})"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔄 Another Recent APOD", callback_data="astro_next_apod"),
            InlineKeyboardButton("🔭 Latest JWST Photo", callback_data="astro_jwst")
        ],
        [
            InlineKeyboardButton("✨ HD Full Image", url=hdurl) if hdurl else InlineKeyboardButton("🪐 Exoplanets", callback_data="astro_planet"),
            InlineKeyboardButton("🔴 Mars Rover", callback_data="astro_mars")
        ],
        [
            InlineKeyboardButton("☄️ Near-Earth Asteroids", callback_data="astro_asteroids"),
            InlineKeyboardButton("🔔 24/7 Updates", callback_data="astro_sub")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if url:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        print(f"Error sending recent APOD photo: {e}")

    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def astronomy_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query handler for inline button actions."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "astro_apod":
        await apod_command(update, context)
    elif data == "astro_latest":
        await latest_astronomy_command(update, context)
    elif data == "astro_next_apod":
        await recent_apod_callback(update, context)
    elif data == "astro_jwst":
        await jwst_command(update, context)
    elif data == "astro_planet":
        await planet_command(update, context)
    elif data == "astro_fact":
        await fact_command(update, context)
    elif data == "astro_asteroids":
        await asteroids_command(update, context)
    elif data == "astro_mars":
        await mars_command(update, context)
    elif data == "astro_sub":
        await subscribe_command(update, context)
    elif data == "astro_unsub":
        await unsubscribe_command(update, context)
