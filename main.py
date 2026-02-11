import re
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# लॉगिंग सेटअप
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8209173464:AAEmsTpmkXjOn6nb7M6AQsE7hikGIg3Yq-k"

async def auto_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    logger.info(f"Message received: {text} from user {update.effective_user.id}")

    # बेहतर पैटर्न: 2 BTC, 10eth, 5 pepe, 2.5 btc/ आदि
    match = re.match(r"^(\d+\.?\d*)\s*([a-zA-Z0-9]+)", text)
    
    if not match:
        logger.debug("Pattern not matched")
        return

    quantity = float(match.group(1))
    symbol = match.group(2).lower()
    
    logger.info(f"Matched: {quantity} {symbol}")

    try:
        # Step 1: Search coin ID from symbol
        search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        response = requests.get(search_url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"CoinGecko API error: {response.status_code}")
            await update.message.reply_text("⚠️ CoinGecko API से कनेक्ट नहीं हो पाया। कृपया बाद में कोशिश करें।")
            return
        
        search_data = response.json()

        if not search_data.get("coins"):
            logger.warning(f"No coins found for symbol: {symbol}")
            await update.message.reply_text(f"❌ '{symbol.upper()}' सिंबल नहीं मिला।")
            return

        # Find exact symbol match
        coin_id = None
        coin_name = None
        
        for coin in search_data["coins"]:
            if coin["symbol"].lower() == symbol:
                coin_id = coin["id"]
                coin_name = coin["name"]
                break

        # If exact symbol not found, use first result
        if not coin_id:
            coin_id = search_data["coins"][0]["id"]
            coin_name = search_data["coins"][0]["name"]
            logger.info(f"Exact symbol not found, using first match: {coin_id}")

        # Step 2: Get price
        price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(price_url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Price API error: {response.status_code}")
            await update.message.reply_text("⚠️ कीमत प्राप्त करने में समस्या।")
            return
        
        price_data = response.json()

        if coin_id not in price_data:
            logger.warning(f"Price not found for coin_id: {coin_id}")
            await update.message.reply_text(f"❌ {symbol.upper()} की कीमत नहीं मिली।")
            return

        price = price_data[coin_id]["usd"]
        total = price * quantity
        
        # Format numbers nicely
        if price < 0.01:
            price_str = f"${price:.8f}"
            total_str = f"${total:.8f}"
        elif price < 1:
            price_str = f"${price:.6f}"
            total_str = f"${total:.6f}"
        else:
            price_str = f"${price:,.2f}"
            total_str = f"${total:,.2f}"

        message = (
            f"💰 *{coin_name} ({symbol.upper()})*\n"
            f"📊 मात्रा: {quantity}\n"
            f"💵 प्रति सिक्का: {price_str}\n"
            f"🧮 कुल मूल्य: {total_str}"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Successfully replied for {quantity} {symbol}")

    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        await update.message.reply_text("⏱️ रिक्वेस्ट टाइमआउट। कृपया बाद में कोशिश करें।")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await update.message.reply_text("🌐 नेटवर्क त्रुटि। कृपया बाद में कोशिश करें।")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("❌ अप्रत्याशित त्रुटि। कृपया बाद में कोशिश करें।")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_price))
    
    logger.info("Bot starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
