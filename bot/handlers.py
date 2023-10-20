import re
from datetime import datetime, timedelta
from typing import List

from aiogram import types
from aiogram.dispatcher import FSMContext

from bot import django_crud as dj
from bot.config import ADM_ID
from bot.dialogue_utils import (send_dialogue_message,
                                send_dialogue_message_with_media)
from bot.loader import dp, bot
from bot.states import Adm_State, Dialogue_State, StartState, CahngeProfileState
from bot.utils import user_notification


async def main_menu_message(msg):
    message = '''<b>Доброе пожаловать в ХК "Катюша"!</b>

Если Вы уже посещали наши тренировки, выберите - <b>"Войти"</b>.
В ином случае выберите - <b>"Регистрация"</b>
'''
    sign_in_button = types.InlineKeyboardButton('Войти', callback_data='sign_in_button')
    sign_up_button = types.InlineKeyboardButton('Регистрация', callback_data='sign_up_button')
    keyboard = types.InlineKeyboardMarkup().row(sign_in_button, sign_up_button)
    await msg.answer(message, reply_markup=keyboard)

#приветстви только новых пользователей бота
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if msg.from_user.id == ADM_ID:
        button_1 = types.KeyboardButton('Уже записались 🏒')
        button_2 = types.KeyboardButton('Оценки тренировок 📊')
        button_3 = types.KeyboardButton('Рупор 📢')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(button_3)
        keyboard.row(button_2, button_1)
        await msg.answer('Добро пожаловать! Админ-мод включен.', reply_markup=keyboard)
    else:
        tg_id = await dj.check_new_user(msg.from_user.id)
        if not tg_id:
            await main_menu_message(msg)

@dp.message_handler(commands=['schedule'])
async def show_shedule(msg: types.Message):
    trainings_data = await dj.get_shedule()
    message = '''
Тренировки на эту неделю:


'''
    for data in trainings_data:
        day = data.get('day')
        time = data.get('time')
        place = data.get('place')
        address = data.get('address')
        message += f'<b>{day} {time} - {place} | {address}</b>\n'
    
    await msg.answer(message)

#диалог с тренером
@dp.message_handler(commands=['dialogue'])
async def start_dialogue(msg: types.Message):
    if msg.from_user.id == ADM_ID:
        await msg.answer('Эта функция доступна только игрокам.')
        return
    message = '''
Режим диалога включён.
Всё, что Вы напишите, будет отправлено тренеру ХК "Катюша".
Чтобы выйти из диалога воспользуйтесь командой /stop_dialogue.
'''
    await msg.answer(message)
    await Dialogue_State.start.set()

@dp.message_handler(commands=['stop_dialogue'], state=Dialogue_State.start)
async def cancel_dialogue(msg: types.Message, state: FSMContext):
    if msg.from_user.id == ADM_ID:
        await msg.answer('Эта функция доступна только игрокам.')
        return
    await msg.answer('Режим диалога выключен.')
    await state.finish()

@dp.message_handler(commands=['training_today'])
async def get_training_info(msg: types.Message):
    if msg.from_user.id == ADM_ID:
        await msg.answer('Эта команда для игроков')
        return
    training_data = await dj.get_training_info()
    if not training_data:
        await msg.answer('Запись на тренировку завершена')
        return
    if training_data == 'not today':
        await msg.answer('На сегодня тренировок нет')
        return
    await user_notification({'id': msg.from_user.id, 'first_not': True} ,training_data, 'today')

async def get_user_profile(msg):
    user_data = await dj.check_new_user(msg.from_user.id)
    if not user_data:
        await msg.answer('Войдите в профиль или зарегистрируйтесь')
        return
    name = user_data.name
    phone = user_data.tel_number
    birthday = user_data.birthday.strftime('%d.%m.%Y')
    message = f'''
ФИО: {name}
Номер телефона: {phone}
День рождения: {birthday}

Что желаете изменить?
'''
    change_name_button = types.InlineKeyboardButton('ФИО', callback_data='change_button_name')
    change_phone_button = types.InlineKeyboardButton('Номер телефона', callback_data='change_button_phone')
    change_birthday_button = types.InlineKeyboardButton('День рождения', callback_data='change_button_birthday')
    keyboard = types.InlineKeyboardMarkup().row(change_name_button, change_phone_button).add(change_birthday_button)
    await msg.answer(message, reply_markup=keyboard)

@dp.message_handler(commands=['my_profile'])
async def get_training_info(msg: types.Message):
    if msg.from_user.id == ADM_ID:
        await msg.answer('Эта команда для игроков')
        return
    await get_user_profile(msg)

