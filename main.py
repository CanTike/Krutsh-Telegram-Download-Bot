import logging
import yt_dlp
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# 1. Render Port Dinleyici (Render'ın botu kapatmaması için gerekli)
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. Loglama
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 3. Token Kontrolü
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Selam {user_name}! Krutsh Bot 7/24 Aktif. ✅\n\nYouTube, Instagram veya TikTok linki gönderebilirsin.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return
    
    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("🎵 Ses (M4A)", callback_data='mp3')],
        [InlineKeyboardButton("🎥 Video (MP4)", callback_data='mp4')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Format seçin:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('url')
    format_type = query.data
    status_msg = await query.edit_message_text(text="📥 İşleniyor, lütfen bekleyin...")

    # YouTube Engelini Aşmaya Yönelik En Yeni Ayarlar
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'player_client': ['android', 'ios'], 'skip': ['hls', 'dash']}},
    }

    if format_type == 'mp3':
        ydl_opts.update({'format': 'bestaudio[ext=m4a]/bestaudio/best'})
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await status_msg.edit_text("📤 Telegram'a yükleniyor...")
        
        with open(filename, 'rb') as file:
            if format_type == 'mp3':
                await query.message.reply_audio(audio=file, title=info.get('title'))
            else:
                await query.message.reply_video(video=file, caption=info.get('title'))
        
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Hata: {e}")
        error_text = str(e)
        if "confirm you’re not a bot" in error_text:
            msg = "❌ YouTube Engeli: Render IP adresi YouTube tarafından kısıtlanmış. (Çözüm için cookies.txt eklenmeli)."
        else:
            msg = "❌ İndirme başarısız oldu. Linkin doğruluğunu kontrol edin."
        await query.message.reply_text(msg)

if __name__ == '__main__':
    if not TOKEN:
        print("HATA: BOT_TOKEN Environment Variable olarak eklenmemiş!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button))
        print("Bot başlatıldı...")
        app.run_polling()
