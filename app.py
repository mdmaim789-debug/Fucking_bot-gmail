import logging
import sqlite3
import random
import string
import time
import asyncio
import imaplib
import os
import json
from datetime import datetime, timedelta

# Aiogram imports
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Flask imports
from flask import Flask, request

# ==========================================
# CONFIGURATION
# ==========================================
API_TOKEN = os.getenv('API_TOKEN', '8492580532:AAF-h9q-344C3dYuV15cVzsaVF_WUWU4DZo')

# Parse ADMIN_IDS from environment
try:
    ADMIN_IDS = json.loads(os.getenv('ADMIN_IDS', '[6375918223, ]'))
except:
    ADMIN_IDS = [6375918223, 6337650436]

LOG_CHANNEL_ID = -1003676517448

# Rates
DEFAULT_EARN_REFERRAL = 5.0
DEFAULT_EARN_GMAIL = 10.0
DEFAULT_VIP_BONUS = 2.0
DEFAULT_MIN_WITHDRAW = 100.0
DEFAULT_VIP_MIN_WITHDRAW = 50.0
DEFAULT_EARN_MAIL_SELL = 10.0

# Fake User System
FAKE_USER_ENABLED = os.getenv('FAKE_USER_ENABLED', 'True') == 'True'
FAKE_USER_RATIO = float(os.getenv('FAKE_USER_RATIO', '0.3'))
MIN_FAKE_USERS = int(os.getenv('MIN_FAKE_USERS', '100'))
MAX_FAKE_USERS = int(os.getenv('MAX_FAKE_USERS', '500'))
FAKE_USER_ID_START = 9000000000

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# Flask App for Render
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Maim Gmail Bot is running on Render!"

@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==========================================
# DATABASE SETUP
# ==========================================
def get_db_path():
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, 'gmailfarmer_pro.db')

DB_FILE = get_db_path()

def get_db_connection():
    return sqlite3.connect(DB_FILE, timeout=10)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        status TEXT DEFAULT 'new',
        account_index INTEGER DEFAULT 0,
        balance REAL DEFAULT 0,
        referral_count INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT 0,
        referral_paid INTEGER DEFAULT 0, 
        current_email TEXT,
        current_password TEXT,
        screenshot_file_id TEXT,
        join_date TEXT,
        banned INTEGER DEFAULT 0,
        is_vip INTEGER DEFAULT 0,
        rejected_verification_count INTEGER DEFAULT 0,
        auto_block_reason TEXT,
        last_bonus_time TEXT,
        mail_sell_earnings REAL DEFAULT 0,
        total_withdrawn REAL DEFAULT 0,
        last_withdraw_time TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        admin_id INTEGER,
        message TEXT,
        reply TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'open'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        payment_method TEXT,
        mobile_number TEXT,
        status TEXT,
        request_time TEXT,
        processed_time TEXT,
        transaction_id TEXT,
        api_response TEXT,
        retry_count INTEGER DEFAULT 0,
        last_retry_time TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sold_mails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_user_id INTEGER,
        seller_username TEXT,
        gmail_address TEXT,
        gmail_password TEXT,
        recovery_email TEXT,
        status TEXT DEFAULT 'pending',
        admin_id INTEGER,
        admin_note TEXT,
        created_at TEXT,
        approved_at TEXT,
        amount REAL DEFAULT 0,
        auto_verified INTEGER DEFAULT 0
    )''')
    
    # Default Settings
    defaults = {
        'earn_referral': str(DEFAULT_EARN_REFERRAL),
        'earn_gmail': str(DEFAULT_EARN_GMAIL),
        'vip_bonus': str(DEFAULT_VIP_BONUS),
        'min_withdraw': str(DEFAULT_MIN_WITHDRAW),
        'vip_min_withdraw': str(DEFAULT_VIP_MIN_WITHDRAW),
        'withdrawals_enabled': '1',
        'notice': 'Welcome to Gmail Buy Sell! Start Earning today.',
        'earn_mail_sell': str(DEFAULT_EARN_MAIL_SELL)
    }
    
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# BOT INITIALIZATION
# ==========================================
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_setting(key):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def update_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def generate_demo_creds():
    digits = ''.join(random.choices(string.digits, k=4))
    char = random.choice(string.ascii_lowercase)
    email = f"maim{digits}{char}@gmail.com"
    pool = string.ascii_letters + string.digits
    rand_part = ''.join(random.choices(pool, k=8))
    password = f"Maim@{rand_part}"
    return email, password

def check_ban(user_id):
    u = get_user(user_id)
    if u and u[12] == 1: 
        return True
    return False

def is_user_in_top10(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user_id FROM users 
        WHERE banned = 0 
        ORDER BY balance DESC 
        LIMIT 10
    """)
    top_users = [row[0] for row in c.fetchall()]
    conn.close()
    return user_id in top_users

async def verify_gmail_login(email, password):
    try:
        server = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
        server.login(email, password)
        server.logout()
        return True, "Login Successful"
    except imaplib.IMAP4.error as e:
        err_msg = str(e)
        if "AUTHENTICATIONFAILED" in err_msg or "credential" in err_msg.lower():
            return False, "❌ Wrong Password or Email not created yet."
        elif "Application-specific password" in err_msg:
            return True, "Verified (2FA Alert)" 
        else:
            return False, f"⚠️ Google Security Block: {err_msg}"
    except Exception as e:
        return False, f"⚠️ Connection Error: {str(e)}"

# ==========================================
# FAKE USER SYSTEM
# ==========================================
def initialize_fake_users():
    if not FAKE_USER_ENABLED:
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE user_id < ?", (FAKE_USER_ID_START,))
    real_count = c.fetchone()[0]
    
    target_fake = max(MIN_FAKE_USERS, int(real_count * FAKE_USER_RATIO))
    target_fake = min(target_fake, MAX_FAKE_USERS)
    
    if fake_count < target_fake:
        to_add = target_fake - fake_count
        print(f"🤖 Adding {to_add} fake users...")
        
        for i in range(to_add):
            try:
                fake_id = FAKE_USER_ID_START + random.randint(100000, 9999999)
                
                c.execute("SELECT user_id FROM users WHERE user_id=?", (fake_id,))
                if c.fetchone():
                    continue
                
                fake_name = random.choice(["Rahim", "Karim", "Sakib", "Mim", "Joya", "Rifat", "Tania", "Fahim"])
                fake_number = random.randint(100, 9999)
                username = f"{fake_name.lower()}{fake_number}"
                
                balance = round(random.uniform(50, 2000), 2)
                verified = random.randint(1, 15)
                referrals = random.randint(0, 8)
                
                days_ago = random.randint(1, 60)
                join_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                hours_ago = random.randint(0, 48)
                last_active = (datetime.now() - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                c.execute('''INSERT INTO users 
                    (user_id, username, status, account_index, balance, referral_count, 
                     join_date, last_bonus_time, is_vip) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (fake_id, username, 'verified', verified, balance, referrals, 
                     join_date, last_active, 1 if balance > 1000 else 0))
                
            except Exception as e:
                print(f"Error adding fake user: {e}")
                continue
        
        conn.commit()
        print(f"✅ Added fake users. Total fake: {c.rowcount}")
    
    conn.close()