@dp.callback_query_handler(lambda call: call.data.startswith('change_button'))
async def change_data(call: types.CallbackQuery):
    await call.message.delete()
    data_for_change = call.data.split('_')[2]
    if data_for_change == 'name':
        await call.message.answer('Напишите ФИО')
        await CahngeProfileState.name.set()
    if data_for_change == 'phone':
        await call.message.answer('Напишите номер телефона в формате: 89000000000(числа подряд)')
        await CahngeProfileState.phone_number.set()
    if data_for_change == 'birthday':
        await call.message.answer('Напишите день рождения в формате: 01.01.1970')
        await CahngeProfileState.birthday.set()
        

@dp.message_handler(state=CahngeProfileState.name)
async def change_name(msg: types.Message, state: FSMContext):
    await dj.change_name(msg.from_user.id, msg.text)
    await msg.answer('Имя изменено')
    await get_user_profile(msg)
    await state.finish()

@dp.message_handler(state=CahngeProfileState.phone_number)
async def change_phone(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and len(msg.text) == 11:
        await dj.change_phone(msg.from_user.id, msg.text)
        await msg.answer('Номер телефона изменен')
        await get_user_profile(msg)
        await state.finish()
    else:
        await msg.answer('Неверный формат. Повторите ввод.')

@dp.message_handler(state=CahngeProfileState.birthday)
async def change_birthday(msg: types.Message, state: FSMContext):
    regex = r"\d{2}\.\d{2}\.\d{4}"
    if not re.search(regex, msg.text):
        await msg.answer('Неверный формат даты. Повторите ввод.', reply_markup=cancel_reg_keyboard())
        return
    date_object = datetime.strptime(msg.text, "%d.%m.%Y")
    birthday = date_object.strftime("%Y-%m-%d")
    await dj.change_birthday(msg.from_user.id, birthday)
    await msg.answer('Дата рождения изменена')
    await get_user_profile(msg)
    await state.finish()


@dp.message_handler(is_media_group=False,
                    content_types=['text', 'audio', 'document', 'sticker', 'photo', 
                                'video', 'voice', 'contact', 'location'],
                    state=Dialogue_State.start)
async def dialog_handler(msg: types.Message):
    await send_dialogue_message(msg)


@dp.message_handler(is_media_group=True, content_types=['audio', 'document', 'photo', 'video'],
                    state=Dialogue_State.start)
async def dialog_handler_media(msg: types.Message, album: List[types.Message]):
    await send_dialogue_message_with_media(msg,album)

#для разбивки крупного сообщения
def split_message(message, max_length=4096):
    """Разбивает сообщение на части, не превышающие max_length символов."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

async def show_users(msg):
    users_data = await dj.get_accept_users()
    if not users_data:
        await msg.answer('Ещё никто не записался')
        return
    message1 = '''Уже записались:
    
'''
    message2 = '''

Передумали и отказались:

'''
    counter1 = 0
    counter2 = 0
    for user in users_data:
        name = user.get('name')
        birthday = user.get('birthday')
        newbie = user.get('newbie')
        if user.get('changed'):
            counter2 += 1
            message2 += f'{counter2}) {name} {birthday} {newbie}\n'
        else:
            counter1 += 1
            message1 += f'{counter1}) {name} {birthday} {newbie}\n'


    message = message1 + message2
    try:
        await msg.answer(message)
    except Exception as e:
        if str(e) == 'Message is too long':
            parts = split_message(message, max_length=4096)
            for part in parts:
                await msg.answer(part)

@dp.message_handler(is_media_group=False,
                    content_types=['text', 'audio', 'document', 'sticker', 'photo', 
                                'video', 'voice', 'contact', 'location'])
async def dialog_handler(msg: types.Message):
    if msg.from_user.id == ADM_ID:
        if msg.text == 'Оценки тренировок 📊':
            message = '''
Какую тренировку хотите посмотреть?
'''
            select_date_button = types.InlineKeyboardButton('Указать дату', callback_data='select_date_button')
            yesterday_training_button = types.InlineKeyboardButton('Вчерашняя', callback_data='yesterday_training_button')
            keyboard = types.InlineKeyboardMarkup().row(select_date_button, yesterday_training_button)
            await msg.answer(message, reply_markup=keyboard)
        elif msg.text == 'Уже записались 🏒':
            await show_users(msg)
        elif msg.text == 'Рупор 📢':
            await msg.answer('Напишите сообщения для всех игроков. (Сообщение может содержать текст и одну картинку)')
            await Adm_State.megaphone.set()
        else:
            await send_dialogue_message(msg)

@dp.message_handler(state=Adm_State.megaphone, content_types=['text', 'photo'])
async def save_message_to_state(msg: types.Message, state: FSMContext):
    if msg.content_type == 'text':
        await state.update_data(text=msg.text, photo=None)
    if msg.content_type == 'photo':
        await state.update_data(text=msg.caption, photo=msg.photo[-1].file_id)
    cancel_megaphone_button = types.InlineKeyboardButton('Отмена', callback_data='cancel_megaphone_button')
    send_megaphone_button = types.InlineKeyboardButton('Отправить', callback_data='send_megaphone_button')
    keyboard = types.InlineKeyboardMarkup().row(cancel_megaphone_button, send_megaphone_button)
    await msg.answer('''
Отправить?

Внимание. Можно отправить только одно сообщение - последнее из написаных.
Если Вы хотите отправить другое, то просто напишите новое сообщение.
''', reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == 'cancel_megaphone_button', state=Adm_State.megaphone)
async def cancel_megaphone(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Отправка отменена.')
    await state.finish()

@dp.callback_query_handler(lambda call: call.data == 'send_megaphone_button', state=Adm_State.megaphone)
async def send_megaphone(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    users_ids = await dj.get_users_ids()
    state_data = await state.get_data()
    state_text = state_data.get('text')
    state_photo = state_data.get('photo')
    for_del = await call.message.answer('📩 Рассылаю...')
    for id in users_ids:
        try:
            if state_photo:
                await bot.send_photo(chat_id=id, photo=state_photo, caption=state_text)
            else:
                await bot.send_message(chat_id=id, text=state_text)
        except Exception as e:
            print(e)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=for_del.message_id)
    await call.message.answer('Сообщение отправлено.')
    await state.finish()

@dp.message_handler(is_media_group=True, content_types=['audio', 'document', 'photo', 'video'])
async def dialog_handler_media(msg: types.Message, album: List[types.Message]):
    if msg.from_user.id == ADM_ID:
        await send_dialogue_message_with_media(msg,album)


#показать оценки за вчершанюю тренировку
@dp.callback_query_handler(lambda call: call.data == 'yesterday_training_button')
async def get_yesterday_rates(call: types.CallbackQuery):
    await call.message.delete()
    rates_data = await dj.get_training_rates()
    if not rates_data:
        await call.message.answer('Вчера тренировок не было.')
        return
    message = 'Оценки за вчершанюю тренировку:\n\n'
    for user in rates_data.get('users'):
        name = user.get('name')
        rate = user.get('rate')
        message += f'{name} - {rate}\n'
    average_score = rates_data.get('average_score')
    message += f'\n<b>Средняя оценка тренировки - {average_score}</b>'
    await call.message.answer(message)

#показать оценки за тренировку по выбранной дате
@dp.callback_query_handler(lambda call: call.data == 'select_date_button')
async def get_rates_by_date(call: types.CallbackQuery):
    await call.message.delete()
    cancel_training_date_button = types.InlineKeyboardButton('Отмена', callback_data='cancel_training_date_button')
    keyboard = types.InlineKeyboardMarkup().add(cancel_training_date_button)
    await call.message.answer('Напишите дату тренировки в формате: 01.01.1970',
                            reply_markup=keyboard)
    await Adm_State.training_date.set()

@dp.callback_query_handler(lambda call: call.data == 'cancel_training_date_button',
                        state=Adm_State.training_date)
async def cancel_training_date(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Действие отменено.')
    await state.finish()


@dp.message_handler(state=Adm_State.training_date)
async def get_rates_by_date(msg: types.Message, state: FSMContext):
    regex = r"\d{2}\.\d{2}\.\d{4}"
    if not re.search(regex, msg.text):
        cancel_training_date_button = types.InlineKeyboardButton('Отмена', callback_data='cancel_training_date_button')
        keyboard = types.InlineKeyboardMarkup().add(cancel_training_date_button)
        await msg.answer('Неверный формат даты. Повторите ввод.', reply_markup=keyboard)
        return
    date_object = datetime.strptime(msg.text, "%d.%m.%Y")
    training_date = date_object.strftime("%Y-%m-%d")
    rates_data = await dj.get_training_rates(training_date)
    if not rates_data:
        await msg.answer('В этот день тренировок не было.')
        await state.finish()
        return
    message = f'Оценки за тренировку от {msg.text}:\n\n'
    for user in rates_data.get('users'):
        name = user.get('name')
        rate = user.get('rate')
        message += f'{name} - {rate}\n'
    average_score = rates_data.get('average_score')
    message += f'\n<b>Средняя оценка тренировки - {average_score}</b>'
    await msg.answer(message)
    await state.finish()

#вход для существующих пользователей
@dp.callback_query_handler(lambda call: call.data == 'sign_in_button')
async def sign_in(call: types.CallbackQuery):
    await call.message.delete()
    message = '''
Пожалуйста укажите Ваш номер телефона для идентификации.
В формате: 89000000000(числа подряд)'''
    await call.message.answer(message)
    await StartState.phone_number_sign_in.set()

#идентификация существующих пользователей по номеру телефона
@dp.message_handler(state=StartState.phone_number_sign_in)
async def get_tel_number(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and len(msg.text) == 11:
        user_name = await dj.identification_by_tel_number(msg.from_user.id, msg.text)
        if not user_name:
            main_menu_button = types.InlineKeyboardButton('В главное меню', callback_data='main_menu_button')
            keyboard = types.InlineKeyboardMarkup().add(main_menu_button)
            await msg.answer('''🚫 <b>Извините, пользователя с этим номером телефона нет в базе данных.
Возможно Вы записаны под другим номером телефона.</b>

Вы можете:
- Обратиться к тренеру (команда /dialogue).
- Повторить вввод
- Вернуться в главное меню и выполнить регистрацию''', reply_markup=keyboard)
            
            return
        await msg.answer(f'{user_name}, рады Вас приветствовать. Совсем скоро я уведомлю Вас о предстоящей тренировке!')
        await state.finish()
        return
    await msg.answer('Вы неверно ввели номер телефона. Должно быть 11 цифр. Пожалуйста повторите попытку.')
    return

#возврат в главное меню при неудачной попытки войти
@dp.callback_query_handler(lambda call: call.data == 'main_menu_button', state=StartState.phone_number_sign_in)
async def back_to_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await main_menu_message(call.message)
    await state.finish()

#клавиатура отмены регистрации
def cancel_reg_keyboard():
    cancel_reg_button = types.InlineKeyboardButton('Отмена', callback_data='cancel_reg_button')
    keyboard = types.InlineKeyboardMarkup().add(cancel_reg_button)
    return keyboard

#регистрация новых пользователей
@dp.callback_query_handler(lambda call: call.data == 'sign_up_button')
async def sign_up(call: types.CallbackQuery):
    await call.message.delete()
    message = '''
Давайте знакомится. Напишите пожалуйста Ваши ФИО.'''

    await call.message.answer(message, reply_markup=cancel_reg_keyboard())
    await StartState.name.set()

#отмена при записи имени
@dp.callback_query_handler(lambda call: call.data == 'cancel_reg_button', state=StartState.name)
async def cancel_name(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await main_menu_message(call.message)

#запись имени в State
@dp.message_handler(state=StartState.name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer('''Принято. Теперь укажите Ваш номер телефона.
В формате: 89000000000(числа подряд)''', 
                    reply_markup=cancel_reg_keyboard())
    await StartState.phone_number_sign_up.set()

#отмена при записи номера телефона
@dp.callback_query_handler(lambda call: call.data == 'cancel_reg_button', state=StartState.phone_number_sign_up)
async def cancel_name(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await main_menu_message(call.message)

#запись номера телефона в State
@dp.message_handler(state=StartState.phone_number_sign_up)
async def get_tel_number(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and len(msg.text) == 11:
        await state.update_data(phone_number_sign_up=msg.text)
        await msg.answer('''И последний вопрос. Когда у Вас день рождения?
Укажите в формате: 01.01.1970''', reply_markup=cancel_reg_keyboard())
        await StartState.birthday.set()
    else:
        await msg.answer('Вы неверно ввели номер телефона. Должно быть 11 цифр. Пожалуйста повторите попытку.',
                        reply_markup=cancel_reg_keyboard())

#отмена при записи дня рождения
@dp.callback_query_handler(state=StartState.birthday)
async def cancel_birthday(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await main_menu_message(call.message)

#получение дня рождения и запись всех полученных данных в бд с галочкой "новичок"
@dp.message_handler(state=StartState.birthday)
async def get_birthday(msg: types.Message, state: FSMContext):
    regex = r"\d{2}\.\d{2}\.\d{4}"
    if not re.search(regex, msg.text):
        await msg.answer('Неверный формат даты. Повторите ввод.', reply_markup=cancel_reg_keyboard())
        return
    state_data = await state.get_data()
    name = state_data.get('name')
    phone_number = state_data.get('phone_number_sign_up')
    date_object = datetime.strptime(msg.text, "%d.%m.%Y")
    birthday = date_object.strftime("%Y-%m-%d")
    user_id = msg.from_user.id
    await dj.add_new_user(name, phone_number, birthday, user_id)
    await msg.answer(f'''
ФИО: {name}
Номер телефона: {phone_number}
День рождения: {msg.text}

Регистрация прошла успешно. Рады приветствовать!
Вы всегда можете изменить свои данные с помощью команды /my_profile
Совсем скоро я сообщу Вам место и время проведения Вашей первой тренировки в нашем клубе.''')
    await state.finish()

#запись на занятие
@dp.callback_query_handler(lambda call: call.data == 'accept_button')
async def first_accept(call: types.CallbackQuery):
    today = datetime.today().date()
    training_data_first = await dj.get_training_data_for_accept(today, call.from_user.id)

    now = datetime.now()
    # раскоментировать и создать файл time.txt для имитации текущего времени
    # в файл записать время в формате 09:00:00
    # time_str = ''
    # with open('Bot/time.txt', 'r') as file:
    #     # Считываем первую строку файлаnow
    #     time_str = file.readline().strip()
    # current_time = datetime.strptime(time_str, '%H:%M:%S').time()
    current_time = datetime.strptime(now.strftime("%H:%M:%S"), '%H:%M:%S').time()
    if today >= training_data_first.get('date') and current_time >= training_data_first.get('time'):
        await call.message.delete()
        await call.message.answer('Запись на занятие окончена. Обратитесь к тренеру.')
        return
    await call.message.delete()
    training_data_second = await dj.accept_training(today, call.from_user.id)
    training_time = training_data_first.get('time').strftime("%H:%M")
    training_place = training_data_second.get('place')
    training_address = training_data_second.get('address')
    
    url = training_data_second.get('route')
    message = f'''
<b>Запись прошла успешно! ✅</b>

Ждём Вас сегодня в {training_time}.
Адрес: {training_place}, {training_address}

<a href="{url}">Построить маршрут</a>'''
    await call.message.answer(message, disable_web_page_preview=True)

@dp.callback_query_handler(lambda call: call.data == 'declain_button')
async def declain(call: types.CallbackQuery):
    date_str = call.message.text.split('\n\n')[1].split('\n')[0].split(' ')
    if len(date_str) == 2:
        date_str = date_str[1]
    if len(date_str) == 3:
        date_str = date_str[2]
    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    date = date_obj.strftime("%Y-%m-%d")
    today = datetime.today().date()
    await dj.declain_training(date, call.from_user.id)
    await call.message.delete()
    await call.message.answer('❌ Тренировка отклонена. Ждём Вас в следующий раз!')


#оценка тренировки
@dp.callback_query_handler(lambda call: call.data and call.data.startswith('rate_button'))
async def get_rate(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = call.data.split('_')
    rate = data[2]
    training_id = data[3]
    await dj.set_rate(rate, training_id)
    await call.message.answer('Спасибо за оценку!')




#запись на игру
@dp.callback_query_handler(lambda call: call.data.startswith('accept_game_button'))
async def first_accept(call: types.CallbackQuery):
    await call.message.delete()
    game_id = call.data.split('_')[3]
    game_data = await dj.get_game_data_for_accept(game_id, call.from_user.id)

    now = datetime.now().replace(microsecond=0)
    game_datetime = game_data.get('datetime')
    if now >= game_datetime:
        await call.message.delete()
        await call.message.answer('Запись на игру окончена. Обратитесь к тренеру.')
        return
    
    await dj.accept_game(game_id, call.from_user.id)
    
    url = game_data.get('route')
    address = game_data.get('address')
    place = game_data.get('place')
    game_datetime = game_datetime.strftime("%d.%m.%Y %H:%M")
    message = f'''
<b>Запись прошла успешно! ✅</b>

<b>{game_datetime}</b> - ждём Вас на игру.
Адрес: {place}, {address}

<a href="{url}">Построить маршрут</a>'''
    await call.message.answer(message, disable_web_page_preview=True)


@dp.callback_query_handler(lambda call: call.data.startswith('declain_game_button'))
async def declain(call: types.CallbackQuery):
    game_id = call.data.split('_')[3]
    await dj.declain_game(game_id, call.from_user.id)
    await call.message.delete()
    await call.message.answer('❌ Игра отклонена. Ждём Вас в следующий раз!')