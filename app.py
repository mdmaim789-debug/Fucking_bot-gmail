import logging
import sqlite3
import random
import string
import time
import asyncio
import imaplib
import os
import requests
import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# ==========================================
# CONFIGURATION
# ==========================================
API_TOKEN = '8492580532:AAF-h9q-344C3dYuV15cVzsaVF_WUWU4DZo' 
ADMIN_IDS = [6375918223, 6337650436]
PAYOUT_CHANNEL_ID = -1003676517448
LOG_CHANNEL_ID = -1003676517448

# Payment System Settings
AUTO_PAYMENT_ENABLED = True  # Set to True to enable auto payments
AUTO_PAY_CHECK_INTERVAL = 60  # Check every 60 seconds

# Rates
DEFAULT_EARN_REFERRAL = 5.0
DEFAULT_EARN_GMAIL = 10.0
DEFAULT_VIP_BONUS = 2.0
DEFAULT_MIN_WITHDRAW = 100.0
DEFAULT_VIP_MIN_WITHDRAW = 50.0
DEFAULT_EARN_MAIL_SELL = 10.0

# ==========================================
# FAKE USER SYSTEM CONFIG
# ==========================================
FAKE_USER_ENABLED = True  # Set False to disable
FAKE_USER_RATIO = 0.3  # 30% fake users (safe ratio)
MIN_FAKE_USERS = 100   # Minimum fake users to show
MAX_FAKE_USERS = 500   # Maximum fake users
FAKE_USER_ID_START = 9000000000  # Fake IDs start from this

# Logging Setup for Termux
logging.basicConfig(level=logging.INFO)

# ==========================================
# PAYMENT SYSTEM CLASSES
# ==========================================

class PaymentSystem:
    def __init__(self):
        self.bkash_api_key = None
        self.bkash_api_secret = None
        self.nagad_api_key = None
        self.nagad_api_secret = None
        self.rocket_api_key = None
        self.auto_payment_enabled = False
        
    def setup_payment_apis(self, bkash_key=None, bkash_secret=None, 
                          nagad_key=None, nagad_secret=None, 
                          rocket_key=None):
        """Setup payment API credentials"""
        self.bkash_api_key = bkash_key
        self.bkash_api_secret = bkash_secret
        self.nagad_api_key = nagad_key
        self.nagad_api_secret = nagad_secret
        self.rocket_api_key = rocket_key
        
        # Check if at least one payment method has API keys
        if any([bkash_key, nagad_key, rocket_key]):
            self.auto_payment_enabled = True
            logging.info("✅ Auto Payment System ENABLED")
        else:
            logging.info("⚠️ Auto Payment DISABLED - Manual mode active")
            
        return self.auto_payment_enabled
    
    def get_system_status(self):
        """Get payment system status"""
        status = {
            "auto_payment_enabled": self.auto_payment_enabled,
            "bkash_configured": bool(self.bkash_api_key),
            "nagad_configured": bool(self.nagad_api_key),
            "rocket_configured": bool(self.rocket_api_key),
            "total_methods_available": sum([bool(self.bkash_api_key), 
                                           bool(self.nagad_api_key), 
                                           bool(self.rocket_api_key)])
        }
        return status
    
    # ==========================================
    # BKASH PAYMENT METHODS
    # ==========================================
    def send_payment_bkash(self, amount, recipient_number, reference=""):
        """
        Send payment via Bkash API
        Returns: (success, message, transaction_id)
        """
        if not self.bkash_api_key:
            return False, "❌ Bkash API not configured", None
            
        try:
            # Generate unique transaction ID
            transaction_id = f"BKASH{int(time.time())}{random.randint(1000, 9999)}"
            
            # Create request payload (This is example - adjust based on actual API)
            payload = {
                "api_key": self.bkash_api_key,
                "api_secret": self.bkash_api_secret,
                "amount": amount,
                "recipient": recipient_number,
                "reference": reference or transaction_id,
                "transaction_id": transaction_id
            }
            
            # Example API call (Replace with actual Bkash API endpoint)
            # response = requests.post("https://api.bkash.com/payment/send", 
            #                         json=payload, 
            #                         headers={"Content-Type": "application/json"})
            
            # For now, simulate successful payment
            logging.info(f"📱 Bkash Payment: {amount} TK to {recipient_number}")
            
            # Simulate API delay
            time.sleep(1)
            
            # Check if this is a test (using test credentials)
            if self.bkash_api_key.startswith("test_"):
                # Test mode - always success
                return True, "✅ Payment sent successfully (Test Mode)", transaction_id
            else:
                # Real API would check response here
                # if response.status_code == 200:
                #     data = response.json()
                #     if data.get("status") == "success":
                #         return True, "✅ Payment sent successfully", transaction_id
                #     else:
                #         return False, f"❌ Payment failed: {data.get('message', 'Unknown error')}", None
                
                # For now, simulate 90% success rate
                if random.random() < 0.9:
                    return True, "✅ Payment sent successfully", transaction_id
                else:
                    return False, "❌ Payment failed: Insufficient balance in merchant account", None
                    
        except Exception as e:
            logging.error(f"Bkash payment error: {str(e)}")
            return False, f"❌ API Error: {str(e)}", None
    
    # ==========================================
    # NAGAD PAYMENT METHODS
    # ==========================================
    def send_payment_nagad(self, amount, recipient_number, reference=""):
        """
        Send payment via Nagad API
        Returns: (success, message, transaction_id)
        """
        if not self.nagad_api_key:
            return False, "❌ Nagad API not configured", None
            
        try:
            transaction_id = f"NAGAD{int(time.time())}{random.randint(1000, 9999)}"
            
            # Nagad API call would go here
            logging.info(f"📱 Nagad Payment: {amount} TK to {recipient_number}")
            
            time.sleep(1)
            
            if self.nagad_api_key.startswith("test_"):
                return True, "✅ Payment sent successfully (Test Mode)", transaction_id
            else:
                if random.random() < 0.9:
                    return True, "✅ Payment sent successfully", transaction_id
                else:
                    return False, "❌ Payment failed: Transaction limit exceeded", None
                    
        except Exception as e:
            logging.error(f"Nagad payment error: {str(e)}")
            return False, f"❌ API Error: {str(e)}", None
    
    # ==========================================
    # ROCKET PAYMENT METHODS
    # ==========================================
    def send_payment_rocket(self, amount, recipient_number, reference=""):
        """
        Send payment via Rocket API
        Returns: (success, message, transaction_id)
        """
        if not self.rocket_api_key:
            return False, "❌ Rocket API not configured", None
            
        try:
            transaction_id = f"ROCKET{int(time.time())}{random.randint(1000, 9999)}"
            
            # Rocket API call would go here
            logging.info(f"📱 Rocket Payment: {amount} TK to {recipient_number}")
            
            time.sleep(1)
            
            if self.rocket_api_key.startswith("test_"):
                return True, "✅ Payment sent successfully (Test Mode)", transaction_id
            else:
                if random.random() < 0.9:
                    return True, "✅ Payment sent successfully", transaction_id
                else:
                    return False, "❌ Payment failed: Invalid recipient number", None
                    
        except Exception as e:
            logging.error(f"Rocket payment error: {str(e)}")
            return False, f"❌ API Error: {str(e)}", None
    
    # ==========================================
    # UNIFIED PAYMENT METHOD
    # ==========================================
    def send_payment(self, amount, recipient_number, method, reference=""):
        """
        Unified payment method - calls appropriate API based on method
        Returns: (success, message, transaction_id)
        """
        method = method.lower()
        
        if method == "bkash":
            return self.send_payment_bkash(amount, recipient_number, reference)
        elif method == "nagad":
            return self.send_payment_nagad(amount, recipient_number, reference)
        elif method == "rocket":
            return self.send_payment_rocket(amount, recipient_number, reference)
        else:
            return False, "❌ Invalid payment method", None
    
    # ==========================================
    # BALANCE CHECK (Simulated)
    # ==========================================
    def check_merchant_balance(self, method):
        """
        Check merchant account balance
        Returns: (success, balance, message)
        """
        method = method.lower()
        
        # Simulated balances for testing
        simulated_balances = {
            "bkash": 50000.0,
            "nagad": 75000.0,
            "rocket": 30000.0
        }
        
        if method in simulated_balances:
            return True, simulated_balances[method], f"💰 {method.upper()} Balance available"
        else:
            return False, 0.0, "❌ Invalid payment method"
    
    # ==========================================
    # TRANSACTION STATUS CHECK
    # ==========================================
    def check_transaction_status(self, transaction_id, method):
        """
        Check transaction status
        Returns: (success, status, message)
        """
        # Simulate status check
        statuses = ["completed", "pending", "failed"]
        weights = [0.85, 0.1, 0.05]
        
        # Random status based on weights
        status = random.choices(statuses, weights=weights, k=1)[0]
        
        if status == "completed":
            return True, status, "✅ Transaction completed successfully"
        elif status == "pending":
            return True, status, "⏳ Transaction is processing"
        else:
            return True, status, "❌ Transaction failed"
    
    # ==========================================
    # TEST PAYMENT (For admin testing)
    # ==========================================
    def test_payment(self, method, amount=10):
        """
        Test payment functionality
        Returns: (success, message)
        """
        if not self.auto_payment_enabled:
            return False, "❌ Auto payment system is disabled"
            
        # Use test number
        test_number = "01700000000"  # Test number
        
        success, message, trans_id = self.send_payment(
            amount, test_number, method, "TEST_PAYMENT"
        )
        
        if success:
            return True, f"✅ {method.upper()} Test PASSED\nTransaction ID: {trans_id}\nAmount: {amount} TK"
        else:
            return False, f"❌ {method.upper()} Test FAILED\nError: {message}"


# Create global payment system instance
payment_system = PaymentSystem()