async def get_smart_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users WHERE user_id < ? AND banned=0", (FAKE_USER_ID_START,))
    real_users = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_users = c.fetchone()[0] or 0
    
    total_shown = real_users + fake_users
    
    if real_users > 10:
        growth_rate = random.randint(3, 10)
    else:
        growth_rate = random.randint(15, 30)
    
    conn.close()
    
    return {
        'total_users': total_shown,
        'active_today': random.randint(int(total_shown * 0.1), int(total_shown * 0.3)),
        'real_users': real_users,
        'fake_users': fake_users,
        'growth_rate': growth_rate
    }

# ==========================================
# STATES
# ==========================================
class RegisterState(StatesGroup):
    waiting_for_screenshot = State()
    
class WithdrawState(StatesGroup):
    waiting_for_method = State()
    waiting_for_number = State()
    waiting_for_amount = State()

class AdminSettings(StatesGroup):
    waiting_for_value = State()

class AdminBroadcast(StatesGroup):
    waiting_for_message = State()

class AdminBanSystem(StatesGroup):
    waiting_for_id = State()

class AdminNotice(StatesGroup):
    waiting_for_text = State()

class SupportState(StatesGroup):
    waiting_for_message = State()

class MailSellState(StatesGroup):
    waiting_for_gmail = State()
    waiting_for_password = State()
    waiting_for_recovery = State()
    verifying_credentials = State()

# ==========================================
# COMMAND HANDLERS
# ==========================================
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if res and res[0] == 1:
        conn.close()
        await message.answer("❌ You are banned.")
        return

    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        referrer = 0
        args = message.get_args()
        if args and args.isdigit():
            try:
                referrer = int(args)
                if referrer == user_id:
                    referrer = 0
                c.execute("SELECT user_id FROM users WHERE user_id=?", (referrer,))
                if not c.fetchone():
                    referrer = 0
            except:
                referrer = 0
        
        email, password = generate_demo_creds()
        c.execute('''INSERT INTO users 
            (user_id, username, join_date, referrer_id, current_email, current_password) 
            VALUES (?, ?, ?, ?, ?, ?)''', 
            (user_id, message.from_user.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
             referrer, email, password))
        conn.commit()
        
        if referrer != 0:
            ref_rate = float(get_setting('earn_referral'))
            c.execute("UPDATE users SET balance=balance+?, referral_count=referral_count+1 WHERE user_id=?", 
                     (ref_rate, referrer))
            conn.commit()
            try:
                await bot.send_message(referrer, f"🎉 **New Referral!**\n+{ref_rate} TK earned!\nTotal Referred: Check 'My Referral'")
            except:
                pass
    
    conn.close()
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("1️⃣ Start Work", "2️⃣ My Account")
    kb.add("🎁 Daily Bonus", "🏆 Leaderboard")
    kb.add("💸 Withdraw", "📢 Notice")
    kb.add("4️⃣ My Referral", "📞 Support")
    kb.add("📧 Mail Sell", "👑 VIP")
    kb.add("ℹ️ Help", "🔙 Main Menu")
    
    await message.answer(
        f"👋 **Welcome to Gmail Buy Sell!**\n\nEarn money by creating verified Gmail accounts.\n\n👇 Select an option:", 
        parse_mode="Markdown", 
        reply_markup=kb
    )

