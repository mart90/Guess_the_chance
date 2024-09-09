from mysql import *
from event import Event
from user import User
from functions import *


public_rating_start = 0
rating_start = 10
kfactor_start = 1

mysql = MySQL().connect(mysql_ip, mysql_db)
mysql.query("""
    select
        e.id,
        e.date_resolved,
        p.user_id,
        p.predicted_probability,
        e.result
    from event e
    join prediction p on p.event_id = e.id
    where 
        e.result is not null""")

result = mysql.cursor.fetchall()
events = []

for event_id in list(set([r[0] for r in result])):
    events.append(Event(event_id))

for row in result:
    event = [e for e in events if e.id == row[0]][0]
    event.resolved_at = row[1]
    event.result = row[4]
    user = User(row[2], None, rating_start, kfactor_start, None)
    user.public_rating = public_rating_start
    user.prediction = row[3]
    event.users.append(user)

for event in sorted(events, key=lambda e: e.resolved_at):
    if event.id == 32:
        pass

    set_new_ratings(event.users, event.result)

    for user in event.users:
        user.update_rating(mysql, event.id)

        for e in events:
            u = [u for u in e.users if u.id == user.id]
            if u:
                u[0].rating = user.rating
                u[0].kfactor = user.kfactor
                u[0].public_rating = user.public_rating


mysql.commit_and_close()
