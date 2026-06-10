import telebot
import json
import os
import ran
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🏔 *Тихий Алтай*\n\nВыбирайте действие на кнопках:",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "🏔 Найти тихое место")
def find_place(message):
    places = load_places()
    good = [p for p in places if p.get('confirm', 0) > 0]
    
    if not good:
        bot.send_message(message.chat.id, "😔 Нет подтверждённых мест. Добавьте первым!")
        return
    
    selected = random.sample(good, min(3, len(good)))
    answer = "🏔 *Где сейчас тихо:*\n\n"
    for i, p in enumerate(selected, 1):
        answer += f"{i}. *{p['name']}*\n   📍 {p['loc']}\n   👍 {p['confirm']}\n\n"
    
    bot.send_message(message.chat.id, answer, parse_mode='Markdown')

user_data = {}

@bot.message_handler(func=lambda m: m.text == "➕ Добавить место")
def add_place_start(message):
    msg = bot.send_message(message.chat.id, "📍 Напишите *название* места:", parse_mode='Markdown')
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    user_data[message.chat.id] = {'name': message.text}
    msg = bot.send_message(message.chat.id, "📍 Напишите *описание* (как найти):", parse_mode='Markdown')
    bot.register_next_step_handler(msg, get_loc)

def get_loc(message):
    name = user_data.get(message.chat.id, {}).get('name', '')
    loc = message.text
    
    places = load_places()
    places.append({
        'name': name,
        'loc': loc,
        'confirm': 0,
        'who': []
    })
    save_places(places)
    
    bot.send_message(message.chat.id, f"✅ *{name}* добавлено!", parse_mode='Markdown')
    del user_data[message.chat.id]

@bot.message_handler(func=lambda m: m.text == "📝 Подтвердить")
def confirm_list(message):
    places = load_places()
    if not places:
        bot.send_message(message.chat.id, "😔 Нет мест")
        return
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for p in places:
        btn = telebot.types.InlineKeyboardButton(p['name'], callback_data=f"c_{p['name']}")
        markup.add(btn)
    
    bot.send_message(message.chat.id, "🗳 Где сейчас тихо?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('c_'))
def confirm_place(call):
    name = call.data.replace('c_', '')
    places = load_places()
    uid = str(call.from_user.id)
    
    for p in places:
        if p['name'] == name:
            if uid not in p.get('who', []):
                p['confirm'] = p.get('confirm', 0) + 1
                p['who'].append(uid)
                save_places(places)
                bot.answer_callback_query(call.id, f"✅ Спасибо! Теперь {p['confirm']} подтверждений")
            else:
                bot.answer_callback_query(call.id, "⚠️ Вы уже подтверждали", show_alert=True)
            return
    
    bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    places = load_places()
    total = len(places)
    confirmed = len([p for p in places if p.get('confirm', 0) > 0])
    bot.send_message(
        message.chat.id,
        f"📊 *