@dp.message_handler(lambda message: message.text == "👑 VIP", state="*")
async def vip_info(message: types.Message):
    if check_ban(message.from_user.id): return
    
    vip_bonus = get_setting('vip_bonus') or DEFAULT_VIP_BONUS
    
    msg = (
        f"👑 **VIP Bonus System**\n\n"
        f"📈 **Top-10 users** (by balance) earn an extra **{vip_bonus} TK** per verified Gmail!\n\n"
        f"💰 **Current VIP Bonus:** {vip_bonus} TK\n\n"
        f"🏆 Check **'Leaderboard'** to see the current Top-10 rankings.\n"
        f"💡 The bonus is automatically added when your account is verified.\n\n"
        f"⚡ **Stay active and climb the ranks to become VIP!**"
    )
    
    await message.answer(msg, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "📧 Mail Sell", state="*")
async def mail_sell_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if check_ban(user_id): return
    
    user = get_user(user_id)
    if not user or user[3] < 1:
        await message.answer(
            "❌ **You need at least 1 verified Gmail account to sell mails!**\n\n"
            "💡 Complete 'Start Work' tasks first to verify accounts."
        )
        return
    
    await MailSellState.waiting_for_gmail.set()
    await message.answer(
        "📧 **Mail Sell System**\n\n"
        "Enter Gmail address:\n"
        "Example: `maim1234@gmail.com` or just `maim1234`\n\n"
        "⚠️ **IMPORTANT:** Only submit REAL working Gmails!",
        parse_mode="Markdown"
    )

@dp.message_handler(state=MailSellState.waiting_for_gmail)
async def process_gmail_address(message: types.Message, state: FSMContext):
    gmail_address = message.text.strip().lower()
    
    if '@' in gmail_address:
        if not gmail_address.endswith('@gmail.com'):
            await message.answer("❌ Only @gmail.com addresses accepted!")
            return
    else:
        gmail_address = f"{gmail_address}@gmail.com"
    
    if len(gmail_address.split('@')[0]) < 4:
        await message.answer("❌ Gmail username too short!")
        return
    
    await state.update_data(gmail_address=gmail_address)
    await MailSellState.waiting_for_password.set()
    
    await message.answer(
        "🔑 **Enter Password:**\n"
        "Enter the EXACT password for this Gmail.\n\n"
        "⚠️ **BOT WILL VERIFY!**\n"
        "Fake credentials will be rejected.",
        parse_mode="Markdown"
    )

@dp.message_handler(state=MailSellState.waiting_for_password)
async def process_gmail_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    
    if len(password) < 6:
        await message.answer("❌ Password must be at least 6 characters!")
        return
    
    await state.update_data(password=password)
    
    data = await state.get_data()
    gmail_address = data['gmail_address']
    
    await MailSellState.verifying_credentials.set()
    
    verification_msg = await message.answer(
        f"🔍 **Verifying Gmail Credentials...**\n"
        f"⏳ Please wait 10-15 seconds...\n\n"
        f"📧 Checking: `{gmail_address}`",
        parse_mode="Markdown"
    )
    
    # Auto verification
    is_valid, msg = await verify_gmail_login(gmail_address, password)
    
    if not is_valid:
        await verification_msg.edit_text(
            f"❌ **VERIFICATION FAILED!**\n\n"
            f"📧 `{gmail_address}`\n\n"
            f"**Reason:** {msg}\n\n"
            f"⚠️ **Warning:** Fake/wrong credentials detected!"
        )
        await state.finish()
        return
    
    await verification_msg.edit_text(
        f"✅ **GMAIL VERIFIED!**\n\n"
        f"📧 `{gmail_address}`\n"
        f"🔑 Password: Verified ✅\n\n"
        f"Now enter recovery email (optional):"
    )
    
    await MailSellState.waiting_for_recovery.set()

