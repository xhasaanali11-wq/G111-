from telethon import TelegramClient, events
import re
import requests
import logging
from datetime import datetime

# लॉगिंग सेटअप
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# कॉन्फ़िगरेशन
API_ID = '7823667'  # https://my.telegram.org से लें
API_HASH = '178e54c6c8dbe5d8543fb06ead54da45'
BOT_TOKEN = '8209173464:AAEmsTpmkXjOn6nb7M6AQsE7hikGIg3Yq-k'

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """स्वागत संदेश"""
    welcome_msg = """
🚀 **क्रिप्टो प्राइस बॉट में आपका स्वागत है!**

मैं आपको क्रिप्टोकरेंसी की लाइव कीमत बताता हूँ।

📝 **कैसे इस्तेमाल करें:**
बस सिक्के का सिंबल और मात्रा लिखें:
• `2 BTC`
• `10 eth`
• `5 pepe`
• `2.5 bnb`

🔍 **उदाहरण:**
`0.5 btc` - 0.5 BTC की कीमत
`100 doge` - 100 DOGE की कीमत

💡 **सपोर्टेड सिक्के:**
BTC, ETH, BNB, SOL, XRP, DOGE, PEPE, SHIB, ADA, DOT, MATIC, और 10000+ अन्य

⚡️ अभी ट्राई करें - सिंबल और मात्रा लिखें!
"""
    await event.reply(welcome_msg, parse_mode='md')
    logger.info(f"Start command from user {event.sender_id}")

@bot.on(events.NewMessage)
async def auto_price(event):
    """क्रिप्टो प्राइस चेकर"""
    # सिर्फ टेक्स्ट मैसेज प्रोसेस करें, कमांड इग्नोर करें
    if event.text.startswith('/'):
        return
    
    text = event.text.strip()
    logger.info(f"Message received: {text} from user {event.sender_id}")

    # पैटर्न: 2 BTC, 10eth, 5 pepe, 2.5 btc/ आदि
    match = re.match(r"^(\d+\.?\d*)\s*([a-zA-Z0-9]+)", text)
    
    if not match:
        logger.debug("Pattern not matched")
        return

    quantity = float(match.group(1))
    symbol = match.group(2).lower()
    
    logger.info(f"Matched: {quantity} {symbol}")

    # टाइपिंग इंडिकेटर दिखाएं
    async with event.client.action(event.chat_id, 'typing'):
        try:
            # Step 1: सिक्के का ID सर्च करें
            search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"CoinGecko API error: {response.status_code}")
                await event.reply("⚠️ CoinGecko API से कनेक्ट नहीं हो पाया। कृपया बाद में कोशिश करें।")
                return
            
            search_data = response.json()

            if not search_data.get("coins"):
                logger.warning(f"No coins found for symbol: {symbol}")
                await event.reply(f"❌ '{symbol.upper()}' सिंबल नहीं मिला।")
                return

            # एक्ट सिंबल मैच खोजें
            coin_id = None
            coin_name = None
            
            for coin in search_data["coins"]:
                if coin["symbol"].lower() == symbol:
                    coin_id = coin["id"]
                    coin_name = coin["name"]
                    break

            # अगर एक्ट सिंबल नहीं मिला, पहला रिजल्ट इस्तेमाल करें
            if not coin_id:
                coin_id = search_data["coins"][0]["id"]
                coin_name = search_data["coins"][0]["name"]
                logger.info(f"Exact symbol not found, using first match: {coin_id}")

            # Step 2: कीमत प्राप्त करें
            price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(price_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Price API error: {response.status_code}")
                await event.reply("⚠️ कीमत प्राप्त करने में समस्या।")
                return
            
            price_data = response.json()

            if coin_id not in price_data:
                logger.warning(f"Price not found for coin_id: {coin_id}")
                await event.reply(f"❌ {symbol.upper()} की कीमत नहीं मिली।")
                return

            price = price_data[coin_id]["usd"]
            total = price * quantity
            
            # नंबरों को फॉर्मेट करें
            if price < 0.01:
                price_str = f"${price:.8f}"
                total_str = f"${total:.8f}"
            elif price < 1:
                price_str = f"${price:.6f}"
                total_str = f"${total:.6f}"
            else:
                price_str = f"${price:,.2f}"
                total_str = f"${total:,.2f}"

            # टाइमस्टैम्प
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            message = (
                f"💰 **{coin_name} ({symbol.upper()})**\n"
                f"📊 **मात्रा:** {quantity}\n"
                f"💵 **प्रति सिक्का:** {price_str}\n"
                f"🧮 **कुल मूल्य:** {total_str}\n"
                f"⏱️ अपडेट: {timestamp}"
            )
            
            await event.reply(message, parse_mode='md')
            logger.info(f"Successfully replied for {quantity} {symbol}")

        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            await event.reply("⏱️ रिक्वेस्ट टाइमआउट। कृपया बाद में कोशिश करें।")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            await event.reply("🌐 नेटवर्क त्रुटि। कृपया बाद में कोशिश करें।")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await event.reply("❌ अप्रत्याशित त्रुटि। कृपया बाद में कोशिश करें।")

async def main():
    """बॉट स्टार्ट करें"""
    logger.info("Bot starting...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # इवेंट लूप में बॉट चलाएं
    with bot:
        bot.loop.run_until_complete(main())
