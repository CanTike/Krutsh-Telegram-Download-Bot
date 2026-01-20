import logging
import yt_dlp
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# 1. Render/Koyeb Health Check Sunucusu
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Sunucu hatası: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. Loglama Ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 3. Güvenli Token Alımı
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Selam {user_name}! Krutsh Bot 7/24 Aktif. 🎥\n\nYouTube, Instagram veya TikTok linki gönderebilirsin.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url:
        return
    
    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("🎵 Ses (M4A)", callback_data='mp3')],
        [InlineKeyboardButton("🎥 Video (MP4)", callback_data='mp4')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Dosya formatını seçin:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('url')
    format_type = query.data
    
    status_msg = await query.edit_message_text(text="📥 Hazırlanıyor... YouTube engeli zorlanıyor.")

    # GÜNCELLENEN: iPhone Taklidi ve Gelişmiş Extractor Ayarları
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Botu iOS Safari gibi gösteriyoruz (Daha az kısıtlama alabilir)
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web'],
                'skip': ['hls', 'dash']
            }
        },
    }

    if format_type == 'mp3':
        ydl_opts.update({'format': 'bestaudio[ext=m4a]/bestaudio/best'})
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await status_msg.edit_text("📤 Hazır! Telegram'a yükleniyor...")
        
        with open(filename, 'rb') as file:
            if format_type == 'mp3':
                await query.message.reply_audio(audio=file, title=info.get('title'))
            else:
                await query.message.reply_video(video=file, caption=info.get('title'))
        
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Hata detayı: {e}")
        error_msg = str(e)
        if "confirm you’re not a bot" in error_msg:
            msg = "❌ YouTube bu sunucunun (Render) IP adresini engellemiş.\n\n💡 Instagram ve TikTok linkleri hala çalışır! YouTube için bilgisayar başına geçtiğinde 'cookies' eklememiz gerekecek."
        else:
            msg = f"❌ Bir hata oluştu: {error_msg[:100]}..."
        
        await query.message.reply_text(msg)

# Ana Çalıştırma
if __name__ == '__main__':
    if not TOKEN:
        print("HATA: BOT_TOKEN bulunamadı!")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button))
        print("Bot başarıyla başlatıldı...")
        app.run_polling()
