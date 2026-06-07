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
NOTIFICATION_PRAYERS = ("Bomdod", "Peshin", "Asr", "Shom", "Xufton")
DEFAULT_SHEET_CACHE_SECONDS = 15
mosques_cache = {"loaded_at": 0, "data": None}
prayer_cache = {"date": None, "times": None}
BTN_ENTRY_TIMES = "🕋 Kirish vaqtlari"
BTN_MOSQUE_TIMES = "🕌 Masjidlardagi vaqtlar"
BTN_MOSQUE_LOCATIONS = "📍 Masjid Joylashuvlari"
BTN_NEAREST_MOSQUE = "🧭 Men turgan joyga eng yaqin masjid"
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
        "mosque_times": "🕌 Masjidlardagi vaqtlar",
        "mosque_locations": "📍 Masjid Joylashuvlari",
        "nearest_mosque": "🧭 Men turgan joyga eng yaqin masjid",
        "send_location": "📡 Lokatsiyamni yuborish",
        "back": "◀️ Ortga",
        "main_menu": "🏠 Bosh menyu",
        "choose_language": "Tilni tanlang",
        "choose_menu": "Menyudan kerakli bo'limni tanlang.",
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
        "mosque_location": "📍 <b>Masjid joylashuvi</b>",
        "mosque_prayer_times": "🕌 <b>Masjiddagi namoz vaqtlari</b>",
    },
    LANG_CYRILLIC: {
        "kokand": "Қўқон шаҳри",
        "entry_times": "🕋 Кириш вақтлари",
        "mosque_times": "🕌 Масжидлардаги вақтлар",
        "mosque_locations": "📍 Масжид жойлашувлари",
        "nearest_mosque": "🧭 Мен турган жойга энг яқин масжид",
        "send_location": "📡 Локациямни юбориш",
        "back": "◀️ Ортга",
        "main_menu": "🏠 Бош меню",
        "choose_language": "Тилни танланг",
        "choose_menu": "Менюдан керакли бўлимни танланг.",
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
    },
    LANG_CYRILLIC: {
        "Bomdod": "Бомдод",
        "Quyosh": "Қуёш",
        "Peshin": "Пешин",
        "Asr": "Аср",
        "Shom": "Шом",
        "Xufton": "Хуфтон",
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
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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
    telegram(token, "sendMessage", payload)


def send_location(token, chat_id, latitude, longitude, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "latitude": latitude,
        "longitude": longitude,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    telegram(token, "sendLocation", payload)


def load_users():
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_users(users):
    DATA_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def register_user(users, chat_id, message):
    user_data = users.setdefault(str(chat_id), {})
    user = message.get("from") or {}
    user_data["active"] = True
    user_data["first_name"] = user.get("first_name", user_data.get("first_name", ""))
    user_data["username"] = user.get("username", user_data.get("username", ""))
    user_data["last_seen"] = datetime.now(BOT_TIMEZONE).isoformat(timespec="seconds")
    save_users(users)


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
            [{"text": tr(lang, "entry_times")}],
            [{"text": tr(lang, "mosque_times")}],
            [{"text": tr(lang, "mosque_locations")}],
            [{"text": tr(lang, "nearest_mosque")}],
        ],
        "resize_keyboard": True,
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
        "/refreshsheet - Google Sheets ma'lumotlarini darhol yangilash\n"
        "/setlocation masjid_id lat lon manzil - lokatsiya saqlash\n"
        "/setmasjidtime masjid_id Bomdod=03:30 Peshin=12:45 Asr=18:00 Shom=19:50 Xufton=21:40\n"
        "/clearmasjidtime masjid_id"
    )


def prayer_times_by_kokand(target_date):
    key = date_key(target_date)
    if prayer_cache["date"] == key and prayer_cache["times"]:
        return prayer_cache["times"]

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
    prayer_cache["date"] = key
    prayer_cache["times"] = times
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
    return "\n".join(lines)


def format_prayer_notification(prayer_name, prayer_time, lang=LANG_LATIN):
    return (
        f"🕋 <b>{tr(lang, 'prayer_entered').format(prayer=prayer_label(prayer_name, lang))}</b>\n\n"
        f"{tr(lang, 'kokand')}\n"
        f"{tr(lang, 'time')}: <b>{prayer_time}</b>"
    )


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
        users = load_users()
        send_message(token, chat_id, f"Foydalanuvchilar soni: <b>{len(active_chat_ids(users))}</b>", main_keyboard(mosques))
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

    if text.startswith(("/admin", "/mosqueids", "/usercount", "/refreshsheet", "/setlocation", "/setmasjidtime", "/clearmasjidtime")):
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
        send_message(token, chat_id, f"<b>{tr(lang, 'main_menu')}</b>", main_keyboard(mosques, lang))
        return

    if text in {BTN_ENTRY_TIMES, tr(lang, "entry_times"), "Kirish vaqtlari", "Кириш вақтлари"}:
        times = prayer_times_by_kokand(today)
        send_message(token, chat_id, format_entry_times(today, times, lang), main_keyboard(mosques, lang))
        return

    if text in {BTN_MOSQUE_TIMES, tr(lang, "mosque_times"), "Masjidlardagi vaqtlar", "Масжидлардаги вақтлар"}:
        users.setdefault(chat_id, {})["mode"] = "mosque_times"
        save_users(users)
        send_message(token, chat_id, tr(lang, "choose_mosque"), mosque_keyboard(mosques, lang))
        return

    if text in {BTN_MOSQUE_LOCATIONS, tr(lang, "mosque_locations"), "Masjid Joylashuvlari", "Масжид жойлашувлари"}:
        users.setdefault(chat_id, {})["mode"] = "mosque_locations"
        save_users(users)
        send_message(token, chat_id, tr(lang, "choose_location_mosque"), mosque_keyboard(mosques, lang))
        return

    if text in {BTN_NEAREST_MOSQUE, tr(lang, "nearest_mosque"), "Men turgan joyga eng yaqin masjid", "Мен турган жойга энг яқин масжид"}:
        users.setdefault(chat_id, {})["mode"] = "nearest"
        save_users(users)
        send_message(token, chat_id, tr(lang, "send_location_prompt"), location_request_keyboard(lang))
        return

    mosque = find_mosque(mosques, text)
    if mosque:
        mode = users.get(chat_id, {}).get("mode")
        users.setdefault(chat_id, {})["mosque_id"] = mosque["id"]
        save_users(users)
        if mode == "mosque_locations":
            send_mosque_location(token, chat_id, mosque, mosques, lang)
            return
        send_message(token, chat_id, format_mosque_prayer_times(mosque, lang), main_keyboard(mosques, lang))
        return

    if text in {"/today", "/entry"}:
        times = prayer_times_by_kokand(today)
        send_message(token, chat_id, format_entry_times(today, times, lang), main_keyboard(mosques, lang))
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


def check_prayer_notifications(token, users, notifications):
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
                text = format_prayer_notification(prayer_name, prayer_time, user_lang(users, chat_id))
                send_message(token, chat_id, text)
            except Exception as exc:
                print(f"Notification yuborish xatosi ({chat_id}): {exc}", file=sys.stderr)
        sent_today.append(prayer_name)
        changed = True

    if changed:
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
    users = load_users()
    notifications = load_notifications()
    offset = None
    print("Bot ishga tushdi. To'xtatish uchun Ctrl+C bosing.")

    while running:
        check_prayer_notifications(token, users, notifications)
        payload = {"timeout": 10}
        if offset is not None:
            payload["offset"] = offset
        try:
            result = telegram(token, "getUpdates", payload)
            for update in result.get("result", []):
                mosques = load_mosques()
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
