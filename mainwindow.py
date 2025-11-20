import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QListWidget, QListWidgetItem,
    QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QFrame, QScrollArea, QDesktopWidget
)
from PyQt5.QtGui import QColor, QFont

from PyQt5 import QtGui

from src.cursor.set_cursor import restore_cursor
from src.orchestrator import run_orchestrator


class UiMessage:
    def __init__(self, sender: str, content: str, timestamp: float = None, meta: Dict[str, Any] = None):
        self.sender = sender  # "user" / "assistant" / "thought" / "tool_result"
        self.content = content
        self.timestamp = timestamp or time.time()
        self.meta = meta or {}


class OrchestratorWorker(QObject):
    step_signal = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self._thread = None

    def start(self):
        # run the generator on a separate Python thread
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            for step in run_orchestrator(self.prompt):
                # emit each step to the main thread
                self.step_signal.emit(step)
                # tiny sleep to allow UI to process events smoothly
                # (and to avoid hammering the event loop if orchestrator yields very fast)
                time.sleep(0.01)
        finally:
            self.finished.emit()


# simple bubble widget factory
def make_bubble_widget(msg: UiMessage) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(6, 6, 6, 6)
    frame = QFrame()
    frame_layout = QVBoxLayout(frame)
    frame_layout.setContentsMargins(12, 8, 12, 8)

    label = QLabel(msg.content)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label.setFont(QFont("Segoe UI", 10))

    # styling per sender/type
    if msg.sender == "user":
        frame.setStyleSheet("background:#2b79ff;color:white;border-radius:10px;")
        label.setStyleSheet("color:white;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignRight)
    elif msg.sender == "assistant":
        frame.setStyleSheet("background:#ffffff;color:#111;border-radius:10px;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)
    elif msg.sender == "thought":
        # gray italic bubble
        label.setStyleSheet("color:#444;font-style:italic;")
        frame.setStyleSheet("background:#efefef;color:#444;border-radius:10px;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)
    elif msg.sender == "tool_result":
        # monospaced block for tool output
        label.setFont(QFont("Consolas", 9))
        frame.setStyleSheet("background:#111111;color:#f6f6f6;border-radius:6px;")
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)
    else:
        frame_layout.addWidget(label)
        layout.addWidget(frame, 0, Qt.AlignLeft)

    return w


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows OS Agent - GUI")
        self.setWindowIcon(QtGui.QIcon("./public/icon.png"))
        
        self.resize(1100, 700)

        # Top-level layout: sidebar + main chat
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(6)

        # Sidebar (minimal)
        sidebar = QWidget()
        s_layout = QVBoxLayout(sidebar)
        header = QLabel("Windows OS Agent")
        header.setStyleSheet("font-weight:700;padding:8px;")
        new_chat_btn = QPushButton("New Chat")
        new_chat_btn.clicked.connect(self.on_new_chat)
        self.conv_list = QListWidget()
        self.conv_list.addItem("Conversation 1")
        self.conv_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        s_layout.addWidget(header)
        s_layout.addWidget(new_chat_btn)
        s_layout.addWidget(self.conv_list)

        # Main chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        # message area: QListWidget with custom widgets
        self.msg_list = QListWidget()
        self.msg_list.setSpacing(8)
        self.msg_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        chat_layout.addWidget(self.msg_list)

        # input bar
        input_bar = QWidget()
        ib_layout = QHBoxLayout(input_bar)
        ib_layout.setContentsMargins(8, 8, 8, 8)
        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(90)
        send_btn = QPushButton("Send")
        send_btn.setFixedWidth(100)
        send_btn.clicked.connect(self.on_send_clicked)
        ib_layout.addWidget(self.input_edit)
        ib_layout.addWidget(send_btn)
        chat_layout.addWidget(input_bar)

        splitter.addWidget(sidebar)
        splitter.addWidget(chat_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 800])

        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        central.setLayout(main_layout)

        # store worker reference to keep alive
        self._worker = None

    def on_new_chat(self):
        self.conv_list.addItem(f"Conversation {self.conv_list.count()+1}")
        self.msg_list.clear()
        self.input_edit.clear()

    def on_send_clicked(self):
        ag = QDesktopWidget().availableGeometry()
        sg = QDesktopWidget().screenGeometry()

        widget = self.geometry()
        x = ag.width() - widget.width()
        y = 2 * ag.height() - sg.height() - widget.height()
        self.move(x, y)

        prompt = self.input_edit.toPlainText().strip()
        if not prompt:
            return
        # add user bubble immediately
        user_msg = UiMessage(sender="user", content=prompt)
        self._append_message(user_msg)
        self.input_edit.clear()

        # start orchestrator worker
        self._worker = OrchestratorWorker(prompt)
        self._worker.step_signal.connect(self.handle_orchestrator_step)
        self._worker.finished.connect(self.on_worker_finished)
        self._worker.start()

    def handle_orchestrator_step(self, step: Dict[str, Any]):
        """
        Called in GUI thread for each orchestrator yielded step.
        step has keys: type, content
        types:
          - user_prompt: we already rendered user message; ignore or show brief note
          - thought: show planner 'thought' as gray bubble (content is planner dict)
          - tool_result: show result block
          - assistant: show assistant final response
        """
        stype = step.get("type")
        content = step.get("content")
        if stype == "user_prompt":
            # optionally render a small system note
            note = UiMessage(sender="thought", content=f"Prompt submitted: {content}")
            self._append_message(note)
        elif stype == "thought":
            # planner thought is typically a dict with 'thought' and maybe 'tool_call'
            # render the 'thought' string if available, otherwise dump dict
            if isinstance(content, dict):
                thought_text = content.get("thought") or str(content)
            else:
                thought_text = str(content)
            thought_msg = UiMessage(sender="thought", content=str(thought_text))
            self._append_message(thought_msg)
        elif stype == "tool_result":
            # tool result is dict; render as monospaced block
            import json
            try:
                text = json.dumps(content, ensure_ascii=False, indent=2)
            except Exception:
                text = str(content)
            tool_msg = UiMessage(sender="tool_result", content=text)
            self._append_message(tool_msg)
        elif stype == "assistant":
            assistant_msg = UiMessage(sender="assistant", content=str(content))
            self._append_message(assistant_msg)
        else:
            # unknown step type: show as assistant note
            other_msg = UiMessage(sender="assistant", content=f"{stype}: {content}")
            self._append_message(other_msg)

    def _append_message(self, ui_msg: UiMessage):
        item = QListWidgetItem()
        widget = make_bubble_widget(ui_msg)
        item.setSizeHint(widget.sizeHint())
        self.msg_list.addItem(item)
        self.msg_list.setItemWidget(item, widget)
        # auto-scroll to bottom
        self.msg_list.scrollToBottom()

    def on_worker_finished(self):
        # optional post-run actions
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open("./src/ui/styles.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Failed to load stylesheet: {e}")
    win = MainWindow()
    win.show()
    restore_cursor()
    sys.exit(app.exec_())