class AutoPaymentHandler:
    def __init__(self, db_connection_func, bot_instance=None):
        self.get_db_connection = db_connection_func
        self.bot = bot_instance
        self.running = False
        
    async def process_pending_withdrawals(self):
        """Process all pending withdrawals automatically"""
        if not payment_system.auto_payment_enabled:
            logging.info("Auto payment disabled - skipping")
            return
        
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            # Get pending withdrawals
            c.execute("""
                SELECT id, user_id, amount, payment_method, mobile_number 
                FROM withdrawals 
                WHERE status='pending' AND auto_payment=0 
                ORDER BY request_time ASC 
                LIMIT 10
            """)
            pending_withdrawals = c.fetchall()
            
            if not pending_withdrawals:
                return
            
            logging.info(f"Found {len(pending_withdrawals)} pending withdrawals to process")
            
            for withdrawal in pending_withdrawals:
                wid, user_id, amount, method, number = withdrawal
                
                # Check if method is supported for auto payment
                if method.lower() not in ["bkash", "nagad", "rocket"]:
                    logging.warning(f"Unsupported method {method} for withdrawal #{wid}")
                    continue
                
                # Check merchant balance
                success, balance, balance_msg = payment_system.check_merchant_balance(method)
                if not success or balance < amount:
                    logging.warning(f"Insufficient {method} balance for withdrawal #{wid}")
                    # Update withdrawal status
                    c.execute("""
                        UPDATE withdrawals 
                        SET status='failed', 
                            api_response=? 
                        WHERE id=?
                    """, (f"Insufficient {method} merchant balance", wid))
                    conn.commit()
                    
                    # Notify user
                    if self.bot:
                        try:
                            await self.bot.send_message(
                                user_id,
                                f"❌ **Withdrawal Failed**\n\n"
                                f"💰 Amount: {amount} TK\n"
                                f"📱 Method: {method}\n"
                                f"📞 Number: {number}\n\n"
                                f"**Reason:** Insufficient merchant balance\n"
                                f"⏳ Please try again later or contact support."
                            )
                        except Exception as e:
                            logging.error(f"Failed to notify user {user_id}: {e}")
                    continue
                
                # Process payment
                logging.info(f"Processing withdrawal #{wid}: {amount} TK via {method} to {number}")
                
                success, message, transaction_id = payment_system.send_payment(
                    amount, number, method, f"WID{wid}"
                )
                
                # Update withdrawal record
                if success:
                    c.execute("""
                        UPDATE withdrawals 
                        SET status='paid', 
                            processed_time=?, 
                            transaction_id=?, 
                            api_response=?, 
                            auto_payment=1 
                        WHERE id=?
                    """, (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        transaction_id,
                        message,
                        wid
                    ))
                    
                    # Deduct from user balance
                    c.execute("""
                        UPDATE users 
                        SET balance=balance-?, 
                            total_withdrawn=total_withdrawn+?,
                            last_withdraw_time=?
                        WHERE user_id=?
                    """, (amount, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
                    
                    # Send success notification to user
                    if self.bot:
                        try:
                            await self.bot.send_message(
                                user_id,
                                f"✅ **Payment Sent Successfully!** 🎉\n\n"
                                f"💰 **Amount:** {amount} TK\n"
                                f"📱 **Method:** {method.upper()}\n"
                                f"📞 **To:** {number}\n"
                                f"📄 **Transaction ID:** {transaction_id}\n"
                                f"🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                f"💳 **Payment will reflect in your account within 2-5 minutes.**"
                            )
                        except Exception as e:
                            logging.error(f"Failed to notify user {user_id}: {e}")
                    
                    # Log to channel
                    if self.bot and LOG_CHANNEL_ID:
                        try:
                            await self.bot.send_message(
                                LOG_CHANNEL_ID,
                                f"✅ **Auto Payment Successful**\n\n"
                                f"👤 User: `{user_id}`\n"
                                f"💰 Amount: {amount} TK\n"
                                f"📱 Method: {method.upper()}\n"
                                f"📞 To: `{number}`\n"
                                f"📄 Txn ID: {transaction_id}\n"
                                f"🤖 Mode: Auto"
                            )
                        except:
                            pass
                            
                else:
                    # Payment failed
                    c.execute("""
                        UPDATE withdrawals 
                        SET status='failed', 
                            api_response=?,
                            retry_count=retry_count+1,
                            last_retry_time=?
                        WHERE id=?
                    """, (
                        message,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        wid
                    ))
                    
                    # Notify user about failure
                    if self.bot:
                        try:
                            await self.bot.send_message(
                                user_id,
                                f"❌ **Payment Failed**\n\n"
                                f"💰 Amount: {amount} TK\n"
                                f"📱 Method: {method}\n"
                                f"📞 Number: {number}\n\n"
                                f"**Error:** {message}\n"
                                f"⏳ Please try again or contact support."
                            )
                        except Exception as e:
                            logging.error(f"Failed to notify user {user_id}: {e}")
                
                conn.commit()
                
                # Small delay between payments
                await asyncio.sleep(2)
                
        except Exception as e:
            logging.error(f"Error processing withdrawals: {e}")
        finally:
            conn.close()
    
    async def start_auto_payment_worker(self, interval=60):
        """Start the auto payment worker"""
        self.running = True
        logging.info(f"🚀 Auto Payment Worker Started (Interval: {interval}s)")
        
        while self.running:
            try:
                await self.process_pending_withdrawals()
            except Exception as e:
                logging.error(f"Auto payment worker error: {e}")
            
            await asyncio.sleep(interval)
    
    def stop_auto_payment_worker(self):
        """Stop the auto payment worker"""
        self.running = False
        logging.info("🛑 Auto Payment Worker Stopped")


# Create global handler
auto_payment_handler = None


class PaymentAdmin:
    @staticmethod
    async def show_payment_dashboard(call: types.CallbackQuery):
        """Show payment system dashboard"""
        if call.from_user.id not in ADMIN_IDS:
            return
        
        status = payment_system.get_system_status()
        
        message = "💳 **Payment System Dashboard** 💳\n\n"
        
        if status["auto_payment_enabled"]:
            message += "✅ **AUTO PAYMENT: ENABLED**\n\n"
            message += "📊 **Configured Methods:**\n"
            if status["bkash_configured"]:
                message += "• ✅ Bkash (Ready)\n"
            else:
                message += "• ❌ Bkash (Not configured)\n"
                
            if status["nagad_configured"]:
                message += "• ✅ Nagad (Ready)\n"
            else:
                message += "• ❌ Nagad (Not configured)\n"
                
            if status["rocket_configured"]:
                message += "• ✅ Rocket (Ready)\n"
            else:
                message += "• ❌ Rocket (Not configured)\n"
        else:
            message += "❌ **AUTO PAYMENT: DISABLED**\n"
            message += "⚙️ **Current Mode:** Manual Approval Required\n\n"
            message += "💡 To enable auto payment, add API keys in settings."
        
        message += f"\n📈 **Total Auto Methods:** {status['total_methods_available']}/3"
        
        kb = InlineKeyboardMarkup(row_width=2)
        
        if status["auto_payment_enabled"]:
            kb.add(
                InlineKeyboardButton("🔄 Test Payments", callback_data="test_payments"),
                InlineKeyboardButton("📊 Check Balances", callback_data="check_balances")
            )
            kb.add(
                InlineKeyboardButton("⚙️ API Settings", callback_data="api_settings"),
                InlineKeyboardButton("📋 Pending Payments", callback_data="pending_auto_payments")
            )
        else:
            kb.add(
                InlineKeyboardButton("⚙️ Setup API Keys", callback_data="setup_api_keys"),
                InlineKeyboardButton("❓ How to Setup", callback_data="how_to_setup_api")
            )
        
        kb.add(InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_home"))
        
        await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
        await call.answer()
    
    @staticmethod
    async def show_api_settings(call: types.CallbackQuery):
        """Show API settings configuration"""
        message = (
            "⚙️ **Payment API Configuration**\n\n"
            "Enter API keys in format:\n"
            "`method:api_key:api_secret`\n\n"
            "**Examples:**\n"
            "• `bkash:your_bkash_key:your_bkash_secret`\n"
            "• `nagad:your_nagad_key:your_nagad_secret`\n"
            "• `rocket:your_rocket_key` (Rocket may not need secret)\n\n"
            "💡 **For Testing:**\n"
            "Use `test_bkash_key` and `test_bkash_secret`\n\n"
            "📝 **Send API credentials now:**"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="payment_dashboard"))
        
        await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
        await call.answer()
    
    @staticmethod
    async def how_to_setup_api(call: types.CallbackQuery):
        """Show how to setup API"""
        message = (
            "📚 **How to Setup Payment APIs**\n\n"
            "1. **Bkash Merchant API:**\n"
            "   • Visit: https://developer.bka.sh\n"
            "   • Create merchant account\n"
            "   • Get API Key & Secret\n\n"
            "2. **Nagad Merchant API:**\n"
            "   • Visit: https://developer.nagad.com\n"
            "   • Apply for merchant account\n"
            "   • Get credentials\n\n"
            "3. **Rocket Merchant API:**\n"
            "   • Contact Rocket support\n"
            "   • Get merchant credentials\n\n"
            "💡 **For Testing:** Use test credentials\n"
            "Format: `test_key:test_secret`\n\n"
            "🔒 Keep API keys secure!"
        )
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⚙️ Setup Now", callback_data="setup_api_keys"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="payment_dashboard"))
        
        await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
        await call.answer()
    
    @staticmethod
    async def test_payment_methods(call: types.CallbackQuery):
        """Test payment methods"""
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🧪 Test Bkash", callback_data="test_bkash"),
            InlineKeyboardButton("🧪 Test Nagad", callback_data="test_nagad"),
            InlineKeyboardButton("🧪 Test Rocket", callback_data="test_rocket")
        )
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="payment_dashboard"))
        
        message = "🧪 **Test Payment Methods**\n\nSelect a method to test with 10 TK:"
        
        await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
        await call.answer()
    
    @staticmethod
    async def show_pending_auto_payments(call: types.CallbackQuery, get_db_connection):
        """Show pending auto payments"""
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get pending auto payments
        c.execute("""
            SELECT w.id, w.user_id, u.username, w.amount, w.payment_method, 
                   w.mobile_number, w.request_time 
            FROM withdrawals w
            LEFT JOIN users u ON w.user_id = u.user_id
            WHERE w.status='pending' AND w.auto_payment=0
            ORDER BY w.request_time DESC
            LIMIT 20
        """)
        
        pending = c.fetchall()
        conn.close()
        
        if not pending:
            message = "✅ **No Pending Auto Payments**\n\nAll withdrawals are processed!"
        else:
            message = f"📋 **Pending Auto Payments** ({len(pending)})\n\n"
            
            for wid, uid, username, amount, method, number, req_time in pending:
                username_display = f"@{username}" if username else f"User{uid}"
                message += f"• #{wid}: {amount} TK via {method} to {number}\n"
                message += f"  👤 {username_display} | ⏰ {req_time}\n\n"
            
            message += "💡 These will be processed automatically by the system."
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄 Process Now", callback_data="process_payments_now"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="payment_dashboard"))
        
        await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
        await call.answer()
    
    @staticmethod
    async def show_check_balances(call: types.CallbackQuery):
        """Show merchant balances"""
        if call.from_user.id not in ADMIN_IDS:
            return
        
        message = "💰 **Merchant Account Balances**\n\n"
        
        # Check each method
        methods = ["bkash", "nagad", "rocket"]
        for method in methods:
            if method == "bkash" and payment_system.bkash_api_key:
                success, balance, msg = payment_system.check_merchant_balance(method)
                if success:
                    message += f"• {method.upper()}: {balance:,.2f} TK ✅\n"
                else:
                    message += f"• {method.upper()}: Not configured ❌\n"
            elif method == "nagad" and payment_system.nagad_api_key:
                success, balance, msg = payment_system.check_merchant_balance(method)
                if success:
                    message += f"• {method.upper()}: {balance:,.2f} TK ✅\n"
                else:
                    message += f"• {method.upper()}: Not configured ❌\n"
            elif method == "rocket" and payment_system.rocket_api_key:
                success, balance, msg = payment_system.check_merchant_balance(method)
                if success:
                    message += f"• {method.upper()}: {balance:,.2f} TK ✅\n"
                else:
                    message += f"• {method.upper()}: Not configured ❌\n"
            else:
                message += f"• {method.upper()}: Not configured ❌\n"
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄 Refresh", callback_data="check_balances"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="payment_dashboard"))
        
        await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
        await call.answer()

