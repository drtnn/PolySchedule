# PolySchedule
Python schedule scraper

Requires
-----
  * beautifulsoup4
  * pytz
  * requests
  
# Usage
Сhecking the existence of the group
-----
``` python
from polyschedule import Schedule

schedule = Schedule('181-722')
print(schedule.group_exists())
```
Getting a schedule for today
-----
``` python
from polyschedule import Schedule

schedule = Schedule('181-722')
for lesson in schedule.get_today_schedule():
    print(lesson)
```
Getting a schedule for the current week
-----
``` python
schedule = Schedule('181-722')
for weekday, lessons in schedule.get_schedule_for_week().items():
    print(f'{weekday}:')
    for lesson in lessons:
        print(f'{lesson}')
```
Getting a schedule for the week by date
-----
``` python
schedule = Schedule('181-722')
for weekday, lessons in schedule.get_schedule_for_week_by_date(datetime.datetime(2020, 11, 6)).items():
    print(f'{weekday}:')
    for lesson in lessons:
        print(f'{lesson}')
```
