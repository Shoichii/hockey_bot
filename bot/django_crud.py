from asgiref.sync import sync_to_async
from shedule_app import models as mdl
from datetime import datetime, timedelta
from bot.config import DAYS
import logging


@sync_to_async()
def check_new_user(user_id):
    tg_id = mdl.User.objects.filter(telegram_id=user_id).first()
    return tg_id

@sync_to_async()
def get_users_ids():
    users = mdl.User.objects.filter(telegram_id__isnull=False).all()
    telegram_ids = [user.telegram_id for user in users]
    return telegram_ids

@sync_to_async()
def change_phone(user_id, phone):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    user.tel_number = phone
    user.save()

@sync_to_async()
def change_birthday(user_id, birthday):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    user.birthday = birthday
    user.save()

@sync_to_async()
def change_name(user_id, name):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    user.name = name
    user.save()

@sync_to_async()
def identification_by_tel_number(user_id, tel_number):
    str_number = str(tel_number)
    formatted_number = '{}({})-{}-{}-{}'.format(str_number[0], 
            str_number[1:4], str_number[4:7], str_number[7:9], str_number[9:])
    user = mdl.User.objects.filter(tel_number=formatted_number).first()
    if not user:
        return None
    user.telegram_id = user_id
    user.save()
    return user.name

@sync_to_async()
def add_new_user(name, phone_number, birthday, user_id):
    new_user = mdl.User.objects.create(
            name=name, 
            tel_number=phone_number,
            birthday=birthday,
            telegram_id=user_id,
            newbie=True
        )
    new_user.save()

@sync_to_async()
def get_trainings(days):
    trainings = mdl.Training.objects.filter(was_end=False).all()
    if not trainings:
        return None
    yesterday = trainings.filter(day=days[0]).first()
    if yesterday:
        yesterday_day = yesterday.day
        yesterday_time = yesterday.time
        yesterday = {
            'day': yesterday_day,
            'time': yesterday_time
        }
    today = trainings.filter(day=days[1]).first()
    if today:
        today_day = today.day
        today_time = today.time
        today = {
            'day': today_day,
            'time': today_time
        }
    # tomorrow = trainings.filter(day=days[2]).first()
    # if tomorrow:
    #     tomorrow_day = tomorrow.day
    #     tomorrow_time = tomorrow.time
    #     tomorrow = {
    #         'day': tomorrow_day,
    #         'time': tomorrow_time
    #     }
    return {
        'yesterday': yesterday,
        'today': today,
    }

# @sync_to_async()
# def get_users_for_not_tomorrow(day):
#     users = mdl.User.objects.filter(telegram_id__isnull=False).all()
#     training = mdl.Training.objects.filter(day=day, was_end=False).first()
#     today = datetime.now().date()
#     tomorrow = today + timedelta(days = 1)
#     formatted_date = tomorrow.strftime("%Y-%m-%d")
#     users_data = []
#     for user in users:
#         journal_entry = mdl.Journal.objects.filter(user=user, date=formatted_date,).first()
#         if not journal_entry:
#             missed_trainings = mdl.Journal.objects.filter(user=user).all()[:6]
#             missed_counter = 0
#             for missed_training in missed_trainings:
#                 if not missed_training.accept:
#                     missed_counter += 1
#                 else:
#                     break
#             truant = False
#             if missed_counter >= 6:
#                 truant = True
#             new_journal_entry = mdl.Journal.objects.create(
#                 training=training,
#                 user = user,
#                 date = formatted_date,
#             )
#             new_journal_entry.save()
#             users_data.append({
#                 'id': user.telegram_id,
#                 'name': user.name,
#                 'truant': truant,
#             })
#     if len(users_data) == 0:
#         return None
#     training_data = {
#         'date': tomorrow,
#         'time': training.time,
#         'place': training.place,
#         'address': training.address,
#     }
#     return {
#         'users_data': users_data,
#         'training_data': training_data
#     }

@sync_to_async()
def get_training_data_for_accept(date,user_id):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    journal_entry = mdl.Journal.objects.filter(user=user, date=date).first()
    training_data = {
        'date': journal_entry.date,
        'time': journal_entry.training.time,
    }
    return training_data


