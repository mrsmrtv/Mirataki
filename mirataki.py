import requests
import time
import json
import os
import random
import hashlib
import logging
from datetime import datetime, timedelta

# -------------------- НАСТРОЙКИ --------------------
TOKEN = "7126743161:AAFaYItWP5tQ8UZyq0B9jLC1bjQqxAD847g"
URL = f"https://api.telegram.org/bot{TOKEN}/"
MODERATOR_IDS = ["5425161302", "940635136"]

USERS_FILE = "users.json"
PENDING_FILE = "photos_pending.json"
CHECKINS_FILE = "checkins.json"
RAFFLE_STATE_FILE = "raffle_state.json"

logging.basicConfig(level=logging.INFO)

# -------------------- ЗАГРУЗКА ДАННЫХ --------------------
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

def generate_short_id(file_id):
    return hashlib.md5(file_id.encode()).hexdigest()[:10]

users = load_json(USERS_FILE)
pending = load_json(PENDING_FILE)
checkins = load_json(CHECKINS_FILE)
raffle_state = load_json(RAFFLE_STATE_FILE)


# -------------------- API --------------------
def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "sendMessage", data=data).raise_for_status()
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

def send_photo(chat_id, photo_id, caption="", reply_markup=None):
    data = {"chat_id": chat_id, "photo": photo_id, "caption": caption}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "sendPhoto", data=data).raise_for_status()
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}")

def send_media_group(chat_id, media):
    data = {
        "chat_id": chat_id,
        "media": json.dumps(media)
    }
    try:
        requests.post(URL + "sendMediaGroup", data=data).raise_for_status()
    except Exception as e:
        logging.error(f"Ошибка при отправке группы фото: {e}")

def show_shop(chat_id):
    media = [
        {
            "type": "photo",
            "media": "https://raw.githubusercontent.com/mrsmrtv/Mirataki/refs/heads/main/%D0%B1%D0%B5%D0%BB%D0%B0%D1%8F%20%D1%81%D0%BF%D0%B5%D1%80%D0%B5%D0%B4%D0%B8.png",
            "caption": "Белая футболка — вид спереди"
        },
        {
            "type": "photo",
            "media": "https://raw.githubusercontent.com/mrsmrtv/Mirataki/refs/heads/main/%D0%B1%D0%B5%D0%BB%D0%B0%D1%8F%20%D1%81%D0%B7%D0%B0%D0%B4%D0%B8.png",
            "caption": "Белая футболка — вид сзади"
        },
        {
            "type": "photo",
            "media": "https://raw.githubusercontent.com/mrsmrtv/Mirataki/refs/heads/main/%D1%87%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%20%D1%81%D0%BF%D0%B5%D1%80%D0%B5%D0%B4%D0%B8.png",
            "caption": "Чёрная футболка — вид спереди"
        },
        {
            "type": "photo",
            "media": "https://raw.githubusercontent.com/mrsmrtv/Mirataki/refs/heads/main/%D1%87%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%20%D1%81%D0%B7%D0%B0%D0%B4%D0%B8.png",
            "caption": "Чёрная футболка — вид сзади"
        },
    ]
    send_media_group(chat_id, media)

    keyboard = {
    "inline_keyboard": [
        [{"text": "🤍 Купить белую", "callback_data": "buy_white_shirt"}],
        [{"text": "🖤 Купить чёрную", "callback_data": "buy_black_shirt"}],
        [{"text": "💳 Конвертировать в тенге", "callback_data": "convert_to_tenge"}]
    ]
    }

    send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


