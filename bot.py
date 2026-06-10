#!/usr/bin/env python3
import csv
import io
import json
import os
import signal
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from zoneinfo import ZoneInfo


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
PRAYER_API = "https://api.aladhan.com/v1/timings/{day}"
PRAYER_CITY_API = "https://api.aladhan.com/v1/timingsByCity/{day}"
DATA_FILE = Path("users.json")
MOSQUES_FILE = Path("mosques.json")
NOTIFICATIONS_FILE = Path("notifications.json")
BOT_TIMEZONE = ZoneInfo("Asia/Tashkent")
KOKAND_CITY = "Kokand"
KOKAND_LABEL = "Qo'qon shahri"
DEFAULT_MOSQUES = [
    {"id": "yangi_chorsu_mir", "name": "Yangi Chorsu (Mir)", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "shayxulislom", "name": "Shayxulislom", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "avgonbog", "name": "Avg'onbog'", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "masjid_ul_latif", "name": "Masjid-ul Latif", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "zaynil_obidin", "name": "Zaynil Obidin (Ayrilish)", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "hadiya_hoji", "name": "Hadiya Hoji (Shaldiramoq)", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "degrezlik", "name": "Degrezlik", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "shayxon", "name": "Shayxon", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "saodat", "name": "Saodat", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "xazirati_abbos", "name": "Xazirati Abbos", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "dangara", "name": "Dang'ara", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "gishtlik", "name": "G'ishtlik Masjid", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "zinbardor", "name": "Zinbardor (Isfaraguzar)", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
    {"id": "muhammad_said_xoja", "name": "Muhammad Said Xo'ja (Tulaboy)", "location": {}, "prayer_times": {}, "times": {}, "offsets": {}},
]
PRAYER_NAMES = ("Bomdod", "Quyosh", "Peshin", "Asr", "Shom", "Xufton")
EXTRA_TIME_NAMES = ("Tahajjud", "Zuho", "Qiyom")
NOTIFICATION_PRAYERS = ("Bomdod", "Peshin", "Asr", "Shom", "Xufton")
DAILY_CLEANUP_TIME = "00:59"
DAILY_SUMMARY_TIME = "01:00"
DEFAULT_SHEET_CACHE_SECONDS = 15
mosques_cache = {"loaded_at": 0, "data": None}
prayer_cache = {}
BTN_ENTRY_TIMES = "🕋 Kirish vaqtlari"
BTN_PRAYER_TIMES_IN_MOSQUES = "🕌 Namoz bo'yicha vaqtlar"
BTN_MOSQUE_TIMES = "📋 Masjid bo'yicha vaqtlar"
BTN_MOSQUE_LOCATIONS = "📍 Masjid Joylashuvlari"
BTN_NEAREST_MOSQUE = "🧭 Menga eng yaqin masjid"
BTN_SEND_LOCATION = "📡 Lokatsiyamni yuborish"
BTN_BACK = "◀️ Ortga"
BTN_MAIN_MENU = "🏠 Bosh menyu"
LANG_LATIN = "latin"
LANG_CYRILLIC = "cyrillic"
BTN_LANG_LATIN = "O'zbekcha"
BTN_LANG_CYRILLIC = "Ўзбекча"
TEXTS = {
    LANG_LATIN: {
        "kokand": "Qo'qon shahri",
        "entry_times": "🕋 Kirish vaqtlari",
        "prayer_times_in_mosques": "🕌 Namoz bo'yicha vaqtlar",
        "mosque_times": "📋 Masjid bo'yicha vaqtlar",
        "mosque_locations": "📍 Masjid Joylashuvlari",
        "nearest_mosque": "🧭 Menga eng yaqin masjid",
        "send_location": "📡 Lokatsiyamni yuborish",
        "back": "◀️ Ortga",
        "main_menu": "🏠 Bosh menyu",
        "choose_language": "Tilni tanlang",
        "choose_menu": "Menyudan kerakli bo'limni tanlang.",
        "choose_prayer": "🕌 <b>Namoz vaqtini tanlang</b>",
        "choose_mosque": "🕌 <b>Masjidni tanlang</b>",
        "choose_location_mosque": "📍 <b>Joylashuvini ko'rish uchun masjidni tanlang</b>",
        "send_location_prompt": "🧭 <b>Eng yaqin masjidni topish uchun lokatsiyangizni yuboring</b>",
        "nearest_title": "🧭 <b>Eng yaqin masjid</b>",
        "mosque": "Masjid",
        "distance": "Masofa",
        "city": "Shahar",
        "date": "Sana",
        "address": "Manzil",
        "map": "Xarita",
        "time": "Vaqt",
        "location_missing": "Bu masjid lokatsiyasi hali kiritilmagan.",
        "all_locations_missing": "Hali masjid lokatsiyalari kiritilmagan.",
        "times_missing": "Bu masjid uchun vaqtlar hali kiritilmagan.",
        "not_understood": "Tushunmadim. /help ni yuboring yoki menyudan tanlang.",
        "prayer_entered": "{prayer} vaqti kirdi",
        "mosque_prayer_section": "Masjidlarda o'qilish vaqti",
        "mosque_prayer_for": "{prayer} namozi masjidlarda",
        "daily_times": "Bugungi namoz vaqtlari",
        "additional_times": "Qo'shimcha vaqtlar",
        "tahajjud_note": "Tahajjud",
        "zuho_note": "Zuho",
        "qiyom_note": "Qiyom",
        "mosque_location": "📍 <b>Masjid joylashuvi</b>",
        "mosque_prayer_times": "🕌 <b>Masjiddagi namoz vaqtlari</b>",
    },
    LANG_CYRILLIC: {
        "kokand": "Қўқон шаҳри",
        "entry_times": "🕋 Кириш вақтлари",
        "prayer_times_in_mosques": "🕌 Намоз бўйича вақтлар",
        "mosque_times": "📋 Масжид бўйича вақтлар",
        "mosque_locations": "📍 Масжид жойлашувлари",
        "nearest_mosque": "🧭 Менга энг яқин масжид",
        "send_location": "📡 Локациямни юбориш",
        "back": "◀️ Ортга",
        "main_menu": "🏠 Бош меню",
        "choose_language": "Тилни танланг",
        "choose_menu": "Менюдан керакли бўлимни танланг.",
        "choose_prayer": "🕌 <b>Намоз вақтини танланг</b>",
        "choose_mosque": "🕌 <b>Масжидни танланг</b>",
        "choose_location_mosque": "📍 <b>Жойлашувини кўриш учун масжидни танланг</b>",
        "send_location_prompt": "🧭 <b>Энг яқин масжидни топиш учун локациянгизни юборинг</b>",
        "nearest_title": "🧭 <b>Энг яқин масжид</b>",
        "mosque": "Масжид",
        "distance": "Масофа",
        "city": "Шаҳар",
        "date": "Сана",
        "address": "Манзил",
        "map": "Харита",
        "time": "Вақт",
        "location_missing": "Бу масжид локацияси ҳали киритилмаган.",
        "all_locations_missing": "Ҳали масжид локациялари киритилмаган.",
        "times_missing": "Бу масжид учун вақтлар ҳали киритилмаган.",
        "not_understood": "Тушунмадим. /help ни юборинг ёки менюдан танланг.",
        "prayer_entered": "{prayer} вақти кирди",
        "mosque_prayer_section": "Масжидларда ўқилиш вақти",
        "mosque_prayer_for": "{prayer} намози масжидларда",
        "daily_times": "Бугунги намоз вақтлари",
        "additional_times": "Қўшимча вақтлар",
        "tahajjud_note": "Таҳажжуд",
        "zuho_note": "Зуҳо",
        "qiyom_note": "Қиём",
        "mosque_location": "📍 <b>Масжид жойлашуви</b>",
        "mosque_prayer_times": "🕌 <b>Масжиддаги намоз вақтлари</b>",
    },
}
PRAYER_LABELS = {
    LANG_LATIN: {
        "Bomdod": "Bomdod",
        "Quyosh": "Quyosh",
        "Peshin": "Peshin",
        "Asr": "Asr",
        "Shom": "Shom",
        "Xufton": "Xufton",
        "Tahajjud": "Tahajjud",
        "Zuho": "Zuho",
        "Qiyom": "Qiyom",
    },
    LANG_CYRILLIC: {
        "Bomdod": "Бомдод",
        "Quyosh": "Қуёш",
        "Peshin": "Пешин",
        "Asr": "Аср",
        "Shom": "Шом",
        "Xufton": "Хуфтон",
        "Tahajjud": "Таҳажжуд",
        "Zuho": "Зуҳо",
        "Qiyom": "Қиём",
    },
}
MOSQUE_NAMES_CYRILLIC = {
    "yangi_chorsu_mir": "Янги Чорсу (Мир)",
    "shayxulislom": "Шайхулислом",
    "avgonbog": "Авғонбоғ",
    "masjid_ul_latif": "Масжид-ул Латиф",
    "zaynil_obidin": "Зайнил Обидин (Айрилиш)",
    "hadiya_hoji": "Ҳадия Ҳожи (Шалдирамоқ)",
    "degrezlik": "Дегрезлик",
    "shayxon": "Шайхон",
    "saodat": "Саодат",
    "xazirati_abbos": "Хазирати Аббос",
    "dangara": "Данғара",
    "gishtlik": "Ғиштлик Масжид",
    "zinbardor": "Зинбардор (Исфарагузар)",
    "muhammad_said_xoja": "Муҳаммад Саид Хўжа (Тўлабой)",
}


running = True


def load_env(path=".env"):
    env_path = Path(path)
    if not env_path.is_absolute() and not env_path.exists():
        env_path = Path(__file__).resolve().parent / path
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not os.environ.get(key):
            os.environ[key] = value


def ssl_context():
    cafile = os.getenv("TELEGRAM_CA_FILE") or os.getenv("SSL_CERT_FILE")
    if cafile:
        return ssl.create_default_context(cafile=cafile)
    if os.getenv("TELEGRAM_SSL_NO_VERIFY") == "1":
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def request_json(url, payload=None, timeout=20):
    data = None
    headers = {"User-Agent": "namoz-vaqtlari-bot/1.0"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def request_text(url, timeout=20):
    request = urllib.request.Request(url, headers={"User-Agent": "namoz-vaqtlari-bot/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
            return response.read().decode("utf-8-sig")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def with_cache_buster(url):
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}_ts={int(time.time())}"


def telegram(token, method, payload=None):
    url = TELEGRAM_API.format(token=token, method=method)
    return request_json(url, payload)


def send_message(token, chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram(token, "sendMessage", payload)


def send_location(token, chat_id, latitude, longitude, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "latitude": latitude,
        "longitude": longitude,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return telegram(token, "sendLocation", payload)


def delete_message(token, chat_id, message_id):
    return telegram(token, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def remember_bot_message(users, chat_id, response):
    message_id = (response or {}).get("result", {}).get("message_id")
    if not message_id:
        return
    data = users.setdefault(str(chat_id), {})
    messages = data.setdefault("bot_messages", [])
    messages.append(message_id)
    data["bot_messages"] = messages[-80:]
    save_users(users)


def forget_bot_message_id(users, chat_id, message_id):
    data = users.setdefault(str(chat_id), {})
    data["bot_messages"] = [item for item in data.get("bot_messages", []) if item != message_id]


def send_tracked_message(token, users, chat_id, text, reply_markup=None):
    response = send_message(token, chat_id, text, reply_markup)
    remember_bot_message(users, chat_id, response)
    return response


def preview_message_key(target_date, prayer_name):
    return f"{date_key(target_date)}:{prayer_name}"


def send_preview_message(token, users, chat_id, preview_key, text):
    response = send_tracked_message(token, users, chat_id, text)
    message_id = (response or {}).get("result", {}).get("message_id")
    if not message_id:
        return response
    data = users.setdefault(str(chat_id), {})
    previews = data.setdefault("preview_messages", {})
    previews[preview_key] = message_id
    save_users(users)
    return response


def delete_preview_message(token, users, chat_id, preview_key):
    data = users.setdefault(str(chat_id), {})
    previews = data.get("preview_messages") or {}
    message_id = previews.pop(preview_key, None)
    if not message_id:
        return
    try:
        delete_message(token, chat_id, message_id)
    except Exception as exc:
        print(f"Preview xabarni o'chirish xatosi ({chat_id}, {message_id}): {exc}", file=sys.stderr)
    forget_bot_message_id(users, chat_id, message_id)
    data["preview_messages"] = previews
    save_users(users)


def clear_tracked_bot_messages(token, users, chat_id):
    data = users.setdefault(str(chat_id), {})
    message_ids = data.get("bot_messages", [])
    if not message_ids:
        return
    kept = []
    for message_id in message_ids:
        try:
            delete_message(token, chat_id, message_id)
        except Exception as exc:
            print(f"Xabarni o'chirish xatosi ({chat_id}, {message_id}): {exc}", file=sys.stderr)
            kept.append(message_id)
    data["bot_messages"] = kept[-20:]
    data["preview_messages"] = {}
    save_users(users)


def load_users():
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_users(users):
    DATA_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def users_sheet_url():
    load_env()
    return os.getenv("USERS_SHEET_WEBAPP_URL", "").strip()


def merge_users(base, incoming):
    merged = dict(base)
    for chat_id, data in incoming.items():
        if not isinstance(data, dict):
            continue
        current = merged.setdefault(str(chat_id), {})
        current.update(data)
    return merged


def load_remote_users():
    url = users_sheet_url()
    if not url:
        return {}
    try:
        response = request_json(f"{with_cache_buster(url)}&action=list")
    except Exception as exc:
        print(f"Google Sheets userlarni o'qish xatosi: {exc}", file=sys.stderr)
        return {}

    users = {}
    rows = response.get("users", response if isinstance(response, list) else [])
    for row in rows:
        chat_id = str(row.get("chat_id", "")).strip()
        if not chat_id:
            continue
        users[chat_id] = {
            "active": str(row.get("active", "true")).lower() != "false",
            "first_name": row.get("first_name", ""),
            "username": row.get("username", ""),
            "lang": row.get("lang", LANG_LATIN) or LANG_LATIN,
            "last_seen": row.get("last_seen", ""),
        }
    return users


def sync_remote_user(chat_id, user_data):
    url = users_sheet_url()
    if not url:
        return False, "USERS_SHEET_WEBAPP_URL sozlanmagan"
    payload = {
        "action": "upsert",
        "chat_id": str(chat_id),
        "active": user_data.get("active", True),
        "first_name": user_data.get("first_name", ""),
        "username": user_data.get("username", ""),
        "lang": user_data.get("lang", LANG_LATIN),
        "last_seen": user_data.get("last_seen", ""),
    }
    try:
        response = request_json(url, payload)
    except Exception as exc:
        print(f"Google Sheets user sync xatosi ({chat_id}): {exc}", file=sys.stderr)
        return False, str(exc)
    if response.get("ok") is not True:
        return False, json.dumps(response, ensure_ascii=False)
    return True, ""


def sync_all_remote_users(users):
    ok_count = 0
    errors = []
    for chat_id, data in users.items():
        if isinstance(data, dict):
            ok, error = sync_remote_user(chat_id, data)
            if ok:
                ok_count += 1
            else:
                errors.append(f"{chat_id}: {error}")
    return ok_count, errors


def register_user(users, chat_id, message):
    user_data = users.setdefault(str(chat_id), {})
    user = message.get("from") or {}
    user_data["active"] = True
    user_data["first_name"] = user.get("first_name", user_data.get("first_name", ""))
    user_data["username"] = user.get("username", user_data.get("username", ""))
    user_data["last_seen"] = datetime.now(BOT_TIMEZONE).isoformat(timespec="seconds")
    save_users(users)
    sync_remote_user(chat_id, user_data)


def load_notifications():
    if not NOTIFICATIONS_FILE.exists():
        return {}
    try:
        data = json.loads(NOTIFICATIONS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_notifications(notifications):
    NOTIFICATIONS_FILE.write_text(json.dumps(notifications, ensure_ascii=False, indent=2), encoding="utf-8")


def load_mosques():
    sheet_url = os.getenv("GOOGLE_SHEET_CSV_URL")
    if sheet_url:
        try:
            return load_mosques_from_sheet(sheet_url)
        except Exception as exc:
            print(f"Google Sheets o'qish xatosi, mosques.json ishlatiladi: {exc}", file=sys.stderr)

    if not MOSQUES_FILE.exists():
        save_mosques(DEFAULT_MOSQUES)
        return DEFAULT_MOSQUES
    try:
        mosques = json.loads(MOSQUES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_MOSQUES
    normalized = []
    for mosque in mosques:
        if not mosque.get("id") or not mosque.get("name"):
            continue
        mosque.setdefault("location", {})
        mosque.setdefault("prayer_times", {})
        mosque.setdefault("times", {})
        mosque.setdefault("offsets", {})
        normalized.append(mosque)
    return normalized


def sheet_cache_seconds():
    try:
        return max(0, int(os.getenv("SHEET_CACHE_SECONDS", DEFAULT_SHEET_CACHE_SECONDS)))
    except ValueError:
        return DEFAULT_SHEET_CACHE_SECONDS


def refresh_mosques_from_sheet():
    sheet_url = os.getenv("GOOGLE_SHEET_CSV_URL")
    if not sheet_url:
        return load_mosques()
    return load_mosques_from_sheet(sheet_url, force=True)


def load_mosques_from_sheet(url, force=False):
    now = time.time()
    cache_seconds = sheet_cache_seconds()
    if not force and mosques_cache["data"] is not None and now - mosques_cache["loaded_at"] < cache_seconds:
        return mosques_cache["data"]

    csv_text = request_text(with_cache_buster(url))
    rows = csv.DictReader(io.StringIO(csv_text))
    mosques = []
    for row in rows:
        mosque = mosque_from_sheet_row(row)
        if mosque:
            mosques.append(mosque)
    if not mosques:
        raise RuntimeError("Sheet ichidan masjid qatori topilmadi")
    mosques_cache["loaded_at"] = now
    mosques_cache["data"] = mosques
    return mosques


def mosque_from_sheet_row(row):
    normalized = {normalize_header(key): (value or "").strip() for key, value in row.items() if key}
    mosque_id = normalized.get("id")
    name = normalized.get("name")
    if not mosque_id or not name:
        return None

    location = parse_location(
        normalized.get("location")
        or normalized.get("llocation")
        or normalized.get("lat_lon")
        or normalized.get("lon")
    )
    address = normalized.get("address")
    if address:
        location["address"] = address

    prayer_times = {}
    for key, prayer_name in {
        "bomdod": "Bomdod",
        "peshin": "Peshin",
        "asr": "Asr",
        "shom": "Shom",
        "xufton": "Xufton",
    }.items():
        value = normalize_time(normalized.get(key, ""))
        if value:
            prayer_times[prayer_name] = value

    return {
        "id": mosque_id,
        "name": name,
        "location": location,
        "prayer_times": prayer_times,
        "times": {},
        "offsets": {},
    }


def normalize_header(value):
    return normalize_text(value).replace(" ", "_").replace("-", "_")


def parse_location(value):
    if not value:
        return {}
    pieces = [item.strip() for item in value.split(",")]
    if len(pieces) < 2:
        return {}
    try:
        return {"lat": float(pieces[0]), "lon": float(pieces[1])}
    except ValueError:
        return {}


def normalize_time(value):
    if not value:
        return ""
    value = value.strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return value if valid_time(value) else ""


def save_mosques(mosques):
    MOSQUES_FILE.write_text(json.dumps(mosques, ensure_ascii=False, indent=2), encoding="utf-8")


def admin_ids():
    value = os.getenv("ADMIN_IDS", "")
    return {item.strip() for item in value.split(",") if item.strip()}


def is_admin(chat_id):
    return str(chat_id) in admin_ids()


def tr(lang, key):
    return TEXTS.get(lang, TEXTS[LANG_LATIN]).get(key, TEXTS[LANG_LATIN][key])


def user_lang(users, chat_id):
    return users.get(str(chat_id), {}).get("lang", LANG_LATIN)


def language_keyboard():
    return {
        "keyboard": [[{"text": BTN_LANG_LATIN}, {"text": BTN_LANG_CYRILLIC}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def mosque_name(mosque, lang):
    if lang == LANG_CYRILLIC:
        return MOSQUE_NAMES_CYRILLIC.get(mosque["id"], mosque["name"])
    return mosque["name"]


def prayer_label(name, lang):
    return PRAYER_LABELS.get(lang, PRAYER_LABELS[LANG_LATIN]).get(name, name)


def prayer_button(name, lang):
    return f"🕌 {prayer_label(name, lang)}"


def prayer_from_button(text):
    normalized = normalize_text(text.replace("🕌", ""))
    for name in NOTIFICATION_PRAYERS:
        if normalized in {normalize_text(name), normalize_text(prayer_label(name, LANG_LATIN)), normalize_text(prayer_label(name, LANG_CYRILLIC))}:
            return name
    return None


def normalize_text(value):
    return (
        value.strip()
        .lower()
        .replace("g'", "g")
        .replace("o'", "o")
        .replace("ʻ", "")
        .replace("’", "")
        .replace("'", "")
    )


def main_keyboard(mosques, lang=LANG_LATIN):
    return {
        "keyboard": [
            [{"text": tr(lang, "entry_times")}, {"text": tr(lang, "prayer_times_in_mosques")}],
            [{"text": tr(lang, "mosque_times")}, {"text": tr(lang, "mosque_locations")}],
            [{"text": tr(lang, "nearest_mosque")}],
        ],
        "resize_keyboard": True,
    }


def prayer_keyboard(lang=LANG_LATIN):
    return {
        "keyboard": [
            [{"text": prayer_button("Bomdod", lang)}, {"text": prayer_button("Peshin", lang)}],
            [{"text": prayer_button("Asr", lang)}, {"text": prayer_button("Shom", lang)}],
            [{"text": prayer_button("Xufton", lang)}],
            [{"text": tr(lang, "back")}, {"text": tr(lang, "main_menu")}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def mosque_keyboard(mosques, lang=LANG_LATIN):
    rows = []
    for index in range(0, len(mosques), 2):
        rows.append([{"text": mosque_name(mosque, lang)} for mosque in mosques[index : index + 2]])
    rows.append([{"text": tr(lang, "back")}, {"text": tr(lang, "main_menu")}])
    return {"keyboard": rows, "resize_keyboard": True, "one_time_keyboard": True}


def location_request_keyboard(lang=LANG_LATIN):
    return {
        "keyboard": [[{"text": tr(lang, "send_location"), "request_location": True}], [{"text": tr(lang, "back")}, {"text": tr(lang, "main_menu")}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def admin_help_text():
    return (
        "<b>Admin buyruqlar</b>\n\n"
        "/mosqueids - masjid ID ro'yxati\n"
        "/usercount - foydalanuvchilar soni\n"
        "/syncusers - lokal userlarni Google Sheets'ga yuborish\n"
        "/envcheck - muhim env sozlamalarini tekshirish\n"
        "/refreshsheet - Google Sheets ma'lumotlarini darhol yangilash\n"
        "/setlocation masjid_id lat lon manzil - lokatsiya saqlash\n"
        "/setmasjidtime masjid_id Bomdod=03:30 Peshin=12:45 Asr=18:00 Shom=19:50 Xufton=21:40\n"
        "/clearmasjidtime masjid_id"
    )


def prayer_times_by_kokand(target_date):
    key = date_key(target_date)
    if key in prayer_cache:
        return prayer_cache[key]

    params = urllib.parse.urlencode(
        {
            "city": KOKAND_CITY,
            "country": "Uzbekistan",
            "method": 2,
            "school": 1,
            "timezonestring": "Asia/Tashkent",
        }
    )
    times = fetch_prayer_times(f"{PRAYER_CITY_API.format(day=target_date.strftime('%d-%m-%Y'))}?{params}")
    prayer_cache[key] = times
    return times


def fetch_prayer_times(url):
    response = request_json(url)
    if response.get("code") != 200:
        raise RuntimeError(response.get("status", "Prayer API error"))
    timings = response["data"]["timings"]
    return {
        "Bomdod": clean_time(timings["Fajr"]),
        "Quyosh": clean_time(timings["Sunrise"]),
        "Peshin": clean_time(timings["Dhuhr"]),
        "Asr": clean_time(timings["Asr"]),
        "Shom": clean_time(timings["Maghrib"]),
        "Xufton": clean_time(timings["Isha"]),
    }


def clean_time(value):
    return value.split(" ", 1)[0]


def apply_offsets(times, offsets):
    adjusted = {}
    for name, value in times.items():
        minutes = int(offsets.get(name, 0) or 0)
        adjusted[name] = add_minutes(value, minutes)
    return adjusted


def add_minutes(value, minutes):
    parsed = datetime.strptime(value, "%H:%M")
    return (parsed + timedelta(minutes=minutes)).strftime("%H:%M")


def time_to_minutes(value):
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def minutes_to_time(minutes):
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def extended_times_for_date(target_date):
    today_times = prayer_times_by_kokand(target_date)
    yesterday_times = prayer_times_by_kokand(target_date - timedelta(days=1))
    shom_previous = time_to_minutes(yesterday_times["Shom"])
    bomdod_today = time_to_minutes(today_times["Bomdod"]) + 24 * 60
    night_length = bomdod_today - shom_previous
    tahajjud_start = shom_previous + (night_length * 2 // 3)
    return {
        "Tahajjud": f"{minutes_to_time(tahajjud_start)} - {today_times['Bomdod']}",
        "Zuho": add_minutes(today_times["Quyosh"], 20),
        "Qiyom": add_minutes(today_times["Peshin"], -5),
    }


def format_times(title, mosque, target_date, times, lang=LANG_LATIN):
    lines = [
        f"🕋 <b>{title}</b>",
        f"{tr(lang, 'city')}: <b>{tr(lang, 'kokand')}</b>",
        f"{tr(lang, 'mosque')}: <b>{mosque_name(mosque, lang)}</b>",
        f"{tr(lang, 'date')}: <b>{target_date.strftime('%d.%m.%Y')}</b>",
        "",
    ]
    location = mosque.get("location") or {}
    if location.get("address"):
        lines.append(f"{tr(lang, 'address')}: <b>{location['address']}</b>")
    if location.get("lat") and location.get("lon"):
        lines.append(f"{tr(lang, 'map')}: https://maps.google.com/?q={location['lat']},{location['lon']}")
    lines.append("")
    lines.extend(f"{prayer_label(name, lang)}: <b>{times[name]}</b>" for name in PRAYER_NAMES if name in times)
    if mosque.get("note"):
        lines.extend(["", mosque["note"]])
    return "\n".join(lines)


def format_entry_times(target_date, times, lang=LANG_LATIN):
    lines = [
        f"<b>{tr(lang, 'entry_times')}</b>",
        f"{tr(lang, 'city')}: <b>{tr(lang, 'kokand')}</b>",
        f"{tr(lang, 'date')}: <b>{target_date.strftime('%d.%m.%Y')}</b>",
        "",
    ]
    lines.extend(f"{prayer_label(name, lang)}: <b>{times[name]}</b>" for name in PRAYER_NAMES if name in times)
    extra_times = extended_times_for_date(target_date)
    lines.extend(["", f"✨ <b>{tr(lang, 'additional_times')}</b>"])
    lines.extend(f"{prayer_label(name, lang)}: <b>{extra_times[name]}</b>" for name in EXTRA_TIME_NAMES if name in extra_times)
    return "\n".join(lines)


def format_daily_times(target_date, times, lang=LANG_LATIN):
    lines = [
        f"📅 <b>{tr(lang, 'daily_times')}</b>",
        f"{tr(lang, 'city')}: <b>{tr(lang, 'kokand')}</b>",
        f"{tr(lang, 'date')}: <b>{target_date.strftime('%d.%m.%Y')}</b>",
        "",
    ]
    lines.extend(f"{prayer_label(name, lang)}: <b>{times[name]}</b>" for name in PRAYER_NAMES if name in times)
    extra_times = extended_times_for_date(target_date)
    lines.extend(["", f"✨ <b>{tr(lang, 'additional_times')}</b>"])
    lines.extend(f"{prayer_label(name, lang)}: <b>{extra_times[name]}</b>" for name in EXTRA_TIME_NAMES if name in extra_times)
    return "\n".join(lines)


def format_prayer_notification(prayer_name, prayer_time, lang=LANG_LATIN, mosques=None):
    lines = [
        f"🕋 <b>{tr(lang, 'prayer_entered').format(prayer=prayer_label(prayer_name, lang))}</b>",
        "",
        tr(lang, "kokand"),
        f"{tr(lang, 'time')}: <b>{prayer_time}</b>",
    ]

    mosque_lines = mosque_prayer_lines(mosques or [], prayer_name, lang)
    if mosque_lines:
        lines.extend(["", f"🕌 <b>{tr(lang, 'mosque_prayer_section')}</b>"])
        lines.extend(mosque_lines)
    return "\n".join(lines)


def format_next_prayer_preview(prayer_name, prayer_time, lang=LANG_LATIN, mosques=None):
    title = "⏭️ <b>Keyingi namoz vaqti</b>" if lang == LANG_LATIN else "⏭️ <b>Кейинги намоз вақти</b>"
    lines = [
        title,
        "",
        tr(lang, "kokand"),
        f"{prayer_label(prayer_name, lang)}: <b>{prayer_time}</b>",
    ]

    mosque_lines = mosque_prayer_lines(mosques or [], prayer_name, lang)
    if mosque_lines:
        lines.extend(["", f"🕌 <b>{tr(lang, 'mosque_prayer_section')}</b>"])
        lines.extend(mosque_lines)
    return "\n".join(lines)


def mosque_prayer_lines(mosques, prayer_name, lang=LANG_LATIN):
    lines = []
    for index, mosque in enumerate(mosques, start=1):
        prayer_time = (mosque.get("prayer_times") or {}).get(prayer_name)
        if not prayer_time:
            continue
        location_url = mosque_location_url(mosque)
        lines.append(f"<b>{index}. {mosque_name(mosque, lang)}</b>")
        if location_url:
            lines.append(f"   {tr(lang, 'time')}: <b>{prayer_time}</b> | <a href=\"{location_url}\">{tr(lang, 'address')}</a>")
        else:
            lines.append(f"   {tr(lang, 'time')}: <b>{prayer_time}</b>")
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def mosque_location_url(mosque):
    location = mosque.get("location") or {}
    if not location.get("lat") or not location.get("lon"):
        return ""
    return f"https://maps.google.com/?q={location['lat']},{location['lon']}"


def format_mosque_prayer_by_name(prayer_name, mosques, lang=LANG_LATIN):
    lines = [
        f"🕌 <b>{tr(lang, 'mosque_prayer_for').format(prayer=prayer_label(prayer_name, lang))}</b>",
        "",
    ]
    prayer_lines = mosque_prayer_lines(mosques, prayer_name, lang)
    if not prayer_lines:
        lines.append(tr(lang, "times_missing"))
        return "\n".join(lines)
    lines.extend(prayer_lines)
    return "\n".join(lines)


def format_mosque_prayer_times(mosque, lang=LANG_LATIN):
    times = mosque.get("prayer_times") or {}
    lines = [
        tr(lang, "mosque_prayer_times"),
        f"{tr(lang, 'mosque')}: <b>{mosque_name(mosque, lang)}</b>",
        "",
    ]
    if not times:
        lines.append(tr(lang, "times_missing"))
        return "\n".join(lines)
    lines.extend(f"{prayer_label(name, lang)}: <b>{times[name]}</b>" for name in PRAYER_NAMES if name in times)
    return "\n".join(lines)


def format_mosque_location(mosque, lang=LANG_LATIN):
    location = mosque.get("location") or {}
    lines = [tr(lang, "mosque_location"), f"{tr(lang, 'mosque')}: <b>{mosque_name(mosque, lang)}</b>", ""]
    if location.get("address"):
        lines.append(f"{tr(lang, 'address')}: <b>{location['address']}</b>")
    if location.get("lat") and location.get("lon"):
        lines.append(f"{tr(lang, 'map')}: https://maps.google.com/?q={location['lat']},{location['lon']}")
    if len(lines) == 3:
        lines.append(tr(lang, "location_missing"))
    return "\n".join(lines)


def send_mosque_location(token, chat_id, mosque, mosques, lang=LANG_LATIN):
    send_message(token, chat_id, format_mosque_location(mosque, lang), main_keyboard(mosques, lang))
    location = mosque.get("location") or {}
    if location.get("lat") and location.get("lon"):
        send_location(token, chat_id, float(location["lat"]), float(location["lon"]), main_keyboard(mosques, lang))


def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def nearest_mosque(mosques, latitude, longitude):
    candidates = []
    for mosque in mosques:
        location = mosque.get("location") or {}
        if not location.get("lat") or not location.get("lon"):
            continue
        distance = distance_km(latitude, longitude, float(location["lat"]), float(location["lon"]))
        candidates.append((distance, mosque))
    if not candidates:
        return None, None
    return min(candidates, key=lambda item: item[0])


def help_text(lang=LANG_LATIN):
    return (
        ("Assalomu alaykum. Bu bot Qo'qon shahri masjidlari uchun namoz vaqtlarini yuboradi.\n\n"
         if lang == LANG_LATIN
         else "Ассалому алайкум. Бу бот Қўқон шаҳри масжидлари учун намоз вақтларини юборади.\n\n")
        + tr(lang, "choose_menu")
        + "\n\n"
        "/admin - admin buyruqlar\n"
        "/lang - tilni o'zgartirish\n"
        "/help - yordam"
    )


def find_mosque(mosques, text):
    normalized = normalize_text(text)
    for mosque in mosques:
        names = {normalize_text(mosque["id"]), normalize_text(mosque["name"])}
        cyrillic_name = MOSQUE_NAMES_CYRILLIC.get(mosque["id"])
        if cyrillic_name:
            names.add(normalize_text(cyrillic_name))
        if normalized in names:
            return mosque
    return None


def mosque_by_id(mosques, mosque_id):
    for mosque in mosques:
        if mosque["id"] == mosque_id:
            return mosque
    return None


def format_mosque_ids(mosques):
    lines = ["<b>Masjid ID ro'yxati</b>", ""]
    lines.extend(f"{mosque['id']} - {mosque['name']}" for mosque in mosques)
    return "\n".join(lines)


def parse_times(parts):
    values = {}
    for item in parts:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        prayer_name = match_prayer_name(key)
        if not prayer_name:
            continue
        if not valid_time(value):
            raise ValueError(f"{prayer_name} vaqti noto'g'ri: {value}")
        values[prayer_name] = value
    missing = [name for name in PRAYER_NAMES if name not in values]
    if missing:
        raise ValueError("Yetishmayotgan vaqtlar: " + ", ".join(missing))
    return values


def parse_partial_times(parts):
    values = {}
    for item in parts:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        prayer_name = match_prayer_name(key)
        if not prayer_name:
            continue
        if not valid_time(value):
            raise ValueError(f"{prayer_name} vaqti noto'g'ri: {value}")
        values[prayer_name] = value
    if not values:
        raise ValueError("Kamida bitta vaqt kiriting.")
    return values


def match_prayer_name(value):
    normalized = normalize_text(value)
    for name in PRAYER_NAMES:
        if normalized == normalize_text(name):
            return name
    return None


def valid_time(value):
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError:
        return False
    return True


def date_key(target_date):
    return target_date.strftime("%Y-%m-%d")


def handle_admin_command(token, chat_id, text, mosques):
    if not is_admin(chat_id):
        send_message(token, chat_id, "Bu buyruq faqat admin uchun.", main_keyboard(mosques))
        return True

    parts = text.split()
    command = parts[0]

    if command == "/admin":
        send_message(token, chat_id, admin_help_text(), main_keyboard(mosques))
        return True

    if command == "/mosqueids":
        send_message(token, chat_id, format_mosque_ids(mosques), main_keyboard(mosques))
        return True

    if command == "/usercount":
        users = merge_users(load_remote_users(), load_users())
        send_message(token, chat_id, f"Foydalanuvchilar soni: <b>{len(active_chat_ids(users))}</b>", main_keyboard(mosques))
        return True

    if command == "/envcheck":
        users_url = users_sheet_url()
        sheet_url = os.getenv("GOOGLE_SHEET_CSV_URL", "")
        text = (
            "<b>Env check</b>\n"
            f"USERS_SHEET_WEBAPP_URL: <b>{'bor' if users_url else 'yoq'}</b>\n"
            f"USERS URL /exec: <b>{'ha' if users_url.endswith('/exec') else 'yoq'}</b>\n"
            f"GOOGLE_SHEET_CSV_URL: <b>{'bor' if sheet_url else 'yoq'}</b>"
        )
        send_message(token, chat_id, text, main_keyboard(mosques))
        return True

    if command == "/syncusers":
        users = load_users()
        ok_count, errors = sync_all_remote_users(users)
        if errors:
            send_message(
                token,
                chat_id,
                f"Sync tugadi.\nMuvaffaqiyatli: <b>{ok_count}</b>\nXato: <b>{len(errors)}</b>\n\nBirinchi xato:\n<code>{errors[0]}</code>",
                main_keyboard(mosques),
            )
            return True
        send_message(token, chat_id, f"Userlar Google Sheets'ga sync qilindi: <b>{ok_count}</b>", main_keyboard(mosques))
        return True

    if command == "/refreshsheet":
        try:
            refreshed = refresh_mosques_from_sheet()
        except Exception as exc:
            send_message(token, chat_id, f"Sheet yangilash xatosi: {exc}", main_keyboard(mosques))
            return True
        send_message(token, chat_id, f"Google Sheets yangilandi. Masjidlar: <b>{len(refreshed)}</b>", main_keyboard(refreshed))
        return True

    if command == "/setlocation":
        if len(parts) < 4:
            send_message(token, chat_id, "Format: /setlocation masjid_id lat lon manzil", main_keyboard(mosques))
            return True
        mosque = mosque_by_id(mosques, parts[1])
        if not mosque:
            send_message(token, chat_id, "Masjid ID topilmadi. /mosqueids ni yuboring.", main_keyboard(mosques))
            return True
        try:
            lat = float(parts[2])
            lon = float(parts[3])
        except ValueError:
            send_message(token, chat_id, "Lat/lon raqam bo'lishi kerak.", main_keyboard(mosques))
            return True
        address = " ".join(parts[4:]).strip()
        mosque["location"] = {"lat": lat, "lon": lon}
        if address:
            mosque["location"]["address"] = address
        save_mosques(mosques)
        send_message(token, chat_id, f"Lokatsiya saqlandi: <b>{mosque['name']}</b>", main_keyboard(mosques))
        return True

    if command == "/setmasjidtime":
        if len(parts) < 3:
            send_message(token, chat_id, admin_help_text(), main_keyboard(mosques))
            return True
        mosque = mosque_by_id(mosques, parts[1])
        if not mosque:
            send_message(token, chat_id, "Masjid ID topilmadi. /mosqueids ni yuboring.", main_keyboard(mosques))
            return True
        try:
            mosque["prayer_times"] = parse_partial_times(parts[2:])
        except ValueError as exc:
            send_message(token, chat_id, str(exc), main_keyboard(mosques))
            return True
        save_mosques(mosques)
        send_message(token, chat_id, f"Masjid vaqtlari saqlandi: <b>{mosque['name']}</b>", main_keyboard(mosques))
        return True

    if command == "/clearmasjidtime":
        if len(parts) != 2:
            send_message(token, chat_id, "Format: /clearmasjidtime masjid_id", main_keyboard(mosques))
            return True
        mosque = mosque_by_id(mosques, parts[1])
        if not mosque:
            send_message(token, chat_id, "Masjid ID topilmadi. /mosqueids ni yuboring.", main_keyboard(mosques))
            return True
        mosque["prayer_times"] = {}
        save_mosques(mosques)
        send_message(token, chat_id, f"Masjid vaqtlari o'chirildi: <b>{mosque['name']}</b>", main_keyboard(mosques))
        return True

    return False


def handle_update(token, update, users, mosques):
    message = update.get("message")
    if not message:
        return

    chat_id = str(message["chat"]["id"])
    text = (message.get("text") or "").strip()
    today = datetime.now(BOT_TIMEZONE).date()
    register_user(users, chat_id, message)
    lang = user_lang(users, chat_id)

    if "location" in message:
        location = message["location"]
        distance, mosque = nearest_mosque(mosques, location["latitude"], location["longitude"])
        if not mosque:
            send_message(token, chat_id, tr(lang, "all_locations_missing"), main_keyboard(mosques, lang))
            return
        response = [
            tr(lang, "nearest_title"),
            f"{tr(lang, 'mosque')}: <b>{mosque_name(mosque, lang)}</b>",
            f"{tr(lang, 'distance')}: <b>{distance:.2f} km</b>",
            "",
            format_mosque_location(mosque, lang),
        ]
        send_message(token, chat_id, "\n".join(response), main_keyboard(mosques, lang))
        location_data = mosque.get("location") or {}
        if location_data.get("lat") and location_data.get("lon"):
            send_location(token, chat_id, float(location_data["lat"]), float(location_data["lon"]), main_keyboard(mosques, lang))
        return

    if text.startswith(("/admin", "/mosqueids", "/usercount", "/envcheck", "/syncusers", "/refreshsheet", "/setlocation", "/setmasjidtime", "/clearmasjidtime")):
        if handle_admin_command(token, chat_id, text, mosques):
            return

    if text == "/start":
        users.setdefault(chat_id, {})["mode"] = "language"
        save_users(users)
        send_message(token, chat_id, "Tilni tanlang / Тилни танланг", language_keyboard())
        return

    if text in {BTN_LANG_LATIN, BTN_LANG_CYRILLIC}:
        lang = LANG_CYRILLIC if text == BTN_LANG_CYRILLIC else LANG_LATIN
        users.setdefault(chat_id, {})["lang"] = lang
        users.setdefault(chat_id, {})["mode"] = "menu"
        save_users(users)
        sync_remote_user(chat_id, users[chat_id])
        send_message(token, chat_id, tr(lang, "choose_menu"), main_keyboard(mosques, lang))
        return

    if text in {"/help", "/lang"}:
        if text == "/lang":
            send_message(token, chat_id, "Tilni tanlang / Тилни танланг", language_keyboard())
            return
        send_message(token, chat_id, help_text(lang), main_keyboard(mosques, lang))
        return

    if text in {BTN_MAIN_MENU, BTN_BACK, tr(lang, "main_menu"), tr(lang, "back"), "Bosh menyu", "Ortga", "Бош меню", "Ортга"}:
        users.setdefault(chat_id, {})["mode"] = "menu"
        save_users(users)
        sync_remote_user(chat_id, users[chat_id])
        send_message(token, chat_id, f"<b>{tr(lang, 'main_menu')}</b>", main_keyboard(mosques, lang))
        return

    if text in {BTN_ENTRY_TIMES, tr(lang, "entry_times"), "Kirish vaqtlari", "Кириш вақтлари"}:
        times = prayer_times_by_kokand(today)
        send_tracked_message(token, users, chat_id, format_entry_times(today, times, lang), main_keyboard(mosques, lang))
        return

    if text in {
        BTN_PRAYER_TIMES_IN_MOSQUES,
        tr(lang, "prayer_times_in_mosques"),
        "Namoz bo'yicha vaqtlar",
        "Namoz vaqtlari masjidlarda",
        "Намоз бўйича вақтлар",
        "Намоз вақтлари масжидларда",
    }:
        users.setdefault(chat_id, {})["mode"] = "prayer_times_in_mosques"
        save_users(users)
        send_message(token, chat_id, tr(lang, "choose_prayer"), prayer_keyboard(lang))
        return

    if text in {
        BTN_MOSQUE_TIMES,
        tr(lang, "mosque_times"),
        "Masjid bo'yicha vaqtlar",
        "Masjidlardagi vaqtlar",
        "Масжид бўйича вақтлар",
        "Масжидлардаги вақтлар",
    }:
        users.setdefault(chat_id, {})["mode"] = "mosque_times"
        save_users(users)
        send_message(token, chat_id, tr(lang, "choose_mosque"), mosque_keyboard(mosques, lang))
        return

    if text in {BTN_MOSQUE_LOCATIONS, tr(lang, "mosque_locations"), "Masjid Joylashuvlari", "Масжид жойлашувлари"}:
        users.setdefault(chat_id, {})["mode"] = "mosque_locations"
        save_users(users)
        send_message(token, chat_id, tr(lang, "choose_location_mosque"), mosque_keyboard(mosques, lang))
        return

    if text in {BTN_NEAREST_MOSQUE, tr(lang, "nearest_mosque"), "Menga eng yaqin masjid", "Men turgan joyga eng yaqin masjid", "Менга энг яқин масжид", "Мен турган жойга энг яқин масжид"}:
        users.setdefault(chat_id, {})["mode"] = "nearest"
        save_users(users)
        send_message(token, chat_id, tr(lang, "send_location_prompt"), location_request_keyboard(lang))
        return

    prayer_name = prayer_from_button(text)
    if prayer_name:
        send_tracked_message(token, users, chat_id, format_mosque_prayer_by_name(prayer_name, mosques, lang), prayer_keyboard(lang))
        return

    mosque = find_mosque(mosques, text)
    if mosque:
        mode = users.get(chat_id, {}).get("mode")
        users.setdefault(chat_id, {})["mosque_id"] = mosque["id"]
        save_users(users)
        if mode == "mosque_locations":
            send_mosque_location(token, chat_id, mosque, mosques, lang)
            return
        send_tracked_message(token, users, chat_id, format_mosque_prayer_times(mosque, lang), main_keyboard(mosques, lang))
        return

    if text in {"/today", "/entry"}:
        times = prayer_times_by_kokand(today)
        send_tracked_message(token, users, chat_id, format_entry_times(today, times, lang), main_keyboard(mosques, lang))
        return

    if text in {"/mosques"}:
        users.setdefault(chat_id, {})["mode"] = "mosque_times"
        save_users(users)
        send_message(token, chat_id, tr(lang, "choose_mosque"), mosque_keyboard(mosques, lang))
        return

    send_message(token, chat_id, tr(lang, "not_understood"), main_keyboard(mosques, lang))


def send_saved_mosque_times(token, chat_id, users, mosques, target_date, title):
    mosque_id = users.get(chat_id, {}).get("mosque_id")
    mosque = mosque_by_id(mosques, mosque_id)
    lang = user_lang(users, chat_id)
    if not mosque:
        send_message(token, chat_id, tr(lang, "choose_mosque"), mosque_keyboard(mosques, lang))
        return
    send_prayer_times(token, chat_id, mosque, target_date, title, mosques, lang)


def send_prayer_times(token, chat_id, mosque, target_date, title, mosques, lang=LANG_LATIN):
    saved_times = mosque.get("times", {}).get(date_key(target_date))
    if saved_times:
        times = saved_times
    else:
        times = prayer_times_by_kokand(target_date)
        times = apply_offsets(times, mosque.get("offsets", {}))
    send_message(token, chat_id, format_times(title, mosque, target_date, times, lang), main_keyboard(mosques, lang))


def active_chat_ids(users):
    return [chat_id for chat_id, data in users.items() if isinstance(data, dict) and data.get("active", True)]


def earliest_mosque_prayer_time(mosques, prayer_name):
    earliest_time = None
    for mosque in mosques:
        prayer_time = (mosque.get("prayer_times") or {}).get(prayer_name)
        if not prayer_time or not valid_time(prayer_time):
            continue
        if earliest_time is None or prayer_time < earliest_time:
            earliest_time = prayer_time
    return earliest_time


def preview_trigger_time(target_date, prayer_time):
    hour, minute = map(int, prayer_time.split(":", 1))
    return datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=BOT_TIMEZONE) - timedelta(hours=1)


def check_next_prayer_previews(token, users, notifications, mosques):
    now = datetime.now(BOT_TIMEZONE)
    today = now.date()
    current_time = now.strftime("%H:%M")
    today_key = date_key(today)
    sent_today = notifications.setdefault(today_key, [])
    changed = False

    for prayer_name in NOTIFICATION_PRAYERS:
        earliest_time = earliest_mosque_prayer_time(mosques, prayer_name)
        if not earliest_time:
            continue

        trigger_at = preview_trigger_time(today, earliest_time)
        if trigger_at.date() != today or trigger_at.strftime("%H:%M") != current_time:
            continue

        notification_key = f"preview:{today_key}:{prayer_name}"
        if notification_key in sent_today:
            continue

        try:
            times = prayer_times_by_kokand(today)
        except Exception as exc:
            print(f"Namoz preview vaqtlarini olish xatosi: {exc}", file=sys.stderr)
            continue

        prayer_time = times.get(prayer_name)
        if not prayer_time:
            continue

        preview_key = preview_message_key(today, prayer_name)
        for chat_id in active_chat_ids(users):
            try:
                text = format_next_prayer_preview(prayer_name, prayer_time, user_lang(users, chat_id), mosques)
                send_preview_message(token, users, chat_id, preview_key, text)
            except Exception as exc:
                print(f"Namoz preview yuborish xatosi ({chat_id}): {exc}", file=sys.stderr)

        sent_today.append(notification_key)
        changed = True

    if changed:
        notifications.clear()
        notifications[today_key] = sent_today
        save_notifications(notifications)


def check_prayer_notifications(token, users, notifications, mosques):
    now = datetime.now(BOT_TIMEZONE)
    today = now.date()
    today_key = date_key(today)
    current_time = now.strftime("%H:%M")

    try:
        times = prayer_times_by_kokand(today)
    except Exception as exc:
        print(f"Notification vaqtlarini olish xatosi: {exc}", file=sys.stderr)
        return

    sent_today = notifications.setdefault(today_key, [])
    changed = False
    for prayer_name in NOTIFICATION_PRAYERS:
        prayer_time = times.get(prayer_name)
        if prayer_time != current_time or prayer_name in sent_today:
            continue

        for chat_id in active_chat_ids(users):
            try:
                delete_preview_message(token, users, chat_id, preview_message_key(today, prayer_name))
                text = format_prayer_notification(prayer_name, prayer_time, user_lang(users, chat_id), mosques)
                send_tracked_message(token, users, chat_id, text)
            except Exception as exc:
                print(f"Notification yuborish xatosi ({chat_id}): {exc}", file=sys.stderr)
        sent_today.append(prayer_name)
        changed = True

    if changed:
        notifications.clear()
        notifications[today_key] = sent_today
        save_notifications(notifications)


def check_daily_cleanup(token, users, notifications):
    now = datetime.now(BOT_TIMEZONE)
    if now.strftime("%H:%M") != DAILY_CLEANUP_TIME:
        return

    today_key = date_key(now.date())
    sent_key = "daily_cleanup"
    sent_today = notifications.setdefault(today_key, [])
    if sent_key in sent_today:
        return

    for chat_id in active_chat_ids(users):
        try:
            clear_tracked_bot_messages(token, users, chat_id)
        except Exception as exc:
            print(f"Kunlik tozalash xatosi ({chat_id}): {exc}", file=sys.stderr)

    sent_today.append(sent_key)
    notifications.clear()
    notifications[today_key] = sent_today
    save_notifications(notifications)


def check_daily_summary(token, users, notifications, mosques):
    now = datetime.now(BOT_TIMEZONE)
    if now.strftime("%H:%M") != DAILY_SUMMARY_TIME:
        return

    today = now.date()
    today_key = date_key(today)
    sent_key = "daily_summary"
    sent_today = notifications.setdefault(today_key, [])
    if sent_key in sent_today:
        return

    try:
        times = prayer_times_by_kokand(today)
    except Exception as exc:
        print(f"Kunlik jadval vaqtlarini olish xatosi: {exc}", file=sys.stderr)
        return

    for chat_id in active_chat_ids(users):
        lang = user_lang(users, chat_id)
        try:
            clear_tracked_bot_messages(token, users, chat_id)
            text = format_daily_times(today, times, lang)
            send_tracked_message(token, users, chat_id, text, main_keyboard(mosques, lang))
        except Exception as exc:
            print(f"Kunlik jadval yuborish xatosi ({chat_id}): {exc}", file=sys.stderr)

    sent_today.append(sent_key)
    notifications.clear()
    notifications[today_key] = sent_today
    save_notifications(notifications)


def shutdown(_signum, _frame):
    global running
    running = False


def run():
    load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN topilmadi. .env fayl yarating yoki environment variable sozlang.", file=sys.stderr)
        sys.exit(1)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    users = merge_users(load_remote_users(), load_users())
    save_users(users)
    notifications = load_notifications()
    offset = None
    print("Bot ishga tushdi. To'xtatish uchun Ctrl+C bosing.")

    while running:
        mosques = load_mosques()
        check_daily_cleanup(token, users, notifications)
        check_daily_summary(token, users, notifications, mosques)
        check_next_prayer_previews(token, users, notifications, mosques)
        check_prayer_notifications(token, users, notifications, mosques)
        payload = {"timeout": 10}
        if offset is not None:
            payload["offset"] = offset
        try:
            result = telegram(token, "getUpdates", payload)
            for update in result.get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle_update(token, update, users, mosques)
                except Exception as exc:
                    chat_id = update.get("message", {}).get("chat", {}).get("id")
                    if chat_id:
                        send_message(token, chat_id, "Xatolik yuz berdi. Keyinroq qayta urinib ko'ring.", main_keyboard(mosques))
                    print(f"Update xatosi: {exc}", file=sys.stderr)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"Ulanish xatosi: {exc}", file=sys.stderr)
            time.sleep(5)
        except RuntimeError as exc:
            if "HTTP 409" in str(exc):
                print("Telegram 409 Conflict: bu token bilan boshqa bot instance ishlayapti.", file=sys.stderr)
                time.sleep(10)
                continue
            print(f"API xatosi: {exc}", file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    run()
