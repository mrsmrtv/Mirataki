import requests
import time
import json
import os
import random
import hashlib


# -------------------- НАСТРОЙКИ --------------------

TOKEN = "7126743161:AAFaYItWP5tQ8UZyq0B9jLC1bjQqxAD847g"
URL = f"https://api.telegram.org/bot{TOKEN}/"
MODERATOR_ID = 5425161302
RAFFLE_STATE_FILE = "raffle_state.json"

# -------------------- ЗАГРУЗКА ДАННЫХ --------------------
def generate_short_id(file_id):
    return hashlib.md5(file_id.encode()).hexdigest()[:10]


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

users = load_json("users.json")
pending = load_json("photos_pending.json")
checkins = load_json("checkins.json")
raffle_state = load_json(RAFFLE_STATE_FILE)

# -------------------- API --------------------

def get_updates(offset=None):
    params = {"timeout": 100, "offset": offset}
    return requests.get(URL + "getUpdates", params=params).json()

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(URL + "sendMessage", data=data)

def send_photo(chat_id, photo_id, caption="", reply_markup=None):
    print(f"📨 Пытаемся отправить фото {photo_id} модератору в чат {chat_id}")
    data = {
        "chat_id": chat_id,
        "photo": photo_id,
        "caption": caption
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    response = requests.post(URL + "sendPhoto", data=data)
    if not response.ok:
        print("❌ Ошибка при отправке фото:", response.text)
    else:
        print("✅ Фото успешно отправлено модератору.")


# -------------------- ОБРАБОТКА ФОТО --------------------

def handle_photo(user_id, chat_id, photo_id):
    if user_id not in users:
        users[user_id] = {"coins": 0, "invited": [], "raffle": False, "registered": False}

    if user_id in checkins and photo_id in checkins[user_id]:
        send_message(chat_id, "❗ Ты уже отправлял это фото.")
        return

    short_id = generate_short_id(photo_id)
    pending[short_id] = {"user_id": user_id, "chat_id": chat_id, "photo_id": photo_id}

    save_json("photos_pending.json", pending)
    send_message(chat_id, "📷 Фото получено! Ожидает модерации.")

    # Кнопки модерации
    keyboard = {
    "inline_keyboard": [[
        {"text": "✅ Принять", "callback_data": f"approve:{short_id}"},
        {"text": "❌ Отклонить", "callback_data": f"reject:{short_id}"}
    ]]
    }
    send_message(MODERATOR_ID, f"🆕 Фото от пользователя {user_id}. file_id: {photo_id}")
    send_photo(MODERATOR_ID, photo_id, caption=f"🕵️ Фото от пользователя {user_id}", reply_markup=keyboard)

    

# -------------------- ОБРАБОТКА ТЕКСТА --------------------

def get_main_keyboard(is_moderator=False):
    if is_moderator:
        return {
            "keyboard": [[
                {"text": "📥 Модерация"},
                {"text": "🚀 Начать розыгрыш"},
                {"text": "🛑 Завершить розыгрыш"}
            ]],
            "resize_keyboard": True
        }
    else:
        return {
            "keyboard": [[
                {"text": "📸 Отправить фото"},
                {"text": "💰 Баланс"},
            ], [
                {"text": "🎁 Розыгрыш"},
                {"text": "📍 Места"}
            ], [
                {"text": "👫 Пригласить друга"}
            ]],
            "resize_keyboard": True
        }


def handle_text(user_id, chat_id, text):
    is_moderator = (str(user_id) == str(MODERATOR_ID))

    if user_id not in users:
        users[user_id] = {"coins": 0, "invited": [], "raffle": False, "registered": False}

    if text == "/start":
        is_moderator = (str(user_id) == str(MODERATOR_ID))
        send_message(chat_id, "👋 Добро пожаловать в Mirataki!", reply_markup=get_main_keyboard(is_moderator))



    elif text == "💰 Баланс":
        coins = users[user_id]["coins"]
        send_message(chat_id, f"💰 У тебя {coins} CityCoin.")

    elif text == "📍 Места":
        msg = "📍 Точки города Алматы:\n1. Кок Тобе\n2. Парк Первого Президента\n3. Центральный Музей\n4. Парк Горького"
        send_message(chat_id, msg)

    elif text == "🎁 Розыгрыш":
        if users[user_id].get("registered", False):
            send_message(chat_id, "📢 Ты уже зарегистрирован на следующий розыгрыш!")
        elif users[user_id]["coins"] >= 1000:
            users[user_id]["coins"] -= 1000
            users[user_id]["registered"] = True
            save_json("users.json", users)
            send_message(chat_id, "✅ Ты зарегистрировался на розыгрыш. Жди начала от модератора!")
        else:
            send_message(chat_id, "❌ Нужно минимум 1000 CityCoin для регистрации.")

    elif text == "👫 Пригласить друга":
        link = f"https://t.me/MiratakiBot?start={user_id}"
        send_message(chat_id, f"🔗 Поделись ссылкой с другом: {link}\nВы оба получите бонус, если он отправит фото!")
    elif is_moderator and text == "🚀 Начать розыгрыш":
        if raffle_state.get("active", False):
            send_message(chat_id, "⚠️ Розыгрыш уже идёт!")
        else:
            raffle_state["active"] = True
            save_json(RAFFLE_STATE_FILE, raffle_state)
            send_message(chat_id, "🚀 Розыгрыш начался! Все зарегистрированные участвуют!")

    elif is_moderator and text == "🛑 Завершить розыгрыш":
        if not raffle_state.get("active", False):
            send_message(chat_id, "⚠️ Розыгрыш ещё не был начат.")
        else:
            participants = [uid for uid, u in users.items() if u.get("registered")]
            if not participants:
                send_message(chat_id, "👥 Нет участников для розыгрыша.")
            else:
                winner = random.choice(participants)
                users[winner]["coins"] += 1000
                for uid in participants:
                    users[uid]["registered"] = False
                save_json("users.json", users)
                send_message(chat_id, f"🏆 Победитель розыгрыша: {winner}! Он получает 1000 CityCoin 🎉")
                for uid in participants:
                    if str(uid) != str(winner):
                        send_message(uid, "🎲 Розыгрыш завершён. Удачи в следующий раз!")
            raffle_state["active"] = False
            save_json(RAFFLE_STATE_FILE, raffle_state)


# -------------------- ОБРАБОТКА CALLBACK --------------------

def handle_callback(query):
    data = query["data"]
    user_id = str(query["from"]["id"])
    message = query["message"]
    chat_id = message["chat"]["id"]
    msg_id = message["message_id"]

    if user_id != str(MODERATOR_ID):
        return

    if data.startswith("approve:"):
        photo_id = data.split(":")[1]
        if photo_id in pending:
            target_id = pending[photo_id]["user_id"]
            target_chat = pending[photo_id]["chat_id"]
            users[target_id]["coins"] += 100
            checkins.setdefault(target_id, []).append(photo_id)
            send_message(target_chat, "✅ Ваше фото одобрено! +100 CityCoin 🎉")
            send_message(chat_id, f"👍 Фото одобрено.\n👤 Пользователь: {target_id}\n📸 Photo ID: {photo_id}\n💰 Новый баланс: {users[target_id]['coins']}")
            del pending[photo_id]
            save_json("users.json", users)
            save_json("checkins.json", checkins)
            save_json("photos_pending.json", pending)

    elif data.startswith("reject:"):
        photo_id = data.split(":")[1]
        if photo_id in pending:
            target_id = pending[photo_id]["user_id"]
            target_chat = pending[photo_id]["chat_id"]
            send_message(target_chat, "❌ Ваше фото отклонено.")
            send_message(chat_id, f"🗑 Фото отклонено.\n👤 Пользователь: {target_id}\n📸 Photo ID: {photo_id}")
            del pending[photo_id]
            save_json("photos_pending.json", pending)

# -------------------- ГЛАВНЫЙ ЦИКЛ --------------------

def main():
    last_update_id = None
    print("🤖 MiratakiBot запущен...")

    while True:
        updates = get_updates(last_update_id)
        for update in updates.get("result", []):
            if "callback_query" in update:
                handle_callback(update["callback_query"])
            else:
                message = update.get("message")
                if message:
                    user_id = str(message["from"]["id"])
                    chat_id = message["chat"]["id"]

                    if "photo" in message:
                        photo_id = message["photo"][-1]["file_id"]
                        handle_photo(user_id, chat_id, photo_id)

                    elif "text" in message:
                        handle_text(user_id, chat_id, message["text"])

                    last_update_id = update["update_id"] + 1

        time.sleep(1)

if __name__ == "__main__":
    main()
