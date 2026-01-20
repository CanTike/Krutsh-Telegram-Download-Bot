import logging
import yt_dlp
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# 1. Koyeb Sağlık Kontrolü Sunucusu
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Sunucu hatası: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- TOKEN ---
TOKEN = '8323309920:AAHpsa1dUseS1dTDYYLQCbPLxhL_3faVg-k'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Selam {update.effective_user.first_name}! Krutsh Bot 7/24 Aktif. 🎥\nLink gönderin!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    context.user_data['url'] = url
    keyboard = [[InlineKeyboardButton("🎵 Ses (M4A)", callback_data='mp3')],
                [InlineKeyboardButton("🎥 Video (MP4)", callback_data='mp4')]]
    await update.message.reply_text('Format seçin:', reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    format_type = query.data
    
    status_msg = await query.edit_message_text(text="📥 Hazırlanıyor... YouTube engeli kontrol ediliyor.")

    # GÜNCELLENEN KISIM BURASI: YouTube'u Android telefon gibi kandırıyoruz
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/114.0 Firefox/114.0',
    }

    if format_type == 'mp3':
        ydl_opts.update({'format': 'bestaudio[ext=m4a]/bestaudio/best'})
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await status_msg.edit_text("📤 Telegram'a gönderiliyor...")
        
        with open(filename, 'rb') as file:
            if format_type == 'mp3':
                await query.message.reply_audio(audio=file)
            else:
                await query.message.reply_video(video=file)
        
        if os.path.exists(filename): os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Hata: {e}")
        await query.message.reply_text(f"❌ Maalesef bu platform (Koyeb) YouTube tarafından engellenmiş.\n\nAlternatif: Instagram veya TikTok linki deneyin.")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
        
