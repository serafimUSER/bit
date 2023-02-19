from aiogram import Bot, Dispatcher, executor, types
from html import escape

import core.config as config
import logging

import random
import json

import aiohttp
import asyncio


async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:5000/api/v1/data') as response:
            data = await response.json()
            return data


async def update():
    loop = asyncio.get_event_loop()
    data = await loop.create_task(fetch_data())

    tasks_data = data['tasks']
    tasks = len(tasks_data)

    # Modes
    modes = data["modes"]

    return tasks_data, tasks, modes



# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

with open("core/sessions.json", 'rb') as data:
    database = json.loads(data.read())

def write_session(json_data):
    with open('core/sessions.json', 'w+') as file:
        file.write(json.dumps(json_data, indent=4))


def random_task(id_session, tasks_data, modes):
    mode = modes[database[id_session]["game"]["status_game"]]
    mode_tags = mode["tags"]

    tasks = tasks_data
    mode_tasks = [task for task in tasks.values() if any(tag in task["tags"] for tag in mode_tags)]

    game_task = mode_tasks[random.randint(0, len(mode_tasks)-1)]
    data = database[id_session]["game"]["users"]
    user = data[random.randint(0, len(data)-1)]

    num = 0

    if database[id_session]["last"] != "":
        while database[id_session]["last"]["user"] != user or database[id_session]["last"]["text"] != game_task['text']:
            if num == 5:
                break
            game_task = mode_tasks[random.randint(0, len(mode_tasks)-1)]

            data = database[id_session]["game"]["users"]
            user = data[random.randint(0, len(data)-1)]

            num += 1

    database[id_session]["last"] = {
        "user": user,
        "text": game_task['text']
    }
    write_session(database)

    tags = ""
    for game_tag in game_task["tags"]:
        tags += f"#{game_tag} "

    return f"Задание для <b>{escape(user)}</b>\n\n{game_task['text']}\n{tags}"
    

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    play_start = types.InlineKeyboardMarkup()
    play_start.add(
        types.InlineKeyboardButton("Играть 🎲", callback_data="play")
    )
    
    database[str(message.chat.id)] = {"game": {"users": [], "status_game": ""}, "status": "", "last": ""}
    write_session(database)

    await message.reply(
    f"""<b>{escape('Добро пожаловать,')}</b> {message.from_user.username}! 👋
    
Если ты хочешь <b>{escape('отлично')}</b> провести время в компании - ты по адресу! Мы предоставляем простую и интересную игру. Ниже можешь ознакомиться с правилами ⬇

Правила игры просты 💫:
1. Выбирай тему, количество игроков и их ники
2. Игроки по очереди отвечают на вопросы или выполняют действия
3. Всем весело и здорово
""", parse_mode="HTML", reply_markup=play_start)


@dp.message_handler(commands=['newgame'])
async def newgame(msg: types.Message):
    database[str(msg.chat.id)] = {"game": {"users": [], "status_game": ""}, "status": ""}
    write_session(database)
    class Call:
        message = msg
        
    await play(Call)

@dp.callback_query_handler(text="play")
async def play(call: types.CallbackQuery):
    team = types.ReplyKeyboardMarkup(resize_keyboard=True)
    num = 0
    
    tasks_data, _, modes = await update()
    
    def gen_tow(team):
        team.row(
                types.KeyboardButton(list(modes.keys())[mode_index]),
                types.KeyboardButton(list(modes.keys())[mode_index+1])
        )
    
    for mode_index in range(len(modes)):
        if len(modes) % 2 == 0:
            if num == 1:
                num = 0
                continue
            
            gen_tow(team)
            num = 1
        else:
            if mode_index == len(list(modes.keys()))-1:
                team.add(types.KeyboardButton(list(modes.keys())[mode_index]))
                break
            
            elif num == 1:
                num = 0
                continue
            
            gen_tow(team)
            num = 1
    
    database[str(call.message.chat.id)]["status"] = "status"
    write_session(database)

    await bot.send_message(call.message.chat.id, "Выберете режим игры: ", reply_markup=team)


@dp.message_handler(content_types=["text"])
async def echo(message: types.Message):
    tasks_data, _, modes = await update()
    if database[str(message.chat.id)]["status"] == "status":
        for i in list(modes.keys()):
            if message.text == i:
                database[str(message.chat.id)]["game"]["status_game"] = i
                database[str(message.chat.id)]["status"] = "users"
                write_session(database)
                
                await bot.send_message(message.chat.id, "Введите через запятую пользователей: ")
                
    elif database[str(message.chat.id)]["status"] == "users":
        database[str(message.chat.id)]["status"] = ""
        users = list(filter(lambda li: li != "", message.text.replace(" ", "").split(",")))
        database[str(message.chat.id)]["game"]["users"] = users
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Закончить игру 🚫", callback_data="game_stop"),
            types.InlineKeyboardButton("Дальше ➡", callback_data="next")
        )
        write_session(database)
        tasks_data, _, modes = await update()
        
        await bot.send_message(message.chat.id, random_task(str(message.chat.id), tasks_data, modes), parse_mode="HTML", reply_markup=markup)

@dp.callback_query_handler(text="next")
async def next(call: types.CallbackQuery):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Закончить игру 🚫", callback_data="game_stop"),
        types.InlineKeyboardButton("Дальше ➡", callback_data="next")
    )
    tasks_data, _, modes = await update()
    await bot.send_message(call.message.chat.id, random_task(str(call.message.chat.id), tasks_data, modes), parse_mode="HTML", reply_markup=markup)

@dp.callback_query_handler(text="game_stop")
async def game_stop(call: types.CallbackQuery):
    database[str(call.message.chat.id)] = {"game": {"users": [], "status_game": ""}, "status": ""}
    write_session(database)
    await bot.send_message(call.message.chat.id, "Хорошего настроения 😇\nЧтобы начать новую игру введит /newgame")



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
