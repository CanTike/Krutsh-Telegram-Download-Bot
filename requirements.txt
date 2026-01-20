import logging
import yt_dlp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOTFATTHER'DAN ALDIĞIN TOKENİ BURAYA YAPIŞTIR ---
TOKEN = 'BURAYA_TOKENINI_YAZ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Selam {update.effective_user.first_name}! Krutsh Bot 7/24 Aktif. 🎥\nLink gönder, indireyim.")

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
    await query.edit_message_text(text="📥 Hazırlanıyor... Lütfen bekleyin.")

    ydl_opts = {'outtmpl': '%(title)s.%(ext)s', 'quiet': True, 'no_warnings': True}
    if format_type == 'mp3':
        ydl_opts.update({'format': 'bestaudio[ext=m4a]/bestaudio/best'})
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        with open(filename, 'rb') as file:
            if format_type == 'mp3':
                await query.message.reply_audio(audio=file)
            else:
                await query.message.reply_video(video=file)
        
        if os.path.exists(filename): os.remove(filename)
    except Exception as e:
        await query.message.reply_text(f"❌ Hata oluştu. Linki kontrol edin.")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