@dp.message_handler(state=MailSellState.waiting_for_recovery)
async def process_recovery_email(message: types.Message, state: FSMContext):
    recovery_email = message.text.strip().lower()
    
    if recovery_email in ['/skip', 'skip', 'none', 'no']:
        recovery_email = ""
    elif recovery_email and '@' not in recovery_email:
        await message.answer("❌ Invalid email format for recovery!")
        return
    
    data = await state.get_data()
    gmail_address = data['gmail_address']
    password = data['password']
    user_id = message.from_user.id
    user = get_user(user_id)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''INSERT INTO sold_mails 
        (seller_user_id, seller_username, gmail_address, gmail_password, recovery_email, status, created_at, admin_note, auto_verified) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, user[1], gmail_address, password, recovery_email, 'verified', 
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Auto-verified by bot", 1))
    
    mail_id = c.lastrowid
    
    mail_sell_rate = float(get_setting('earn_mail_sell') or DEFAULT_EARN_MAIL_SELL)
    
    c.execute("UPDATE users SET balance=balance+?, mail_sell_earnings=mail_sell_earnings+? WHERE user_id=?",
              (mail_sell_rate, mail_sell_rate, user_id))
    
    conn.commit()
    conn.close()
    
    await state.finish()
    
    success_msg = (
        f"🎉 **MAIL SALE COMPLETED!**\n\n"
        f"📧 **Gmail:** `{gmail_address}`\n"
        f"✅ **Status:** Auto-Verified & Approved\n"
        f"💰 **Earned:** {mail_sell_rate} TK\n\n"
        f"💳 **Added to your balance automatically!**\n"
        f"📈 Check 'My Account' for updated balance."
    )
    
    await message.answer(success_msg, parse_mode="Markdown")
    
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                f"📧 **Auto-Verified Mail Sale** #{mail_id}\n\n"
                f"👤 **Seller:** `{user_id}` (@{user[1] or 'No username'})\n"
                f"📧 **Gmail:** `{gmail_address}`\n"
                f"🔑 **Password:** `{password}`\n"
                f"📩 **Recovery:** `{recovery_email or 'None'}`\n"
                f"💰 **Paid:** {mail_sell_rate} TK\n"
                f"✅ **Status:** Auto-approved"
            )
            
            await bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
        except:
            pass

@dp.message_handler(lambda message: message.text == "4️⃣ My Referral", state="*")
async def referral_menu(message: types.Message):
    if check_ban(message.from_user.id): return
    user = get_user(message.from_user.id)
    if not user: return
    
    ref_count = user[5]
    ref_earnings = ref_count * float(get_setting('earn_referral'))
    
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    
    msg = (f"🔗 **My Referral**\n\n"
           f"📎 **Link:** `{ref_link}`\n\n"
           f"👥 **Total Referred:** {ref_count}\n"
           f"💰 **Total Earnings:** {ref_earnings:.2f} TK\n\n"
           f"💡 **Share your link and earn {get_setting('earn_referral')} TK per referral!**")
    
    await message.answer(msg, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "📞 Support", state="*")
async def support_start(message: types.Message, state: FSMContext):
    if check_ban(message.from_user.id): return
    await SupportState.waiting_for_message.set()
    await message.answer("💬 **Support Ticket**\n\nPlease describe your issue:", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=SupportState.waiting_for_message)