# -------------------- Геймдизайн --------------------
def get_rank(user_id):
    count = len(set(checkins.get(user_id, [])))
    if count >= 1000:
        return f"🌟 Легенда ({count} одобренных фотографий)"
    elif count >= 750:
        return f"🛸 Гуру Городов ({count} одобренных фотографий)"
    elif count >= 500:
        return f"🏔️ Покоритель вершин ({count} одобренных фотографий)"
    elif count >= 250:
        return f"🎯 Профи ({count} одобренных фотографий)"
    elif count >= 150:
        return f"🔥 Активист ({count} одобренных фотографий)"
    elif count >= 100:
        return f"🚴‍♂️ Турист ({count} одобренных фотографий)"
    elif count >= 50:
        return f"🏞️ Активный исследователь ({count} одобренных фотографий)"
    elif count >= 25:
        return f"🧭 Городской путник ({count} одобренных фотографий)"
    elif count >= 10:
        return f"👟 Исследователь-стажёр ({count} одобренных фотографий)"
    elif count >= 5:
        return f"🐣 Любопытный ({count} одобренных фотографий)"
    else:
        return f"👶 Новичок ({count} одобренных фотографий)"

def daily_bonus(user_id):
    today = datetime.utcnow().date().isoformat()
    if users[user_id].get("last_bonus") != today:
        users[user_id]["coins"] += 10
        users[user_id]["last_bonus"] = today
        save_json(USERS_FILE, users)
        return True
    return False
def check_achievements(user_id):
    count = len(set(checkins.get(user_id, [])))
    unlocked = users[user_id].get("achievements", [])
    rewards = {
        5: ("🎯 Исследователь I", 10),
        10: ("🥈 Исследователь II", 25),
        20: ("🥇 Исследователь III", 50)
    }
    for threshold, (name, reward) in rewards.items():
        if count >= threshold and name not in unlocked:
            users[user_id]["coins"] += reward
            unlocked.append(name)
            send_message(user_id, f"🏅 Достижение разблокировано: {name}! +{reward} Mirataki")
    users[user_id]["achievements"] = unlocked
    save_json(USERS_FILE, users)

# -------------------- Клавиатуры --------------------
def get_main_keyboard(is_moderator=False):
    if is_moderator:
        return {"keyboard": [[{"text": "📥 Модерация"}, {"text": "🚀 Начать розыгрыш"}, {"text": "🛑 Завершить розыгрыш"}]], "resize_keyboard": True}
    return {"keyboard": [[{"text": "💰 Баланс"}], [{"text": "🎁 Розыгрыш"}, {"text": "📍 Места"}], [{"text": "👫 Пригласить друга"}, {"text": "📊 Статистика"}],[{"text":"🏅 Мои ачивки"},{"text": "🛍 Магазин"}],[{"text": "🎁 Ежедневный подарок"}]], "resize_keyboard": True}
def get_location_keyboard(photo_id):
    return {
        "inline_keyboard": [[
            {"text": "🏔 Горы", "callback_data": f"reward:{photo_id}:mountain"},
            {"text": "🌳 Парк", "callback_data": f"reward:{photo_id}:park"},
            {"text": "🏙 Центр", "callback_data": f"reward:{photo_id}:city"},
        ]]
    }