@sync_to_async()
def accept_training(date,user_id):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    journal_entry = mdl.Journal.objects.filter(user=user, date=date).first()
    
    journal_entry.previuos_answer = journal_entry.accept
    journal_entry.accept = True
    journal_entry.second_not = True
    journal_entry.answer_time = datetime.now()
    journal_entry.save()

    training_data = {
        'date': journal_entry.date,
        'time': journal_entry.training.time,
        'place': journal_entry.training.place,
        'address': journal_entry.training.address,
        'route': journal_entry.training.route
    }
    return training_data

@sync_to_async()
def declain_training(date,user_id):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    journal_entry = mdl.Journal.objects.filter(user=user, date=date).first()
    journal_entry.previuos_answer = journal_entry.accept
    journal_entry.accept = False
    journal_entry.second_not = True
    journal_entry.answer_time = datetime.now()
    journal_entry.save()

@sync_to_async()
def get_users_for_first_not(day):
    now = datetime.now()
    current_time = datetime.strptime(now.strftime("%H:%M:%S"), '%H:%M:%S').time()
    training = mdl.Training.objects.filter(day=day, was_end=False).first()
    if current_time >= training.time:
        return None
    
    users = mdl.User.objects.filter(telegram_id__isnull=False).all()
    today = now.date()
    formatted_date = today.strftime("%Y-%m-%d")
    users_data = []
    for user in users:
        user_trainings = mdl.Journal.objects.filter(user=user).all()
        truant = False
        #если клиент первый раз воспользовался ботом, то у него него не будет записей тренировок
        #в журнале, поэтому проверяем. если тренировки есть
        if user_trainings:
            # смотрим сколько пропущенных подряд было до этого из последних 6ти
            last_trainings = len(user_trainings)-6
            if last_trainings >= 0:
                missed_trainings = user_trainings[last_trainings:]
                missed_counter = 0
                for missed_training in missed_trainings:
                    if not missed_training.accept:
                        missed_counter += 1
                    else:
                        break
                if missed_counter == 6:
                    #если пропущенных 6 подряд, то объявлем клиента прогульщиком
                    truant = True
            #далее смотрим есть ли у него запись на сегодняшнюю тренировку
            #если он останавливал бота и снова его запустил, то записи может и не быть
            journal_entry = user_trainings.filter(date=formatted_date).first()
            if not journal_entry:
                #и добавляем пользователя в список для оповещения
                users_data.append({
                    'id': user.telegram_id,
                    'name': user.name,
                    'truant': truant,
                    'first_not': True
                })
        else:
            #если пользователь ни разу не был на тренировках и сегодня
            #добавился в бота оповестить его
            users_data.append({
                'id': user.telegram_id,
                'name': user.name,
                'truant': truant,
                'first_not': True
            })
    #если оповещать некого
    if len(users_data) == 0:
        return None
    training_data = {
        'day': day,
        'date': today,
        'time': training.time,
        'place': training.place,
        'address': training.address,
        'route': training.route,
    }
    return {
        'users_data': users_data,
        'training_data': training_data
    }

@sync_to_async()
def get_users_for_second_not(day):
    now = datetime.now()
    today = now.date()
    training = mdl.Training.objects.filter(day=day, was_end=False).first()
    entries = mdl.Journal.objects.filter(date=today, accept=None, second_not=False).all()
    
    users_data = []
    users = mdl.User.objects.filter(telegram_id__isnull=False).all()
    for user in users:
        entry = mdl.Journal.objects.filter(date=today, user=user).first()
        if not entry:
            users_data.append({
                'id': user.telegram_id,
                'name': user.name,
                'first_not': True,
                'newbie': True
            })
    if not entries and not users_data:
        return None
    for entry in entries:
        users_data.append({
                'id': entry.user.telegram_id,
                'name': entry.user.name,
                'first_not': False
            })
    training_data = {
        'day': day,
        'date': today,
        'time': training.time,
        'place': training.place,
        'address': training.address,
        'route': training.route,
    }
    return {
        'users_data': users_data,
        'training_data': training_data
    }

