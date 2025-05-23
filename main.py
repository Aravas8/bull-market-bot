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
coins_cache = {}
cache_timestamp = 0

class UltimateCoinFinder:
    def __init__(self):
        self.session = None
        self.base_url = "https://api.coingecko.com/api/v3"

    async def get_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def search_coin(self, query: str):
        try:
            session = await self.get_session()
            search_url = f"{self.base_url}/search?query={query}"
            async with session.get(search_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    coins = data.get('coins', [])
                    if coins:
                        best_match = coins[0]
                        return {
                            'found': True,
                            'coin_id': best_match['id'],
                            'name': best_match['name'],
                            'symbol': best_match['symbol'],
                            'rank': best_match.get('market_cap_rank', 999)
                        }
            async with session.get(f"{self.base_url}/coins/{query.lower()}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'found': True,
                        'coin_id': data['id'],
                        'name': data['name'],
                        'symbol': data['symbol'],
                        'rank': data.get('market_cap_rank', 999)
                    }
            return {'found': False, 'error': f'No cryptocurrency found for "{query}"'}
        except Exception as e:
            logger.error(f"Search error for {query}: {e}")
            return {'found': False, 'error': 'Search temporarily unavailable'}

    async def get_coin_data(self, coin_id: str):
        try:
            session = await self.get_session()
            url = f"{self.base_url}/coins/{coin_id}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error(f"Data fetch error for {coin_id}: {e}")
            return None

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

finder = UltimateCoinFinder()

async def start_handler(message: types.Message):
    await message.reply("Welcome to the Bull Market Predictor Bot! Use /predict <coin> to begin.")

async def predict_handler(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("Usage: /predict <coin>")
            return

        search_query = parts[1]
        search_result = await finder.search_coin(search_query)
        if not search_result['found']:
            await message.reply(search_result['error'])
            return

        coin_id = search_result['coin_id']
        coin_data = await finder.get_coin_data(coin_id)
        if not coin_data:
            await message.reply("Error fetching data.")
            return

        market_data = coin_data['market_data']
        current = market_data['current_price']['usd']
        ath = market_data['ath']['usd']
        change_24h = market_data.get('price_change_percentage_24h', 0)

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

        user_states[message.from_user.id] = {
            'coin_id': coin_id,
            'coin_name': search_result['name'],
            'current': current,
            'ath': ath,
            'sentiment': sentiment
        }

        await message.reply(
            f"{search_result['name']} (ATH: ${ath}, Current: ${current})\n"
            f"Estimated sentiment: {sentiment:.2f}\n"
            "Now, send me the cycle strength factor (e.g., 1.5)"
        )
    except Exception as e:
        logger.error(f"Error in predict: {e}")
        await message.reply("Unexpected error occurred.")

async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        await message.reply("Please use /predict <coin> first.")
        return

    try:
        strength = float(message.text.strip())
        data = user_states.pop(user_id)
        bmp = data['ath'] * data['sentiment'] * strength
        roi = bmp / data['current']

        await message.reply(
            f"{data['coin_name']} Bull Market Prediction:\n"
            f"Target Price: ${bmp:.4f}\n"
            f"Potential ROI: {roi:.2f}x"
        )
    except Exception as e:
        logger.error(f"Error calculating BMP: {e}")
        await message.reply("Invalid input. Please enter a valid number.")

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.message.register(start_handler, Command('start'))
    dp.message.register(predict_handler, Command('predict'))
    dp.message.register(handle_message)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
