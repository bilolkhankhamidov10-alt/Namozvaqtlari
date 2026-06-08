# Qo'qon Namoz Vaqtlari Telegram Bot

Qo'qon shahri masjidlari uchun namoz vaqtlarini yuboradigan Telegram bot. Python bilan yozilgan, tashqi Python kutubxonalar talab qilmaydi.

## Ishga tushirish

1. BotFather orqali Telegram bot oching va token oling.
2. `.env.example` faylidan `.env` yarating.
3. `.env` ichiga tokenni yozing:

```env
TELEGRAM_BOT_TOKEN=1234567890:token
ADMIN_IDS=123456789
```

4. Botni ishga tushiring:

```bash
python3 bot.py
```

## SSL sertifikat xatosi

MacOS'da `CERTIFICATE_VERIFY_FAILED` chiqsa, avval Python bilan kelgan `Install Certificates.command` faylini ishga tushiring. Odatda u Applications ichidagi Python papkasida bo'ladi.

Agar internetingiz company proxy yoki antivirus orqali o'tsa, CA fayl yo'lini `.env`ga yozing:

```env
TELEGRAM_CA_FILE=/path/to/ca.pem
```

Faqat lokal test uchun tekshiruvni vaqtincha o'chirish mumkin:

```env
TELEGRAM_SSL_NO_VERIFY=1
```

Bu oxirgi variantni production uchun ishlatmang.

## Bosh Menyu

`/start` bosilganda bot avval til tanlashni ko'rsatadi:

- `O'zbekcha` - lotin yozuvidagi menyu va javoblar
- `Ўзбекча` - kirill yozuvidagi menyu va javoblar

Bot bosh menyusida 5 ta bo'lim bor:

- `🕋 Kirish vaqtlari` - Qo'qon shahri namoz kirish vaqtlari, bot avtomatik oladi
- `🕌 Namoz bo'yicha vaqtlar` - 5 vaqt namozdan birini tanlab, masjidlarda o'qiladigan vaqtlarni ko'rish
- `📋 Masjid bo'yicha vaqtlar` - masjidni tanlab, o'sha masjiddagi barcha namoz vaqtlarini ko'rish
- `📍 Masjid Joylashuvlari` - masjid xarita havolasi va manzili
- `🧭 Menga eng yaqin masjid` - foydalanuvchi lokatsiyasiga eng yaqin masjid

Bot tugmalarida yo'nalish uchun ikonlar ishlatiladi:

- `◀️ Ortga`
- `🏠 Bosh menyu`
- `📡 Lokatsiyamni yuborish`

Bot faqat Qo'qon shahri uchun ishlaydi.

## Notificationlar

Bot foydalanuvchi bir marta yozganidan keyin uni `users.json` ichida saqlaydi. Bomdod, Peshin, Asr, Shom va Xufton vaqti kirganda barcha saqlangan foydalanuvchilarga xabar yuboradi.

Takror yubormaslik holati `notifications.json` faylida saqlanadi.

Har kuni soat `01:00` da bot foydalanuvchilarga bugungi namoz vaqtlarini yuboradi. Xabarda Tahajjud oralig'i, Zuho va Qiyom vaqti ham bo'ladi.

Telegram cheklovi sabab bot foydalanuvchining eski yozgan xabarlarini o'chira olmaydi. Bot faqat o'zi kuzatib saqlagan bot xabarlarini o'chirishga harakat qiladi.

## Userlarni Google Sheets'da Saqlash

`users.json` lokal fayl bo'lgani uchun hosting/deploy almashganda yo'qolishi mumkin. Userlarni Google Sheets'da saqlash uchun Google Apps Script web app ishlatiladi.

Sheet ustunlari:

```text
chat_id | active | first_name | username | lang | last_seen
```

Apps Script kodi:

