import requests
import json
from mysql import *


username = "Notification bot"
notify_webhook = "https://discord.com/api/webhooks/1278236084945551423/UAPZzNhlEhEqg3686_SiCf26WRqC4S9vGBN_GuFVjjycehOI64XUsYPqXWVsTZvbpEGf"

mysql = MySQL().connect(mysql_ip, mysql_db)

mysql.query("""
    SELECT 
        e.id,
        e.description,
        ec.discord_role_id 
    FROM event e 
    JOIN event_category ec ON e.category_id = ec.id
    WHERE 
        e.discord_notified = 0
        e.date_close <= (CURRENT_TIMESTAMP + INTERVAL 28 HOUR)""")

result = mysql.cursor.fetchall()

for row in result:
    event_name = row[1]
    category_role_id = row[2]
    link = f"https://guessthechance.com/events/{row[0]}"

    data = {
        "content": f"Guessing for event \"{event_name}\" closes soon. {link} <@&{category_role_id}>",
        "username": username
    }
    requests.post(notify_webhook, data=json.dumps(data), headers={"Content-Type": "application/json"})

    mysql.query("UPDATE event SET discord_notified = 1 WHERE id = %s", (row[0]))

mysql.commit_and_close()
