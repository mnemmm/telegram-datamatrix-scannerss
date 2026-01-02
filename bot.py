import sqlite3, json, re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

DB_FILE = "scans.db"
PHONE_RE = re.compile(r"^\+?\d{10,15}$")
ADMIN_KEY = "89139991122a"

# ---------------- база ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dm_code TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn

conn = init_db()

def code_exists(code): 
    return conn.execute("SELECT 1 FROM scans WHERE dm_code=? LIMIT 1", (code,)).fetchone() is not None

def save_scan(code, phone):
    conn.execute("INSERT INTO scans(dm_code, phone) VALUES (?,?)", (code, phone))
    conn.commit()

def delete_code(code):
    conn.execute("DELETE FROM scans WHERE dm_code=?", (code,))
    conn.commit()

# ---------------- команды ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Сканировать код", web_app=WebAppInfo(url="https://github.com/mnemmm/telegram-datamatrix-scannerss.git"))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нажмите кнопку для сканирования:", reply_markup=reply_markup)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.web_app_data.data)
    code = data['code']
    phone = data['phone']

    if code_exists(code):
        await update.message.reply_text("Этот код уже есть в базе")
        return

    if not PHONE_RE.fullmatch(phone):
        await update.message.reply_text("Неверный формат телефона")
        return

    save_scan(code, phone)
    await update.message.reply_text(f"Успешно сохранено!\nКод: {code}\nТелефон: {phone}")

# ---------------- админ ----------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or args[0] != ADMIN_KEY:
        await update.message.reply_text("Неверный ключ")
        return
    rows = conn.execute("SELECT dm_code, phone, ts FROM scans ORDER BY ts DESC").fetchall()
    msg = "\n".join([f"{r[0]} | {r[1]} | {r[2]}" for r in rows])
    await update.message.reply_text(msg or "Нет данных")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /delete <код>")
        return
    code = context.args[0]
    delete_code(code)
    await update.message.reply_text(f"Код {code} удален из базы")

# ---------------- запуск ----------------
app = ApplicationBuilder().token("7986246299:AAFbFdbB2P3_J6xEdxG9u1GHwOypzTL4PR4").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("delete", delete))

print("Бот запущен...")
app.run_polling()
