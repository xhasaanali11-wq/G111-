import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8209173464:AAEmsTpmkXjOn6nb7M6AQsE7hikGIg3Yq-k"

async def auto_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Match: 2 BTC / 10 eth / 5 pepe
    match = re.match(r"(\d+\.?\d*)\s*([a-zA-Z0-9]+)", text)

    if not match:
        return

    quantity = float(match.group(1))
    symbol = match.group(2).lower()

    try:
        # Step 1: Search coin ID from symbol
        search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        search_data = requests.get(search_url).json()

        if not search_data["coins"]:
            return

        # Find exact symbol match
        coin_id = None
        for coin in search_data["coins"]:
            if coin["symbol"].lower() == symbol:
                coin_id = coin["id"]
                break

        if not coin_id:
            coin_id = search_data["coins"][0]["id"]

        # Step 2: Get price
        price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        price_data = requests.get(price_url).json()

        if coin_id not in price_data:
            return

        price = price_data[coin_id]["usd"]
        total = price * quantity

        await update.message.reply_text(
            f"🪙 Coin: {symbol.upper()}\n"
            f"💲 Price: ${price}\n"
            f"📦 Quantity: {quantity}\n"
            f"🧮 Total Value: ${total}"
        )

    except:
        pass

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_price))

app.run_polling()
