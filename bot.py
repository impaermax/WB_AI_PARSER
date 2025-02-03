import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from parser import WBProductParser

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WB_DOMAINS = ['wildberries.ru', 'www.wildberries.ru']
MAX_HTML_LENGTH = 3500  # С запасом для Markdown

# Инициализация
parser = WBProductParser()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = update.message.text.strip()
        
        if not any(domain in url for domain in WB_DOMAINS):
            await update.message.reply_text("⚠️ Пожалуйста, отправьте корректную ссылку на товар Wildberries")
            return

        logging.info(f"Обработка запроса: {url}")
        
        # Парсинг данных
        result = parser.parse_product(url)
        
        if not result['success']:
            raise Exception(result['error'])

        # Форматирование ответа
        response = format_response(result)
        html_preview = escape_markdown(result['raw_html'][:MAX_HTML_LENGTH])

        # Отправка сообщений
        await update.message.reply_text(response, parse_mode='MarkdownV2')
        await update.message.reply_text(
            f"`{html_preview}...`\n\n⚠️ HTML обрезан для отображения",
            parse_mode='MarkdownV2'
        )

    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        logging.error(error_msg)
        await update.message.reply_text(error_msg)

def format_response(data):
    return f"""
📦 *Wildberries Parser Report* 📦

🆔 *Артикул:* `{data['product_id']}`
📛 *Название:* {escape_markdown(data['name'])}
💰 *Цена:* {data['price']['current']} {'(Скидка!' if data['price']['original'] else '')}
{"🎯 Старая цена: " + data['price']['original'] if data['price']['original'] else ''}

🏪 *Продавец:*
ID: `{data['seller']['id']}`
Название: {escape_markdown(data['seller']['name'])}
Ссылка: {data['seller']['url']}

⭐ *Рейтинг:* {data['rating']['score']} ({data['rating']['reviews']} отзывов)
📷 *Изображений:* {len(data['images'])}
📋 *Характеристики:* {len(data['characteristics'])} позиций
    """.strip()

def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Бот запущен...")
    app.run_polling()