# -------------------- Обработка текста --------------------
def handle_text(user_id, chat_id, text):
    is_moderator = str(user_id) in MODERATOR_IDS
    users.setdefault(user_id, {"coins": 0, "invited": [], "raffle": False, "registered": False})

    if text == "/start":
        send_message(chat_id, "👋 Добро пожаловать в Mirataki!", reply_markup=get_main_keyboard(is_moderator))

    elif text == "💰 Баланс":
        coins = users[user_id]["coins"]
        rank = get_rank(user_id)
        send_message(chat_id, f"💰 У тебя {coins} Mirataki\n🎖️ Твой ранг: {rank}")

    elif text == "📍 Места":
        map_url = "https://www.google.com/maps/d/u/2/edit?mid=1sZKyM_fDqSzCyiTPXTNk92_kM-XUyhU&ll=43.25679420494812%2C76.94126883771627&z=13" 
        reply_markup = {
            "inline_keyboard": [
                [{"text": "🗺 Открыть карту мест", "url": map_url}]
            ]
        }
        send_message(chat_id, "📍 Нажми кнопку ниже, чтобы открыть карту:", reply_markup=reply_markup)

    elif text == "🎁 Розыгрыш":
        if users[user_id].get("registered"):
            send_message(chat_id, "📢 Ты уже зарегистрирован на розыгрыш!")
        elif users[user_id]["coins"] >= 100:
            users[user_id]["coins"] -= 100
            users[user_id]["registered"] = True
            save_json(USERS_FILE, users)
            send_message(chat_id, "✅ Ты участвуешь в розыгрыше!")
        else:
            send_message(chat_id, "❌ Нужно 100 Mirataki для участия.")

    elif text == "👫 Пригласить друга":
        link = f"https://t.me/MiratakiBot?start={user_id}"
        send_message(chat_id, f"🔗 Приглашай друзей: {link}")

    elif text == "📊 Статистика":
        count = len(checkins.get(user_id, []))
        coins = users[user_id]["coins"]
        send_message(chat_id, f"📸 Фото отправлено: {count}\n💰 Баланс: {coins}\n🎖️ Ранг: {get_rank(coins)}")

    elif text == "🎁 Ежедневный подарок":
        if daily_bonus(user_id):
            send_message(chat_id, "🎉 Ты получил 10 Mirataki за сегодня!")
        else:
            send_message(chat_id, "📆 Ты уже получил подарок сегодня. Возвращайся завтра!")

    elif text == "🏅 Мои ачивки":
        ach = users.get(user_id, {}).get("achievements", [])
        if not ach:
            send_message(chat_id, "😕 У тебя пока нет достижений.")
        else:
            send_message(chat_id, "🏅 Твои достижения:\n" + "\n".join(ach))
    
    elif text == "🛍 Магазин":
        show_shop(chat_id)


   
        # Обработка ввода адреса доставки
    elif users[user_id].get("state", {}).get("action") == "await_address":
        address = text.strip()

    # Сохраняем адрес временно
        users[user_id]["state"]["temp_address"] = address
        save_json(USERS_FILE, users)

        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Подтвердить", "callback_data": "confirm_address"}]
            ]
        }

        send_message(
            chat_id,
            f"📬 Ты указал адрес:\n\n{address}\n\nЕсли всё верно, нажми «Подтвердить».",
            reply_markup=keyboard
        )

    elif users[user_id].get("state", {}).get("action") == "enter_convert_amount":
        try:
            amount = int(text)
            if amount <= 0 or amount > users[user_id]["coins"]:
                send_message(chat_id, "❌ Укажи корректное количество Mirataki.")
            else:
                users[user_id]["state"] = {
                    "action": "enter_card",
                    "amount": amount
                }
                send_message(chat_id, "💳 Введи номер своей банковской карты (пример: 4400 1234 5678 9012):")
        except ValueError:
            send_message(chat_id, "⚠️ Введи число.")
        return

    elif users[user_id].get("state", {}).get("action") == "enter_card":
        card_number = text.strip()
        amount = users[user_id]["state"]["amount"]
        rate = 10
        tenge = amount * rate

        if len(card_number.replace(" ", "")) < 16:
            send_message(chat_id, "⚠️ Похоже, номер карты некорректен. Попробуй снова.")
            return

        users[user_id]["coins"] -= amount
        users[user_id].setdefault("conversions", []).append({
            "amount": amount,
            "received": tenge,
            "card": card_number,
            "time": datetime.utcnow().isoformat()
        })
        users[user_id]["state"] = {}
        save_json(USERS_FILE, users)

        send_message(chat_id, f"✅ Заявка на вывод {tenge} ₸ отправлена.\n💳 Карта: {card_number}\nОжидай перевода.")

        # Уведомление модераторов
        for mod_id in MODERATOR_IDS:
            send_message(mod_id, f"💸 Заявка на вывод:\nПользователь {user_id}\n🔢 {amount} Mirataki\n💰 {tenge} ₸\n💳 {card_number}")
        return


    
    elif is_moderator and text == "🚀 Начать розыгрыш":
        if raffle_state.get("active"):
            send_message(chat_id, "⚠️ Розыгрыш уже идёт")
        else:
            raffle_state["active"] = True
            save_json(RAFFLE_STATE_FILE, raffle_state)
            send_message(chat_id, "🚀 Розыгрыш начался!")

    elif is_moderator and text == "🛑 Завершить розыгрыш":
        if not raffle_state.get("active"):
            send_message(chat_id, "⚠️ Розыгрыш не запущен")
        else:
            participants = [uid for uid, u in users.items() if u.get("registered")]
            if not participants:
                send_message(chat_id, "👥 Нет участников")
            else:
                winner = random.choice(participants)
                users[winner]["coins"] += 2000
                send_message(winner, "🎉 Поздравляем! Ты выиграл розыгрыш и получил 2000 Mirataki!")
                for uid in participants:
                    users[uid]["registered"] = False
                save_json(USERS_FILE, users)
                send_message(chat_id, f"🏆 Победитель: {winner}")
                for uid in participants:
                    if uid != winner:
                        send_message(uid, "🎲 Розыгрыш завершён. Удачи в следующий раз!")
            raffle_state["active"] = False
            save_json(RAFFLE_STATE_FILE, raffle_state)

