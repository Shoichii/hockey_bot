from aiogram import types
import asyncio
import aioschedule
from bot import django_crud as dj
from bot.loader import bot
from datetime import datetime, timedelta


async def user_notification(user_data, training_data, when):
    alarm = ''
    if user_data.get('truant'):
        alarm = 'Вы давно не посещали тренировку. Ждём Вас снова!'
    if when == 'today':
        if user_data.get('first_not'):
            when = 'Сегодня '
        else:
            when = 'Напоминаем, сегодня '
    if when == 'tomorrow':
        when = 'Завтра '
    date = training_data.get('date').strftime("%d.%m.%Y")
    time = training_data.get('time').strftime("%H:%M")
    place = training_data.get('place')
    address = training_data.get('address')
    url = training_data.get('route')
    if training_data.get('day') == 'friday':
        training_type = '( *игровая тренировка* )'
    else:
        training_type = '( *тренировка* )'
    message = f'''Уважаемый хоккеист!
<b>{alarm}</b>
{when}{date}
🕖Лёд в {time}{training_type} 
🏟Стадион: {place} 
{address}

Вы пойдёте на тренировку?
Спасибо.

<a href="{url}">Построить маршрут</a>
'''
    second_accept_button = types.InlineKeyboardButton('Пойду', callback_data='accept_button')
    declain_button = types.InlineKeyboardButton('Не пойду', callback_data='declain_button')
    keyboard = types.InlineKeyboardMarkup().row(declain_button, second_accept_button)
    try:
        await bot.send_message(disable_web_page_preview=True, chat_id=user_data.get('id'), text=message, reply_markup=keyboard)
        await dj.make_entry(user_data.get('id'), training_data, user_data.get('newbie'))
    except Exception as e:
        print(e)

async def rate_notification(user, training_id):
    message = '''
Оцените пожалуйста тренировку.
'''
    rate_button_1 = types.InlineKeyboardButton('1🌟', callback_data=f'rate_button_1_{training_id}')
    rate_button_2 = types.InlineKeyboardButton('2🌟', callback_data=f'rate_button_2_{training_id}')
    rate_button_3 = types.InlineKeyboardButton('3🌟', callback_data=f'rate_button_3_{training_id}')
    rate_button_4 = types.InlineKeyboardButton('4🌟', callback_data=f'rate_button_4_{training_id}')
    rate_button_5 = types.InlineKeyboardButton('5🌟', callback_data=f'rate_button_5_{training_id}')
    keyboard = types.InlineKeyboardMarkup().row(rate_button_1, rate_button_2, rate_button_3,
                                            rate_button_4, rate_button_5)
    try:
        await bot.send_message(chat_id=user.get('id'), text=message, reply_markup=keyboard)
        await dj.add_0_to_entry(training_id)
    except Exception as e:
        print(e)

async def game_notification(user, game, was_call=False):
    date = game.date_time.strftime("%d.%m.%Y") 
    time = game.date_time.strftime("%H:%M")
    name = user.get('name')
    place = game.place
    address = game.address
    url = game.route
    if was_call:
        when = ''
    else:
        when = 'Завтра '
    message = f'''
Уважаемый, {name}

<b>{when}{date} в {time} состоится игра.</b>
Место: {place}
Адрес: {address}
<a href="{url}">Построить маршрут</a>
'''
    id = user.get('id')
    game_id = game.id
    second_accept_button = types.InlineKeyboardButton('Пойду', callback_data=f'accept_game_button_{game_id}')
    declain_button = types.InlineKeyboardButton('Не пойду', callback_data=f'declain_game_button_{game_id}')
    keyboard = types.InlineKeyboardMarkup().row(declain_button, second_accept_button)
    print(name)
    print(user.get('id'))
    try:
        await bot.send_message(disable_web_page_preview=True, chat_id=id, text=message, reply_markup=keyboard)
        await dj.make_game_entry(game.date_time, user.get('id'))
    except Exception as e:
        print(e)

async def training_checker():
    now = datetime.now()
    yesterday_day = now - timedelta(days=1)
    # tomorrow_day = now + timedelta(days=1)
    today_day = now.strftime("%A").lower()
    yesterday_day = yesterday_day.strftime("%A").lower()
    # tomorrow_day = tomorrow_day.strftime("%A").lower()
    trainings = await dj.get_trainings([yesterday_day, today_day])
    if not trainings:
        return
    if trainings.get('yesterday'):
        not_data = await dj.get_users_for_not_yesterday(trainings.get('yesterday').get('day'))
        if not not_data:
                return
        for i,user in enumerate(not_data.get('users_data')):
            training_id = not_data.get('training_ids')[i]
            await rate_notification(user, training_id)
        
    if trainings.get('today'):
        current_time = datetime.strptime(now.strftime("%H:%M:%S"), '%H:%M:%S').time()
        # раскоментировать и создать файл time.txt для имитации текущего времени
        # в файл записать время в формате 09:00:00
        # time_str = ''
        # with open('Bot/time.txt', 'r') as file:
        #     # Считываем первую строку файла
        #     time_str = file.readline().strip()
        # current_time = datetime.strptime(time_str, '%H:%M:%S').time()
        current_hours = int(current_time.hour)
        training_time = trainings.get('today').get('time')
        training_hours = int(training_time.hour)
        difference_hours = training_hours - current_hours
        if 4 < difference_hours <= 13:
            not_data = await dj.get_users_for_first_not(trainings.get('today').get('day'))
            if not not_data:
                return
            users_data = not_data.get('users_data')
            for user_data in users_data:
                await user_notification(user_data, not_data.get('training_data'), 'today')

        if 0 < difference_hours <= 4:
            not_data = await dj.get_users_for_second_not(trainings.get('today').get('day'))
            if not not_data:
                return
            users_data = not_data.get('users_data')
            for user_data in users_data:
                await user_notification(user_data, not_data.get('training_data'), 'today')
    # if trainings.get('tomorrow'):
    #     current_time = datetime.strptime(now.strftime("%H:%M:%S"), '%H:%M:%S').time()
    #     current_hours = int(current_time.hour)
    #     training_time = trainings.get('tomorrow').get('time')
    #     training_hours = int(training_time.hour)
        
    #     difference_hours = training_hours - current_hours
    #     if difference_hours <= 4:
    #         not_data = await dj.get_users_for_not_tomorrow(trainings.get('tomorrow').get('day'))
    #         if not not_data:
    #             return
    #         users_data = not_data.get('users_data')
    #         for user_data in users_data:
    #             await user_notification(user_data, not_data.get('training_data'), 'tomorrow')

async def game_checker():
    games_data = await dj.get_games()
    if not games_data:
        return
    for game in games_data:
        users_data = await dj.get_users_game_notfn(game.date_time)
        if users_data:
            for user in users_data:
                await game_notification(user, game)




async def scheduler():
    aioschedule.every(5).seconds.do(training_checker)
    aioschedule.every(5).seconds.do(game_checker)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())