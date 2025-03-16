from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio
import os
import nest_asyncio

# Asenkron işlemler için nest_asyncio'yu etkinleştir
nest_asyncio.apply()

app = Flask(__name__)

# Telegram API bilgileri
api_id = os.getenv('API_ID')  # Environment variable'dan alınır
api_hash = os.getenv('API_HASH')  # Environment variable'dan alınır
session_string = os.getenv('SESSION_STRING')  # StringSession string'i

# Telethon client oluşturma
client = TelegramClient(StringSession(session_string), api_id, api_hash)

# Kullanıcıdan telefon numarası al ve kod iste
@app.route('/request_code', methods=['POST'])
def request_code():
    phone_number = request.json.get('phone_number')
    if not phone_number:
        return jsonify({"error": "Telefon numarası gereklidir"}), 400

    async def send_code():
        await client.connect()
        await client.send_code_request(phone_number)
        return "Kod gönderildi"

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(send_code())
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Kullanıcıdan kodu al ve oturum aç
@app.route('/submit_code', methods=['POST'])
def submit_code():
    phone_number = request.json.get('phone_number')
    code = request.json.get('code')
    password = request.json.get('password')

    if not phone_number or not code:
        return jsonify({"error": "Telefon numarası ve kod gereklidir"}), 400

    async def sign_in():
        await client.connect()
        try:
            await client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            if not password:
                return "İki adımlı doğrulama şifresi gereklidir"
            await client.sign_in(password=password)
        return "Oturum açıldı"

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(sign_in())
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Mesajları çek ve dosyaya kaydet
@app.route('/fetch_messages', methods=['GET'])
def fetch_messages():
    async def fetch():
        if not await client.is_user_authorized():
            return "Oturum açılmamış"

        dialogs = await client.get_dialogs()
        messages = []
        for dialog in dialogs:
            chat_messages = await client.get_messages(dialog.id, limit=5)
            for message in chat_messages:
                messages.append({
                    'chat_name': dialog.name,
                    'sender_id': message.sender_id,
                    'message_text': message.text
                })

        # Mesajları dosyaya kaydet
        with open('messages.txt', 'w') as f:
            for msg in messages:
                f.write(f"{msg['chat_name']}: {msg['message_text']}\n")

        return "Mesajlar dosyaya kaydedildi"

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(fetch())
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)