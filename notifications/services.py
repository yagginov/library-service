from telegram import Bot

from django.conf import settings
from notifications.interfaces import NotificationInterface


class NotificationTelegramService(NotificationInterface):

    def __init__(self, bot_token: str = settings.TG_API_TOKEN, admin_chat_id: int = settings.CHAT_ID):
        self.bot = Bot(token=bot_token)
        self.admin_chat_id = admin_chat_id

    def send(self, message: str) -> None:
        self.bot.send_message(chat_id=self.admin_chat_id, text=message)

notification = NotificationTelegramService()