@sync_to_async()
def get_training_info():
    # раскоментировать и создать файл time.txt для имитации текущего времени
    # в файл записать время в формате 09:00:00
    # time_str = ''
    # with open('Bot/time.txt', 'r') as file:
    #     # Считываем первую строку файла
    #     time_str = file.readline().strip()
    now = datetime.now()
    today = now.date()
    week_day = now.strftime("%A").lower()
    training = mdl.Training.objects.filter(day=week_day, was_end=False).first()
    if not training:
        return 'not today'
    current_time = datetime.strptime(now.strftime("%H:%M:%S"), '%H:%M:%S').time()
    # current_time = datetime.strptime(time_str, '%H:%M:%S').time()
    current_hours = int(current_time.hour)
    training_time = training.time
    training_hours = int(training_time.hour)
    if training_hours <= current_hours:
        return None
    training_data = {
        'day': week_day,
        'date': today,
        'time': training.time,
        'place': training.place,
        'address': training.address,
        'route': training.route,
    }
    return training_data

@sync_to_async()
def make_entry(user_telegram_id, training_data, newbie=False):
    user = mdl.User.objects.filter(telegram_id=user_telegram_id).first()
    training = mdl.Training.objects.filter(day=training_data.get('day')).first()
    entry = mdl.Journal.objects.filter(user=user, date=training_data.get('date')).first()
    if not entry:
        if newbie:
            second_not = True
        else:
            second_not = False
        new_entry = mdl.Journal.objects.create(
            training=training,
            user=user,
            date = training_data.get('date'),
            second_not=second_not
        )
        new_entry.save()
    else:
        entry.second_not = True
        entry.save()

@sync_to_async()
def get_users_for_not_yesterday(day):
    #по дню определяем тренировку
    training = mdl.Training.objects.filter(day=day, was_end=False).first()
    #ищем эту тренировку среди всех записей в журнале
    journal_entries = mdl.Journal.objects.filter(training=training).all()
    #берём последнюю запись с этой тренировкой
    last_journal_entry = journal_entries[len(journal_entries)-1]
    #находим все записи с такой же датой и этой же тренировкой
    journal_entries = journal_entries.filter(date=last_journal_entry.date).all()
    users_data = []
    journal_entries_ids = []
    if journal_entries:
        for journal_entry in journal_entries:
            if journal_entry.rate is None and journal_entry.accept:
                users_data.append({
                    'id': journal_entry.user.telegram_id,
                    'name': journal_entry.user.name,
                })
                journal_entry.user.newbie = False
                journal_entry.user.save()
                journal_entry.save()
                journal_entries_ids.append(journal_entry.id)
        rate_entry = mdl.Rate.objects.filter(date=journal_entries[0].date).first()
        if not rate_entry:
            new_rate = mdl.Rate.objects.create(
                date = journal_entries[0].date,
                place = training.place,
                address = training.address,
            )
            new_rate.save()
        if not training.repeat:
            training.was_end = True
            training.save()
        if len(users_data) == 0:
            return None
        return {
            'training_ids': journal_entries_ids,
            'users_data': users_data
        }
    return None

@sync_to_async()
def add_0_to_entry(training_id):
    journal_entry = mdl.Journal.objects.filter(id=training_id).first()
    journal_entry.rate = 0
    journal_entry.save()

@sync_to_async()
def set_rate(rate, training_id):
    journal_entry = mdl.Journal.objects.filter(id=training_id).first()
    journal_entry.rate = rate
    journal_entry.save()
    date = journal_entry.date
    rate_entry = mdl.Rate.objects.filter(date=date).first()
    journal_entries_yesterday = mdl.Journal.objects.filter(date=date).all()
    rates = []
    for entry in journal_entries_yesterday:
        if entry.rate != 0 and entry.rate != None:
            rates.append(entry.rate)
    average_score = round(sum(rates) / float(len(rates)), 1)
    rate_entry.rate = average_score
    rate_entry.save()

