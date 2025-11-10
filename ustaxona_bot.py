import logging
import pandas as pd
import sqlite3
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import sys
import re

# === ⚙️ Sozlamalar ===
# !!! BOT_TOKEN ni o'zingizniki bilan almashtiring !!!
BOT_TOKEN = "8280685098:AAHTCx8zYx5H04pJAeOJO8zduRIDUXGGDuI"
# Fayl nomi
EXCEL_PATH = "customers.xlsx"
DB_PATH = "customers.db"
# Har bir mijoz bloki 10 qatordan iborat
ROWS_PER_CLIENT = 10

# !!! ADMIN_ID ni o'zingizning Telegram ID'ingiz bilan almashtiring (raqam ko'rinishida) !!!
ADMIN_ID = 914525724

# === 📜 Log sozlamalari ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def init_db():
    """SQLite bazasini yaratish va jadvallarni o'rnatish. (O'zbekcha nomlar)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Mijoz jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Mijoz (
        id INTEGER PRIMARY KEY,
        telefon_raqami TEXT UNIQUE,
        ism TEXT,
        familiya TEXT
    );
    """)

    # 2. Avto jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Avto (
        id INTEGER PRIMARY KEY,
        mijoz_id INTEGER,
        model TEXT,
        raqam TEXT UNIQUE,
        FOREIGN KEY(mijoz_id) REFERENCES Mijoz(id)
    );
    """)

    # 3. Tashrif jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Tashrif (
        id INTEGER PRIMARY KEY,
        avto_id INTEGER,
        sana TEXT,
        joriy_km INTEGER,
        keyingi_km INTEGER,
        keyingi_sana TEXT,
        xizmatlar TEXT,
        FOREIGN KEY(avto_id) REFERENCES Avto(id)
    );
    """)

    conn.commit()
    conn.close()


def clean_phone(phone: str) -> str:
    """Telefon raqamdan faqat raqamlarni ajratib oladi va uni 998 formatida 12 xonali qilib qaytaradi."""
    if not phone: return ""
    digits = "".join(filter(str.isdigit, str(phone)))
    if len(digits) == 12 and digits.startswith("998"): return digits
    if len(digits) == 9: return "998" + digits
    if len(digits) == 11 and digits.startswith("8"): return "998" + digits[1:]
    if len(digits) == 10 and digits.startswith("9"): return "998" + digits
    return digits


def clean_km(km_str: str) -> int:
    """Km satridan faqat raqamni int sifatida ajratib oladi."""
    if not km_str: return 0
    digits = re.sub(r'\D', '', str(km_str).split('/')[0])
    return int(digits) if digits else 0


# --- ANIQ VA TUZATILGAN MIGRATSIYA FUNKSIYASI ---

