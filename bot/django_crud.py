from asgiref.sync import sync_to_async
from shedule_app import models as mdl
from datetime import datetime, timedelta
from bot.config import DAYS

@sync_to_async()
def check_new_user(user_id):
    tg_id = mdl.User.objects.filter(telegram_id=user_id).first()
    return tg_id

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
    tomorrow = trainings.filter(day=days[2]).first()
    if tomorrow:
        tomorrow_day = tomorrow.day
        tomorrow_time = tomorrow.time
        tomorrow = {
            'day': tomorrow_day,
            'time': tomorrow_time
        }
    return {
        'yesterday': yesterday,
        'today': today,
        'tomorrow': tomorrow,
    }

@sync_to_async()
def get_users_for_not_tomorrow(day):
    users = mdl.User.objects.filter(telegram_id__isnull=False).all()
    training = mdl.Training.objects.filter(day=day, was_end=False).first()
    today = datetime.now().date()
    tomorrow = today + timedelta(days = 1)
    formatted_date = tomorrow.strftime("%Y-%m-%d")
    users_data = []
    for user in users:
        journal_entry = mdl.Journal.objects.filter(user=user, date=formatted_date,).first()
        if not journal_entry:
            missed_trainings = mdl.Journal.objects.filter(user=user).all()[:6]
            missed_counter = 0
            for missed_training in missed_trainings:
                if not missed_training.accept:
                    missed_counter += 1
                else:
                    break
            truant = False
            if missed_counter >= 6:
                truant = True
            new_journal_entry = mdl.Journal.objects.create(
                training=training,
                user = user,
                date = formatted_date,
            )
            new_journal_entry.save()
            users_data.append({
                'id': user.telegram_id,
                'name': user.name,
                'truant': truant,
            })
    if len(users_data) == 0:
        return None
    training_data = {
        'date': tomorrow,
        'time': training.time,
        'place': training.place,
        'address': training.address,
    }
    return {
        'users_data': users_data,
        'training_data': training_data
    }

@sync_to_async()
def training_data(date,user_id):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    journal_entry = mdl.Journal.objects.filter(user=user, date=date).first()
    journal_entry.accept = True
    journal_entry.save()

    training_data = {
        'date': journal_entry.date,
        'time': journal_entry.training.time,
        'place': journal_entry.training.place,
        'address': journal_entry.training.address,
    }
    return training_data

@sync_to_async()
def declain_training(date,user_id):
    user = mdl.User.objects.filter(telegram_id=user_id).first()
    journal_entry = mdl.Journal.objects.filter(user=user, date=date).first()
    journal_entry.accept = False
    journal_entry.save()

@sync_to_async()
def get_users_for_not_today(day):
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
            missed_trainings = user_trainings[:6]
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
                #если записи нет, то создаём её в журнале
                new_journal_entry = mdl.Journal.objects.create(
                    training=training,
                    user = user,
                    date = formatted_date,
                    second_not = True
                    )
                new_journal_entry.save()
                #и добавляем пользователя в список для оповещения
                users_data.append({
                    'id': user.telegram_id,
                    'name': user.name,
                    'truant': truant,
                    'first_not': True
                })
            else:
                #если запись в журнале создалась вчера, но подтверждения до сих пор нет
                #то снова оповещаем пользователя(напоминание)
                if journal_entry.accept is None and not journal_entry.second_not:
                    journal_entry.second_not = True
                    journal_entry.save()
                    users_data.append({
                        'id': user.telegram_id,
                        'name': user.name,
                        'truant': truant,
                    })
        else:
            #если пользователь ни разу не был на тренировках и сегодня
            #добавился в бота, то нужно сделать запись и оповестить его
            new_journal_entry = mdl.Journal.objects.create(
                training=training,
                user = user,
                date = formatted_date,
                second_not = True
                )
            new_journal_entry.save()
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
        'date': today,
        'time': training.time,
        'place': training.place,
        'address': training.address,
    }
    return {
        'users_data': users_data,
        'training_data': training_data
    }


@sync_to_async()
def get_users_for_not_yesterday(day):
    #по дню определяем тренировку
    training = mdl.Training.objects.filter(day=day, was_end=False).first()
    #ищем эту тренировку среди всех записей в журнале
    journal_entries = mdl.Journal.objects.filter(training=training).all()
    #берём последнюю запись с этой тренировкой
    last_journal_entry = journal_entries[0]
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
                journal_entry.rate = 0
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
def set_rate(rate, training_id):
    journal_entry = mdl.Journal.objects.filter(id=training_id).first()
    journal_entry.rate = rate
    journal_entry.save()
    date = journal_entry.date
    rate_entry = mdl.Rate.objects.filter(date=date).first()
    journal_entries_yesterday = mdl.Journal.objects.filter(date=date).all()
    rates = []
    for entry in journal_entries_yesterday:
        if entry.rate != 0:
            rates.append(entry.rate)
    average_score = round(sum(rates) / float(len(rates)), 1)
    rate_entry.rate = average_score
    rate_entry.save()

@sync_to_async()
def get_accept_users(day):
    now = datetime.now().date()
    then = now + timedelta(days = 1)
    today = now.strftime("%Y-%m-%d")
    tomorrow = then.strftime("%Y-%m-%d")
    if day == 'today':
        date = today
    if day == 'tomorrow':
        date = tomorrow

    journal_entries = mdl.Journal.objects.filter(date=date).all()
    if not journal_entries:
        return None
    
    users_data = []
    for journal_entry in journal_entries:
        if journal_entry.accept:
            birthday = ''
            if journal_entry.user.birthday.strftime("%d.%m") == now.strftime("%d.%m"):
                birthday = '(Сегодня день рождения🥳)'
            if journal_entry.user.birthday.strftime("%d.%m") == then.strftime("%d.%m"):
                birthday = '(Завтра день рождения🥳)'
            newbie = ''
            if journal_entry.user.newbie:
                newbie = '(Новичок)'
            users_data.append({
                'name': journal_entry.user.name,
                'birthday': birthday,
                'newbie': newbie
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
    dif = timedelta(hours=24)
    games = mdl.Game.objects.filter().all()
    if not games:
        return None
    games_data = []
    for game in games:
        if game.date_time - now <= dif:
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
            new_entry = mdl.GameJournal.objects.create(
                game = game,
                user = user,
                date_time = date_time
            )
            new_entry.save()
    if len(users_data) == 0:
        return None
    return users_data
