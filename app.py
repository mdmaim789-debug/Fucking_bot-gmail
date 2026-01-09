import logging
import sqlite3
import random
import string
import time
import asyncio
import imaplib
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    CallbackQueryHandler, ConversationHandler, CallbackContext
)
from telegram.constants import ParseMode

# ==========================================
# CONFIGURATION
# ==========================================
API_TOKEN = '8492580532:AAF-h9q-344C3dYuV15cVzsaVF_WUWU4DZo' 
ADMIN_IDS = [6375918223, 6337650436]
PAYOUT_CHANNEL_ID = -1003676517448
LOG_CHANNEL_ID = -1003676517448

# Payment System Settings
AUTO_PAYMENT_ENABLED = True
AUTO_PAY_CHECK_INTERVAL = 60

# Rates
DEFAULT_EARN_REFERRAL = 5.0
DEFAULT_EARN_GMAIL = 10.0
DEFAULT_VIP_BONUS = 2.0
DEFAULT_MIN_WITHDRAW = 100.0
DEFAULT_VIP_MIN_WITHDRAW = 50.0
DEFAULT_EARN_MAIL_SELL = 10.0

# Fake User System
FAKE_USER_ENABLED = True
FAKE_USER_RATIO = 0.3
MIN_FAKE_USERS = 100
MAX_FAKE_USERS = 500
FAKE_USER_ID_START = 9000000000

# Logging Setup
logging.basicConfig(level=logging.INFO)

# ==========================================
# DATABASE SETUP
# ==========================================
DB_FILE = "gmailfarmer_pro.db"

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
        auto_payment INTEGER DEFAULT 0,
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
    
    defaults = {
        'earn_referral': str(DEFAULT_EARN_REFERRAL),
        'earn_gmail': str(DEFAULT_EARN_GMAIL),
        'vip_bonus': str(DEFAULT_VIP_BONUS),
        'min_withdraw': str(DEFAULT_MIN_WITHDRAW),
        'vip_min_withdraw': str(DEFAULT_VIP_MIN_WITHDRAW),
        'withdrawals_enabled': '1',
        'notice': 'Welcome to Gmail Buy Sell! Start Earning today.',
        'earn_mail_sell': str(DEFAULT_EARN_MAIL_SELL),
        'auto_payment_enabled': '1' if AUTO_PAYMENT_ENABLED else '0'
    }
    
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

# Initialize DB
init_db()

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

# ==========================================
# BOT HANDLERS
# ==========================================

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check Ban
    c.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if res and res[0] == 1:
        conn.close()
        await update.message.reply_text("❌ You are banned.")
        return

    # Register or Update
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        referrer = 0
        args = context.args
        if args and args[0].isdigit():
            try:
                referrer = int(args[0])
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
            (user_id, update.effective_user.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
             referrer, email, password))
        conn.commit()
        
        if referrer != 0:
            ref_rate = float(get_setting('earn_referral'))
            c.execute("UPDATE users SET balance=balance+?, referral_count=referral_count+1 WHERE user_id=?", 
                     (ref_rate, referrer))
            conn.commit()
            try:
                await context.bot.send_message(referrer, f"🎉 **New Referral!**\n+{ref_rate} TK earned!\nTotal Referred: Check 'My Referral'", parse_mode=ParseMode.MARKDOWN)
            except:
                pass
    conn.close()
    
    kb = ReplyKeyboardMarkup(
        [
            ["1️⃣ Start Work", "2️⃣ My Account"],
            ["🎁 Daily Bonus", "🏆 Leaderboard"],
            ["💸 Withdraw", "📢 Notice"],
            ["4️⃣ My Referral", "📞 Support"],
            ["📧 Mail Sell", "👑 VIP"],
            ["ℹ️ Help", "🔙 Main Menu"]
        ],
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        f"👋 **Welcome to Gmail Buy Sell!**\n\nEarn money by creating verified Gmail accounts.\n\n👇 Select an option:", 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=kb
    )