# -------------------- Обработка фото --------------------
def handle_photo(user_id, chat_id, photo_id):
    if user_id not in users:
        users[user_id] = {"coins": 0, "invited": [], "raffle": False, "registered": False}

    if user_id in checkins and photo_id in checkins[user_id]:
        send_message(chat_id, "❗ Ты уже отправлял это фото.")
        return

    short_id = generate_short_id(photo_id)
    if short_id in pending:
        send_message(chat_id, "⏳ Это фото уже на модерации.")
        return

    pending[short_id] = {"user_id": user_id, "chat_id": chat_id, "photo_id": photo_id}
    save_json(PENDING_FILE, pending)

    send_message(chat_id, "📷 Фото получено! Ожидает модерации.")
    keyboard = {"inline_keyboard": [[
        {"text": "✅ Принять", "callback_data": f"approve:{short_id}"},
        {"text": "❌ Отклонить", "callback_data": f"reject:{short_id}"}
    ]]}
    for mod_id in MODERATOR_IDS:
        send_photo(mod_id, photo_id, caption=f"🕵️ Фото от пользователя {user_id}", reply_markup=keyboard)

# -------------------- Callback --------------------
def handle_callback(query):
    data = query["data"]
    user_id = str(query["from"]["id"])
    message = query["message"]
    chat_id = message["chat"]["id"]
    if data == "buy_white_shirt" or data == "buy_black_shirt":
        price = 500
        if users[user_id]["coins"] < price:
            send_message(chat_id, f"❌ У тебя недостаточно Mirataki. Нужно {price}.")
            return

        color = "белую" if data == "buy_white_shirt" else "чёрную"

        users[user_id]["state"] = {
            "action": "await_address",
            "product": f"shirt_{color}",
            "price": price,
            "color": color
        }

        save_json(USERS_FILE, users)
        send_message(
    chat_id,
    f"📦 Введи адрес доставки для получения {color} футболки.\n\n📌 Пример: г. Алматы, улица Пушкина 7а, +77001234567"
)
        return

    if data == "confirm_address":
        state = users[user_id].get("state", {})
        address = state.get("temp_address")
        price = state.get("price")
        color = state.get("color", "неизвестный цвет")


        if not address:
            send_message(chat_id, "⚠️ Адрес не найден. Попробуй снова.")
            return

        users[user_id]["coins"] -= price
        users[user_id].setdefault("purchases", []).append({
            "product": "Футболка Mirataki",
            "address": address,
            "time": datetime.utcnow().isoformat()
        })

        users[user_id]["state"] = {}
        save_json(USERS_FILE, users)

        send_message(chat_id, f"✅ Заказ оформлен!\nФутболка Mirataki ({color}) будет отправлена по адресу:\n📍 {address}")


        for mod_id in MODERATOR_IDS:
            send_message(mod_id, f"📦 Новый заказ от пользователя {user_id}:\nФутболка Mirataki ({color})\n📍 Адрес: {address}")
        return
    elif data == "convert_to_tenge":
        users[user_id]["state"] = {"action": "enter_convert_amount"}
        send_message(chat_id, "💱 Введи количество Mirataki, которое хочешь обменять (1 Mirataki = 10 ₸):")
        return



    if str(user_id) not in MODERATOR_IDS:
        return

    parts = data.split(":")
    action = parts[0]

    if action == "approve":
        photo_id = parts[1]
        if photo_id not in pending:
            send_message(chat_id, "⚠️ Это фото уже обработано.")
            return

        target_id = pending[photo_id]["user_id"]
        target_chat = pending[photo_id]["chat_id"]

        #send_message(target_chat, "✅ Фото одобрено! Ожидается подтверждение уровня местности.")
        send_message(chat_id, f"👍 Фото одобрено. Пользователь: {target_id}")

        # Показать кнопки для выбора уровня
        reward_markup = {
            "inline_keyboard": [
                [{"text": "🟢 Лёгкий (Парк)", "callback_data": f"reward:{photo_id}:парк"}],
                [{"text": "🟡 Средний (Центр)", "callback_data": f"reward:{photo_id}:центр"}],
                [{"text": "🔴 Сложный (Горы)", "callback_data": f"reward:{photo_id}:горы"}],
            ]
        }
        send_message(chat_id, "Выберите уровень сложности местности:", reply_markup=reward_markup)

    elif action == "reject":
        photo_id = parts[1]
        if photo_id not in pending:
            send_message(chat_id, "⚠️ Это фото уже обработано.")
            return

        target_id = pending[photo_id]["user_id"]
        target_chat = pending[photo_id]["chat_id"]

        send_message(target_chat, "❌ Фото отклонено.")
        send_message(chat_id, f"🗑 Фото отклонено. Пользователь: {target_id}")
        del pending[photo_id]

    elif action == "reward":
        photo_id = parts[1]
        level = parts[2]

        if photo_id not in pending:
            send_message(chat_id, "⚠️ Это фото уже обработано.")
            return

        target_id = pending[photo_id]["user_id"]
        target_chat = pending[photo_id]["chat_id"]

        # Выдаём награду в зависимости от уровня
        reward_map = {
            "парк": 25,
            "центр": 75,
            "горы": 150,
        }
        reward = reward_map.get(level.lower(), 25)

        users.setdefault(target_id, {"coins": 0, "invited": [], "raffle": False, "registered": False})
        checkins.setdefault(target_id, [])

        if photo_id not in checkins[target_id]:
            checkins[target_id].append(photo_id)
            users[target_id]["coins"] += reward
            check_achievements(target_id)
            send_message(target_chat, f"✅ Фото одобрено! +{reward} Mirataki 🎉")
        else:
            send_message(target_chat, "⚠️ Это фото уже было принято ранее.")

        send_message(chat_id, f"🏔 Награда за фото выдана: {reward} Mirataki. ({level})")
        del pending[photo_id]

    # Сохраняем изменения
    save_json(USERS_FILE, users)
    save_json(CHECKINS_FILE, checkins)
    save_json(PENDING_FILE, pending)
# -------------------- Главный цикл --------------------
def get_updates(offset=None):
    try:
        params = {"timeout": 100, "offset": offset}
        return requests.get(URL + "getUpdates", params=params).json()
    except Exception as e:
        logging.error(f"Ошибка getUpdates: {e}")
        return {}

def main():
    last_update_id = None
    logging.info("🤖 MiratakiBot запущен...")
    while True:
        updates = get_updates(last_update_id)
        for update in updates.get("result", []):
            if "callback_query" in update:
                handle_callback(update["callback_query"])
            elif "message" in update:
                msg = update["message"]
                user_id = str(msg["from"]["id"])
                chat_id = msg["chat"]["id"]
                if "photo" in msg:
                    photo_id = msg["photo"][-1]["file_id"]
                    handle_photo(user_id, chat_id, photo_id)
                elif "text" in msg:
                    handle_text(user_id, chat_id, msg["text"])
            last_update_id = update["update_id"] + 1
        time.sleep(1)

if __name__ == "__main__":
    main()
