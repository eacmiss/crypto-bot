import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from fastapi import FastAPI, Request

load_dotenv()

COINGECKO_API = "https://api.coingecko.com/api/v3"
OPENSEA_API = "https://api.opensea.io/api/v2"
ETH_RPC = "https://eth.llamarpc.com"

app = FastAPI()

bot_app = None

def get_bot_app():
    global bot_app
    if bot_app is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        bot_app = Application.builder().token(token).build()
        
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CallbackQueryHandler(handle_callback))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return bot_app

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = [
        [InlineKeyboardButton("💰 Token Price", callback_data="token_price")],
        [InlineKeyboardButton("🖼️ NFT Collection", callback_data="nft_collection")],
        [InlineKeyboardButton("⛽ Gas Prices", callback_data="gas_prices")],
        [InlineKeyboardButton("📊 Top Tokens", callback_data="top_tokens")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚀 Crypto/NFT Token Info Bot\n\n"
        "Get instant information about:\n"
        "• Token prices\n"
        "• NFT collection stats\n"
        "• Gas prices\n\n"
        "Select an option below or type a token symbol (e.g., BTC, ETH):",
        reply_markup=reply_markup
    )

async def token_price_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show token price menu"""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    await query.edit_message_text(
        "💰 Token Price Lookup\n\n"
        "Type a token symbol (e.g., BTC, ETH, SOL) to get its price.\n\n"
        "Examples:\n"
        "• BTC - Bitcoin\n"
        "• ETH - Ethereum\n"
        "• SOL - Solana\n"
        "• MATIC - Polygon",
        reply_markup=reply_markup
    )

async def nft_collection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show NFT collection menu"""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    await query.edit_message_text(
        "🖼️ NFT Collection Info\n\n"
        "Type an NFT collection name or slug to get stats.\n\n"
        "Examples:\n"
        "• bored-ape-yacht-club\n"
        "• azuki\n"
        "• doodles-official\n"
        "• moonbirds",
        reply_markup=reply_markup
    )

async def get_gas_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current gas prices"""
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

        gas_text = "⛽ Current Gas Price\n\n"
        gas_text += f"⚡ {gas_gwei:.1f} gwei\n\n"
        gas_text += f"💰 Estimated ETH Transfer Cost (21,000 gas):\n"
        gas_text += f"• {transfer_eth:.6f} ETH (~${transfer_eth * eth_usd:.2f})"
    except Exception:
        gas_text = "⚠️ Unable to fetch gas prices. Please try again later."
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="gas_prices")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(gas_text, reply_markup=reply_markup)

async def get_top_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top tokens by market cap"""
    query = update.callback_query
    
    try:
        response = await asyncio.to_thread(
            requests.get,
            f"{COINGECKO_API}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false",
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            
            text = "📊 Top 10 Cryptocurrencies\n\n"
            for i, coin in enumerate(data, 1):
                change_24h = coin.get('price_change_percentage_24h', 0)
                emoji = "📈" if change_24h >= 0 else "📉"
                text += f"{i}. {coin['symbol'].upper()} - ${coin['current_price']:,.2f}\n"
                text += f"   {emoji} {change_24h:.2f}% (24h)\n\n"
        else:
            text = "⚠️ Unable to fetch token data. Please try again later."
    except Exception as e:
        text = f"⚠️ Error fetching tokens: {str(e)}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="top_tokens")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def handle_token_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle token price lookup"""
    token_symbol = update.message.text.upper().strip()
    
    try:
        response = await asyncio.to_thread(
            requests.get,
            f"{COINGECKO_API}/coins/markets?vs_currency=usd&ids={token_symbol.lower()}",
            timeout=10,
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                coin = data[0]
                change_24h = coin.get('price_change_percentage_24h', 0)
                change_7d = coin.get('price_change_percentage_7d_in_currency', 0)
                emoji_24h = "📈" if change_24h >= 0 else "📉"
                emoji_7d = "📈" if change_7d >= 0 else "📉"
                
                text = f"💰 {coin['name']} ({coin['symbol'].upper()})\n\n"
                text += f"💵 Price: ${coin['current_price']:,.2f}\n\n"
                text += f"📊 Market Cap: ${coin['market_cap']:,.0f}\n"
                text += f"📊 24h Volume: ${coin['total_volume']:,.0f}\n\n"
                text += f"📈 24h Change: {emoji_24h} {change_24h:.2f}%\n"
                text += f"📈 7d Change: {emoji_7d} {change_7d:.2f}%\n\n"
                text += f"🏆 Rank: #{coin['market_cap_rank'] or 'N/A'}"
            else:
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
                                coin = detail_data[0]
                                change_24h = coin.get('price_change_percentage_24h', 0)
                                emoji = "📈" if change_24h >= 0 else "📉"
                                
                                text = f"💰 {coin['name']} ({coin['symbol'].upper()})\n\n"
                                text += f"💵 Price: ${coin['current_price']:,.2f}\n\n"
                                text += f"📊 Market Cap: ${coin['market_cap']:,.0f}\n"
                                text += f"📊 24h Volume: ${coin['total_volume']:,.0f}\n\n"
                                text += f"📈 24h Change: {emoji} {change_24h:.2f}%\n\n"
                                text += f"🏆 Rank: #{coin['market_cap_rank'] or 'N/A'}"
                            else:
                                text = f"⚠️ Token '{token_symbol}' not found."
                        else:
                            text = f"⚠️ Error fetching token details."
                    else:
                        text = f"⚠️ Token '{token_symbol}' not found.\n\nTry: BTC, ETH, SOL, MATIC, etc."
                else:
                    text = f"⚠️ Token '{token_symbol}' not found."
        else:
            text = "⚠️ Error fetching token data. Please try again later."
    except Exception as e:
        text = f"⚠️ Error: {str(e)}"
    
    await update.message.reply_text(text)

async def handle_nft_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle NFT collection lookup"""
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
            
            text = f"🖼️ {collection.get('name', 'Unknown Collection')}\n\n"
            text += f"📊 Floor Price: {collection.get('floor_price', 'N/A')}\n"
            text += f"👥 Total Supply: {collection.get('total_supply', 'N/A')}\n"
            text += f"🔗 Owners: {collection.get('owner_count', 'N/A')}\n"
            text += f"📈 24h Volume: {collection.get('one_day_volume', 'N/A')}\n\n"
            text += f"📝 Description: {collection.get('description', 'N/A')[:200]}..."
        elif response.status_code in (401, 403):
            text = "⚠️ OpenSea API requires an API key.\n\n"
            text += "Get a free key at opensea.io and set OPENSEA_API_KEY in env vars."
        else:
            text = f"⚠️ Collection '{collection_slug}' not found.\n\n"
            text += "Try: bored-ape-yacht-club, azuki, doodles-official, moonbirds"
    except Exception as e:
        text = f"⚠️ Error fetching NFT data: {str(e)}\n\n"
        text += "Note: Some collections may require API key access."
    
    await update.message.reply_text(text)

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    keyboard = [
        [InlineKeyboardButton("💰 Token Price", callback_data="token_price")],
        [InlineKeyboardButton("🖼️ NFT Collection", callback_data="nft_collection")],
        [InlineKeyboardButton("⛽ Gas Prices", callback_data="gas_prices")],
        [InlineKeyboardButton("📊 Top Tokens", callback_data="top_tokens")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    await query.edit_message_text(
        "🚀 Crypto/NFT Token Info Bot\n\n"
        "Get instant information about:\n"
        "• Token prices\n"
        "• NFT collection stats\n"
        "• Gas prices\n\n"
        "Select an option below or type a token symbol (e.g., BTC, ETH):",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    data = query.data
    
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.lower()
    
    if len(text) <= 10 and text.isalpha():
        await handle_token_lookup(update, context)
    else:
        await handle_nft_lookup(update, context)

@app.post("/")
@app.post("/webhook")
@app.post("/api/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook"""
    application = get_bot_app()
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "crypto-nft-bot is running"}
