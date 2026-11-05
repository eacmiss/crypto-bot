import os
import asyncio
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

COINGECKO_API = "https://api.coingecko.com/api/v3"
OPENSEA_API = "https://api.opensea.io/api/v2"
ETH_RPC = "https://eth.llamarpc.com"

MAIN_TEXT = (
    "🚀 Крипто/NFT инфо-бот\n\n"
    "Получай мгновенную информацию о:\n"
    "• Курсах токенов\n"
    "• Статистике NFT-коллекций\n"
    "• Ценах газа\n\n"
    "Выбери опцию ниже или введи символ токена (например, BTC, ETH):"
)


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Курс токена", callback_data="token_price")],
        [InlineKeyboardButton("🖼️ NFT-коллекция", callback_data="nft_collection")],
        [InlineKeyboardButton("⛽ Цены газа", callback_data="gas_prices")],
        [InlineKeyboardButton("📊 Топ токенов", callback_data="top_tokens")]
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_main")]
    ])


async def start(update, context):
    """Обработка команды /start"""
    await update.message.reply_text(MAIN_TEXT, reply_markup=main_keyboard())


async def token_price_menu(update, context):
    """Меню курса токена"""
    await update.callback_query.edit_message_text(
        "💰 Курс токена\n\n"
        "Введи символ токена (например, BTC, ETH, SOL), чтобы узнать цену.\n\n"
        "Примеры:\n"
        "• BTC — Bitcoin\n"
        "• ETH — Ethereum\n"
        "• SOL — Solana\n"
        "• MATIC — Polygon",
        reply_markup=back_keyboard()
    )


async def nft_collection_menu(update, context):
    """Меню NFT-коллекции"""
    await update.callback_query.edit_message_text(
        "🖼️ Инфо о NFT-коллекции\n\n"
        "Введи название или slug NFT-коллекции, чтобы получить статистику.\n\n"
        "Примеры:\n"
        "• bored-ape-yacht-club\n"
        "• azuki\n"
        "• doodles-official\n"
        "• moonbirds",
        reply_markup=back_keyboard()
    )


async def get_gas_prices(update, context):
    """Получить текущие цены газа"""
    query = update.callback_query

    try:
        def fetch_gas():
            rpc = requests.post(
                ETH_RPC,
                json={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1},
                timeout=10,
            ).json()
            gas_wei = int(rpc["result"], 16)
            price = requests.get(
                f"{COINGECKO_API}/simple/price?ids=ethereum&vs_currencies=usd",
                timeout=10,
            ).json()
            return gas_wei, price["ethereum"]["usd"]

        gas_wei, eth_usd = await asyncio.to_thread(fetch_gas)
        gas_gwei = gas_wei / 1e9
        transfer_eth = gas_wei * 21000 / 1e18

        gas_text = "⛽ Текущая цена газа\n\n"
        gas_text += f"⚡ {gas_gwei:.1f} gwei\n\n"
        gas_text += "💰 Примерная стоимость перевода ETH (21,000 gas):\n"
        gas_text += f"• {transfer_eth:.6f} ETH (~${transfer_eth * eth_usd:.2f})"
    except Exception:
        gas_text = "⚠️ Не удалось получить цены газа. Попробуй позже."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data="gas_prices")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_main")]
    ])

    await query.edit_message_text(gas_text, reply_markup=keyboard)


async def get_top_tokens(update, context):
    """Топ токенов по капитализации"""
    query = update.callback_query

    try:
        response = await asyncio.to_thread(
            requests.get,
            f"{COINGECKO_API}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false",
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()

            text = "📊 Топ-10 криптовалют\n\n"
            for i, coin in enumerate(data, 1):
                change_24h = coin.get('price_change_percentage_24h', 0)
                emoji = "📈" if change_24h >= 0 else "📉"
                text += f"{i}. {coin['symbol'].upper()} — ${coin['current_price']:,.2f}\n"
                text += f"   {emoji} {change_24h:.2f}% (24ч)\n\n"
        else:
            text = "⚠️ Не удалось получить данные о токенах. Попробуй позже."
    except Exception as e:
        text = f"⚠️ Ошибка при получении токенов: {str(e)}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data="top_tokens")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_main")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard)