def migrate_excel_to_db() -> str:
    """CSV/Excel fayldan ma'lumotlarni o'qish va DBga saqlash (10-qatorli blok mantig'ida)."""
    try:
        # skiprows=1: 1-qatorni tashlab yuboramiz (Excel sarlavhasi). Ma'lumotlar endi indeks 0 dan boshlanadi.
        df = pd.read_csv(EXCEL_PATH, header=None, dtype=str, encoding='utf-8', engine="python", skiprows=1)
        if df.empty:
            return "⚠️ **Xatolik:** Fayl bo'sh yoki noto'g'ri formatda."
    except FileNotFoundError:
        return f"⚠️ **Xatolik:** '{EXCEL_PATH}' fayli topilmadi."
    except Exception as e:
        return f"⚠️ **Faylni o‘qishda xatolik:** {e}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Jadvallarni tozalash (O'zbekcha nomlar)
    cursor.execute("DELETE FROM Mijoz")
    cursor.execute("DELETE FROM Avto")
    cursor.execute("DELETE FROM Tashrif")
    conn.commit()

    total_rows = len(df)
    total_blocks = total_rows // ROWS_PER_CLIENT

    mijoz_soni = 0
    tashrif_soni = 0

    for i in range(0, total_rows, ROWS_PER_CLIENT):
        block_rows = df.iloc[i: i + ROWS_PER_CLIENT].values.tolist()
        if len(block_rows) < ROWS_PER_CLIENT: continue

        mijoz_data = {"tel": "", "ism_full": "", "model": "", "raqam": ""}
        tashrif_data = {"sana": "", "joriy_km": 0, "keyingi_km": 0, "keyingi_sana": "", "xizmatlar": []}

        # 1. Telefon Raqamini olish (3-index, 5 va 6-ustunlar)
        row_phone = block_rows[3]
        if len(row_phone) > 6:
            country_code = str(row_phone[5]).strip()
            phone_number_part = str(row_phone[6]).strip()
            cleaned_combined_phone = clean_phone(country_code + phone_number_part)
            if len(cleaned_combined_phone) == 12:
                mijoz_data["tel"] = cleaned_combined_phone

        # 2. Tashrif Sanasini olish (1-index, 6-ustun)
        row_date = block_rows[1]
        if len(row_date) > 6:
            date_str = str(row_date[6]).strip()
            if date_str and date_str.count('.') >= 2:
                tashrif_data["sana"] = date_str

        # 3. Asosiy ma'lumotlarni qat'iy joylashuvdan olish
        for r_idx in range(4, 9):
            row = block_rows[r_idx]
            if len(row) > 6:
                label = str(row[5]).strip().lower()
                value = str(row[6]).strip()

                if label and value:
                    if "ism" in label and r_idx == 4:
                        mijoz_data["ism_full"] = value
                    elif "модель" in label and r_idx == 5:
                        mijoz_data["model"] = value
                    elif "теку. км" in label and r_idx == 6:
                        tashrif_data["joriy_km"] = clean_km(value)
                    elif "след. км" in label and r_idx == 7:
                        tashrif_data["keyingi_km"] = clean_km(value.split('/')[0])
                        if '/' in value: tashrif_data["keyingi_sana"] = value.split('/')[-1].strip()
                    elif "номер" in label and r_idx == 8:
                        mijoz_data["raqam"] = value

        # 4. Xizmatlarni to'plash
        for r_idx in range(3, 10):
            if r_idx < len(block_rows):
                row = block_rows[r_idx]
                if len(row) > 2:
                    service_name = str(row[1]).strip()
                    service_detail = str(row[2]).strip()

                    if service_name != 'nan' or service_detail != 'nan':
                        if service_name or service_detail:
                            formatted_detail = service_detail if service_detail and service_detail != 'nan' else "N/A"
                            if service_name != 'nan' or formatted_detail != 'N/A':
                                service_name_clean = service_name.replace('nan', '').strip()
                                if service_name_clean or formatted_detail != 'N/A':
                                    tashrif_data["xizmatlar"].append(f"• {service_name_clean}: {formatted_detail}")

        # --- DBga kiritish mantiqi (O'zbekcha nomlar) ---

        if not mijoz_data["tel"] or not mijoz_data["raqam"]:
            logger.warning(f"Blok {i // ROWS_PER_CLIENT + 1}: Telefon/Raqam ma'lumotlari yo'q, o'tkazib yuborildi.")
            continue

        # 1. MIJOZ kiritish (yoki topish)
        name_parts = mijoz_data["ism_full"].split(maxsplit=1)
        ism = name_parts[0] if name_parts else ""
        familiya = name_parts[1] if len(name_parts) > 1 else ""

        try:
            cursor.execute("SELECT id FROM Mijoz WHERE telefon_raqami = ?", (mijoz_data["tel"],))
            mijoz_row = cursor.fetchone()
            if mijoz_row:
                mijoz_id = mijoz_row[0]
            else:
                cursor.execute("INSERT INTO Mijoz (telefon_raqami, ism, familiya) VALUES (?, ?, ?)",
                               (mijoz_data["tel"], ism, familiya))
                mijoz_id = cursor.lastrowid
                mijoz_soni += 1
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM Mijoz WHERE telefon_raqami = ?", (mijoz_data["tel"],))
            mijoz_id = cursor.fetchone()[0]

        # 2. AVTO kiritish (yoki topish)
        try:
            cursor.execute("SELECT id FROM Avto WHERE raqam = ?", (mijoz_data["raqam"],))
            avto_row = cursor.fetchone()
            if avto_row:
                avto_id = avto_row[0]
            else:
                cursor.execute("INSERT INTO Avto (mijoz_id, model, raqam) VALUES (?, ?, ?)",
                               (mijoz_id, mijoz_data["model"], mijoz_data["raqam"]))
                avto_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM Avto WHERE raqam = ?", (mijoz_data["raqam"],))
            avto_id = cursor.fetchone()[0]

        # 3. TASHRIF kiritish
        if avto_id and tashrif_data["sana"] and tashrif_data["joriy_km"] > 0:
            xizmatlar_text = "\n".join([s for s in tashrif_data["xizmatlar"] if s.strip()])
            cursor.execute("""
            INSERT INTO Tashrif (avto_id, sana, joriy_km, keyingi_km, keyingi_sana, xizmatlar) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                avto_id,
                tashrif_data["sana"],
                tashrif_data["joriy_km"],
                tashrif_data["keyingi_km"] if tashrif_data["keyingi_km"] > 0 else None,
                tashrif_data["keyingi_sana"] if tashrif_data["keyingi_sana"] else None,
                xizmatlar_text
            ))
            tashrif_soni += 1
        else:
            logger.warning(
                f"Blok {i // ROWS_PER_CLIENT + 1}: Tashrif ma'lumotlari (sana/km) yetarli emas, tashrif o'tkazib yuborildi.")

    conn.commit()
    conn.close()

    return (f"✅ **Ma'lumotlar muvaffaqiyatli migratsiya qilindi!**\n"
            f"Jami bloklar: **{total_blocks}**\n"
            f"Kiritildi: Mijozlar: **{mijoz_soni}** (Yangi), Tashriflar: **{tashrif_soni}**.")


# --- QIDIRUV VA TELEGRAM HANDLER FUNKSIYALARI (O'zbekcha nomlar) ---

def get_client_data_from_db(phone: str) -> str:
    """Toza jadvallardan mijozning to'liq ma'lumotlarini topadi va chiroyli formatlaydi."""
    phone_clean = clean_phone(phone)
    if not phone_clean or len(phone_clean) < 12:
        return "⚠️ Telefon raqamni aniqlab bo‘lmadi. Iltimos, **to‘liq 9 xonali** raqamni yoki **kontaktni** yuboring."

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Mijozni qidirish
        cursor.execute("SELECT id, ism, familiya FROM Mijoz WHERE telefon_raqami = ?", (phone_clean,))
        mijoz_row = cursor.fetchone()

        if not mijoz_row:
            partial_search = "%" + phone_clean[-9:]
            cursor.execute("SELECT id, ism, familiya FROM Mijoz WHERE telefon_raqami LIKE ?", (partial_search,))
            mijoz_row = cursor.fetchone()

        if not mijoz_row:
            return f"❌ Sizning raqamingiz (+{phone_clean}) bo‘yicha maʼlumot topilmadi."

        mijoz_id, ism, familiya = mijoz_row
        full_name = f"{ism} {familiya}".strip() if familiya else ism

        # Avtomobillarni topish
        cursor.execute("SELECT id, model, raqam FROM Avto WHERE mijoz_id = ?", (mijoz_id,))
        avtolar = cursor.fetchall()

        if not avtolar:
            return (f"👤 *Mijoz:* `{full_name}`\n📞 *Telefon:* `+{phone_clean}`\n\n"
                    f"⚠️ _Bu mijoz uchun avtomobil ma'lumotlari topilmadi._")

        all_avto_data = []
        for avto_id, model, raqam in avtolar:
            cursor.execute("""
            SELECT sana, joriy_km, keyingi_km, keyingi_sana, xizmatlar
            FROM Tashrif WHERE avto_id = ? ORDER BY sana DESC
            """, (avto_id,))
            tashriflar = cursor.fetchall()

            tashriflar_formatted = []
            for index, tashrif in enumerate(tashriflar):
                sana, joriy_km, keyingi_km, keyingi_sana, xizmatlar = tashrif

                keyingi_xizmat_info = []
                if keyingi_km: keyingi_xizmat_info.append(f"Km: `{keyingi_km:,}`".replace(",", " "))
                if keyingi_sana and keyingi_sana != 'None': keyingi_xizmat_info.append(f"Muddat: `{keyingi_sana}`")
                keyingi_xizmat_text = " / ".join(keyingi_xizmat_info) if keyingi_xizmat_info else "Noma'lum"

                tashrif_block = [
                    f"  ━━━━━━━━━━",
                    f"  ➡️ *Tashrif ({len(tashriflar) - index}):* `{sana}`",
                    f"   odometer *Joriy Km:* `{joriy_km:,}`".replace(",", " "),
                    f"  🗓️ *Keyingi xizmat:* {keyingi_xizmat_text}",
                    f"  🛠️ *Xizmatlar:*",
                    f"{xizmatlar}",
                ]
                tashriflar_formatted.extend(tashrif_block)

            avto_block = [
                f"\n\n🚗 *Avtomobil:* `{model}`",
                f"🏷️ *Raqam:* `{raqam}`",
                f"━━━━━━━━━━━━━━━━━━"
            ]
            avto_block.extend(tashriflar_formatted)
            all_avto_data.extend(avto_block)

        main_info_formatted = [
            f"👤 *Ism/Familiya:* `{full_name}`",
            f"📞 *Telefon:* `+{phone_clean}`",
        ]
        formatted_output = [
            f"🚗 *MIJOZNING TO'LIQ TA'RIXI ({len(avtolar)} ta avtomobil)*",
            f"━━━━━━━━━━━━━━━━━━",
            "\n".join(main_info_formatted),
        ]
        formatted_output.extend(all_avto_data)
        formatted_output.append("\n---")
        formatted_output.append(f"🔍 _Qidiruv raqami: +{phone_clean}_")

        return "\n".join(formatted_output)

    except sqlite3.Error as e:
        logger.error(f"DB so'rovida xatolik: {e}")
        return "⚠️ **Bazaga ulanishda ichki xatolik yuz berdi.**"
    finally:
        if conn: conn.close()


# --- Telegram Handler funksiyalari (O'zgarishsiz) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    button = KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
    text = (f"👋 Salom, {user.first_name or 'mijoz'}!\n\n"
            "Bu bot orqali siz moy almashtirish tarixi va xizmat tafsilotlarini ko‘rishingiz mumkin.\n\n"
            "📲 Quyidagi tugma orqali raqamingizni yuboring yoki qo‘lda yozing (Masalan: 90 123-45-67):")
    await update.message.reply_text(text, reply_markup=keyboard)


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number
    await update.message.reply_text("🔍 Ma’lumotlar tekshirilmoqda...")
    result = get_client_data_from_db(phone)
    await update.message.reply_text(result, parse_mode="Markdown")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not any(ch.isdigit() for ch in text):
        await update.message.reply_text("⚠️ Iltimos, telefon raqamni yozing yoki kontaktni yuboring.")
        return

    await update.message.reply_text("🔍 Ma’lumotlar tekshirilmoqda...")
    result = get_client_data_from_db(text)
    await update.message.reply_text(result, parse_mode="Markdown")


async def migrate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun ma'lumotlarni Exceldan DBga migratsiya qilish buyrug'i."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bu buyruq faqat administratorlar uchun.")
        return

    await update.message.reply_text("⏳ Ma'lumotlar Exceldan DBga o'tkazilmoqda (normalizatsiya)...")
    result_message = migrate_excel_to_db()
    await update.message.reply_text(result_message, parse_mode="Markdown")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Xatolik yuz berdi:", exc_info=context.error)
    if ADMIN_ID:
        try:
            error_message = f"⚠️ **Botda xatolik!**\n\n**Xato turi:** `{type(context.error).__name__}`\n\n**Xabar:** {context.error}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=error_message, parse_mode="Markdown")
        except Exception:
            pass


def main():
    logger.info("🤖 'Class Oil' bot ishga tushmoqda...")
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("migrate", migrate_handler, filters=filters.User(user_id=ADMIN_ID)))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)
    logger.info("✅ Bot ishga tushdi. Telegram’da /start yuboring.")
    app.run_polling()


if __name__ == "__main__":
    main()