@sync_to_async()
def get_accept_users():
    now = datetime.now().date()
    then = now + timedelta(days = 1)
    today = now.strftime("%Y-%m-%d")

    journal_entries = mdl.Journal.objects.filter(date=today).order_by('answer_time').all()
    if not journal_entries:
        return None
    
    users_data = []
    for journal_entry in journal_entries:
        if journal_entry.accept or (journal_entry.accept == False and journal_entry.previuos_answer):
            birthday = ''
            if journal_entry.user.birthday.strftime("%d.%m") == now.strftime("%d.%m"):
                birthday = '(Сегодня день рождения🥳)'
            if journal_entry.user.birthday.strftime("%d.%m") == then.strftime("%d.%m"):
                birthday = '(Завтра день рождения🥳)'
            newbie = ''
            if journal_entry.user.newbie:
                newbie = '(Новичок)'
            changed = False
            if journal_entry.accept == False and journal_entry.previuos_answer:
                changed = True
            users_data.append({
                'name': journal_entry.user.name,
                'birthday': birthday,
                'newbie': newbie,
                'changed': changed
            })
    return users_data

@sync_to_async()
def get_training_rates(training_date=None):
    if not training_date:
        now = datetime.now().date()
        training_date = now - timedelta(days = 1)
    journal_entries = mdl.Journal.objects.filter(date=training_date).exclude(rate=None).exclude(rate=0).all()
    if not journal_entries:
        return None
    rate = mdl.Rate.objects.filter(date=training_date).first()
    users = []
    for entry in journal_entries:
        users.append({
            'name': entry.user.name,
            'rate': entry.rate,
        })
    return {
        'users': users,
        'average_score': rate.rate
    }


@sync_to_async()
def get_shedule():
    trainings = mdl.Training.objects.filter(was_end=False).all()
    trainings_data = []
    for training in trainings:
        for day in DAYS:
            if training.day == day[0]:
                week_day = day[1]
        trainings_data.append({
            'day': week_day,
            'time': training.time.strftime("%H:%M"),
            'place': training.place,
            'address': training.address
        })
    return trainings_data

@sync_to_async()
def save_new_messages(user_id, outgoing, incoming):
    user = mdl.Message.objects.create(
        user_id=user_id,
        outgoing_msg_id=outgoing,
        incoming_msg_id=incoming
    )
    user.save()


@sync_to_async()
def get_msg_id_for_reply(reply_msg_id):
    msg = mdl.Message.objects.filter(incoming_msg_id=reply_msg_id).first()
    if msg:
        return {
            'msg_id': msg.outgoing_msg_id,
            'user_id': msg.user_id
        }
    msg = mdl.Message.objects.filter(outgoing_msg_id=reply_msg_id).first()
    if msg:
        return {
            'msg_id': msg.incoming_msg_id,
            'user_id': msg.user_id
        }
        
    return None

@sync_to_async()
def get_games():
    now = datetime.now()
    dif = timedelta(seconds=24 * 60 * 60)
    games = mdl.Game.objects.filter().all()
    if not games:
        return None
    games_data = []
    for game in games:
        if game.date_time - now <= dif and game.date_time > now:
            journal_entry = mdl.GameJournal.objects.filter(date_time=game.date_time).first()
            if not journal_entry:
                games_data.append(game)
    if len(games_data) == 0:
        return None
    return games_data

@sync_to_async()
def get_users_game_notfn(date_time):
    game = mdl.Game.objects.filter(date_time=date_time).first()
    users_data = []
    for user in game.team.users.all():
        journal_entry = mdl.GameJournal.objects.filter(date_time=date_time, user=user).first()
        if not journal_entry:
            telegram_id = user.telegram_id
            name = user.name
            users_data.append({
                'id': telegram_id,
                'name': name
            })
    if len(users_data) == 0:
        return None
    return users_data

@sync_to_async()
def make_game_entry(date_time, user_id):
    game = mdl.Game.objects.filter(date_time=date_time).first()
    for user in game.team.users.all():
        journal_entry = mdl.GameJournal.objects.filter(date_time=date_time, user=user).first()
        if not journal_entry:
            new_entry = mdl.GameJournal.objects.create(
                    game = game,
                    user = user,
                    date_time = date_time
                )
            new_entry.save()


