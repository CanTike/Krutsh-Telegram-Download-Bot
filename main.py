import logging
import yt_dlp
import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# 1. Koyeb Sağlık Kontrolü (Health Check) İçin Sahte Sunucu
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"Sunucu hatası: {e}")

# Arka planda sunucuyu başlat
threading.Thread(target=run_dummy_server, daemon=True).start()

# Loglama ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- TOKEN ---
TOKEN = '8323309920:AAHpsa1dUseS1dTDYYLQCbPLxhL_3faVg-k'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Selam {update.effective_user.first_name}! Krutsh Bot 7/24 Aktif. 🎥\nLink gönderin, hemen indireyim.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    context.user_data['url'] = url
    keyboard = [[InlineKeyboardButton("🎵 Ses (M4A)", callback_data='mp3')],
                [InlineKeyboardButton("🎥 Video (MP4)", callback_data='mp4')]]
    await update.message.reply_text('Hangi formatta istersiniz?', reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    format_type = query.data
    
    status_msg = await query.edit_message_text(text="📥 Hazırlanıyor... Bu işlem sunucu yoğunluğuna göre biraz sürebilir.")

    # Ortak yt-dlp Ayarları (YouTube Engelini Aşmak İçin Optimize Edildi)
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Tarayıcı gibi görünmek için User-Agent ekledik
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    if format_type == 'mp3':
        # En iyi ses dosyasını (m4a) seçer, FFmpeg gerektirmez
        ydl_opts.update({'format': 'bestaudio[ext=m4a]/bestaudio/best'})
    else:
        # Görüntü ve sesi birleşik hazır olan en iyi mp4'ü seçer (FFmpeg gerektirmez)
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # Dosya ismini kontrol et (indirme sırasında değişmiş olabilir)
        if not os.path.exists(filename):
            # Bazı durumlarda uzantı farklı bitebilir, kontrol et
            possible_files = [f for f in os.listdir('.') if f.startswith(info['title'][:10])]
            if possible_files:
                filename = possible_files[0]

        await status_msg.edit_text("📤 Dosya Telegram'a yükleniyor...")
        
        with open(filename, 'rb') as file:
            if format_type == 'mp3':
                await query.message.reply_audio(audio=file, title=info.get('title'))
            else:
                await query.message.reply_video(video=file, caption=info.get('title'))
        
        if os.path.exists(filename): os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Hata detayı: {e}")
        await query.message.reply_text(f"❌ Üzgünüm, bir hata oluştu.\nSebep: YouTube sunucusu erişimi engelledi veya dosya çok büyük.")

# Botu çalıştır
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot 7/24 modunda başlatıldı...")
    app.run_polling()
                
