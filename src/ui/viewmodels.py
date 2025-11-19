from PyQt5.QtCore import (
    Qt, QModelIndex, QAbstractListModel, QVariant, pyqtSignal, QObject
)
from typing import List
from .models import Message
from datetime import datetime

class MessageListModel(QAbstractListModel):
    SenderRole = Qt.UserRole + 1
    TextRole = Qt.UserRole + 2
    TimeRole = Qt.UserRole + 3

    def __init__(self, messages: List[Message] = None):
        super().__init__()
        self._messages = messages or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._messages)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        msg = self._messages[index.row()]
        if role == self.SenderRole:
            return msg.sender
        if role == self.TextRole or role == Qt.DisplayRole:
            return msg.text
        if role == self.TimeRole:
            return msg.timestamp.isoformat()
        return QVariant()

    def roleNames(self):
        return {
            self.SenderRole: b"sender",
            self.TextRole: b"text",
            self.TimeRole: b"time",
        }

    def add_message(self, message: Message):
        self.beginInsertRows(QModelIndex(), len(self._messages), len(self._messages))
        self._messages.append(message)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self._messages.clear()
        self.endResetModel()

class ChatViewModel(QObject):
    message_added = pyqtSignal(int)  # index added
    def __init__(self):
        super().__init__()
        self.model = MessageListModel()

    def send_user(self, text: str):
        msg = Message(sender="user", text=text, timestamp=datetime.utcnow())
        self.model.add_message(msg)
        self.message_added.emit(self.model.rowCount()-1)

    def send_assistant(self, text: str):
        msg = Message(sender="assistant", text=text, timestamp=datetime.utcnow())
        self.model.add_message(msg)
        self.message_added.emit(self.model.rowCount()-1)

class SidebarListModel(QAbstractListModel):
    TitleRole = Qt.UserRole + 1
    def __init__(self, items: List[str] = None):
        super().__init__()
        self._items = items or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole or role == self.TitleRole:
            return self._items[index.row()]
        return QVariant()

    def add(self, title: str):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(title)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

class MainViewModel(QObject):
    def __init__(self):
        super().__init__()
        self.chat = ChatViewModel()
        self.sidebar = SidebarListModel(["Welcome"])