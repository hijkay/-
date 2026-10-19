"""Приложение «Заметки» на PySide6. Запуск: python notes_app_short.py"""
import os
from abc import ABC, abstractmethod
from datetime import datetime
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeyEvent, QCloseEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QTextEdit, QPushButton, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QFrame, QStatusBar, QComboBox)

DATA_FILE, REPORT_FILE = "notes.txt", "report.txt"
TIME_FORMAT = "%d.%m.%Y %H:%M:%S"

class Entity(ABC):
    @abstractmethod
    def get_name(self): raise NotImplementedError

class User(Entity):
    def __init__(self, username="UserName"): self.__username = username
    @property
    def username(self): return self.__username
    def get_name(self): return self.username

class Note(Entity):
    def __init__(self, title, content="", category="Личное", created=None):
        self.title, self.content, self.category = title, content, category or "Личное"
        self.created = created or datetime.now().strftime(TIME_FORMAT)
    def get_name(self): return self.title
    def __eq__(self, other):
        if not isinstance(other, Note): return NotImplemented
        return (self.title.casefold(), self.content.casefold(), self.category.casefold()) == (other.title.casefold(), other.content.casefold(), other.category.casefold())
    def __lt__(self, other):
        if not isinstance(other, Note): return NotImplemented
        return self.title.casefold() < other.title.casefold()
    def __str__(self): return f"{self.title} ({self.category})"
    def __repr__(self): return f"Note(title={self.title!r}, category={self.category!r})"
    def __len__(self): return len(self.content)
    def __contains__(self, text): return text.casefold() in self.content.casefold()

class PairEntry:
    def __init__(self, key, value): self.key, self.value = key, value
    def __str__(self): return f"{self.key}: {self.value.title}"
    def __repr__(self): return f"PairEntry({self.key!r}, {self.value!r})"

class NoteCollection(Entity):
    def __init__(self): self.entries, self.next_id = [], 1
    def get_name(self): return "Коллекция заметок"
    def add(self, note):
        key = str(self.next_id); self.next_id += 1
        self.entries.append(PairEntry(key, note)); return key
    def find(self, key): return next((e.value for e in self.entries if e.key == key), None)
    def remove(self, key):
        for e in self.entries:
            if e.key == key: self.entries.remove(e); return True
        return False
    def search(self, query=""):
        q = query.casefold().strip()
        return [(e.key, e.value) for e in self.entries if q in (e.value.title+" "+e.value.content+" "+e.value.category).casefold()]
    def all_notes(self): return [e.value for e in self.entries]
    def __len__(self): return len(self.entries)
    def __iter__(self): return iter(self.entries)
    def __contains__(self, key): return any(e.key == key for e in self.entries)
    def __str__(self): return f"NoteCollection({len(self)} заметок)"
    def __repr__(self): return f"NoteCollection({self.entries!r})"

class SessionReport(Entity):
    def __init__(self, username): self.username, self.started, self.finished = username, datetime.now(), None
    def get_name(self): return self.username
    def close_session(self): self.finished = datetime.now()
    def write(self):
        new = not os.path.exists(REPORT_FILE) or os.path.getsize(REPORT_FILE) == 0
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            if new: f.write("login | time_in | time_out\n")
            end = self.finished or datetime.now()
            f.write(f"{self.username} | {self.started.strftime(TIME_FORMAT)} | {end.strftime(TIME_FORMAT)}\n")

class AppButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent); self.setMinimumHeight(36); self.setCursor(Qt.CursorShape.PointingHandCursor)
    def sizeHint(self):
        s = super().sizeHint(); return QSize(max(90, s.width()), max(36, s.height()))
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter): self.click()
        else: super().keyPressEvent(event)

class SearchField(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent); self.setPlaceholderText("Поиск по заметкам..."); self.setClearButtonEnabled(True)
    def sizeHint(self):
        s = super().sizeHint(); return QSize(max(220, s.width()), s.height())

class NoteEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent); self.setPlaceholderText("Напишите что-нибудь важное..."); self.setAcceptRichText(False)
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab: self.insertPlainText("    ")
        else: super().keyPressEvent(event)

class NotesList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setAlternatingRowColors(True); self.setUniformItemSizes(True)
    def sizeHint(self):
        s = super().sizeHint(); return QSize(260, max(350, s.height()))

class CategoryBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent); self.addItems(["Личное", "Учёба", "Работа", "Идеи", "Важно"])
    def sizeHint(self):
        s = super().sizeHint(); return QSize(max(150, s.width()), s.height())

class NoteWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.user = User(); self.notes = NoteCollection()
        self.session = SessionReport(self.user.username); self.current_key = None
        self.setWindowTitle("Заметки — личное пространство"); self.resize(1000, 650)
        self._build_ui(); self._style(); self._load_notes(); self._refresh(); self.statusBar().showMessage("Готово")
    def _build_ui(self):
        root = QVBoxLayout(); root.setContentsMargins(22, 18, 22, 18)
        central = QWidget(); central.setLayout(root); self.setCentralWidget(central)
        header = QHBoxLayout(); title = QLabel("Мои заметки"); title.setObjectName("heading")
        self.counter = QLabel(); header.addWidget(title); header.addStretch(); header.addWidget(self.counter); root.addLayout(header)
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); root.addWidget(line)
        self.search = SearchField(); self.search.textChanged.connect(self._refresh); root.addWidget(self.search)
        columns, left, right = QHBoxLayout(), QVBoxLayout(), QVBoxLayout()
        left.addWidget(QLabel("Список заметок")); self.list = NotesList(); self.list.currentItemChanged.connect(self._select); left.addWidget(self.list); columns.addLayout(left, 1)
        right.addWidget(QLabel("Редактор")); form = QGridLayout()
        self.title_input = QLineEdit(); self.title_input.setPlaceholderText("Название заметки")
        self.category, self.editor = CategoryBox(), NoteEditor()
        for label, widget, row in [("Заголовок", self.title_input, 0), ("Категория", self.category, 1), ("Содержание", self.editor, 2)]:
            form.addWidget(QLabel(label), row, 0, Qt.AlignmentFlag.AlignTop if row == 2 else Qt.AlignmentFlag(0)); form.addWidget(widget, row, 1)
        form.setRowStretch(2, 1); right.addLayout(form); self.created = QLabel("Новая заметка"); right.addWidget(self.created)
        buttons = QHBoxLayout(); new_btn, del_btn, save_btn = AppButton("Новая"), AppButton("Удалить"), AppButton("Сохранить")
        new_btn.clicked.connect(self._new); del_btn.clicked.connect(self._delete); save_btn.clicked.connect(self._save)
        buttons.addWidget(new_btn); buttons.addWidget(del_btn); buttons.addStretch(); buttons.addWidget(save_btn); right.addLayout(buttons)
        columns.addLayout(right, 2); root.addLayout(columns, 1); self.setStatusBar(QStatusBar())
    def _style(self):
        self.setStyleSheet('''QMainWindow,QWidget{background:#f5f7fb;color:#20283a;font-family:Arial;font-size:14px;} QLabel#heading{font-size:27px;font-weight:bold;color:#17213a;} QLineEdit,QTextEdit,QListWidget,QComboBox{background:white;border:1px solid #dce2ed;border-radius:8px;padding:8px;} QPushButton{background:#e6ebf5;border:0;border-radius:8px;padding:8px 14px;font-weight:bold;} QPushButton[text="Сохранить"]{background:#345bd6;color:white;}''')
    def _load_notes(self):
        if not os.path.exists(DATA_FILE):
            examples = [("План на день","Составить список задач.","Личное"),("Подготовка к экзамену","Повторить классы и методы.","Учёба"),("Идея проекта","Сделать интерфейс удобным.","Идеи"),("Покупки","Бумага, ручка, блокнот.","Личное"),("Вопрос преподавателю","Уточнить требования.","Учёба"),("Рабочая задача","Проверить текущие задачи.","Работа"),("Не забыть","Сохранить изменения.","Важно"),("Идея интерфейса","Использовать ровные отступы.","Идеи"),("Практика Python","Повторить списки и классы.","Учёба"),("Цель недели","Закончить проект.","Личное")]
            for t, c, cat in examples: self.notes.add(Note(t, c, cat))
            self._write_notes(); return
        with open(DATA_FILE, encoding="utf-8") as f:
            for row in f:
                p = row.rstrip("\n").split("|", 3)
                if len(p) == 4: self.notes.add(Note(p[0], p[3].replace("\\n", "\n"), p[1], p[2]))
    def _write_notes(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            for n in self.notes.all_notes():
                body = n.content.replace("|", "/").replace("\n", "\\n")
                f.write(f"{n.title}|{n.category}|{n.created}|{body}\n")
    def _refresh(self, *_):
        selected = self.current_key; self.list.clear()
        for key, note in self.notes.search(self.search.text()):
            item = QListWidgetItem(f"{note.title}\n{note.category} · {note.created}"); item.setData(Qt.ItemDataRole.UserRole, key); self.list.addItem(item)
            if key == selected: self.list.setCurrentItem(item)
        self.counter.setText(f"{len(self.notes)} заметок")
    def _select(self, current, *_):
        if current is None: return
        key = current.data(Qt.ItemDataRole.UserRole); note = self.notes.find(key)
        if note:
            self.current_key = key; self.title_input.setText(note.title); self.editor.setPlainText(note.content)
            self.category.setCurrentText(note.category); self.created.setText(f"Создано: {note.created}")
    def _new(self):
        self.current_key = None; self.list.clearSelection(); self.title_input.clear(); self.editor.clear()
        self.category.setCurrentText("Личное"); self.created.setText("Новая заметка")
    def _save(self):
        title = self.title_input.text().strip()
        if not title: QMessageBox.information(self, "Нужен заголовок", "Введите название заметки."); return
        note = self.notes.find(self.current_key) if self.current_key else None
        if note: note.title, note.content, note.category = title, self.editor.toPlainText(), self.category.currentText()
        else:
            note = Note(title, self.editor.toPlainText(), self.category.currentText()); self.current_key = self.notes.add(note)
        self._write_notes(); self._refresh(); self.created.setText(f"Создано: {note.created}"); self.statusBar().showMessage("Заметка сохранена", 3000)
    def _delete(self):
        if not self.current_key: QMessageBox.information(self, "Удаление", "Сначала выберите заметку."); return
        answer = QMessageBox.question(self, "Удалить", "Удалить выбранную заметку?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.notes.remove(self.current_key); self.current_key = None; self._write_notes(); self._new(); self._refresh()
    def closeEvent(self, event: QCloseEvent):
        self._write_notes(); self.session.close_session(); self.session.write(); event.accept()

if __name__ == "__main__":
    app = QApplication([]); window = NoteWindow(); window.show(); app.exec()
