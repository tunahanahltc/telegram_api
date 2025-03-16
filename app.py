from telethon import TelegramClient
from flask import Flask, jsonify
import asyncio

# Telegram API bilgileri
api_id = '9144604'  # my.telegram.org'dan alın
api_hash = '8645242a0dffb9e10489ce2402f1790e'  # my.telegram.org'dan alın

# Telethon client oluşturma
client = TelegramClient('session_name', api_id, api_hash)

# Flask uygulaması
app = Flask(__name__)

# Mesajları çekme fonksiyonu
async def fetch_telegram_messages():
    if not await client.is_user_authorized():
        await client.start()

    dialogs = await client.get_dialogs()
    messages = []
    for dialog in dialogs:
        chat_messages = await client.get_messages(dialog.id, limit=5)  # Son 5 mesajı al
        for message in chat_messages:
            messages.append({
                'chat_name': dialog.name,
                'sender_id': message.sender_id,
                'message_text': message.text
            })
    return messages

# REST API endpoint'i
@app.route('/messages', methods=['GET'])
def get_messages():
    with client:
        messages = client.loop.run_until_complete(fetch_telegram_messages())
    return jsonify(messages)

# Uygulamayı çalıştır
if __name__ == '__main__':
    app.run(debug=True)