from bs4 import BeautifulSoup as BS
import datetime
import json
import pytz
import requests


# Время проведения пар
time_schedule = {
	1 : '🕘 9:00 – 10:30',
	2 : '🕥 10:40 – 12:10',
	3 : '🕧 12:20 – 13:50',
	4 : '🕝 14:30 – 16:00',
	5 : '🕓 16:10 – 17:40',
	6 : '🕕 17:50 – 19:20',
	7 : '🕢 19:30 – 21:00',
}

# Дни недели
weekdays = {
	1 : 'Понедельник',
	2 : 'Вторник',
	3 : 'Среда',
	4 : 'Четверг',
	5 : 'Пятница',
	6 : 'Суббота',
	7 : 'Воскресенье',
}

# Часовой пояс – "Москва"
MOSCOW = pytz.timezone('Europe/Moscow')

# Класс "Пара"
class Lesson():

	def __init__(self, json):
		self.name = json['sbj']
		self.time = json['time_schedule']
		self.dates = json['dts']
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

	def __str__(self):
		return f'{self.name}\n{self.time}\n{self.dates}\n{self.type}\n{self.teacher}\n{self.place}\n'

# Класс "Расписание"
class Schedule():
	
	def __init__(self, group: str):
		if not group:
			self.group = None
		else:
			self.group = group.replace(' ', '').replace('–', '-').replace('—', '-').replace('‒', '-').replace('᠆', '-')

	# Получить расписание с сайта в формате JSON
	def get_schedule_json(self, session):
		session = 0 if not session else 1
		url = f'https://rasp.dmami.ru/site/group?group={self.group}&session={session}'
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
			'cookie': '_ym_uid=15749743621061641749; _ym_d=1604048375; _ym_isad=1; group=181-722',
		}
		r = requests.post(url=url, headers=headers)
		return r.json()

	# Получить расписание на день текущей недели 
	def get_schedule_by_weekday(self, day: int, session=False):
		rasp_json = self.get_schedule_json(session)
		schedule = []

		if rasp_json['status'] == 'error':
			return None
		elif rasp_json['status'] == 'ok':
			if str(day) not in rasp_json['grid']:
				return []
			for key, value in rasp_json['grid'][str(day)].items():
				if not len(value):
					continue
				now = datetime.datetime.now(datetime.timezone.utc).astimezone(MOSCOW).date()
				for lesson in value:
					if now >= datetime.datetime.strptime(lesson['df'], "%Y-%m-%d").date() and now <= datetime.datetime.strptime(lesson['dt'], "%Y-%m-%d").date():
						lesson['time_schedule'] = time_schedule[int(key)]
						schedule.append(Lesson(lesson))
			return schedule

	# Получить расписание на сегодня
	def get_today_schedule(self, session=False):
		rasp_json = self.get_schedule_json(session)
		schedule = []
		day = datetime.datetime.now(datetime.timezone.utc).astimezone(MOSCOW).weekday()

		if rasp_json['status'] == 'error':
			return None
		elif rasp_json['status'] == 'ok':
			if str(day) not in rasp_json['grid']:
				return []
			for key, value in rasp_json['grid'][str(day)].items():
				if not len(value):
					continue
				now = datetime.datetime.now(datetime.timezone.utc).astimezone(MOSCOW).date()
				for lesson in value:
					if now >= datetime.datetime.strptime(lesson['df'], "%Y-%m-%d").date() and now <= datetime.datetime.strptime(lesson['dt'], "%Y-%m-%d").date():
						lesson['time_schedule'] = time_schedule[int(key)]
						schedule.append(Lesson(lesson))
			return schedule

	# Получить расписание по дате
	def get_schedule_by_date(self, date: datetime.datetime, session=False):
		rasp_json = self.get_schedule_json(session)
		schedule = []
		day = date.weekday() + 1

		if rasp_json['status'] == 'error':
			return None
		elif rasp_json['status'] == 'ok':
			if str(day) not in rasp_json['grid']:
				return []
			for key, value in rasp_json['grid'][str(day)].items():
				if not len(value):
					continue
				now = date.date()
				for lesson in value:
					if now >= datetime.datetime.strptime(lesson['df'], "%Y-%m-%d").date() and now <= datetime.datetime.strptime(lesson['dt'], "%Y-%m-%d").date():
						lesson['time_schedule'] = time_schedule[int(key)]
						schedule.append(Lesson(lesson))
			return schedule
	
	# Получить список всех групп
	def get_groups(self):
		url = 'https://rasp.dmami.ru/groups-list.json'
		headers = {
			'authority': 'rasp.dmami.ru',
			'pragma': 'no-cache',
			'cache-control': 'no-cache',
			'accept': 'application/json, text/javascript, */*; q=0.01',
			'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
			'x-requested-with': 'XMLHttpRequest',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'cors',
			'sec-fetch-dest': 'empty',
			'referer': 'https://rasp.dmami.ru/',
			'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
			'cookie': '_ym_uid=15749743621061641749; _ym_d=1604048375; _ym_isad=1; group=181-722',
		}
		r = requests.post(url=url, headers=headers)
		return r.json()['groups']
	
	# Группа существует?
	def group_exists(self):
		return True if self.group in self.get_groups() else False

	# Получить расписание на текущую неделю
	def get_schedule_for_week(self, session=False):
		weekly_schedule = dict()
		rasp_json = self.get_schedule_json(session)

		if rasp_json['status'] == 'error':
			return None
		elif rasp_json['status'] == 'ok':
			for day in range(1,8):
				schedule = []
				if str(day) not in rasp_json['grid']:
					continue
				weekday_date = datetime.datetime.now(datetime.timezone.utc).astimezone(MOSCOW).date() + datetime.timedelta( - datetime.datetime.now(datetime.timezone.utc).astimezone(MOSCOW).weekday() + day - 1)
				for key, value in rasp_json['grid'][str(day)].items():
					if not len(value):
						continue
					now = weekday_date
					for lesson in value:
						if now >= datetime.datetime.strptime(lesson['df'], "%Y-%m-%d").date() and now <= datetime.datetime.strptime(lesson['dt'], "%Y-%m-%d").date():
							lesson['time_schedule'] = time_schedule[int(key)]
							schedule.append(Lesson(lesson))
				weekly_schedule[weekdays[day]] = schedule.copy()
			return weekly_schedule

	# Получить расписание на неделю по дате (указывается дата любого дня недели)
	def get_schedule_for_week_by_date(self, date: datetime.datetime, session=False):
		weekly_schedule = dict()
		rasp_json = self.get_schedule_json(session)
		day = date.weekday() + 1
		count = 0

		if rasp_json['status'] == 'error':
			return None
		elif rasp_json['status'] == 'ok':
			for day in range(1,8):
				schedule = []
				if str(day) not in rasp_json['grid']:
					continue
				weekday_date = date.date() + datetime.timedelta( - date.weekday() + day - 1)
				for key, value in rasp_json['grid'][str(day)].items():
					if not len(value):
						continue
					now = weekday_date
					for lesson in value:
						if now >= datetime.datetime.strptime(lesson['df'], "%Y-%m-%d").date() and now <= datetime.datetime.strptime(lesson['dt'], "%Y-%m-%d").date():
							lesson['time_schedule'] = time_schedule[int(key)]
							schedule.append(Lesson(lesson))
							count += 1
				weekly_schedule[weekdays[day]] = schedule.copy()
			return weekly_schedule if count else {}
