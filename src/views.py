from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QListView, QVBoxLayout, QLabel,
    QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QFrame, QStackedWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation
from PyQt5.QtGui import QPainter, QColor, QFont, QPalette
from .ui.viewmodels import MainViewModel, MessageListModel
from .ui.models import Message
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QStyledItemDelegate
from .orchestrator import run_orchestrator

class BubbleDelegate(QStyledItemDelegate):
    PADDING = 12
    MAX_WIDTH = 520
    RADIUS = 10

    def paint(self, painter: QPainter, option, index):
        sender = index.model().data(index, MessageListModel.SenderRole)
        text = index.model().data(index, MessageListModel.TextRole)
        rect = option.rect
        painter.save()

        # choose bubble color and alignment
        if sender == "user":
            color = QColor("#DCF8C6")
            align_right = True
            x = rect.right() - min(self.MAX_WIDTH, rect.width()) - 10
        else:
            color = QColor("#FFFFFF")
            align_right = False
            x = rect.left() + 10

        # prepare text wrapping
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_wrapped = fm.elidedText(text, Qt.ElideRight, self.MAX_WIDTH)
        # compute size using boundingRect
        text_rect = fm.boundingRect(0, 0, self.MAX_WIDTH, 1000, Qt.TextWordWrap, text)
        bubble_w = text_rect.width() + self.PADDING*2
        bubble_h = text_rect.height() + self.PADDING*2

        bubble_rect = QRect(x, rect.top() + 6, bubble_w, bubble_h)
        # draw shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0,0,0,10))
        painter.drawRoundedRect(bubble_rect.adjusted(1,2,1,2), self.RADIUS, self.RADIUS)
        # draw bubble
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bubble_rect, self.RADIUS, self.RADIUS)

        # draw text
        painter.setPen(QColor("#222"))
        painter.drawText(bubble_rect.adjusted(self.PADDING, self.PADDING, -self.PADDING, -self.PADDING),
                         Qt.TextWordWrap, text)

        painter.restore()

    def sizeHint(self, option, index):
        text = index.model().data(index, MessageListModel.TextRole)
        fm = option.fontMetrics
        text_rect = fm.boundingRect(0, 0, self.MAX_WIDTH, 1000, Qt.TextWordWrap, text)
        return QSize(text_rect.width() + self.PADDING*4, text_rect.height() + self.PADDING*3)

class EnterTextEdit(QTextEdit):
    send_requested = lambda self, text: None
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            # emit send
            text = self.toPlainText().strip()
            if text:
                print(self.parent())
                self.parent().on_send_clicked()  # call parent's handler
            self.clear()
            return
        super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows OS Agent")
        self.resize(1100, 700)

        self.vm = MainViewModel()
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(6)

        # Sidebar
        sidebar = QWidget()
        s_layout = QVBoxLayout(sidebar)
        header = QLabel("Windows OS Agent")
        header.setObjectName("appHeader")
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(self.on_new_chat)
        conv_list = QListView()
        conv_list.setModel(self.vm.sidebar)
        conv_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        s_layout.addWidget(header)
        s_layout.addWidget(new_chat_btn)
        s_layout.addWidget(conv_list)

        # Main chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        self.list_view = QListView()
        self.list_view.setModel(self.vm.chat.model)
        self.list_view.setItemDelegate(BubbleDelegate())
        self.list_view.setSpacing(8)
        self.list_view.setUniformItemSizes(False)
        self.list_view.setEditTriggers(QListView.NoEditTriggers)

        # auto-scroll when new rows inserted
        self.vm.chat.model.rowsInserted.connect(self.on_rows_inserted)
        self.vm.chat.message_added.connect(self.animate_new_message)

        chat_layout.addWidget(self.list_view)

        # input bar
        input_bar = QWidget()
        ib_layout = QHBoxLayout(input_bar)
        ib_layout.setContentsMargins(8,8,8,8)
        self.input_edit = EnterTextEdit()
        self.input_edit.setFixedHeight(90)
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(100)
        send_btn.clicked.connect(self.on_send_clicked)
        ib_layout.addWidget(self.input_edit)
        ib_layout.addWidget(send_btn)
        chat_layout.addWidget(input_bar)

        # Settings placeholder panel
        settings_panel = QLabel("Settings placeholder")
        settings_panel.setAlignment(Qt.AlignCenter)

        # put sidebar and chat in splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(chat_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 800])

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        central.setLayout(layout)

        # minimal menu / theme toggle placeholder
        self._apply_default_focus()

    def _apply_default_focus(self):
        self.input_edit.setFocus()

    def on_new_chat(self):
        title = f"Chat {self.vm.sidebar.rowCount()+1}"
        self.vm.sidebar.add(title)
        self.vm.chat.model.clear()
        self.input_edit.clear()

    def on_send_clicked(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        # add user message
        self.vm.chat.send_user(text)
        # placeholder assistant response (in real app call Planner)
        self.vm.chat.send_assistant("Processing: " + (text[:200] + ("..." if len(text) > 200 else "")))
        self.input_edit.clear()
        self.input_edit.setText()("")
        for step in run_orchestrator(text):
            self.handle_orchestrator_step(step)

    def handle_orchestrator_step(self, step):
            if step["thought"] is not None:
                self.vm.chat.message_added("thought : ", step["thought"])
            
            elif step["result"] is not None:
                self.vm.chat.message_added("result : ", step["result"])


    def on_rows_inserted(self, parent, first, last):
        # scroll to bottom
        self.list_view.scrollToBottom()

    def animate_new_message(self, index):
        # simple fade-in using opacity effect on the viewport (coarse)
        effect = self.list_view.graphicsEffect()
        # not a per-item animation (QListView complexity), use small flash by repaint
        anim = QPropertyAnimation(self.list_view, b"windowOpacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()