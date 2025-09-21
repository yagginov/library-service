from typing import Protocol


class NotificationInterface(Protocol):
    def send(self, message) -> None:
        ...
