import logging
import yt_dlp
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# 1. Koyeb Health Check Sunucusu (Botun Kapanmaması İçin)
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

# 3. Güvenli Token Alımı (Koyeb Environment Variables kısmına BOT_TOKEN eklemelisin)
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Selam {user_name}! Krutsh Bot 7/24 Aktif. 🎥\n\nBana bir YouTube, Instagram veya TikTok linki gönder, hemen indireyim!")

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
    
    status_msg = await query.edit_message_text(text="📥 Hazırlanıyor... Sunucu engeli kontrol ediliyor.")

    # YouTube Engelini Aşmak İçin En Güçlü Ayarlar
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        
        # Temizlik: İndirilen dosyayı sunucudan sil
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Hata detayı: {e}")
        error_text = "❌ Hata: Bu platform şu an erişimi engelledi.\n"
        if "confirm you’re not a bot" in str(e):
            error_text += "Sebep: YouTube sunucu IP adresini geçici olarak engelledi."
        else:
            error_text += "Sebep: Link hatalı veya dosya çok büyük."
        
        await query.message.reply_text(error_text)

# Ana Çalıştırma
if __name__ == '__main__':
    if not TOKEN:
        print("HATA: BOT_TOKEN bulunamadı! Lütfen Koyeb ayarlarına ekleyin.")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button))
        print("Bot başlatıldı...")
        app.run_polling()
        
