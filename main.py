import os
import asyncio
import requests
import nest_asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import logging

# Fix async di Replit
nest_asyncio.apply()

app = Flask(__name__)
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class NexusMonitor:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
        self.CHAT_ID = os.environ['CHAT_ID']

        # Inisialisasi Application
        self.application = ApplicationBuilder().token(self.TELEGRAM_TOKEN).post_init(self.on_init).build()

        # Tambahkan command handler
        self.application.add_handler(CommandHandler("hello", self.hello_command))

        self.wallets = {
            "0xE58d5905b86e38A1bfC453225815d6f4C194b721": "hunterairdrop200@gmail.com",
            "0x2d33966F295DBFe12103c431851D17A563FF99fE": "barudakteabager@gmail.com",
            "0x33EA404D04185ff937460F0491c6D29B893254F1": "karujangbagerchel@gmail.com"
        }

        self.last_balance = {}

    async def on_init(self, application):
        """Callback saat bot siap"""
        await application.bot.send_message(
            chat_id=self.CHAT_ID,
            text="🤖 Bot Nexus Monitor Aktif!\n"
                 "✅ Siap memantunjan wallet\n"
                 "🚀 Gunakan /hello untuk cek status"
        )

    async def hello_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk command /hello"""
        await update.message.reply_text("🟢 Saya aktif dan berjalan!")

    async def check_balance(self):
        for address, email in self.wallets.items():
            try:
                url = f"https://explorer.nexus.xyz/api/v2/addresses/{address}"
                response = requests.get(url, headers={'accept': 'application/json'}, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    current_balance = float(data["coin_balance"]) / 1e18
                    block_number = data["block_number_balance_updated_at"]

                    message = (
                        f"Akun {email}\n"
                        f"{address}\n"
                        f"Block Number: {block_number}\n"
                        f"Coin Balance: {current_balance:.2f}"
                    )

                    if address in self.last_balance:
                        increase = current_balance - self.last_balance[address]['balance']
                        if increase > 0:
                            message += f"\nTambah {increase:.2f} koin"

                    if address not in self.last_balance or message != self.last_balance[address].get('message'):
                        await self.send_alert(message)
                        self.last_balance[address] = {
                            "balance": current_balance,
                            "message": message
                        }

            except Exception as e:
                logging.error(f"Error: {str(e)}")

    async def send_alert(self, message: str):
        await self.application.bot.send_message(
            chat_id=str(self.CHAT_ID),
            text=message
        )

    async def run(self):
        """Jalankan semua task"""
        await asyncio.gather(
            self.application.run_polling(),
            self.check_balance_loop()
        )

    async def check_balance_loop(self):
        """Loop pengecekan balance"""
        while True:
            await self.check_balance()
            await asyncio.sleep(60)

def keep_alive():
    monitor = NexusMonitor()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(monitor.run())
    except Exception as e:
        logging.error(f"Error utama: {str(e)}")
    finally:
        loop.close()

@app.route('/')
def home():
    return "Nexus Monitor Active ✅"

if __name__ == "__main__":
    Thread(target=keep_alive).start()
    app.run(host='0.0.0.0', port=8080)