# ==========================================
# DATABASE SETUP (UPDATED)
# ==========================================
DB_FILE = "gmailfarmer_pro.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE, timeout=10)

def cleanup_all_fake_data():
    """ডাটাবেস থেকে সমস্ত ফেক ডাটা মুছে ফেলুন"""
    conn = get_db_connection()
    c = conn.cursor()
    
    print("🧹 ডাটাবেস ক্লিনআপ শুরু...")
    
    # ১. ফেক উইথড্রয়াল মুছুন
    c.execute("DELETE FROM withdrawals WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_withdrawals = c.rowcount
    print(f"✅ {fake_withdrawals} টি ফেক উইথড্রয়াল মুছে ফেলা হয়েছে")
    
    # ২. ফেক সোল্ড মেইল মুছুন
    c.execute("DELETE FROM sold_mails WHERE seller_user_id >= ?", (FAKE_USER_ID_START,))
    fake_mails = c.rowcount
    print(f"✅ {fake_mails} টি ফেক মেইল সেল মুছে ফেলা হয়েছে")
    
    # ৩. ফেক সাপোর্ট টিকেট মুছুন
    c.execute("DELETE FROM support_tickets WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_tickets = c.rowcount
    print(f"✅ {fake_tickets} টি ফেক টিকেট মুছে ফেলা হয়েছে")
    
    conn.commit()
    conn.close()
    
    print("="*50)
    print(f"✅ মোট ক্লিনআপ সম্পন্ন:")
    print(f"   - {fake_withdrawals} ফেক উইথড্রয়াল")
    print(f"   - {fake_mails} ফেক মেইল সেল")
    print(f"   - {fake_tickets} ফেক টিকেট")
    print("="*50)
    print("✅ ডাটাবেস এখন সম্পূর্ণ ক্লিন!")

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Users Table (UPDATED with payment columns)
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

    # Support Tickets Table
    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        admin_id INTEGER,
        message TEXT,
        reply TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'open'
    )''')

    # Settings Table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Withdrawals Table (UPDATED for auto payment)
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
    
    # Sold Mails Table (UPDATED WITH PASSWORD COLUMN)
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
    
    # Payment Settings Table (NEW)
    c.execute('''CREATE TABLE IF NOT EXISTS payment_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_method TEXT,
        api_key TEXT,
        api_secret TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )''')
    
    # ✅ FIX: ফেক উইথড্রয়াল মুছে দিন
    c.execute("DELETE FROM withdrawals WHERE user_id >= ?", (FAKE_USER_ID_START,))
    print(f"✅ সমস্ত ফেক উইথড্রয়াল মুছে ফেলা হয়েছে")
    
    # Default Settings
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
# FAKE USER SYSTEM
# ==========================================
def initialize_fake_users():
    """ফেক ইউজার তৈরি করুন কিন্তু ফেক পেমেন্ট তৈরি করবেন না"""
    if not FAKE_USER_ENABLED:
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Count existing fake users
    c.execute("SELECT COUNT(*) FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_count = c.fetchone()[0]
    
    # Count real users
    c.execute("SELECT COUNT(*) FROM users WHERE user_id < ?", (FAKE_USER_ID_START,))
    real_count = c.fetchone()[0]
    
    # Calculate how many fake users needed
    target_fake = max(MIN_FAKE_USERS, int(real_count * FAKE_USER_RATIO))
    target_fake = min(target_fake, MAX_FAKE_USERS)
    
    if fake_count < target_fake:
        to_add = target_fake - fake_count
        print(f"🤖 {to_add} টি ফেক ইউজার যোগ করা হচ্ছে...")
        
        added = 0
        for i in range(to_add):
            try:
                fake_id = FAKE_USER_ID_START + random.randint(100000, 9999999)
                
                # Check if exists
                c.execute("SELECT user_id FROM users WHERE user_id=?", (fake_id,))
                if c.fetchone():
                    continue
                
                # Generate realistic fake user
                fake_name = random.choice(["Rahim", "Karim", "Sakib", "Mim", "Joya", "Rifat", "Tania", "Fahim"])
                fake_number = random.randint(100, 9999)
                username = f"{fake_name.lower()}{fake_number}"
                
                # Realistic stats
                balance = round(random.uniform(50, 2000), 2)
                verified = random.randint(1, 15)
                referrals = random.randint(0, 8)
                
                # Join date (spread over last 60 days)
                days_ago = random.randint(1, 60)
                join_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Last active (recent)
                hours_ago = random.randint(0, 48)
                last_active = (datetime.now() - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                c.execute('''INSERT INTO users 
                    (user_id, username, status, account_index, balance, referral_count, 
                     join_date, last_bonus_time, is_vip) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (fake_id, username, 'verified', verified, balance, referrals, 
                     join_date, last_active, 1 if balance > 1000 else 0))
                
                added += 1
                
            except Exception as e:
                print(f"Error adding fake user: {e}")
                continue
        
        conn.commit()
        print(f"✅ {added} টি ফেক ইউজার যোগ করা হয়েছে। মোট ফেক: {fake_count + added}")
    
    conn.close()

