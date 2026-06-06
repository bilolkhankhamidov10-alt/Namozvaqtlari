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

Bot bosh menyusida 4 ta bo'lim bor:

- `🕋 Kirish vaqtlari` - Qo'qon shahri namoz kirish vaqtlari, bot avtomatik oladi
- `🕌 Masjidlardagi vaqtlar` - har bir masjidda o'qiladigan namoz vaqtlari
- `📍 Masjid Joylashuvlari` - masjid xarita havolasi va manzili
- `🧭 Men turgan joyga eng yaqin masjid` - foydalanuvchi lokatsiyasiga eng yaqin masjid

Bot tugmalarida yo'nalish uchun ikonlar ishlatiladi:

- `◀️ Ortga`
- `🏠 Bosh menyu`
- `📡 Lokatsiyamni yuborish`

Bot faqat Qo'qon shahri uchun ishlaydi.

## Notificationlar

Bot foydalanuvchi bir marta yozganidan keyin uni `users.json` ichida saqlaydi. Bomdod, Peshin, Asr, Shom va Xufton vaqti kirganda barcha saqlangan foydalanuvchilarga xabar yuboradi.

Takror yubormaslik holati `notifications.json` faylida saqlanadi.

## Admin Sozlash

Admin buyruqlar ishlashi uchun o'zingizning Telegram ID raqamingizni `.env` ichidagi `ADMIN_IDS`ga yozing. Bir nechta admin bo'lsa vergul bilan ajrating:

```env
ADMIN_IDS=123456789,987654321
```

Admin buyruqlar:

- `/mosqueids` - masjid ID ro'yxatini ko'rish
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

Bot sheetdagi o'zgarishlarni 60 soniya cache bilan o'qiydi.

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
