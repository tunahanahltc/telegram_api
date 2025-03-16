from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio
import os

app = Flask(__name__)

# Telegram API bilgileri
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
session_string = os.getenv('SESSION_STRING')

# Telethon client oluşturma
client = TelegramClient(StringSession(session_string), api_id, api_hash)

# Flask uygulaması başlarken Telegram istemcisine bağlan
async def start_client():
    if not client.is_connected():
        await client.connect()

@app.before_request
def init_client():
    asyncio.create_task(start_client())

@app.route('/', methods=['GET'])
def home():
    return "Telegram API'ye hoş geldiniz!"

@app.route('/request_code', methods=['POST'])
async def request_code():
    phone_number = request.json.get('phone_number')
    if not phone_number:
        return jsonify({"error": "Telefon numarası gereklidir"}), 400

    try:
        await client.send_code_request(phone_number)
        return jsonify({"message": "Kod gönderildi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit_code', methods=['POST'])
async def submit_code():
    phone_number = request.json.get('phone_number')
    code = request.json.get('code')
    password = request.json.get('password')

    if not phone_number or not code:
        return jsonify({"error": "Telefon numarası ve kod gereklidir"}), 400

    try:
        await client.sign_in(phone_number, code)
        return jsonify({"message": "Oturum açıldı"})
    except SessionPasswordNeededError:
        if not password:
            return jsonify({"error": "İki adımlı doğrulama şifresi gereklidir"}), 400
        await client.sign_in(password=password)
        return jsonify({"message": "Oturum açıldı"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fetch_messages', methods=['GET'])
async def fetch_messages():
    if not await client.is_user_authorized():
        return jsonify({"error": "Oturum açılmamış"}), 401

    try:
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

        return jsonify({"message": "Mesajlar dosyaya kaydedildi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