def _format_coin(coin):
    change_24h = coin.get('price_change_percentage_24h', 0)
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0)
    emoji_24h = "📈" if change_24h >= 0 else "📉"
    emoji_7d = "📈" if change_7d >= 0 else "📉"

    text = f"💰 {coin['name']} ({coin['symbol'].upper()})\n\n"
    text += f"💵 Цена: ${coin['current_price']:,.2f}\n\n"
    text += f"📊 Капитализация: ${coin['market_cap']:,.0f}\n"
    text += f"📊 Объём 24ч: ${coin['total_volume']:,.0f}\n\n"
    text += f"📈 Изменение 24ч: {emoji_24h} {change_24h:.2f}%\n"
    text += f"📈 Изменение 7д: {emoji_7d} {change_7d:.2f}%\n\n"
    text += f"🏆 Ранг: #{coin['market_cap_rank'] or 'N/A'}"
    return text


async def handle_token_lookup(update, context):
    """Поиск курса токена"""
    token_symbol = update.message.text.upper().strip()

    try:
        response = await asyncio.to_thread(
            requests.get,
            f"{COINGECKO_API}/coins/markets?vs_currency=usd&ids={token_symbol.lower()}",
            timeout=10,
        )

        text = None
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                text = _format_coin(data[0])
            else:
                # Поиск по списку монет
                search_response = await asyncio.to_thread(
                    requests.get, f"{COINGECKO_API}/coins/list", timeout=15
                )
                if search_response.status_code == 200:
                    coins_list = search_response.json()
                    matching_coins = [c for c in coins_list if c['symbol'].upper() == token_symbol]

                    if matching_coins:
                        coin_id = matching_coins[0]['id']
                        detail_response = await asyncio.to_thread(
                            requests.get,
                            f"{COINGECKO_API}/coins/markets?vs_currency=usd&ids={coin_id}",
                            timeout=10,
                        )
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            if detail_data:
                                text = _format_coin(detail_data[0])

        if text is None:
            text = f"⚠️ Токен '{token_symbol}' не найден.\n\nПопробуй: BTC, ETH, SOL, MATIC и т.д."
    except Exception as e:
        text = f"⚠️ Ошибка: {str(e)}"

    await update.message.reply_text(text)


async def handle_nft_lookup(update, context):
    """Поиск NFT-коллекции"""
    collection_slug = update.message.text.lower().strip()

    try:
        headers = {
            "X-API-KEY": os.getenv("OPENSEA_API_KEY", ""),
            "Accept": "application/json"
        }

        response = await asyncio.to_thread(
            requests.get,
            f"{OPENSEA_API}/collections/{collection_slug}",
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            collection = data.get('collection', {})

            text = f"🖼️ {collection.get('name', 'Неизвестная коллекция')}\n\n"
            text += f"📊 Минимальная цена: {collection.get('floor_price', 'N/A')}\n"
            text += f"👥 Всего в коллекции: {collection.get('total_supply', 'N/A')}\n"
            text += f"🔗 Владельцев: {collection.get('owner_count', 'N/A')}\n"
            text += f"📈 Объём 24ч: {collection.get('one_day_volume', 'N/A')}\n\n"
            text += f"📝 Описание: {collection.get('description', 'N/A')[:200]}..."
        elif response.status_code in (401, 403):
            text = "⚠️ OpenSea API требует ключ.\n\n"
            text += "Получи бесплатный ключ на opensea.io и добавь OPENSEA_API_KEY в переменные окружения."
        else:
            text = f"⚠️ Коллекция '{collection_slug}' не найдена.\n\n"
            text += "Попробуй: bored-ape-yacht-club, azuki, doodles-official, moonbirds"
    except Exception as e:
        text = f"⚠️ Ошибка при получении данных NFT: {str(e)}\n\n"
        text += "Некоторые коллекции могут требовать API-ключ."

    await update.message.reply_text(text)


async def back_main(update, context):
    """Возврат в главное меню"""
    await update.callback_query.edit_message_text(MAIN_TEXT, reply_markup=main_keyboard())


async def handle_callback(update, context):
    """Обработка нажатий на кнопки"""
    data = update.callback_query.data

    if data == "token_price":
        await token_price_menu(update, context)
    elif data == "nft_collection":
        await nft_collection_menu(update, context)
    elif data == "gas_prices":
        await get_gas_prices(update, context)
    elif data == "top_tokens":
        await get_top_tokens(update, context)
    elif data == "back_main":
        await back_main(update, context)


async def handle_message(update, context):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()

    # Короткий текст из букв — считаем символом токена
    if len(text) <= 10 and text.isalpha():
        await handle_token_lookup(update, context)
    else:
        await handle_nft_lookup(update, context)


def register_handlers(application):
    """Регистрация обработчиков для polling и webhook"""
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
