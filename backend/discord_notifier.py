import requests
import json


class DiscordNotifier:
    def __init__(self):
        self.username = "NotificationBot"
        self.notify_webhook = "https://discord.com/api/webhooks/1278236084945551423/UAPZzNhlEhEqg3686_SiCf26WRqC4S9vGBN_GuFVjjycehOI64XUsYPqXWVsTZvbpEGf"
    
    def message(self, message):
        data = {
            "content": message,
            "username": self.username
        }
        requests.post(self.notify_webhook, data=json.dumps(data), headers={"Content-Type": "application/json"})


discord_notifier = DiscordNotifier()