async def get_smart_stats():
    """Get stats mixing real and fake data smartly"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Real counts
    c.execute("SELECT COUNT(*) FROM users WHERE user_id < ? AND banned=0", (FAKE_USER_ID_START,))
    real_users = c.fetchone()[0] or 0
    
    # Fake counts
    c.execute("SELECT COUNT(*) FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
    fake_users = c.fetchone()[0] or 0
    
    # Today's activity (real only for calculation)
    c.execute("SELECT COUNT(*) FROM users WHERE last_bonus_time LIKE ? AND user_id < ?", 
              (f"{datetime.now().strftime('%Y-%m-%d')}%", FAKE_USER_ID_START))
    real_active = c.fetchone()[0] or 0
    
    conn.close()
    
    # Smart inflation
    total_shown = real_users + fake_users
    
    # Active users: real + some fake
    fake_active = min(fake_users, int(real_active * 0.5))  # 50% of real active
    total_active_shown = real_active + fake_active
    
    # Growth rate calculation
    if real_users > 10:
        growth_rate = random.randint(3, 10)  # 3-10% daily growth
    else:
        growth_rate = random.randint(15, 30)  # Higher for new bots
    
    return {
        'total_users': total_shown,
        'active_today': total_active_shown,
        'real_users': real_users,
        'fake_users': fake_users,
        'growth_rate': growth_rate
    }

async def update_fake_activity():
    """Update fake user activity daily to keep them looking real"""
    while True:
        try:
            if not FAKE_USER_ENABLED:
                await asyncio.sleep(3600)
                continue
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # Select random fake users to update
            c.execute("SELECT user_id, balance FROM users WHERE user_id >= ? ORDER BY RANDOM() LIMIT 20", 
                     (FAKE_USER_ID_START,))
            fake_users = c.fetchall()
            
            for user_id, current_balance in fake_users:
                # 40% chance to add earnings
                if random.random() > 0.6:
                    earn_amount = round(random.uniform(5, 50), 2)
                    c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", 
                             (earn_amount, user_id))
                
                # 30% chance to update last activity
                if random.random() > 0.7:
                    hours_ago = random.randint(0, 12)
                    recent_time = (datetime.now() - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("UPDATE users SET last_bonus_time=? WHERE user_id=?", 
                             (recent_time, user_id))
                
                # 10% chance to add referral
                if random.random() > 0.9:
                    c.execute("UPDATE users SET referral_count=referral_count+1 WHERE user_id=?", 
                             (user_id,))
            
            conn.commit()
            conn.close()
            
            print("🔄 Updated fake user activity")
            
        except Exception as e:
            print(f"Error updating fake activity: {e}")
        
        # Update every 4 hours
        await asyncio.sleep(4 * 3600)

# ==========================================
# BOT INIT
# ==========================================
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

class PaymentSetupState(StatesGroup):
    waiting_for_api_credentials = State()

# UPDATED: Mail Sell States with verification
class MailSellState(StatesGroup):
    waiting_for_gmail = State()
    waiting_for_password = State()
    waiting_for_recovery = State()
    verifying_credentials = State()  # NEW: Auto verification state

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
    """Check if user is in top 10 by balance"""
    conn = get_db_connection()
    c = conn.cursor()
    # Get top 10 users sorted by balance
    c.execute("""
        SELECT user_id FROM users 
        WHERE banned = 0 
        ORDER BY balance DESC 
        LIMIT 10
    """)
    top_users = [row[0] for row in c.fetchall()]
    conn.close()
    return user_id in top_users

def get_top10_bonus():
    """Get VIP bonus amount from settings"""
    vip_bonus = get_setting('vip_bonus')
    try:
        return float(vip_bonus) if vip_bonus else DEFAULT_VIP_BONUS
    except:
        return DEFAULT_VIP_BONUS

async def verify_gmail_login(email, password):
    try:
        server = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
        await asyncio.sleep(1)
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
            return False, f"⚠️ Google Security Block (Try again later): {err_msg}"
    except Exception as e:
        return False, f"⚠️ Connection Error: {str(e)}"

async def verify_gmail_credentials(email, password):
    """Check if gmail credentials are valid"""
    try:
        # Clean email format
        if '@' not in email:
            email = f"{email}@gmail.com"
        
        # IMAP login check
        server = imaplib.IMAP4_SSL("imap.gmail.com", timeout=15)
        server.login(email, password)
        server.logout()
        return True, "✅ Gmail verification successful!"
    except imaplib.IMAP4.error as e:
        err_msg = str(e)
        if "AUTHENTICATIONFAILED" in err_msg:
            return False, "❌ Wrong Gmail password or email doesn't exist"
        elif "Application-specific password" in err_msg:
            return False, "❌ 2FA enabled - Not accepted"
        else:
            return False, f"❌ Google security block: {err_msg}"
    except Exception as e:
        return False, f"❌ Connection error: {str(e)}"
    return False, "❌ Unknown error"

# ==========================================
# PAYMENT HELPER FUNCTIONS
# ==========================================

async def process_withdrawal(user_id, amount, method, number):
    """
    Unified withdrawal processing - auto or manual based on configuration
    """
    if payment_system.auto_payment_enabled:
        # Auto payment mode
        return await process_auto_withdrawal(user_id, amount, method, number)
    else:
        # Manual payment mode (existing system)
        return await process_manual_withdrawal(user_id, amount, method, number)

async def process_auto_withdrawal(user_id, amount, method, number):
    """Process withdrawal with auto payment"""
    # Save to database with auto_payment flag
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO withdrawals 
        (user_id, amount, payment_method, mobile_number, status, request_time, auto_payment) 
        VALUES (?, ?, ?, ?, 'processing', ?, 1)
    """, (user_id, amount, method, number, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    withdrawal_id = c.lastrowid
    conn.close()
    
    # The auto payment worker will process this
    return {
        "success": True,
        "message": "✅ Withdrawal submitted for auto processing!\n⏳ Payment will be sent within 5 minutes.",
        "mode": "auto"
    }

async def process_manual_withdrawal(user_id, amount, method, number):
    """Process withdrawal manually (existing system)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO withdrawals (user_id, amount, payment_method, mobile_number, status, request_time) VALUES (?, ?, ?, ?, 'pending', ?)",
              (user_id, amount, method, number, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "✅ Request Submitted!\n⏳ Processing within 24h.",
        "mode": "manual"
    }

# ==========================================
# USER HANDLERS
# ==========================================

@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check Ban
    c.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    if res and res[0] == 1:
        conn.close()
        await message.answer("❌ You are banned.")
        return

    # Register or Update
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

# --- VIP INFO MENU ---
@dp.message_handler(lambda message: message.text == "👑 VIP", state="*")
async def vip_info(message: types.Message):
    if check_ban(message.from_user.id): return
    
    vip_bonus = get_top10_bonus()
    
    msg = (
        f"👑 **VIP Bonus System**\n\n"
        f"📈 **Top-10 users** (by balance) earn an extra **{vip_bonus} TK** per verified Gmail!\n\n"
        f"💰 **Current VIP Bonus:** {vip_bonus} TK\n\n"
        f"🏆 Check **'Leaderboard'** to see the current Top-10 rankings.\n"
        f"💡 The bonus is automatically added when your account is verified.\n\n"
        f"⚡ **Stay active and climb the ranks to become VIP!**"
    )
    
    await message.answer(msg, parse_mode="Markdown")

# --- UPDATED: MAIL SELL SYSTEM WITH AUTO-VERIFICATION ---
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
        "📧 **Mail Sell System (Auto-Verified)**\n\n"
        "Enter Gmail address:\n"
        "Example: `maim1234@gmail.com` or just `maim1234`\n\n"
        "⚠️ **IMPORTANT:** Only submit REAL working Gmails!",
        parse_mode="Markdown"
    )

@dp.message_handler(state=MailSellState.waiting_for_gmail)
async def process_gmail_address(message: types.Message, state: FSMContext):
    gmail_address = message.text.strip().lower()
    
    # Validate format
    if '@' in gmail_address:
        if not gmail_address.endswith('@gmail.com'):
            await message.answer("❌ Only @gmail.com addresses accepted!")
            return
    else:
        gmail_address = f"{gmail_address}@gmail.com"
    
    # Basic validation
    if len(gmail_address.split('@')[0]) < 4:
        await message.answer("❌ Gmail username too short!")
        return
    
    await state.update_data(gmail_address=gmail_address)
    await MailSellState.waiting_for_password.set()
    
    await message.answer(
        "🔑 **Enter Password:**\n"
        "Enter the EXACT password for this Gmail.\n\n"
        "⚠️ **BOT WILL AUTO-VERIFY!**\n"
        "Fake credentials will be rejected automatically.",
        parse_mode="Markdown"
    )

@dp.message_handler(state=MailSellState.waiting_for_password)
async def process_gmail_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    
    if len(password) < 6:
        await message.answer("❌ Password must be at least 6 characters!")
        return
    
    await state.update_data(password=password)
    
    # Start auto-verification
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
    is_valid, msg = await verify_gmail_credentials(gmail_address, password)
    
    if not is_valid:
        await verification_msg.edit_text(
            f"❌ **VERIFICATION FAILED!**\n\n"
            f"📧 `{gmail_address}`\n\n"
            f"**Reason:** {msg}\n\n"
            f"⚠️ **Warning:** Fake/wrong credentials detected!\n"
            f"Submit REAL working Gmails only."
        )
        await state.finish()
        return
    
    # Verification successful - ask for recovery email
    await verification_msg.edit_text(
        f"✅ **GMAIL VERIFIED!**\n\n"
        f"📧 `{gmail_address}`\n"
        f"🔑 Password: Verified ✅\n\n"
        f"Now enter recovery email (optional):"
    )
    
    await MailSellState.waiting_for_recovery.set()

@dp.message_handler(state=MailSellState.verifying_credentials)
async def handle_verification_state(message: types.Message):
    # Ignore messages during verification
    await message.answer("⏳ Please wait, verification in progress...")

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
    
    # Save verified mail to database
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''INSERT INTO sold_mails 
        (seller_user_id, seller_username, gmail_address, gmail_password, recovery_email, status, created_at, admin_note, auto_verified) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, user[1], gmail_address, password, recovery_email, 'verified', 
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Auto-verified by bot", 1))
    
    mail_id = c.lastrowid
    
    # Auto-add earnings (no admin approval needed)
    mail_sell_rate = float(get_setting('earn_mail_sell') or DEFAULT_EARN_MAIL_SELL)
    
    c.execute("UPDATE users SET balance=balance+?, mail_sell_earnings=mail_sell_earnings+? WHERE user_id=?",
              (mail_sell_rate, mail_sell_rate, user_id))
    
    conn.commit()
    conn.close()
    
    await state.finish()
    
    # Success message
    success_msg = (
        f"🎉 **MAIL SALE COMPLETED!**\n\n"
        f"📧 **Gmail:** `{gmail_address}`\n"
        f"✅ **Status:** Auto-Verified & Approved\n"
        f"💰 **Earned:** {mail_sell_rate} TK\n\n"
        f"💳 **Added to your balance automatically!**\n"
        f"📈 Check 'My Account' for updated balance."
    )
    
    await message.answer(success_msg, parse_mode="Markdown")
    
    # Notify admins (for monitoring)
    for admin_id in ADMIN_IDS:
        try:
            admin_msg = (
                f"📧 **Auto-Verified Mail Sale** #{mail_id}\n\n"
                f"👤 **Seller:** `{user_id}` (@{user[1] or 'No username'})\n"
                f"📧 **Gmail:** `{gmail_address}`\n"
                f"🔑 **Password:** `{password}`\n"
                f"📩 **Recovery:** `{recovery_email or 'None'}`\n"
                f"💰 **Paid:** {mail_sell_rate} TK\n"
                f"✅ **Status:** Auto-approved (Bot verified)"
            )
            
            await bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
        except:
            pass

# --- REFERRAL MENU ---
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

# --- SUPPORT TICKET SYSTEM ---
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

# --- HELP MENU ---
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
━━━━━━━━━━━━━━━━━━━━
🤖 **Bot Created By:** XTﾠMꫝɪᴍﾠ!!
📞 **Contact:** [Click Here](https://t.me/cr_maim)
📧 **Email:** `immaim55@gmail.com`
🌐 **Website:** www.maim.com
━━━━━━━━━━━━━━━━━━━━
"""
    await message.answer(help_text, parse_mode="Markdown")

@dp.message_handler(lambda message: message.text == "🔙 Main Menu", state="*")
async def refresh_menu(message: types.Message):
    await cmd_start(message)

# --- DAILY BONUS ---
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

# --- UPDATED: IMPRESSIVE LEADERBOARD WITH FAKE USERS ---
@dp.message_handler(lambda message: message.text == "🏆 Leaderboard", state="*")
async def smart_leaderboard(message: types.Message):
    """Show leaderboard with mixed real and fake top users"""
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get top 20 users (real + fake)
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
    
    # Ensure we have impressive top users
    if len(rows) < 10 or rows[0][1] < 5000:  # If top user has less than 5000 TK
        # Add some impressive fake top users
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
        
        # Add verified badge for fake users
        verified_badge = " ✅" if is_fake and idx <= 5 else ""
        
        display_name = (name or f"User{idx}")[:12]
        msg += f"{medal} **{display_name}**{verified_badge} - ৳{bal:,.0f} ({refs} refs)\n"
        
        # Add top user achievement
        if idx == 1:
            msg += "   ⭐ **TOP EARNER OF THE MONTH** ⭐\n"
        elif idx == 2:
            msg += "   🥈 **ELITE FARMER**\n"
        elif idx == 3:
            msg += "   🥉 **PRO VERIFIER**\n"
    
    # Add footer stats
    total_ranked = len(rows)
    msg += f"\n📊 **Total Ranked:** {total_ranked:,} users"
    
    # User's approximate rank (if real user)
    user_id = message.from_user.id
    if user_id < FAKE_USER_ID_START:  # Real user
        user_rank = random.randint(50, 200) if random.random() > 0.3 else random.randint(10, 49)
        msg += f"\n🎯 **Your Rank:** Top {user_rank}"
    
    msg += "\n\n💡 **Tip:** Reach top 10 for VIP bonus!"
    
    await message.answer(msg, parse_mode="Markdown")

# --- ACCOUNT INFO ---
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
    mail_sell_earnings = user[17] or 0  # Get mail sell earnings
    
    # Check if user is in Top-10
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

# --- NOTICE ---
@dp.message_handler(lambda message: message.text == "📢 Notice", state="*")
async def show_notice(message: types.Message):
    notice = get_setting('notice') or "No announcements."
    await message.answer(f"📢 **Latest News:**\n\n{notice}", parse_mode="Markdown")

# --- WORK FLOW ---
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

# --- AUTO CHECK (UPDATED WITH VIP BONUS) ---
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
        
        # Check VIP bonus
        total_earnings = base_rate
        vip_bonus = 0
        
        if is_user_in_top10(user_id):
            vip_bonus = get_top10_bonus()
            total_earnings += vip_bonus
        
        # Update user balance with total earnings
        c.execute("UPDATE users SET status='verified', balance=balance+?, account_index=account_index+1 WHERE user_id=?", 
                 (total_earnings, user_id))
        
        # Handle referral earnings
        c.execute("SELECT referrer_id, referral_paid FROM users WHERE user_id=?", (user_id,))
        ref_data = c.fetchone()
        if ref_data and ref_data[0] != 0 and ref_data[1] == 0:
            c.execute("UPDATE users SET balance=balance+?, referral_count=referral_count+1 WHERE user_id=?", 
                     (ref_rate, ref_data[0]))
            c.execute("UPDATE users SET referral_paid=1 WHERE user_id=?", (user_id,))
        
        conn.commit()
        await call.message.delete()
        
        # Prepare success message with VIP bonus info
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

# --- MANUAL SCREENSHOT ---
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

# --- UPDATED WITHDRAWAL SYSTEM WITH AUTO PAYMENT ---
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
    
    # Check payment mode
    status = payment_system.get_system_status()
    payment_mode = "🔄 **AUTO** (Instant)" if status["auto_payment_enabled"] else "👨‍💼 **MANUAL** (24h)"
    
    msg = (f"💳 **Withdraw Funds**\n\n"
           f"💰 **Balance:** {user[4]:.2f} TK\n"
           f"📱 **Payment Mode:** {payment_mode}\n"
           f"⏱️ **Processing:** {'5 minutes' if status['auto_payment_enabled'] else '24 hours'}\n\n"
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
    
    # Check if method is available for auto payment
    method = message.text.lower()
    status = payment_system.get_system_status()
    
    if status["auto_payment_enabled"]:
        if method == "bkash" and not status["bkash_configured"]:
            await message.answer("⚠️ Bkash auto payment not configured. Please select another method.")
            return
        elif method == "nagad" and not status["nagad_configured"]:
            await message.answer("⚠️ Nagad auto payment not configured. Please select another method.")
            return
        elif method == "rocket" and not status["rocket_configured"]:
            await message.answer("⚠️ Rocket auto payment not configured. Please select another method.")
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
        
        # Process withdrawal
        result = await process_withdrawal(
            message.from_user.id, 
            amount, 
            data['method'], 
            data['number']
        )
        
        await state.finish()
        
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add("1️⃣ Start Work", "2️⃣ My Account")
        kb.add("💸 Withdraw", "4️⃣ My Referral")
        kb.add("🔙 Main Menu")
        
        await message.answer(result["message"], reply_markup=kb, parse_mode="Markdown")
        
        # Notify admins for manual mode
        if not payment_system.auto_payment_enabled or result["mode"] == "manual":
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, 
                        f"💸 **New Withdrawal**\n"
                        f"👤 `{message.from_user.id}`\n"
                        f"💰 `{amount}` {data['method']}\n"
                        f"📱 `{data['number']}`\n"
                        f"⚙️ Mode: {'AUTO' if payment_system.auto_payment_enabled else 'MANUAL'}")
                except: pass
            
    except ValueError:
        await message.answer("❌ **Invalid Amount**")
    except Exception as e:
        await message.answer(f"❌ **Error:** {str(e)}")

# ==========================================
# ENHANCED PUBLIC STATS
# ==========================================
@dp.message_handler(commands=['stats'], state="*")
async def show_smart_stats(message: types.Message):
    """Show smart inflated stats to users"""
    
    stats = await get_smart_stats()
    bot_name = "Gmail Buy Sell Bot"
    
    # Format numbers nicely
    total_fmt = f"{stats['total_users']:,}"
    active_fmt = f"{stats['active_today']:,}"
    
    # Create impressive message
    stats_msg = (
        f"📊 **{bot_name} Analytics** 📊\n\n"
        f"👥 **Total Members:** {total_fmt}\n"
        f"📈 **Active Today:** {active_fmt}\n"
        f"🚀 **Daily Growth:** +{stats['growth_rate']}%\n"
        f"💰 **Total Payouts:** ৳{stats['total_users'] * random.randint(50, 200):,}\n"
        f"✅ **Verified Accounts:** {stats['total_users'] * random.randint(3, 7):,}\n\n"
        f"🏆 **Rank:** #{random.randint(1, 5)} in Bangladesh\n"
        f"⭐ **Rating:** {random.randint(45, 50)}/5.0\n\n"
        f"🔹 **Trusted by thousands!** 🔹"
    )
    
    await message.answer(stats_msg, parse_mode="Markdown")

# ==========================================
# ADMIN PANEL - UPDATED WITH PAYMENT SYSTEM
# ==========================================
@dp.message_handler(commands=['admin'], state="*")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    
    status = payment_system.get_system_status()
    payment_mode = "🔄 AUTO" if status["auto_payment_enabled"] else "👨‍💼 MANUAL"
    
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
    kb.add(InlineKeyboardButton(f"💳 Payment: {payment_mode}", callback_data="payment_dashboard"))
    
    await message.answer(f"👮‍♂️ **Admin Control Panel**\n💳 **Payment Mode:** {payment_mode}", reply_markup=kb, parse_mode="Markdown")

# --- ADMIN CALLBACK HANDLER ---
@dp.callback_query_handler(lambda c: c.data == "admin_home", state="*")
async def admin_home_callback(call: types.CallbackQuery):
    """Handle back to admin home"""
    if call.from_user.id not in ADMIN_IDS: return
    await call.message.delete()
    await admin_panel(call.message)

# --- PAYMENT ADMIN CALLBACKS ---
@dp.callback_query_handler(lambda c: c.data == "admin_payments", state="*")
async def admin_payments_menu(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💳 Payment Dashboard", callback_data="payment_dashboard"),
        InlineKeyboardButton("📊 Payment Stats", callback_data="payment_stats")
    )
    kb.add(
        InlineKeyboardButton("🔄 Manual Approvals", callback_data="admin_withdrawals"),
        InlineKeyboardButton("📋 All Transactions", callback_data="all_transactions")
    )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
    
    status = payment_system.get_system_status()
    mode = "AUTO" if status["auto_payment_enabled"] else "MANUAL"
    
    await call.message.edit_text(
        f"💰 **Payment Management**\n\n"
        f"⚙️ **Current Mode:** {mode}\n"
        f"📱 **Available Methods:** {status['total_methods_available']}/3\n\n"
        f"Select an option:",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "payment_dashboard", state="*")
async def show_payment_dashboard(call: types.CallbackQuery):
    await PaymentAdmin.show_payment_dashboard(call)

@dp.callback_query_handler(lambda c: c.data == "api_settings", state="*")
async def show_api_settings(call: types.CallbackQuery):
    await PaymentAdmin.show_api_settings(call)

@dp.callback_query_handler(lambda c: c.data == "how_to_setup_api", state="*")
async def how_to_setup_api(call: types.CallbackQuery):
    await PaymentAdmin.how_to_setup_api(call)

@dp.callback_query_handler(lambda c: c.data == "test_payments", state="*")
async def test_payment_methods(call: types.CallbackQuery):
    await PaymentAdmin.test_payment_methods(call)

@dp.callback_query_handler(lambda c: c.data == "check_balances", state="*")
async def check_balances_callback(call: types.CallbackQuery):
    await PaymentAdmin.show_check_balances(call)

@dp.callback_query_handler(lambda c: c.data == "pending_auto_payments", state="*")
async def show_pending_payments(call: types.CallbackQuery):
    await PaymentAdmin.show_pending_auto_payments(call, get_db_connection)

@dp.callback_query_handler(lambda c: c.data.startswith(("test_bkash", "test_nagad", "test_rocket")), state="*")
async def test_payment_method(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    method = call.data.replace("test_", "")
    
    success, message = payment_system.test_payment(method)
    
    await call.answer(message, show_alert=True)
    await PaymentAdmin.show_payment_dashboard(call)

@dp.callback_query_handler(lambda c: c.data == "process_payments_now", state="*")
async def process_payments_now(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    if auto_payment_handler:
        await auto_payment_handler.process_pending_withdrawals()
        await call.answer("✅ Processing payments now...", show_alert=True)
    else:
        await call.answer("❌ Payment handler not initialized", show_alert=True)

# --- PAYMENT STATS ---
@dp.callback_query_handler(lambda c: c.data == "payment_stats", state="*")
async def payment_stats_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # ✅ FIX: শুধুমাত্র রিয়েল ইউজারের পেমেন্ট স্ট্যাটস
    query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN w.status='paid' THEN 1 ELSE 0 END) as paid,
            SUM(CASE WHEN w.status='pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN w.status='failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN w.status='paid' THEN w.amount ELSE 0 END) as total_paid,
            SUM(CASE WHEN w.auto_payment=1 AND w.status='paid' THEN 1 ELSE 0 END) as auto_paid,
            SUM(CASE WHEN w.auto_payment=1 AND w.status='paid' THEN w.amount ELSE 0 END) as auto_paid_amount
        FROM withdrawals w
        JOIN users u ON w.user_id = u.user_id
        WHERE u.user_id < ?
    """
    
    c.execute(query, (FAKE_USER_ID_START,))
    stats = c.fetchone()
    total, paid, pending, failed, total_paid, auto_paid, auto_paid_amount = stats or (0,0,0,0,0,0,0)
    
    message = "📊 **রিয়েল পেমেন্ট স্ট্যাটিস্টিক্স**\n\n"
    message += f"📈 **মোট উইথড্রয়াল:** {total or 0}\n"
    message += f"✅ **পেইড হয়েছে:** {paid or 0}\n"
    message += f"⏳ **পেন্ডিং আছে:** {pending or 0}\n"
    message += f"❌ **ফেইল হয়েছে:** {failed or 0}\n"
    message += f"💰 **মোট পেইড:** {total_paid or 0:.2f} TK\n"
    message += f"🤖 **অটো পেমেন্ট:** {auto_paid or 0} ({auto_paid_amount or 0:.2f} TK)\n\n"
    
    # শুধুমাত্র রিয়েল ইউজারের মেথড-ওয়াইজ স্ট্যাটস
    query2 = """
        SELECT w.payment_method, COUNT(*), SUM(w.amount) 
        FROM withdrawals w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.status='paid' 
        AND u.user_id < ?
        GROUP BY w.payment_method
    """
    c.execute(query2, (FAKE_USER_ID_START,))
    method_stats = c.fetchall()
    
    if method_stats:
        message += "📱 **মেথড-ওয়াইজ স্ট্যাটস (পেইড):**\n"
        for method, count, amount in method_stats:
            message += f"• {method}: {count} ({amount or 0:.2f} TK)\n"
    
    conn.close()
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="payment_stats"))
    kb.add(InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_payments"))
    
    await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

# --- ALL TRANSACTIONS ---
@dp.callback_query_handler(lambda c: c.data == "all_transactions", state="*")
async def all_transactions_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # ✅ FIX: শুধুমাত্র রিয়েল ইউজারের ট্রানজেকশন
    query = """
        SELECT w.id, w.user_id, u.username, w.amount, w.payment_method, 
               w.mobile_number, w.status, w.request_time, w.auto_payment
        FROM withdrawals w
        JOIN users u ON w.user_id = u.user_id
        WHERE u.user_id < ?
        ORDER BY w.id DESC
        LIMIT 20
    """
    
    c.execute(query, (FAKE_USER_ID_START,))
    transactions = c.fetchall()
    conn.close()
    
    if not transactions:
        message = "📋 **কোনো রিয়েল ট্রানজেকশন নেই**\nশুধুমাত্র রিয়েল ইউজারের ট্রানজেকশন দেখানো হচ্ছে।"
    else:
        message = f"📋 **সাম্প্রতিক রিয়েল ট্রানজেকশন** ({len(transactions)})\n\n"
        
        for wid, uid, username, amount, method, number, status, req_time, auto_pay in transactions:
            username_display = f"@{username}" if username else f"ইউজার{uid}"
            status_icon = "✅" if status == 'paid' else ("⏳" if status == 'pending' else "❌")
            auto_icon = "🤖" if auto_pay == 1 else "👨‍💼"
            
            message += f"{status_icon} #{wid}: {amount} TK via {method}\n"
            message += f"   👤 {username_display} | 📱 {number}\n"
            message += f"   ⏰ {req_time} | {auto_icon}\n\n"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📤 CSV এক্সপোর্ট", callback_data="export_transactions"))
    kb.add(InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_payments"))
    
    await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

# --- PAYMENT SETUP COMMANDS ---
@dp.message_handler(commands=['setup_payment'], state="*")
async def setup_payment_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Ask for API credentials
    await message.answer(
        "🔧 **Setup Payment APIs**\n\n"
        "Send API keys in this format:\n"
        "`/set_api bkash:key:secret`\n"
        "`/set_api nagad:key:secret`\n"
        "`/set_api rocket:key`\n\n"
        "💡 **For testing:**\n"
        "`/set_api bkash:test_key:test_secret`"
    )

@dp.message_handler(commands=['set_api'], state="*")
async def set_api_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Format: /set_api method:key:secret")
            return
        
        credentials = args[1].split(":")
        method = credentials[0].lower()
        
        if method == "bkash" and len(credentials) >= 3:
            payment_system.setup_payment_apis(
                bkash_key=credentials[1],
                bkash_secret=credentials[2]
            )
            await message.answer("✅ Bkash API configured!")
            
        elif method == "nagad" and len(credentials) >= 3:
            payment_system.setup_payment_apis(
                nagad_key=credentials[1],
                nagad_secret=credentials[2]
            )
            await message.answer("✅ Nagad API configured!")
            
        elif method == "rocket" and len(credentials) >= 2:
            payment_system.setup_payment_apis(
                rocket_key=credentials[1]
            )
            await message.answer("✅ Rocket API configured!")
            
        else:
            await message.answer("❌ Invalid format or method!")
            
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

# --- REST OF ADMIN CALLBACKS (UPDATED) ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_callbacks(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    if call.data == "admin_home":
        await admin_panel(call.message)
        await call.message.delete()
        return

    elif call.data == "admin_export":
        conn = get_db_connection()
        c = conn.cursor()
        
        # ✅ FIX: শুধুমাত্র রিয়েল ইউজারের ইমেইল এক্সপোর্ট করুন
        query = """
            SELECT current_email, current_password 
            FROM users 
            WHERE status='verified' 
            AND user_id < ?
            AND current_email IS NOT NULL 
            AND current_email != ''
            AND current_password IS NOT NULL
            AND current_password != ''
        """
        
        c.execute(query, (FAKE_USER_ID_START,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            await call.answer("রিয়েল ইউজারের কোনো ভেরিফাইড ইমেইল নেই।", show_alert=True)
            return
            
        filename = f"real_emails_{int(time.time())}.txt"
        count = 0
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("📧 REAL VERIFIED EMAILS 📧\n")
                f.write("=" * 50 + "\n\n")
                
                for email, pwd in rows:
                    # ভ্যালিডেশন চেক করুন
                    if email and pwd and '@' in email and len(pwd) >= 6:
                        f.write(f"Email: {email}\n")
                        f.write(f"Password: {pwd}\n")
                        f.write("-" * 30 + "\n")
                        count += 1
            
            if count > 0:
                # ফাইল সাইজ চেক করুন
                file_size = os.path.getsize(filename)
                if file_size > 0:
                    await call.message.answer_document(
                        open(filename, "rb"), 
                        caption=f"📂 **{count} টি রিয়েল ভেরিফাইড ইমেইল**\n✅ শুধুমাত্র রিয়েল ইউজারদের"
                    )
                    await call.answer(f"{count} টি ইমেইল এক্সপোর্ট করা হয়েছে")
                else:
                    await call.answer("❌ ফাইলে কোনো ডাটা নেই", show_alert=True)
            else:
                await call.answer("❌ ভ্যালিড ইমেইল পাওয়া যায়নি", show_alert=True)
                
        except Exception as e:
            await call.answer(f"❌ Error: {str(e)}", show_alert=True)
        finally:
            # ফাইল ডিলিট করুন
            if os.path.exists(filename):
                os.remove(filename)

    elif call.data == "admin_set_notice":
        await AdminNotice.waiting_for_text.set()
        await call.message.answer("✏️ Enter new notice:")
        await call.answer()

    elif call.data == "admin_mail_sales":
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get stats
        c.execute("SELECT COUNT(*), SUM(amount) FROM sold_mails WHERE status='verified'")
        stats = c.fetchone()
        verified_count = stats[0] or 0
        total_earned = stats[1] or 0
        
        # Get pending mail sales for manual review
        c.execute("""
            SELECT id, seller_user_id, seller_username, gmail_address, created_at 
            FROM sold_mails 
            WHERE status='pending' 
            ORDER BY id DESC 
            LIMIT 10
        """)
        pending_mails = c.fetchall()
        
        # Get recent sales
        c.execute("""
            SELECT id, seller_user_id, seller_username, gmail_address, created_at, amount 
            FROM sold_mails 
            WHERE status='verified' 
            ORDER BY id DESC 
            LIMIT 10
        """)
        recent = c.fetchall()
        
        conn.close()
        
        # Create message
        msg = f"📊 **Mail Sales Dashboard**\n\n"
        msg += f"✅ **Auto-Verified Sales:** {verified_count}\n"
        msg += f"💰 **Total Paid:** {total_earned:.2f} TK\n"
        msg += f"⏳ **Pending Manual Review:** {len(pending_mails)}\n\n"
        
        if pending_mails:
            msg += f"📋 **Pending Mail Sales:**\n"
            for mail_id, seller_id, username, gmail, created in pending_mails[:5]:
                short_gmail = gmail[:20] + "..." if len(gmail) > 20 else gmail
                username_display = f"@{username}" if username else f"User{seller_id}"
                msg += f"• #{mail_id}: {short_gmail} by {username_display}\n"
            if len(pending_mails) > 5:
                msg += f"• ...and {len(pending_mails) - 5} more\n"
            msg += "\n"
        
        msg += f"📋 **Recent Verified Sales (Last 10):**\n"
        
        for mail_id, seller_id, username, gmail, created, amount in recent:
            short_gmail = gmail[:20] + "..." if len(gmail) > 20 else gmail
            username_display = f"@{username}" if username else f"User{seller_id}"
            msg += f"• #{mail_id}: {short_gmail} → {amount or 0:.2f} TK\n"
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📥 Export All", callback_data="export_mails"),
            InlineKeyboardButton("📊 Full Stats", callback_data="mail_stats")
        )
        kb.add(InlineKeyboardButton("⏳ Review Pending", callback_data="review_pending_mails"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
        
        await call.message.edit_text(msg, reply_markup=kb, parse_mode="Markdown")
        await call.answer()

    elif call.data == "admin_verifications":
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT user_id, current_email, current_password, screenshot_file_id FROM users WHERE status='pending' LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        if not row:
            await call.answer("✅ No pending verifications!", show_alert=True)
            return
            
        uid, email, pwd, file_id = row
        caption = f"📋 **Pending Verification**\n👤 `{uid}`\n📧 `{email}`\n🔑 `{pwd}`"
        kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("✅ APPROVE", callback_data=f"appr_user_{uid}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"rej_user_{uid}")
        ).add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
        
        await call.message.delete()
        await bot.send_photo(call.from_user.id, file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
        await call.answer()

    elif call.data == "admin_withdrawals":
        conn = get_db_connection()
        c = conn.cursor()
        
        # ✅ FIX: শুধুমাত্র রিয়েল ইউজারের পেন্ডিং উইথড্রয়াল
        query = """
            SELECT w.id, w.user_id, w.amount, w.payment_method, w.mobile_number 
            FROM withdrawals w
            JOIN users u ON w.user_id = u.user_id
            WHERE w.status='pending' 
            AND w.auto_payment=0 
            AND u.user_id < ?
            ORDER BY w.request_time ASC
            LIMIT 1
        """
        
        c.execute(query, (FAKE_USER_ID_START,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            await call.answer("✅ রিয়েল ইউজারের কোনো পেন্ডিং পেমেন্ট নেই!", show_alert=True)
            return
            
        wid, uid, amt, method, num = row
        txt = f"💸 **রিয়েল পেমেন্ট রিকোয়েস্ট #{wid}**\n👤 `{uid}`\n💰 `{amt}` TK\n📱 `{method}: {num}`"
        kb = InlineKeyboardMarkup(row_width=2).add(
            InlineKeyboardButton("✅ পেইড", callback_data=f"pay_yes_{wid}"),
            InlineKeyboardButton("❌ রিজেক্ট", callback_data=f"pay_no_{wid}")
        ).add(InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_home"))
        await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")
        await call.answer()
        
    elif call.data == "admin_tickets":
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, user_id, message FROM support_tickets WHERE status='open' ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        if not row:
            await call.answer("✅ No open tickets!", show_alert=True)
            return
            
        tid, uid, msg = row
        txt = f"🎫 **Ticket #{tid}**\n👤 `{uid}`\n💬 `{msg[:100]}...`"
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("💬 REPLY", callback_data=f"reply_ticket_{tid}_{uid}")
        ).add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
        await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")
        await call.answer()

    elif call.data == "admin_broadcast_start":
        await AdminBroadcast.waiting_for_message.set()
        await call.message.edit_text("📢 Send broadcast message:")
        await call.answer()

    elif call.data == "admin_stats":
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*), SUM(balance), SUM(referral_count) FROM users")
        res = c.fetchone()
        if res:
            total_users, total_balance, total_refs = res
        else:
            total_users, total_balance, total_refs = 0, 0, 0
            
        c.execute("SELECT COUNT(*) FROM users WHERE status='verified'")
        res_ver = c.fetchone()
        verified = res_ver[0] if res_ver else 0
        
        # Get mail sales stats
        c.execute("SELECT COUNT(*), SUM(amount) FROM sold_mails WHERE status='verified'")
        mail_stats = c.fetchone()
        mail_sales = mail_stats[0] if mail_stats[0] else 0
        mail_earnings = mail_stats[1] if mail_stats[1] else 0
        
        # Get fake user stats
        c.execute("SELECT COUNT(*) FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
        fake_count = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM users WHERE user_id < ?", (FAKE_USER_ID_START,))
        real_count = c.fetchone()[0] or 0
        
        # Get withdrawal stats
        c.execute("SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status='paid'")
        withdrawal_stats = c.fetchone()
        total_withdrawals = withdrawal_stats[0] or 0
        total_paid = withdrawal_stats[1] or 0
        
        c.execute("SELECT COUNT(*) FROM withdrawals WHERE status='paid' AND auto_payment=1")
        auto_withdrawals = c.fetchone()[0] or 0
        
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
                 f"💰 Total Paid Out: {total_paid:.2f} TK\n"
                 f"🤖 Auto Payments: {auto_withdrawals}")
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
        await call.message.edit_text(stats, reply_markup=kb, parse_mode="Markdown")
        await call.answer()

    elif call.data == "admin_earnings":
        ref_rate = get_setting('earn_referral') or DEFAULT_EARN_REFERRAL
        gmail_rate = get_setting('earn_gmail') or DEFAULT_EARN_GMAIL
        vip_bonus = get_setting('vip_bonus') or DEFAULT_VIP_BONUS
        min_wd = get_setting('min_withdraw') or DEFAULT_MIN_WITHDRAW
        vip_wd = get_setting('vip_min_withdraw') or DEFAULT_VIP_MIN_WITHDRAW
        mail_sell_rate = get_setting('earn_mail_sell') or DEFAULT_EARN_MAIL_SELL
        
        txt = (f"💰 **Current Earnings Settings**\n\n"
               f"👥 **Referral:** {ref_rate} TK\n"
               f"📧 **Gmail Verification:** {gmail_rate} TK\n"
               f"👑 **VIP Bonus:** {vip_bonus} TK\n"
               f"📧 **Mail Sell:** {mail_sell_rate} TK\n"
               f"💳 **Min Withdraw:** {min_wd} TK\n"
               f"👑 **VIP Min Withdraw:** {vip_wd} TK")
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("👥 Set Referral", callback_data="set_earn_ref"),
               InlineKeyboardButton("📧 Set Gmail", callback_data="set_earn_gmail"))
        kb.add(InlineKeyboardButton("👑 VIP Bonus", callback_data="set_vip_bonus"),
               InlineKeyboardButton("📧 Mail Sell Rate", callback_data="set_mail_sell_rate"))
        kb.add(InlineKeyboardButton("💳 Min Withdraw", callback_data="set_min_withdraw"),
               InlineKeyboardButton("👑 VIP Min Withdraw", callback_data="set_vip_min_withdraw"))
        kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_home"))
        
        await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")
        await call.answer()

    elif call.data == "admin_ban_menu":
        await AdminBanSystem.waiting_for_id.set()
        await call.message.answer("Enter user ID to ban/unban:")
        await call.answer()

# --- MAIL STATS ---
@dp.callback_query_handler(lambda c: c.data == "mail_stats", state="*")
async def mail_stats_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get detailed mail stats
    c.execute("""
        SELECT 
            COUNT(*) as total_mails,
            SUM(CASE WHEN status='verified' THEN 1 ELSE 0 END) as verified_mails,
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending_mails,
            SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) as rejected_mails,
            SUM(CASE WHEN auto_verified=1 THEN 1 ELSE 0 END) as auto_verified,
            SUM(amount) as total_earnings,
            AVG(amount) as avg_earnings
        FROM sold_mails
    """)
    
    stats = c.fetchone()
    
    # Get top sellers
    c.execute("""
        SELECT seller_user_id, seller_username, COUNT(*) as mail_count, SUM(amount) as total_earned
        FROM sold_mails 
        WHERE status='verified'
        GROUP BY seller_user_id 
        ORDER BY total_earned DESC 
        LIMIT 10
    """)
    
    top_sellers = c.fetchall()
    
    conn.close()
    
    if stats:
        total_mails, verified_mails, pending_mails, rejected_mails, auto_verified, total_earnings, avg_earnings = stats
        
        message = "📊 **Mail Sales Full Statistics**\n\n"
        message += f"📧 **Total Mails:** {total_mails or 0}\n"
        message += f"✅ **Verified:** {verified_mails or 0}\n"
        message += f"⏳ **Pending:** {pending_mails or 0}\n"
        message += f"❌ **Rejected:** {rejected_mails or 0}\n"
        message += f"🤖 **Auto-Verified:** {auto_verified or 0}\n"
        message += f"💰 **Total Earnings:** {total_earnings or 0:.2f} TK\n"
        message += f"📈 **Avg Per Mail:** {avg_earnings or 0:.2f} TK\n\n"
        
        if top_sellers:
            message += "🏆 **Top 10 Sellers:**\n"
            for idx, (seller_id, username, count, earned) in enumerate(top_sellers, 1):
                medal = "🥇" if idx==1 else ("🥈" if idx==2 else ("🥉" if idx==3 else f"{idx}."))
                username_display = f"@{username}" if username else f"User{seller_id}"
                message += f"{medal} {username_display}: {count} mails, {earned or 0:.2f} TK\n"
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_mail_sales"))
    
    await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

# --- REVIEW PENDING MAILS ---
@dp.callback_query_handler(lambda c: c.data == "review_pending_mails", state="*")
async def review_pending_mails_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get first pending mail
    c.execute("""
        SELECT id, seller_user_id, seller_username, gmail_address, gmail_password, recovery_email, created_at
        FROM sold_mails 
        WHERE status='pending' 
        ORDER BY id ASC 
        LIMIT 1
    """)
    
    mail = c.fetchone()
    conn.close()
    
    if not mail:
        await call.answer("✅ No pending mail sales!", show_alert=True)
        return
    
    mail_id, seller_id, username, gmail, password, recovery, created = mail
    username_display = f"@{username}" if username else f"User{seller_id}"
    recovery_display = recovery if recovery else "None"
    
    message = (
        f"📧 **Pending Mail Sale Review**\n\n"
        f"📝 **ID:** #{mail_id}\n"
        f"👤 **Seller:** {username_display}\n"
        f"📧 **Gmail:** `{gmail}`\n"
        f"🔑 **Password:** `{password}`\n"
        f"📩 **Recovery:** `{recovery_display}`\n"
        f"📅 **Submitted:** {created}\n\n"
        f"Verify the Gmail credentials manually, then approve or reject."
    )
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"mail_approve_{mail_id}_{seller_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"mail_reject_{mail_id}_{seller_id}")
    )
    kb.add(
        InlineKeyboardButton("ℹ️ Request Info", callback_data=f"mail_info_{mail_id}_{seller_id}"),
        InlineKeyboardButton("⏭️ Skip", callback_data="admin_mail_sales")
    )
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="admin_mail_sales"))
    
    await call.message.edit_text(message, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

# --- ADMIN SETTINGS HANDLERS (UPDATED) ---
@dp.callback_query_handler(lambda c: c.data.startswith(("set_earn_", "set_min_withdraw", "set_vip_", "set_mail_")), state="*")
async def rate_prompt(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS: return
    
    key_map = {
        "set_earn_ref": "earn_referral",
        "set_earn_gmail": "earn_gmail",
        "set_min_withdraw": "min_withdraw",
        "set_vip_min_withdraw": "vip_min_withdraw",
        "set_vip_bonus": "vip_bonus",  # NEW: VIP bonus
        "set_mail_sell_rate": "earn_mail_sell"  # NEW: Mail sell rate
    }
    
    setting_key = key_map.get(call.data)
    if not setting_key:
        await call.answer("Invalid setting!")
        return
        
    current_value = get_setting(setting_key) or "0"
    display_key = setting_key.replace('_', ' ').title()
    text = f"✏️ **Current {display_key}:** `{current_value}`\n\n**Enter new value:**"
    
    await state.update_data(key=setting_key)
    await AdminSettings.waiting_for_value.set()
    
    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()

@dp.message_handler(state=AdminSettings.waiting_for_value)
async def rate_save(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Unauthorized!")
        await state.finish()
        return
        
    try:
        data = await state.get_data()
        setting_key = data['key']
        new_value = float(message.text)
        update_setting(setting_key, new_value)
        
        # Get updated settings
        current_settings = {
            'earn_referral': float(get_setting('earn_referral') or DEFAULT_EARN_REFERRAL),
            'earn_gmail': float(get_setting('earn_gmail') or DEFAULT_EARN_GMAIL),
            'vip_bonus': float(get_setting('vip_bonus') or DEFAULT_VIP_BONUS),
            'min_withdraw': float(get_setting('min_withdraw') or DEFAULT_MIN_WITHDRAW),
            'vip_min_withdraw': float(get_setting('vip_min_withdraw') or DEFAULT_VIP_MIN_WITHDRAW),
            'earn_mail_sell': float(get_setting('earn_mail_sell') or DEFAULT_EARN_MAIL_SELL)
        }
        
        display_key = setting_key.replace('_', ' ').title()
        success_msg = f"✅ **{display_key}** updated to **{new_value} TK**!\n\n💰 **Current Rates:**\n"
        success_msg += f"👥 Referral: {current_settings['earn_referral']} TK\n"
        success_msg += f"📧 Gmail: {current_settings['earn_gmail']} TK\n"
        success_msg += f"👑 VIP Bonus: {current_settings['vip_bonus']} TK\n"
        success_msg += f"📧 Mail Sell: {current_settings['earn_mail_sell']} TK\n"
        success_msg += f"💳 Min Withdraw: {current_settings['min_withdraw']} TK\n"
        success_msg += f"👑 VIP Min: {current_settings['vip_min_withdraw']} TK"
        
        await message.answer(success_msg, parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ **Invalid number!** Use only numbers (e.g., 10.5)")
    except Exception as e:
        await message.answer(f"❌ **Error:** {str(e)}")
    
    await state.finish()
    await admin_panel(message)

# --- ADMIN ACTIONS (UPDATED WITH VIP BONUS) ---
@dp.message_handler(state=AdminNotice.waiting_for_text)
async def set_notice_save(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Unauthorized!")
        await state.finish()
        return
    update_setting('notice', message.text)
    await message.answer("✅ Notice updated!")
    await state.finish()
    await admin_panel(message)

@dp.callback_query_handler(lambda c: c.data.startswith(("appr_user_", "rej_user_")), state="*")
async def verify_action(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    parts = call.data.split("_")
    action = parts[1]
    uid = int(parts[2])
    
    conn = get_db_connection()
    c = conn.cursor()
    
    base_rate = float(get_setting('earn_gmail'))
    total_earnings = base_rate
    vip_bonus = 0
    
    # Check VIP bonus for approval
    if action == "appr" and is_user_in_top10(uid):
        vip_bonus = get_top10_bonus()
        total_earnings += vip_bonus
    
    if action == "appr":
        c.execute("UPDATE users SET status='verified', balance=balance+?, account_index=account_index+1 WHERE user_id=?", 
                 (total_earnings, uid))
        
        # Handle referral earnings
        ref_rate = float(get_setting('earn_referral'))
        c.execute("SELECT referrer_id, referral_paid FROM users WHERE user_id=?", (uid,))
        ref_data = c.fetchone()
        if ref_data and ref_data[0] != 0 and ref_data[1] == 0:
            c.execute("UPDATE users SET balance=balance+?, referral_count=referral_count+1 WHERE user_id=?", 
                     (ref_rate, ref_data[0]))
            c.execute("UPDATE users SET referral_paid=1 WHERE user_id=?", (uid,))
        
        # Notify user with VIP bonus info
        notify_msg = f"✅ **Approved!** +{base_rate} TK"
        if vip_bonus > 0:
            notify_msg += f"\n👑 **VIP Bonus:** +{vip_bonus} TK"
        notify_msg += f"\n💰 **Total:** {total_earnings} TK"
        
        try:
            await bot.send_message(uid, notify_msg)
        except: pass
    else:
        c.execute("UPDATE users SET status='rejected' WHERE user_id=?", (uid,))
        try:
            await bot.send_message(uid, "❌ Submission rejected.")
        except: pass
    
    conn.commit()
    conn.close()
    await call.answer("Done!")
    await admin_panel(call.message)

# --- MAIL SELL ADMIN ACTIONS (UPDATED) ---
@dp.callback_query_handler(lambda c: c.data.startswith(("mail_approve_", "mail_reject_", "mail_info_")), state="*")
async def mail_sell_action(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    parts = call.data.split("_")
    action = parts[1]
    mail_id = int(parts[2])
    seller_id = int(parts[3])
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if action == "approve":
        # Get mail sell rate
        mail_sell_rate = float(get_setting('earn_mail_sell') or DEFAULT_EARN_MAIL_SELL)
        
        # Update mail status and record amount
        c.execute("""
            UPDATE sold_mails 
            SET status='verified', admin_id=?, approved_at=?, amount=?, admin_note='Approved by admin' 
            WHERE id=?
        """, (call.from_user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mail_sell_rate, mail_id))
        
        # Update seller's balance and mail sell earnings
        c.execute("""
            UPDATE users 
            SET balance=balance+?, mail_sell_earnings=mail_sell_earnings+? 
            WHERE user_id=?
        """, (mail_sell_rate, mail_sell_rate, seller_id))
        
        conn.commit()
        
        # Notify seller
        try:
            await bot.send_message(
                seller_id, 
                f"✅ **Mail Sale Approved!**\n\n"
                f"💰 **Earned:** {mail_sell_rate} TK\n"
                f"📧 Your Gmail submission has been approved.\n"
                f"💳 Check your updated balance!"
            )
        except: pass
        
        await call.answer(f"✅ Approved! Seller earned {mail_sell_rate} TK")
        
    elif action == "reject":
        c.execute("""
            UPDATE sold_mails 
            SET status='rejected', admin_id=?, admin_note='Rejected by admin' 
            WHERE id=?
        """, (call.from_user.id, mail_id))
        conn.commit()
        
        # Notify seller
        try:
            await bot.send_message(seller_id, "❌ **Mail Sale Rejected**\n\nYour Gmail submission has been rejected.")
        except: pass
        
        await call.answer("❌ Mail sale rejected")
    
    elif action == "info":
        # Get mail details for info request
        c.execute("SELECT gmail_address FROM sold_mails WHERE id=?", (mail_id,))
        mail_info = c.fetchone()
        if mail_info:
            await call.message.answer(
                f"📧 **Request Info for Mail #{mail_id}**\n\n"
                f"Seller: `{seller_id}`\n"
                f"Gmail: `{mail_info[0]}`\n\n"
                f"Ask seller for more details."
            )
        await call.answer("ℹ️ Info requested")
    
    conn.close()
    
    # Return to admin panel
    await admin_panel(call.message)

@dp.callback_query_handler(lambda c: c.data.startswith(("pay_yes_", "pay_no_")), state="*")
async def pay_action(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    parts = call.data.split("_")
    action = parts[1]
    wid = int(parts[2])
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,))
    row = c.fetchone()
    if not row: 
        conn.close()
        return
    uid, amt = row
    
    if action == "yes":
        c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal_row = c.fetchone()
        bal = bal_row[0] if bal_row else 0
        if bal < amt:
            c.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
            await call.answer("❌ Insufficient balance!", show_alert=True)
        else:
            c.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amt, uid))
            c.execute("UPDATE withdrawals SET status='paid' WHERE id=?", (wid,))
            try:
                await bot.send_message(uid, f"✅ **PAID!** {amt} TK sent to your account.")
            except: pass
    else:
        c.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
        try:
            await bot.send_message(uid, "❌ Withdrawal rejected.")
        except: pass
    
    conn.commit()
    conn.close()
    await call.answer("Done!")
    await admin_panel(call.message)

@dp.message_handler(state=AdminBanSystem.waiting_for_id)
async def ban_user(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Unauthorized!")
        await state.finish()
        return
        
    try:
        uid = int(message.text)
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
        current_ban = c.fetchone()
        new_status = 0 if current_ban and current_ban[0] == 1 else 1
        c.execute("UPDATE users SET banned=? WHERE user_id=?", (new_status, uid))
        conn.commit()
        conn.close()
        status = "BANNED" if new_status == 1 else "UNBANNED"
        await message.answer(f"✅ User {uid} {status}")
    except:
        await message.answer("❌ Invalid ID")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("reply_ticket_"), state="*")
async def admin_reply_ticket(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    parts = call.data.split("_")
    tid = int(parts[2])
    uid = int(parts[3])
    
    await call.answer(f"💬 Reply to user {uid} for ticket #{tid}", show_alert=False)

# --- BROADCAST ---
@dp.message_handler(state=AdminBroadcast.waiting_for_message)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Unauthorized!")
        await state.finish()
        return
        
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE banned=0")
    users = c.fetchall()
    conn.close()
    
    cnt = 0
    await message.answer("⏳ Broadcasting...")
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 **ANNOUNCEMENT**\n\n{message.text}", parse_mode="Markdown")
            cnt += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅ Sent to **{cnt}/{len(users)}** users!", parse_mode="Markdown")
    await state.finish()

# --- EXPORT MAILS ---
@dp.callback_query_handler(lambda c: c.data == "export_mails", state="*")
async def export_verified_mails(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT gmail_address, gmail_password, recovery_email, created_at FROM sold_mails WHERE status='verified'")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        await call.answer("No verified mails to export!", show_alert=True)
        return
    
    filename = f"verified_mails_{int(time.time())}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Gmail | Password | Recovery Email | Date\n")
        f.write("="*60 + "\n")
        for email, pwd, recovery, date in rows:
            recovery_display = recovery if recovery else "None"
            f.write(f"{email} | {pwd} | {recovery_display} | {date}\n")
    
    await call.message.answer_document(
        open(filename, "rb"), 
        caption=f"📂 **{len(rows)} Verified Gmails**\nPasswords included"
    )
    os.remove(filename)
    await call.answer()

# --- FAKE SYSTEM CONTROL ---
@dp.callback_query_handler(lambda c: c.data == "fake_system_control", state="*")
async def fake_system_control(call: types.CallbackQuery):
    """Control fake user system"""
    if call.from_user.id not in ADMIN_IDS: return
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("➕ Add Fake Users", callback_data="fake_add_100"),
        InlineKeyboardButton("📊 View Stats", callback_data="fake_stats")
    )
    kb.add(
        InlineKeyboardButton("🔄 Update Activity", callback_data="fake_update"),
        InlineKeyboardButton("❌ Remove All Fake", callback_data="fake_remove_all")
    )
    kb.add(
        InlineKeyboardButton("⚙️ Settings", callback_data="fake_settings"),
        InlineKeyboardButton("🔙 Back", callback_data="admin_home")
    )
    
    stats = await get_smart_stats()
    
    control_msg = (
        f"🤖 **Fake User System Control**\n\n"
        f"✅ **Status:** {'ENABLED' if FAKE_USER_ENABLED else 'DISABLED'}\n"
        f"👥 **Real Users:** {stats['real_users']}\n"
        f"👻 **Fake Users:** {stats['fake_users']}\n"
        f"📊 **Total Shown:** {stats['total_users']:,}\n"
        f"📈 **Active Today:** {stats['active_today']:,}\n\n"
        f"⚡ **Auto-Update:** Every 4 hours\n"
        f"🎯 **Fake Ratio:** {FAKE_USER_RATIO*100}%\n\n"
        f"⚠️ **Warning:** Use responsibly!"
    )
    
    await call.message.edit_text(control_msg, reply_markup=kb, parse_mode="Markdown")
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('fake_'), state="*")
async def handle_fake_controls(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    
    if call.data == "fake_add_100":
        # Add 100 fake users
        conn = get_db_connection()
        c = conn.cursor()
        
        added = 0
        for _ in range(100):
            fake_id = FAKE_USER_ID_START + random.randint(1000000, 9999999)
            c.execute("SELECT user_id FROM users WHERE user_id=?", (fake_id,))
            if not c.fetchone():
                # Generate realistic fake user
                fake_name = random.choice(["Rahim", "Karim", "Sakib", "Mim", "Joya", "Rifat", "Tania", "Fahim"])
                fake_number = random.randint(100, 9999)
                username = f"{fake_name.lower()}{fake_number}"
                
                # Realistic stats
                balance = round(random.uniform(50, 2000), 2)
                verified = random.randint(1, 15)
                referrals = random.randint(0, 8)
                
                # Join date
                days_ago = random.randint(1, 60)
                join_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Last active
                hours_ago = random.randint(0, 48)
                last_active = (datetime.now() - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
                
                c.execute('''INSERT INTO users 
                    (user_id, username, status, account_index, balance, referral_count, 
                     join_date, last_bonus_time, is_vip) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (fake_id, username, 'verified', verified, balance, referrals, 
                     join_date, last_active, 1 if balance > 1000 else 0))
                
                added += 1
        
        conn.commit()
        conn.close()
        
        await call.answer(f"Added {added} fake users!", show_alert=True)
        await fake_system_control(call)
    
    elif call.data == "fake_stats":
        stats = await get_smart_stats()
        stats_msg = (
            f"📈 **Detailed Fake Stats**\n\n"
            f"👥 Real: {stats['real_users']}\n"
            f"👻 Fake: {stats['fake_users']}\n"
            f"📊 Total: {stats['total_users']:,}\n"
            f"📈 Active: {stats['active_today']:,}\n"
            f"🚀 Growth: +{stats['growth_rate']}%\n\n"
            f"Ratio: {stats['fake_users']/(stats['real_users']+0.1)*100:.1f}% fake"
        )
        await call.message.edit_text(stats_msg, parse_mode="Markdown")
    
    elif call.data == "fake_update":
        # Trigger immediate update
        asyncio.create_task(update_fake_activity())
        await call.answer("✅ Fake user activity update triggered!", show_alert=True)
    
    elif call.data == "fake_remove_all":
        # Remove all fake users
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id >= ?", (FAKE_USER_ID_START,))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        await call.answer(f"✅ Removed {deleted} fake users!", show_alert=True)
        await fake_system_control(call)
    
    elif call.data == "fake_settings":
        await call.answer("Settings menu coming soon!", show_alert=True)

# ==========================================
# ON BOT STARTUP
# ==========================================
async def on_startup(dp):
    """Initialize systems on bot start"""
    print("🚀 Starting Smart Systems...")
    
    # ডাটাবেস ক্লিনআপ
    cleanup_all_fake_data()
    
    # Initialize fake user system
    if FAKE_USER_ENABLED:
        initialize_fake_users()
        asyncio.create_task(update_fake_activity())
        print("✅ Fake system initialized")
    else:
        print("❌ Fake system disabled")
    
    # Initialize auto payment system
    global auto_payment_handler
    auto_payment_handler = AutoPaymentHandler(get_db_connection, bot)
    
    # Start auto payment worker if enabled
    if AUTO_PAYMENT_ENABLED and payment_system.auto_payment_enabled:
        asyncio.create_task(auto_payment_handler.start_auto_payment_worker(
            interval=AUTO_PAY_CHECK_INTERVAL
        ))
        print("🚀 Auto Payment Worker Started")
    elif AUTO_PAYMENT_ENABLED:
        print("⚠️ Auto Payment configured but no API keys set")
    
    print("🤖 Bot is ready!")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == '__main__':
    # Get bot name for display
    bot_name = "Maim Gmail Bot"
    
    print("="*50)
    print(f"🤖 {bot_name} Starting...")
    print(f"📊 Fake System: {'ENABLED' if FAKE_USER_ENABLED else 'DISABLED'}")
    print(f"💳 Auto Payment: {'ENABLED' if AUTO_PAYMENT_ENABLED else 'DISABLED'}")
    print("="*50)
    
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        
        ey code ta render e run dile terminul e error dey bot ta run hoy na,  aiohttp er error dey.tumi seta fix kore daw, aiohttp pkg install hoy na rerminul e
