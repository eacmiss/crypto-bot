# 🚀 Crypto/NFT Token Info Bot

Telegram бот для получения информации о криптовалютах и NFT коллекциях в реальном времени.

## ✨ Возможности

- **Цены токенов** - Мгновенная информация о ценах криптовалют
- **Статистика NFT** - Данные о NFT коллекциях
- **Цены на газ** - Текущие цены газа в сети Ethereum
- **Топ токены** - Список топ криптовалют по капитализации
- **Умный поиск** - Автоматическое определение типа запроса

## 📦 Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd crypto-nft-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env`:
```bash
cp .env.example .env
```

4. Добавьте токен бота в `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
COINGECKO_API_KEY=your_api_key_optional
ETHEREUM_RPC_URL=https://eth.llamarpc.com
```

## 🚀 Запуск

### Локально (polling):
```bash
python src/bot.py
```

### На Vercel (webhook):
1. Разверните на Vercel
2. Установите webhook:
```bash
curl -F "url=https://your-app.vercel.app/api/webhook" https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook
```

## 📁 Структура проекта

```
crypto-nft-bot/
├── src/
│   └── bot.py          # Основной код бота
├── api/
│   └── webhook.py      # Webhook для Vercel
├── requirements.txt
├── vercel.json
└── .env.example
```

## 📊 Используемые API

- **CoinGecko API** - Данные о криптовалютах
- **OpenSea API** - Данные о NFT коллекциях
- **ETH Gas Station** - Цены на газ Ethereum

## 💡 Примеры использования

### Получение цены токена:
```
BTC
ETH
SOL
```

### Информация о NFT коллекции:
```
bored-ape-yacht-club
azuki
doodles-official
```

### Топ криптовалют:
Нажмите кнопку "📊 Top Tokens" в меню

## 🔧 Настройка

### CoinGecko API
Опционально. Бесплатный лимит: 50 запросов/минуту.

### OpenSea API
Опционально для детальной информации о NFT.

## 👨‍💻 Разработчик

Разработано @eacmiss

## 📄 Лицензия

MIT License
