from bs4 import BeautifulSoup as BS
from datetime import datetime, timezone, timedelta
import pytz
import re
import requests

# Время проведения пар
time_schedule = {
    1: '🕘 9:00 – 10:30',
    2: '🕥 10:40 – 12:10',
    3: '🕧 12:20 – 13:50',
    4: '🕝 14:30 – 16:00',
    5: '🕓 16:10 – 17:40',
    6: '🕕 17:50 – 19:20',
    7: '🕢 19:30 – 21:00',
}

# Дни недели
weekdays = {
    1: 'Понедельник',
    2: 'Вторник',
    3: 'Среда',
    4: 'Четверг',
    5: 'Пятница',
    6: 'Суббота',
    7: 'Воскресенье',
}

# Часовой пояс – "Москва"
MOSCOW = pytz.timezone('Europe/Moscow')

# Хэдеры POST-запроса
headers = {
    'authority': 'rasp.dmami.ru',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'accept': '*/*',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://rasp.dmami.ru/',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}


# Класс "Пара"
class Lesson:

    def __init__(self, json):
        self.name = json['sbj']
        self.time = json['time_schedule']
        self.dates = json['dts'] if 'dts' in json else None
        self.type = json['type']
        self.teacher = json['teacher']
        if isinstance(json['auditories'], list):
            temp = False
            for place in json['auditories']:
                if '</a>' in place['title']:
                    soup = BS(place['title'], 'html.parser')
                    place['title'] = soup.a.text
                if not temp:
                    self.place = place['title']
                    temp = True
                else:
                    self.place += ', ' + place['title']
        else:
            self.place = None
        self.link = json['el'] if json['el'] else None

    def __str__(self):
        return f'{self.name}\n{self.time}\n{self.dates}\n{self.type}\n{self.teacher}\n{self.place}\n'


# Класс "Расписание"
class Schedule:

    def __init__(self, group=None):
        if not group or not isinstance(group, str):
            self.group = None
        else:
            self.group = group.replace(' ', '').replace(
                '–', '-').replace('—', '-').replace('‒', '-').replace('᠆', '-')

    # Получить список всех групп
    @classmethod
    def get_groups(cls):
        url = 'https://rasp.dmami.ru/groups-list.json'
        r = requests.post(url=url, headers=headers)
        return r.json()['groups'] if r.status_code == 200 else {'status': 'error'}

    # Получить расписание с сайта в формате JSON
    def get_schedule_json(self, session):
        session = 0 if not session else 1
        url = f'https://rasp.dmami.ru/site/group?group={self.group}&session={session}'
        r = requests.post(url=url, headers=headers)
        return r.json() if r.status_code == 200 else {'status': 'error'}

    # Получить расписание на день текущей недели
    def get_schedule_by_weekday(self, day: int, schedule_json: dict = None):
        schedule_json = self.get_schedule_json(
            False) if not schedule_json else schedule_json
        schedule = []

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            now = datetime.now(
                timezone.utc).astimezone(MOSCOW).date()
            if now > datetime.strptime(schedule_json['group']['dateTo'],
                                       '%Y-%m-%d').date() or now < datetime.strptime(
                schedule_json['group']['dateFrom'], '%Y-%m-%d').date():
                return None
            elif str(day) not in schedule_json['grid']:
                return []
            for key, value in schedule_json['grid'][str(day)].items():
                if not len(value):
                    continue
                for lesson in value:
                    if datetime.strptime(lesson['df'],
                                         '%Y-%m-%d').date() <= now <= datetime.strptime(lesson['dt'],
                                                                                        '%Y-%m-%d').date():
                        lesson['time_schedule'] = time_schedule[int(key)]
                        schedule.append(Lesson(lesson))
            return schedule

    # Получить расписание на сегодня
    def get_today_schedule(self, schedule_json: dict = None):
        schedule_json = self.get_schedule_json(
            False) if not schedule_json else schedule_json
        schedule = []
        day = datetime.now(
            timezone.utc).astimezone(MOSCOW).weekday() + 1
        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            now = datetime.now(
                timezone.utc).astimezone(MOSCOW).date()
            if now > datetime.strptime(schedule_json['group']['dateTo'],
                                       '%Y-%m-%d').date() or now < datetime.strptime(
                schedule_json['group']['dateFrom'], '%Y-%m-%d').date():
                return None
            elif str(day) not in schedule_json['grid']:
                return []
            for key, value in schedule_json['grid'][str(day)].items():
                if not len(value):
                    continue
                for lesson in value:
                    if datetime.strptime(lesson['df'],
                                         '%Y-%m-%d').date() <= now <= datetime.strptime(lesson['dt'],
                                                                                        '%Y-%m-%d').date():
                        lesson['time_schedule'] = time_schedule[int(key)]
                        schedule.append(Lesson(lesson))
            return schedule

    # Получить расписание по дате
    def get_schedule_by_date(self, date: datetime, session=False, schedule_json: dict = None):
        schedule_json = self.get_schedule_json(
            session) if not schedule_json else schedule_json
        schedule = []
        day = date.weekday() + 1

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            if re.fullmatch(r'\d{4}-\d\d-\d\d', list(schedule_json['grid'].keys())[0]):
                if date.strftime("%Y-%m-%d") not in schedule_json['grid']:
                    return None
                for key, value in schedule_json['grid'][date.strftime("%Y-%m-%d")].items():
                    if not len(value):
                        continue
                    for lesson in value:
                        lesson['time_schedule'] = time_schedule[int(key)]
                        schedule.append(Lesson(lesson))
            else:
                if date.date() > datetime.strptime(schedule_json['group']['dateTo'],
                                                   '%Y-%m-%d').date() or date.date() < datetime.strptime(
                    schedule_json['group']['dateFrom'], '%Y-%m-%d').date():
                    return None
                elif str(day) not in schedule_json['grid']:
                    return []
                for key, value in schedule_json['grid'][str(day)].items():
                    if not len(value):
                        continue
                    now = date.date()
                    for lesson in value:
                        if datetime.strptime(lesson['df'],
                                             '%Y-%m-%d').date() <= now <= datetime.strptime(
                            lesson['dt'], '%Y-%m-%d').date():
                            lesson['time_schedule'] = time_schedule[int(key)]
                            schedule.append(Lesson(lesson))
            return schedule

    # Группа существует?
    def group_exists(self):
        return True if self.group in self.get_groups() else False

    # Получить расписание на текущую неделю
    def get_schedule_for_week(self, schedule_json: dict = None):
        weekly_schedule = dict()
        schedule_json = self.get_schedule_json(
            False) if not schedule_json else schedule_json

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            for day in range(1, 8):
                schedule = []
                if str(day) not in schedule_json['grid']:
                    continue
                weekday_date = datetime.now(timezone.utc).astimezone(MOSCOW).date(
                ) + timedelta(
                    - datetime.now(timezone.utc).astimezone(MOSCOW).weekday() + day - 1)
                if weekday_date > datetime.strptime(schedule_json['group']['dateTo'],
                                                    '%Y-%m-%d').date() or weekday_date < datetime.strptime(
                    schedule_json['group']['dateFrom'], '%Y-%m-%d').date():
                    return None
                for key, value in schedule_json['grid'][str(day)].items():
                    if not len(value):
                        continue
                    now = weekday_date
                    for lesson in value:
                        if datetime.strptime(lesson['df'],
                                             '%Y-%m-%d').date() <= now <= datetime.strptime(
                            lesson['dt'], "%Y-%m-%d").date():
                            lesson['time_schedule'] = time_schedule[int(key)]
                            schedule.append(Lesson(lesson))
                weekly_schedule[weekdays[day]] = schedule.copy()
            return weekly_schedule

    # Получить расписание на неделю по дате (указывается дата любого дня недели)
    def get_schedule_for_week_by_date(self, date: datetime, schedule_json: dict = None):
        weekly_schedule = dict()
        schedule_json = self.get_schedule_json(False) if not schedule_json else schedule_json

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            for day in range(1, 8):
                schedule = []
                weekday_date = date.date() + timedelta(- date.weekday() + day - 1)
                if weekday_date > datetime.strptime(schedule_json['group']['dateTo'],
                                                    '%Y-%m-%d').date() or weekday_date < datetime.strptime(
                    schedule_json['group']['dateFrom'], '%Y-%m-%d').date():
                    return None
                if str(day) not in schedule_json['grid']:
                    continue
                for key, value in schedule_json['grid'][str(day)].items():
                    if not len(value):
                        continue
                    now = weekday_date
                    for lesson in value:
                        if datetime.strptime(lesson['df'],
                                             '%Y-%m-%d').date() <= now <= datetime.strptime(
                            lesson['dt'], "%Y-%m-%d").date():
                            lesson['time_schedule'] = time_schedule[int(key)]
                            schedule.append(Lesson(lesson))
                weekly_schedule[weekdays[day]] = schedule.copy()
            return weekly_schedule

    # Получить расписание сессии по дате
    def get_schedule_session_by_date(self, date: datetime, schedule_json: dict = None):
        schedule_json = self.get_schedule_json(
            True) if not schedule_json else schedule_json
        schedule = []

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            if date.strftime("%Y-%m-%d") not in schedule_json['grid']:
                return None
            for key, value in schedule_json['grid'][date.strftime("%Y-%m-%d")].items():
                if not len(value):
                    continue
                for lesson in value:
                    lesson['time_schedule'] = time_schedule[int(key)]
                    schedule.append(Lesson(lesson))
            return schedule

    # Получить расписание всей сессии
    def get_schedule_session(self, schedule_json: dict = None):
        schedule_json = self.get_schedule_json(
            True) if not schedule_json else schedule_json
        session_schedule = {}

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            for date in schedule_json['grid']:
                schedule = []
                for key, value in schedule_json['grid'][date].items():
                    if not len(value):
                        continue
                    for lesson in value:
                        lesson['time_schedule'] = time_schedule[int(key)]
                        schedule.append(Lesson(lesson))
                session_schedule[date] = schedule.copy()
            return session_schedule

    # Получить расписание на каждую дату
    def get_full_schedule(self, schedule_json: dict = None):
        full_schedule = dict()
        schedule_json = self.get_schedule_json(
            False) if not schedule_json else schedule_json

        if schedule_json['status'] == 'error':
            return None
        elif schedule_json['status'] == 'ok':
            date_from = datetime.strptime(
                schedule_json['group']['dateFrom'], '%Y-%m-%d')
            date_to = datetime.strptime(
                schedule_json['group']['dateTo'], '%Y-%m-%d')
            days = (date_to - date_from).days
            for day in range(days + 1):
                tmp_date = date_from + timedelta(day)
                tmp_day = tmp_date.weekday() + 1
                if str(tmp_day) not in schedule_json['grid']:
                    continue
                full_schedule[tmp_date.strftime('%Y-%m-%d')] = []
                for key, value in schedule_json['grid'][str(tmp_day)].items():
                    if not len(value):
                        continue
                    now = tmp_date.date()
                    for lesson in value:
                        if datetime.strptime(lesson['df'],
                                             '%Y-%m-%d').date() <= now <= datetime.strptime(
                            lesson['dt'], "%Y-%m-%d").date():
                            lesson['time_schedule'] = time_schedule[int(key)]
                            full_schedule[tmp_date.strftime(
                                '%Y-%m-%d')].append(Lesson(lesson))
            return full_schedule