async def support_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        await message.answer("❌ User not found.")
        await state.finish()
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO support_tickets (user_id, message, created_at) VALUES (?, ?, ?)",
             (user_id, message.text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    ticket_id = c.lastrowid
    conn.close()
    
    for admin_id in ADMIN_IDS:
        try:
            caption = f"🎫 **New Ticket #{ticket_id}**\n\n👤 **User:** `{user_id}`\n🆔 **Username:** @{user[1] or 'No username'}\n💬 **Message:**\n\n{message.text}"
            kb = InlineKeyboardMarkup().add(
                InlineKeyboardButton("💬 Reply", callback_data=f"reply_ticket_{ticket_id}_{user_id}")
            )
            await bot.send_message(admin_id, caption, parse_mode="Markdown", reply_markup=kb)
        except:
            pass
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("1️⃣ Start Work", "2️⃣ My Account")
    kb.add("🎁 Daily Bonus", "🏆 Leaderboard")
    kb.add("💸 Withdraw", "📢 Notice")
    kb.add("4️⃣ My Referral", "📞 Support")
    kb.add("📧 Mail Sell", "👑 VIP")
    kb.add("ℹ️ Help", "🔙 Main Menu")

    await message.answer("✅ **Ticket Submitted!**\n⏳ Admins will reply soon.", reply_markup=kb)
    await state.finish()

@dp.message_handler(lambda message: message.text == "ℹ️ Help", state="*")
async def help_menu(message: types.Message):
    if check_ban(message.from_user.id): return
    
    help_text = """
📖 **How to Earn Money:**

1️⃣ **Click "Start Work"**
   • Get Email + Password
   • Create Gmail account EXACTLY as shown
   
2️⃣ **Create Account:**
   • Nikname: `Maim`
   • Email: Copy from bot
   • Password: Copy from bot
   
3️⃣ **Verify:**
   • Click "🔄 Check Login"
   • Bot auto-checks login
   
4️⃣ **Get Paid:**
   • ✅ 10 TK per verified account
   • 🎁 Daily bonus
   • 👥 Referral bonus
   • 👑 VIP bonus for Top-10 users
   • 📧 Earn from selling verified emails

💰 **Minimum Withdraw:** 100 TK
📧 **Mail Sell:** Submit your verified Gmails for extra income

🤖 **Bot Created By:** XTﾠMꫝɪᴍﾠ!!
📞 **Contact:** @cr_maim
"""
    await message.answer(help_text, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "🔙 Main Menu", state="*")
async def refresh_menu(message: types.Message):
    await cmd_start(message)

@dp.message_handler(lambda message: message.text == "🎁 Daily Bonus", state="*")
async def daily_bonus(message: types.Message):
    user_id = message.from_user.id
    if check_ban(user_id): return
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT balance, last_bonus_time FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row: 
        conn.close()
        return

    balance, last_time_str = row
    current_time = datetime.now()
    bonus_amt = 1.0
    
    can_claim = False
    if last_time_str is None:
        can_claim = True
    else:
        try:
            last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
            diff = (current_time - last_time).total_seconds()
            if diff >= 86400: 
                can_claim = True
            else:
                rem = 86400 - diff
                hrs, mins = int(rem // 3600), int((rem % 3600) // 60)
                await message.answer(f"⏳ **Cooldown!**\nCome back in: {hrs}h {mins}m")
                conn.close()
                return
        except:
            can_claim = True

    if can_claim:
        c.execute("UPDATE users SET balance=balance+?, last_bonus_time=? WHERE user_id=?", 
                 (bonus_amt, current_time.strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
        await message.answer(f"🎉 **Bonus Claimed!**\n+{bonus_amt} TK\n💰 New Balance: {balance + bonus_amt:.2f} TK")
    conn.close()

@dp.message_handler(lambda message: message.text == "🏆 Leaderboard", state="*")
async def smart_leaderboard(message: types.Message):
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT username, balance, referral_count, 
               CASE WHEN user_id >= ? THEN 1 ELSE 0 END as is_fake
        FROM users 
        WHERE banned=0 
        ORDER BY balance DESC 
        LIMIT 20
    """, (FAKE_USER_ID_START,))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("No data available yet!")
        return
    
    if len(rows) < 10 or rows[0][1] < 5000:
        impressive_fakes = [
            ("👑 ProFarmerX", 15800.50, 92, 1),
            ("💎 DiamondTrader", 12900.75, 78, 1),
            ("🚀 RocketEarnPro", 11200.25, 65, 1),
            ("💰 CashMasterBD", 9800.00, 54, 1),
            ("⭐ StarGmailer", 8450.30, 48, 1)
        ]
        rows = list(impressive_fakes) + list(rows)[:15]
    
    msg = "🏆 **TOP EARNERS LEADERBOARD** 🏆\n\n"
    
    for idx, (name, bal, refs, is_fake) in enumerate(rows[:15], 1):
        medal = "🥇" if idx==1 else ("🥈" if idx==2 else ("🥉" if idx==3 else f"{idx}."))
        display_name = (name or f"User{idx}")[:12]
        msg += f"{medal} **{display_name}** - ৳{bal:,.0f} ({refs} refs)\n"
        
        if idx == 1:
            msg += "   ⭐ **TOP EARNER OF THE MONTH** ⭐\n"
    
    total_ranked = len(rows)
    msg += f"\n📊 **Total Ranked:** {total_ranked:,} users"
    
    user_id = message.from_user.id
    if user_id < FAKE_USER_ID_START:
        user_rank = random.randint(50, 200) if random.random() > 0.3 else random.randint(10, 49)
        msg += f"\n🎯 **Your Rank:** Top {user_rank}"
    
    msg += "\n\n💡 **Tip:** Reach top 10 for VIP bonus!"
    
    await message.answer(msg, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "2️⃣ My Account", state="*")
async def menu_account(message: types.Message):
    if check_ban(message.from_user.id): return
    user = get_user(message.from_user.id)
    if not user: return
    
    verified_count = user[3]
    rank = "🐣 Noob"
    if verified_count >= 10: rank = "🚜 Pro Farmer"
    if verified_count >= 50: rank = "👑 Legend"
    
    ref_earnings = user[5] * float(get_setting('earn_referral'))
    mail_sell_earnings = user[17] or 0
    
    in_top10 = is_user_in_top10(user[0])
    vip_status = "👑 VIP (Top-10)" if in_top10 else "👤 Regular"
    
    msg = (f"👤 **My Profile**\n\n"
           f"🆔 ID: `{user[0]}`\n"
           f"🎖️ **Rank:** {rank}\n"
           f"⭐ **Status:** {vip_status}\n"
           f"💰 **Balance:** {user[4]:.2f} TK\n"
           f"📧 **Verified Accounts:** {verified_count}\n"
           f"👥 **Referrals:** {user[5]} (+{ref_earnings:.2f} TK)\n"
           f"📧 **Mail Sell Earnings:** {mail_sell_earnings:.2f} TK\n"
           f"📅 **Joined:** {str(user[11])[:10]}\n"
           f"💳 **Total Withdrawn:** {user[18] or 0:.2f} TK")
    await message.answer(msg, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "📢 Notice", state="*")
async def show_notice(message: types.Message):
    notice = get_setting('notice') or "No announcements."
    await message.answer(f"📢 **Latest News:**\n\n{notice}", parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "1️⃣ Start Work", state="*")
async def work_start(message: types.Message):
    user_id = message.from_user.id
    if check_ban(user_id): return
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT status, current_email, current_password FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    if not row:
        await cmd_start(message)
        conn.close()
        return

    status, email, password = row
    user = get_user(user_id)
    
    if status == 'verified':
        email, password = generate_demo_creds()
        c.execute("UPDATE users SET current_email=?, current_password=?, status='new' WHERE user_id=?", 
                 (email, password, user_id))
        conn.commit()

    msg = (f"🛠 **Create Gmail Task #{user[3]+1}**\n\n"
           f"👤 **Nikname:** `Maim`\n"
           f"👤 **Per Gmail 9-13৳ \n"
           f"✉️ **Email:** `{email}`\n"
           f"🔑 **Password:** `{password}`\n\n"
           f"⚠️ **EXACT Instructions:**\n"
           f"• Create account with EXACT details above\n"
           f"• Use recovery email/phone if asked\n"
           f"• Click **Check Login** after creation")
           
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔄 Check Login (Auto)", callback_data="auto_check_login"))
    kb.add(InlineKeyboardButton("📸 Screenshot (Manual)", callback_data="submit_ss"))
    
    await message.answer(msg, parse_mode="Markdown", reply_markup=kb)
    conn.close()

@dp.callback_query_handler(lambda c: c.data == "auto_check_login", state="*")
async def process_auto_check(call: types.CallbackQuery):
    user_id = call.from_user.id
    await call.answer("🔄 Verifying login...", show_alert=False)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT current_email, current_password, status FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    if not row: 
        conn.close()
        return
    email, password, status = row
    
    if status == 'verified':
        await call.message.answer("✅ Already verified! Click Start Work for next.")
        conn.close()
        return

    is_valid, msg = await verify_gmail_login(email, password)
    
    if is_valid:
        base_rate = float(get_setting('earn_gmail'))
        ref_rate = float(get_setting('earn_referral'))
        
        total_earnings = base_rate
        vip_bonus = 0
        
        if is_user_in_top10(user_id):
            vip_bonus = float(get_setting('vip_bonus') or DEFAULT_VIP_BONUS)
            total_earnings += vip_bonus
        
        c.execute("UPDATE users SET status='verified', balance=balance+?, account_index=account_index+1 WHERE user_id=?", 
                 (total_earnings, user_id))
        
        c.execute("SELECT referrer_id, referral_paid FROM users WHERE user_id=?", (user_id,))
        ref_data = c.fetchone()
        if ref_data and ref_data[0] != 0 and ref_data[1] == 0:
            c.execute("UPDATE users SET balance=balance+?, referral_count=referral_count+1 WHERE user_id=?", 
                     (ref_rate, ref_data[0]))
            c.execute("UPDATE users SET referral_paid=1 WHERE user_id=?", (user_id,))
        
        conn.commit()
        await call.message.delete()
        
        success_msg = f"✅ **SUCCESS!** 🎉\n\n✅ Login Verified\n💰 **+{base_rate} TK**"
        
        if vip_bonus > 0:
            success_msg += f"\n👑 **VIP Bonus:** +{vip_bonus} TK"
        
        success_msg += f"\n\n💰 **Total Earned:** {total_earnings} TK\n\n👆 Click **Start Work** for next task!"
        
        await call.message.answer(success_msg, parse_mode="Markdown")
        
        if LOG_CHANNEL_ID:
            try: 
                log_msg = f"🤖 **Auto-Verified**\n👤 User: `{user_id}`\n📧 {email}\n💰 Earned: {total_earnings} TK"
                if vip_bonus > 0:
                    log_msg += f" (VIP Bonus: {vip_bonus} TK)"
                await bot.send_message(LOG_CHANNEL_ID, log_msg)
            except: pass
            
    else:
        await call.message.answer(f"❌ **Failed**\n\n{msg}\n\n💡 Create account first, then try again.")
        
    conn.close()

@dp.callback_query_handler(lambda c: c.data == "submit_ss", state="*")
async def process_submit_ss(call: types.CallbackQuery):
    await RegisterState.waiting_for_screenshot.set()
    await call.message.answer("📸 Upload screenshot of Gmail inbox/welcome page:")

@dp.message_handler(content_types=['photo'], state=RegisterState.waiting_for_screenshot)
async def process_photo_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.photo:
        await message.answer("❌ Please upload a photo.")
        return

    photo_id = message.photo[-1].file_id
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT current_email, current_password FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    email, password = row if row else ("Unknown", "Unknown")
    
    c.execute("UPDATE users SET screenshot_file_id=?, status='pending' WHERE user_id=?", (photo_id, user_id))
    conn.commit()
    conn.close()

    if LOG_CHANNEL_ID:
        caption = f"📄 **Manual Review**\n👤 User: `{user_id}`\n📧 `{email}`\n🔑 `{password}`"
        try: 
            await bot.send_photo(LOG_CHANNEL_ID, photo_id, caption=caption, parse_mode="Markdown")
        except: pass

    await state.finish()
    await message.answer("⏳ ✅ Submitted for Admin Review!\n⏳ Wait for approval...")

@dp.message_handler(lambda message: message.text == "💸 Withdraw", state="*")
async def withdraw_start(message: types.Message):
    user_id = message.from_user.id
    if check_ban(user_id): return
    if get_setting('withdrawals_enabled') != '1':
        await message.answer("⚠️ Withdrawals temporarily disabled.")
        return
        
    user = get_user(user_id)
    if not user: return

    min_w = float(get_setting('vip_min_withdraw') if user[13] else get_setting('min_withdraw'))
    
    if user[4] < min_w:
        await message.answer(f"❌ **Low Balance**\n💰 Need: {min_w} TK\n💳 Current: {user[4]:.2f} TK")
        return
    
    msg = (f"💳 **Withdraw Funds**\n\n"
           f"💰 **Balance:** {user[4]:.2f} TK\n"
           f"⏱️ **Processing:** 24 hours\n\n"
           f"💡 **Minimum:** {min_w} TK")
    
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    kb.add("Bkash", "Nagad")
    kb.add("Rocket", "❌ Cancel")
    await WithdrawState.waiting_for_method.set()
    await message.answer(msg, reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(state=WithdrawState.waiting_for_method)
async def withdraw_method(message: types.Message, state: FSMContext):
    if message.text == "❌ Cancel":
        await state.finish()
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add("1️⃣ Start Work", "2️⃣ My Account")
        kb.add("💸 Withdraw", "4️⃣ My Referral")
        kb.add("🔙 Main Menu")
        await message.answer("Cancelled.", reply_markup=kb)
        return
    
    await state.update_data(method=message.text)
    await WithdrawState.waiting_for_number.set()
    await message.answer("📱 **Enter Mobile Number:**\n`01XXXXXXXXX`", parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=WithdrawState.waiting_for_number)
async def withdraw_number(message: types.Message, state: FSMContext):
    await state.update_data(number=message.text)
    await WithdrawState.waiting_for_amount.set()
    await message.answer("💰 **Enter Amount:**\n💡 Min: 100 TK")

@dp.message_handler(state=WithdrawState.waiting_for_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        user = get_user(message.from_user.id)
        
        if amount > user[4]:
            await message.answer("❌ **Insufficient Balance**")
            return
        
        data = await state.get_data()
        
        # Save withdrawal request
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO withdrawals 
            (user_id, amount, payment_method, mobile_number, status, request_time) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.from_user.id, 
            amount, 
            data['method'], 
            data['number'], 
            'pending',
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
        
        await state.finish()
        
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add("1️⃣ Start Work", "2️⃣ My Account")
        kb.add("💸 Withdraw", "4️⃣ My Referral")
        kb.add("🔙 Main Menu")
        
        await message.answer("✅ **Withdrawal Request Submitted!**\n⏳ Processing within 24 hours.", reply_markup=kb, parse_mode="Markdown")
        
        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, 
                    f"💸 **New Withdrawal**\n"
                    f"👤 `{message.from_user.id}`\n"
                    f"💰 `{amount}` {data['method']}\n"
                    f"📱 `{data['number']}`")
            except: pass
            
    except ValueError:
        await message.answer("❌ **Invalid Amount**")
    except Exception as e:
        await message.answer(f"❌ **Error:** {str(e)}")

# ==========================================
# ADMIN PANEL
# ==========================================
@dp.message_handler(commands=['admin'], state="*")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📥 Manual Reviews", callback_data="admin_verifications"),
           InlineKeyboardButton("💸 Payouts", callback_data="admin_payments"))
    kb.add(InlineKeyboardButton("📂 Export Emails", callback_data="admin_export"),
           InlineKeyboardButton("🎫 Support Tickets", callback_data="admin_tickets"))
    kb.add(InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_start"),
           InlineKeyboardButton("🚫 Ban System", callback_data="admin_ban_menu"))
    kb.add(InlineKeyboardButton("📈 Stats", callback_data="admin_stats"),
           InlineKeyboardButton("💰 Rates", callback_data="admin_earnings"))
    kb.add(InlineKeyboardButton("✏️ Notice", callback_data="admin_set_notice"),
           InlineKeyboardButton("📧 Mail Sales", callback_data="admin_mail_sales"))
    kb.add(InlineKeyboardButton("🤖 Fake System", callback_data="fake_system_control"))
    
    await message.answer("👮‍♂️ **Admin Control Panel**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "admin_stats", state="*")
async def admin_stats(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # User stats
    c.execute("SELECT COUNT(*), SUM(balance), SUM(referral_count) FROM users")
    res = c.fetchone()
    total_users, total_balance, total_refs = res if res else (0, 0, 0)
    
    c.execute("SELECT COUNT(*) FROM users WHERE status='verified'")
    res_ver = c.fetchone()
    verified = res_ver[0] if res_ver else 0
    
    # Fake user stats
    c.execute("SELECT COUNT(*) FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_count = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE user_id < ?", (FAKE_USER_ID_START,))
    real_count = c.fetchone()[0] or 0
    
    # Mail sales stats
    c.execute("SELECT COUNT(*), SUM(amount) FROM sold_mails WHERE status='verified'")
    mail_stats = c.fetchone()
    mail_sales = mail_stats[0] if mail_stats[0] else 0
    mail_earnings = mail_stats[1] if mail_stats[1] else 0
    
    # Withdrawal stats
    c.execute("SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status='paid'")
    withdrawal_stats = c.fetchone()
    total_withdrawals = withdrawal_stats[0] or 0
    total_paid = withdrawal_stats[1] or 0
    
    conn.close()
    
    stats = (f"📈 **Stats**\n"
             f"👥 Real Users: {real_count}\n"
             f"👻 Fake Users: {fake_count}\n"
             f"📊 Total Shown: {real_count + fake_count}\n"
             f"💰 Total Balance: {total_balance or 0:.2f} TK\n"
             f"✅ Verified Accounts: {verified}\n"
             f"🔗 Referrals: {total_refs or 0}\n"
             f"📧 Auto-Verified Mails: {mail_sales}\n"
             f"💵 Mail Sales Earnings: {mail_earnings:.2f} TK\n"
             f"💸 Total Withdrawals: {total_withdrawals}\n"
             f"💰 Total Paid Out: {total_paid:.2f} TK")
    
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
    await call.message.edit_text(stats, reply_markup=kb, parse_mode="Markdown")
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "fake_system_control", state="*")
async def fake_system_control(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Add Fake Users", callback_data="fake_add_100"),
        InlineKeyboardButton("📊 View Stats", callback_data="fake_stats")
    )
    kb.add(
        InlineKeyboardButton("❌ Remove All Fake", callback_data="fake_remove_all"),
        InlineKeyboardButton("🔙 Back", callback_data="admin_home")
    )
    
    stats = await get_smart_stats()
    
    control_msg = (
        f"🤖 **Fake User System Control**\n\n"
        f"✅ **Status:** {'ENABLED' if FAKE_USER_ENABLED else 'DISABLED'}\n"
        f"👥 **Real Users:** {stats['real_users']}\n"
        f"👻 **Fake Users:** {stats['fake_users']}\n"
        f"📊 **Total Shown:** {stats['total_users']:,}\n"
        f"📈 **Active Today:** {stats['active_today']:,}\n"
        f"🎯 **Fake Ratio:** {FAKE_USER_RATIO*100}%"
    )
    
    await call.message.edit_text(control_msg, reply_markup=kb, parse_mode="Markdown")
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('fake_'), state="*")
async def handle_fake_controls(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    if call.data == "fake_add_100":
        initialize_fake_users()
        await call.answer("✅ Fake users added!", show_alert=True)
        await fake_system_control(call)
    
    elif call.data == "fake_stats":
        stats = await get_smart_stats()
        stats_msg = (
            f"📈 **Fake Stats**\n\n"
            f"👥 Real: {stats['real_users']}\n"
            f"👻 Fake: {stats['fake_users']}\n"
            f"📊 Total: {stats['total_users']:,}\n"
            f"📈 Active: {stats['active_today']:,}\n"
            f"🚀 Growth: +{stats['growth_rate']}%"
        )
        await call.message.edit_text(stats_msg, parse_mode="Markdown")
    
    elif call.data == "fake_remove_all":
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        await call.answer(f"✅ Removed {deleted} fake users!", show_alert=True)
        await fake_system_control(call)

# ==========================================
# STARTUP FUNCTION
# ==========================================
async def on_startup(dp):
    """Initialize systems on bot start"""
    print("🚀 Starting Maim Gmail Bot...")
    
    # Initialize fake user system
    if FAKE_USER_ENABLED:
        initialize_fake_users()
        print("✅ Fake system initialized")
    else:
        print("❌ Fake system disabled")
    
    print("🤖 Bot is ready!")

# ==========================================
# MAIN EXECUTION
# ==========================================
def run_bot():
    """Run the bot in polling mode"""
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

def run_flask():
    """Run Flask app"""
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))

if __name__ == '__main__':
    import threading
    
    print("="*50)
    print("🤖 Maim Gmail Bot Starting...")
    print("🌐 Render Mode: YES")
    print("="*50)
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run bot in main thread
    try:
        run_bot()
    except KeyboardInterrupt:
        print("Bot stopped")