@sync_to_async()
def get_game_data_for_accept(game_id, user_telegram_id):
    game = mdl.Game.objects.filter(id=game_id).first()
    user = mdl.User.objects.filter(telegram_id=user_telegram_id).first()
    journal_entry = mdl.GameJournal.objects.filter(game=game, user=user).first()
    return {
        'datetime': journal_entry.date_time,
        'place': game.place,
        'address': game.address,
        'route': game.route,
    }

@sync_to_async()
def accept_game(game_id, user_telegram_id):
    game = mdl.Game.objects.filter(id=game_id).first()
    user = mdl.User.objects.filter(telegram_id=user_telegram_id).first()
    journal_entry = mdl.GameJournal.objects.filter(game=game, user=user).first()
    if not journal_entry:
        return None
    journal_entry.answer_time = datetime.now()
    journal_entry.previuos_answer = journal_entry.accept
    journal_entry.accept = True
    journal_entry.save()
    return True

@sync_to_async()
def declain_game(game_id, user_telegram_id):
    game = mdl.Game.objects.filter(id=game_id).first()
    user = mdl.User.objects.filter(telegram_id=user_telegram_id).first()
    journal_entry = mdl.GameJournal.objects.filter(game=game, user=user).first()
    if not journal_entry:
        return None
    journal_entry.answer_time = datetime.now()
    journal_entry.previuos_answer = journal_entry.accept
    journal_entry.accept = False
    journal_entry.save()
    return True


@sync_to_async()
def check_games(user_telegram_id):
    now = datetime.now()
    dif = timedelta(seconds=24 * 60 * 60)
    user = mdl.User.objects.filter(telegram_id=user_telegram_id).first()
    teams = mdl.Team.objects.filter(users=user).all()
    games = mdl.Game.objects.filter(team__in=teams).all()
    if not games:
        return None
    games_data = []
    for game in games:
        if game.date_time - now <= dif and game.date_time > now:
            journal_entry = mdl.GameJournal.objects.filter(user=user,date_time=game.date_time).first()
            if journal_entry:
                games_data.append(game)
    if len(games_data) == 0:
        return None
    print(games_data)
    return games_data

@sync_to_async()
def get_game_data(game_id, user_telegram_id):
    now = datetime.now()
    dif = timedelta(seconds=24 * 60 * 60)
    user = mdl.User.objects.filter(telegram_id=user_telegram_id).first()
    game = mdl.Game.objects.filter(id=game_id).first()
    if game.date_time - now <= dif and game.date_time > now:
        user = {
            'id': user.telegram_id,
            'name': user.name
        }
        return {
            'game': game,
            'user': user
        }


@sync_to_async()
def check_games_admin():
    now = datetime.now()
    dif = timedelta(seconds=24 * 60 * 60)
    dif2 = timedelta(seconds=2 * 60 * 60)
    games = mdl.Game.objects.all()
    if not games:
        return None
    games_data = []
    for game in games:
        game_date = game.date_time.date()
        current_date = now.date()
        logging.debug(game_date == current_date)
        if game.date_time - now <= dif or game_date == current_date:
            games_data.append({
                'id': game.id,
                'place': game.place,
                'team': game.team.name,
                'date_time': game.date_time
            })
    if len(games_data) == 0:
        return None
    
    return games_data

@sync_to_async()
def get_game_users_admin(game_id):
    game = mdl.Game.objects.filter(id=game_id).first()
    users_data = []
    for user in game.team.users.all():
        journal_entry = mdl.GameJournal.objects.filter(game=game, user=user).first()
        if journal_entry:
            if not journal_entry.accept and journal_entry.previuos_answer:
                changed = True
            else:
                changed = False
            users_data.append({
                'id': user.telegram_id,
                'name': user.name,
                'newbie': user.newbie,
                'birthday': user.birthday,
                'changed': changed,
                'team': game.team.name,
                'game': game
            })
    if len(users_data) == 0:
        return None
    return users_data