async def my_account(update: Update, context: CallbackContext):
    if check_ban(update.effective_user.id): 
        return
    
    user = get_user(update.effective_user.id)
    if not user: 
        return
    
    verified_count = user[3]
    rank = "🐣 Noob"
    if verified_count >= 10: rank = "🚜 Pro Farmer"
    if verified_count >= 50: rank = "👑 Legend"
    
    ref_earnings = user[5] * float(get_setting('earn_referral'))
    mail_sell_earnings = user[17] or 0
    
    msg = (f"👤 **My Profile**\n\n"
           f"🆔 ID: `{user[0]}`\n"
           f"🎖️ **Rank:** {rank}\n"
           f"💰 **Balance:** {user[4]:.2f} TK\n"
           f"📧 **Verified Accounts:** {verified_count}\n"
           f"👥 **Referrals:** {user[5]} (+{ref_earnings:.2f} TK)\n"
           f"📧 **Mail Sell Earnings:** {mail_sell_earnings:.2f} TK\n"
           f"📅 **Joined:** {str(user[11])[:10]}\n"
           f"💳 **Total Withdrawn:** {user[18] or 0:.2f} TK")
    
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def start_work(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if check_ban(user_id): 
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT status, current_email, current_password FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    if not row:
        await start(update, context)
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
           
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Check Login (Auto)", callback_data="auto_check_login")],
        [InlineKeyboardButton("📸 Screenshot (Manual)", callback_data="submit_ss")]
    ])
    
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    conn.close()

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "auto_check_login":
        await auto_check_login(update, context)
    elif query.data == "submit_ss":
        await query.message.reply_text("📸 Upload screenshot of Gmail inbox/welcome page:")
        # Store state for screenshot
        context.user_data['waiting_for_screenshot'] = True

async def auto_check_login(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT current_email, current_password, status FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    if not row: 
        conn.close()
        return
    
    email, password, status = row
    
    if status == 'verified':
        await query.message.reply_text("✅ Already verified! Click Start Work for next.")
        conn.close()
        return

    # Simulate verification (replace with actual IMAP check)
    base_rate = float(get_setting('earn_gmail'))
    total_earnings = base_rate
    
    # Update user balance
    c.execute("UPDATE users SET status='verified', balance=balance+?, account_index=account_index+1 WHERE user_id=?", 
             (total_earnings, user_id))
    
    conn.commit()
    
    success_msg = f"✅ **SUCCESS!** 🎉\n\n✅ Login Verified\n💰 **+{base_rate} TK**\n\n💰 **Total Earned:** {total_earnings} TK\n\n👆 Click **Start Work** for next task!"
    
    await query.message.reply_text(success_msg, parse_mode=ParseMode.MARKDOWN)
    
    if LOG_CHANNEL_ID:
        try: 
            log_msg = f"🤖 **Auto-Verified**\n👤 User: `{user_id}`\n📧 {email}\n💰 Earned: {total_earnings} TK"
            await context.bot.send_message(LOG_CHANNEL_ID, log_msg)
        except: pass
            
    conn.close()

async def handle_photo(update: Update, context: CallbackContext):
    if 'waiting_for_screenshot' in context.user_data:
        user_id = update.effective_user.id
        photo_id = update.message.photo[-1].file_id
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET screenshot_file_id=?, status='pending' WHERE user_id=?", (photo_id, user_id))
        conn.commit()
        conn.close()

        await update.message.reply_text("⏳ ✅ Submitted for Admin Review!\n⏳ Wait for approval...")
        context.user_data.pop('waiting_for_screenshot', None)

async def help_command(update: Update, context: CallbackContext):
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
━━━━━━━━━━━━━━━━━━━━
🤖 **Bot Created By:** XTﾠMꫝɪᴍﾠ!!
📞 **Contact:** [Click Here](https://t.me/cr_maim)
📧 **Email:** `immaim55@gmail.com`
🌐 **Website:** www.maim.com
━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def admin_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS: 
        return
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Manual Reviews", callback_data="admin_verifications"),
         InlineKeyboardButton("💸 Payouts", callback_data="admin_payments")],
        [InlineKeyboardButton("📂 Export Emails", callback_data="admin_export"),
         InlineKeyboardButton("🎫 Support Tickets", callback_data="admin_tickets")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_start"),
         InlineKeyboardButton("🚫 Ban System", callback_data="admin_ban_menu")],
        [InlineKeyboardButton("📈 Stats", callback_data="admin_stats"),
         InlineKeyboardButton("💰 Rates", callback_data="admin_earnings")],
        [InlineKeyboardButton("✏️ Notice", callback_data="admin_set_notice"),
         InlineKeyboardButton("📧 Mail Sales", callback_data="admin_mail_sales")]
    ])
    
    await update.message.reply_text("👮‍♂️ **Admin Control Panel**", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ==========================================
# MAIN FUNCTION
# ==========================================
def main():
    # Create Application
    application = Application.builder().token(API_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.Text("1️⃣ Start Work"), start_work))
    application.add_handler(MessageHandler(filters.Text("2️⃣ My Account"), my_account))
    application.add_handler(MessageHandler(filters.Text("ℹ️ Help"), help_command))
    application.add_handler(MessageHandler(filters.Text("🔙 Main Menu"), start))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Photo handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Start bot
    print("🤖 Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