```javascript
const SHEET_NAME = 'users';
const HEADERS = ['chat_id', 'active', 'first_name', 'username', 'lang', 'last_seen'];

function sheet() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
  }
  ensureHeaders(sh);
  return sh;
}

function ensureHeaders(sh) {
  const firstRow = sh.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const hasHeaders = HEADERS.every((header, index) => firstRow[index] === header);
  if (!hasHeaders) {
    sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }
}

function doGet(e) {
  const sh = sheet();
  const rows = sh.getDataRange().getValues();
  const headers = rows.shift();
  const users = rows
    .filter(row => row[0])
    .map(row => Object.fromEntries(headers.map((key, index) => [key, row[index]])));
  return ContentService
    .createTextOutput(JSON.stringify({ users }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  const data = JSON.parse(e.postData.contents);
  const sh = sheet();
  const rows = sh.getDataRange().getValues();
  const headers = rows[0];
  const chatIdIndex = headers.indexOf('chat_id');
  let targetRow = -1;

  for (let i = 1; i < rows.length; i++) {
    if (String(rows[i][chatIdIndex]) === String(data.chat_id)) {
      targetRow = i + 1;
      break;
    }
  }

  const values = headers.map(key => data[key] ?? '');
  if (targetRow === -1) {
    sh.appendRow(values);
  } else {
    sh.getRange(targetRow, 1, 1, headers.length).setValues([values]);
  }

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

Apps Script deploy qilingandan keyin web app URL'ni `.env`ga yozing:

```env
USERS_SHEET_WEBAPP_URL=https://script.google.com/macros/s/.../exec
```

Eski lokal userlarni bir marta sheetga yuborish:

```text
/syncusers
```

## Admin Sozlash

Admin buyruqlar ishlashi uchun o'zingizning Telegram ID raqamingizni `.env` ichidagi `ADMIN_IDS`ga yozing. Bir nechta admin bo'lsa vergul bilan ajrating:

```env
ADMIN_IDS=123456789,987654321
```

Admin buyruqlar:

- `/mosqueids` - masjid ID ro'yxatini ko'rish
- `/usercount` - foydalanuvchilar sonini ko'rish
- `/setlocation masjid_id lat lon manzil` - masjid lokatsiyasini saqlash
- `/setmasjidtime masjid_id Bomdod=03:30 Peshin=12:45 Asr=18:00 Shom=19:50 Xufton=21:40` - masjidda o'qiladigan vaqtlarni saqlash
- `/clearmasjidtime masjid_id` - masjidda o'qiladigan vaqtlarni o'chirish

Masalan:

```text
/setlocation yangi_chorsu_mir 40.5281 70.9421 Yangi Chorsu atrofida
/setmasjidtime yangi_chorsu_mir Bomdod=03:30 Peshin=12:45 Asr=18:00 Shom=19:50 Xufton=21:40
```

## Masjidlar

Masjidlar ro'yxati Google Sheets'dan olinadi. Agar `GOOGLE_SHEET_CSV_URL` sozlanmagan bo'lsa, bot `mosques.json` faylini fallback sifatida ishlatadi.

Google Sheets ustunlari:

```text
ID | NAME | LOCATION | ADDRESS | BOMDOD | PESHIN | ASR | SHOM | XUFTON
```

`LOCATION` qiymati `lat, lon` formatida bo'lishi kerak:

```text
40.538890925019835, 70.95234283818272
```

Sheetni ulash:

1. Google Sheets'da `File -> Share -> Publish to web` ni oching.
2. Kerakli sheetni tanlang.
3. Format sifatida `Comma-separated values (.csv)` ni tanlang.
4. Chiqqan CSV linkni `.env` ichiga yozing:

```env
GOOGLE_SHEET_CSV_URL=https://docs.google.com/spreadsheets/d/e/.../pub?gid=0&single=true&output=csv
```

Bot sheetdagi o'zgarishlarni odatda 15 soniya cache bilan o'qiydi.
Cache muddatini `.env` orqali o'zgartirish mumkin:

```env
SHEET_CACHE_SECONDS=15
```

Admin sheetni darhol yangilashi mumkin:

```text
/refreshsheet
```

Fallback `mosques.json` formati:

```json
{
  "id": "masjid_id",
  "name": "Masjid nomi",
  "location": {},
  "prayer_times": {},
  "times": {},
  "offsets": {}
}
```

Masjidda o'qiladigan vaqtlar `prayer_times` ichida saqlanadi:

```json
{
  "id": "namuna",
  "name": "Namuna masjidi",
  "location": {
    "lat": 40.5281,
    "lon": 70.9421,
    "address": "Yangi Chorsu atrofida"
  },
  "prayer_times": {
    "Bomdod": "03:30",
    "Peshin": "12:45",
    "Asr": "18:00",
    "Shom": "19:50",
    "Xufton": "21:40"
  },
  "times": {},
  "offsets": {}
}
```

Kirish vaqtlari admin tomonidan kiritilmaydi. Bot ularni Qo'qon shahri uchun avtomatik oladi. Google Sheets'da faqat masjid lokatsiyalari va masjidda o'qiladigan vaqtlar bo'ladi.
# Namozvaqtlari
