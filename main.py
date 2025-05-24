import logging
import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os

API_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_states = {}
coin_selection_states = {}

class UltimateCoinFinder:
    def __init__(self):
        self.session = None
        self.base_url = "https://api.coingecko.com/api/v3"

    async def get_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def search_coin_multiple(self, query: str):
        try:
            session = await self.get_session()
            async with session.get(f"{self.base_url}/search?query={query}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('coins', [])
        except Exception as e:
            logger.error(f"Error searching for coins: {e}")
        return []

    async def get_coin_data(self, coin_id: str):
        try:
            session = await self.get_session()
            async with session.get(f"{self.base_url}/coins/{coin_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Error fetching coin data for {coin_id}: {e}")
        return None

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

finder = UltimateCoinFinder()

async def start_handler(message: types.Message):
    await message.reply("Welcome to the Bull Market Predictor Bot!\nUse /predict <coin name or symbol> to start.") 


async def predict_handler(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: /predict <coin>")
        return

    query = parts[1].strip()
    matches = await finder.search_coin_multiple(query)

    if not matches:
        await message.reply("❌ No coins found. Try another name or symbol.")
        return

    top_matches = matches[:3]
    coin_selection_states[user_id] = top_matches

reply_text = "🔍 Multiple matches found. Reply with a number:\n\n"
for i, coin in enumerate(top_matches, start=1):
    reply_text += f"{i}. {coin['name']} ({coin['symbol'].upper()}) — Rank: #{coin.get('market_cap_rank', 'N/A')}\n"
await message.reply(reply_text)


async def handle_coin_selection(message: types.Message):
    user_id = message.from_user.id

    if user_id not in coin_selection_states:
                await message.reply(
            f"🎯 {selected_coin['name']} ({selected_coin['symbol'].upper()}) PREDICTION\n\n"
            f"📊 Current Data:\n"
            f"• Current Price: ${current:.4f}\n"
            f"• All-Time High: ${ath:.2f}\n"
            f"• Market Rank: #{rank}\n\n"
            f"🧮 Calculation:\n"
            f"• Sentiment: {sentiment:.3f}\n"
            f"• Strength (default): {strength:.1f}\n\n"
            f"🚀 BULL MARKET PREDICTION:\n"
            f"• Target Price: ${bmp:.2f}\n"
            f"• Potential ROI: {roi:.1f}x ({roi_percent:.0f}% gain)\n\n"
            f"📈 Assessment: {assessment}\n\n"
            f"⚠️ This is not financial advice. Always do your own research before investing.",
            parse_mode='Markdown'
        )
        market_data = coin_data['market_data']
        current = market_data['current_price']['usd']
        ath = market_data['ath']['usd']
        change_24h = market_data.get('price_change_percentage_24h', 0)
        rank = coin_data.get('market_cap_rank', 'N/A')

        sentiment = 0.5
        if change_24h > 15:
            sentiment = 0.9
        elif change_24h > 5:
            sentiment = 0.7
        elif change_24h > 0:
            sentiment = 0.6
        elif change_24h > -5:
            sentiment = 0.4
        else:
            sentiment = 0.2

        ath_distance = current / ath if ath > 0 else 0
        if ath_distance > 0.8:
            sentiment = max(sentiment, 0.8)
        elif ath_distance > 0.5:
            sentiment = max(sentiment, 0.6)
        elif ath_distance > 0.2:
            sentiment = max(sentiment, 0.5)

        strength = 1.5
        bmp = ath * sentiment * strength
        roi = bmp / current
        roi_percent = (roi - 1) * 100

        if roi >= 100:
            assessment = "🚀 MOONSHOT POTENTIAL"
        elif roi >= 50:
            assessment = "🌟 EXTREME UPSIDE"
        elif roi >= 20:
            assessment = "📈 VERY BULLISH"
        elif roi >= 10:
            assessment = "💪 STRONG UPSIDE"
        elif roi >= 5:
            assessment = "📊 MODERATE UPSIDE"
        elif roi >= 2:
            assessment = "📉 LIMITED UPSIDE"
        else:
            assessment = "⚠️ BEARISH OUTLOOK"

       await message.reply(
    f"🎯 {selected_coin['name']} ({selected_coin['symbol'].upper()}) PREDICTION\n\n"
    f"📊 Current Data:\n"
    f"• Current Price: ${current:.4f}\n"
    f"• All-Time High: ${ath:.2f}\n"
    f"• Market Rank: #{rank}\n\n"
    f"🧮 Calculation:\n"
    f"• Sentiment: {sentiment:.3f}\n"
    f"• Strength (default): {strength:.1f}\n\n"
    f"🚀 BULL MARKET PREDICTION:\n"
    f"• Target Price: ${bmp:.2f}\n"
    f"• Potential ROI: {roi:.1f}x ({roi_percent:.0f}% gain)\n\n"
    f"📈 Assessment: {assessment}\n\n"
    f"⚠️ This is not financial advice. Always do your own research before investing.",
    parse_mode='Markdown'
)
         await message.reply(
    f"🎯 {selected_coin['name']} ({selected_coin['symbol'].upper()}) PREDICTION\\n\\n"
    f"📊 Current Data:\\n"
    f"• Current Price: ${current:.4f}\\n"
    f"• All-Time High: ${ath:.2f}\\n"
    f"• Market Rank: #{rank}\\n\\n"
    f"🧮 Calculation:\\n"
    f"• Sentiment: {sentiment:.3f}\\n"
    f"• Strength (default): {strength:.1f}\\n\\n"
    f"🚀 BULL MARKET PREDICTION:\\n"
    f"• Target Price: ${bmp:.2f}\\n"
    f"• Potential ROI: {roi:.1f}x ({roi_percent:.0f}% gain)\\n\\n"
    f"📈 Assessment: {assessment}\\n\\n"
    f"⚠️ This is not financial advice. Always do your own research before investing.",
    parse_mode='Markdown'
)


    except Exception as e:
        logger.error(f"Error during coin selection or prediction: {e}")
        await message.reply("❌ Invalid input or error occurred. Try /predict again.")

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.message.register(start_handler, Command("start"))
    dp.message.register(predict_handler, Command("predict"))
    dp.message.register(handle_coin_selection)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
