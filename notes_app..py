"""
Приложение «Заметки» для экзамена по ООП.
Зависимость: pip install PySide6
Запуск: python notes_app.py

Данные заметок хранятся в notes.txt в простом текстовом формате.
При закрытии создаётся/дополняется report.txt:
login | time_in | time_out
Формат времени: %d.%m.%Y %H:%M:%S
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCloseEvent, QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QFrame, QStatusBar, QToolButton, QComboBox
)

DATA_FILE = "notes.txt"
REPORT_FILE = "report.txt"
TIME_FORMAT = "%d.%m.%Y %H:%M:%S"


class Entity(ABC):
    """Абстрактная базовая сущность приложения."""

    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя/название сущности."""
        raise NotImplementedError


class Note(Entity):
    """Модель заметки с геттерами, сеттерами и специальными методами."""

    def __init__(self, title: str, content: str, category: str = "Личное",
                 created_at: str | None = None):
        self.__title = title
        self.__content = content
        self.__category = category
        self.__created_at = created_at or datetime.now().strftime(TIME_FORMAT)

    def get_name(self) -> str:
        return self.__title

    def get_title(self) -> str:
        return self.__title

    def set_title(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Заголовок не может быть пустым.")
        self.__title = value.strip()

    def get_content(self) -> str:
        return self.__content

    def set_content(self, value: str) -> None:
        self.__content = value

    def get_category(self) -> str:
        return self.__category

    def set_category(self, value: str) -> None:
        self.__category = value.strip() or "Личное"

    def get_created_at(self) -> str:
        return self.__created_at

    def set_created_at(self, value: str) -> None:
        self.__created_at = value

    title = property(get_title, set_title)
    content = property(get_content, set_content)
    category = property(get_category, set_category)
    created_at = property(get_created_at, set_created_at)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Note):
            return NotImplemented
        return (self.title.casefold(), self.content.casefold(),
                self.category.casefold()) == (
                other.title.casefold(), other.content.casefold(),
                other.category.casefold())

    def __lt__(self, other: "Note") -> bool:
        if not isinstance(other, Note):
            return NotImplemented
        return self.title.casefold() < other.title.casefold()

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"

    def __repr__(self) -> str:
        return f"Note(title={self.title!r}, category={self.category!r})"

    def __len__(self) -> int:
        return len(self.content)

    def __contains__(self, text: str) -> bool:
        return text.casefold() in (self.title + " " + self.content).casefold()


class User(Entity):
    """Пользователь приложения."""

    def __init__(self, username: str):
        self.__username = username.strip() or "User"

    def get_name(self) -> str:
        return self.__username

    def get_username(self) -> str:
        return self.__username

    def set_username(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self.__username = value.strip()

    username = property(get_username, set_username)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.username.casefold() == other.username.casefold()

    def __lt__(self, other: "User") -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.username.casefold() < other.username.casefold()

    def __str__(self) -> str:
        return self.username

    def __repr__(self) -> str:
        return f"User(username={self.username!r})"


class PairEntry(Entity):
    """Одна пара ключ-значение; используется вместо dict."""

    def __init__(self, key: str, value: Note):
        self.__key = key
        self.__value = value

    def get_name(self) -> str:
        return self.__key

    def get_key(self) -> str:
        return self.__key

    def set_key(self, value: str) -> None:
        self.__key = value

    def get_value(self) -> Note:
        return self.__value

    def set_value(self, value: Note) -> None:
        if not isinstance(value, Note):
            raise TypeError("Значение должно быть объектом Note.")
        self.__value = value

    key = property(get_key, set_key)
    value = property(get_value, set_value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PairEntry):
            return NotImplemented
        return self.key == other.key and self.value == other.value

    def __str__(self) -> str:
        return f"{self.key}: {self.value.title}"

    def __repr__(self) -> str:
        return f"PairEntry(key={self.key!r}, value={self.value!r})"


class NoteCollection(Entity):
    """Кастомное хранилище пар, без использования dict."""

    def __init__(self):
        self.__entries: list[PairEntry] = []
        self.__next_id = 1

    def get_name(self) -> str:
        return "Коллекция заметок"

    def all_notes(self) -> list[Note]:
        return [entry.value for entry in self.__entries]

    def add(self, note: Note) -> str:
        key = str(self.__next_id)
        self.__next_id += 1
        self.__entries.append(PairEntry(key, note))
        return key

    def remove(self, key: str) -> bool:
        for index, entry in enumerate(self.__entries):
            if entry.key == key:
                del self.__entries[index]
                return True
        return False

    def find(self, key: str) -> Note | None:
        for entry in self.__entries:
            if entry.key == key:
                return entry.value
        return None

    def key_for(self, note: Note) -> str | None:
        for entry in self.__entries:
            if entry.value is note:
                return entry.key
        return None

    def replace(self, key: str, note: Note) -> bool:
        for entry in self.__entries:
            if entry.key == key:
                entry.value = note
                return True
        return False

    def search(self, query: str) -> list[tuple[str, Note]]:
        query = query.casefold().strip()
        return [(entry.key, entry.value) for entry in self.__entries
                if not query or query in entry.value.title.casefold()
                or query in entry.value.content.casefold()
                or query in entry.value.category.casefold()]

    def __len__(self) -> int:
        return len(self.__entries)

    def __iter__(self):
        return iter(self.__entries)

    def __contains__(self, key: str) -> bool:
        return any(entry.key == key for entry in self.__entries)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NoteCollection):
            return NotImplemented
        return self.all_notes() == other.all_notes()

    def __str__(self) -> str:
        return f"NoteCollection({len(self)} заметок)"

    def __repr__(self) -> str:
        return f"NoteCollection(entries={self.__entries!r})"


class SessionReport(Entity):
    """Журнал времени работы приложения."""

    def __init__(self, username: str):
        self.__username = username
        self.__time_in = datetime.now()
        self.__time_out: datetime | None = None

    def get_name(self) -> str:
        return self.__username

    def close_session(self) -> None:
        if self.__time_out is None:
            self.__time_out = datetime.now()

    def write(self, filename: str = REPORT_FILE) -> None:
        is_new = not os.path.exists(filename) or os.path.getsize(filename) == 0
        with open(filename, "a", encoding="utf-8") as file:
            if is_new:
                file.write("+----------------+---------------------+---------------------+\\n")
                file.write("| login          | time_in             | time_out            |\\n")
                file.write("+----------------+---------------------+---------------------+\\n")
            out_time = self.__time_out or datetime.now()
            file.write(
                f"| {self.__username[:14]:<14} | "
                f"{self.__time_in.strftime(TIME_FORMAT):<19} | "
                f"{out_time.strftime(TIME_FORMAT):<19} |\\n"
            )
            file.write("+----------------+---------------------+---------------------+\\n")

    def __str__(self) -> str:
        return f"Сеанс пользователя {self.__username}"

    def __repr__(self) -> str:
        return f"SessionReport(username={self.__username!r})"


class AppButton(QPushButton):
    """Кнопка с переопределёнными методами."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)

    def sizeHint(self) -> QSize:
        size = super().sizeHint()
        return QSize(max(size.width(), 90), max(size.height(), 36))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Return:
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)


class SearchField(QLineEdit):
    """Поле поиска."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Поиск по заметкам...")
        self.setClearButtonEnabled(True)

    def sizeHint(self) -> QSize:
        size = super().sizeHint()
        return QSize(max(size.width(), 220), size.height())


class NoteEditor(QTextEdit):
    """Редактор содержимого заметки."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Напишите что-нибудь важное...")
        self.setAcceptRichText(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("    ")
            event.accept()
        else:
            super().keyPressEvent(event)


class NotesList(QListWidget):
    """Список заметок."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setUniformItemSizes(True)

    def sizeHint(self) -> QSize:
        return QSize(260, max(350, super().sizeHint().height()))


class CategoryBox(QComboBox):
    """Выбор категории."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItems(["Личное", "Учёба", "Работа", "Идеи", "Важно"])

    def sizeHint(self) -> QSize:
        size = super().sizeHint()
        return QSize(max(150, size.width()), size.height())


class NoteWindow(QMainWindow):
    """Главное окно приложения и его функциональность."""

    def __init__(self):
        super().__init__()
        self.user = User("UserName")
        self.notes = NoteCollection()
        self.session = SessionReport(self.user.username)
        self.current_key: str | None = None
        self._loading = False
        self.setWindowTitle("Заметки — личное пространство")
        self.resize(1000, 650)
        self.setMinimumSize(760, 500)
        self._build_ui()
        self._apply_style()
        self._load_notes()
        self._refresh_list()
        self.statusBar().showMessage("Готово")

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        heading = QLabel("Мои заметки")
        heading.setObjectName("heading")
        self.counter = QLabel("0 заметок")
        self.counter.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(heading, 1)
        header.addWidget(self.counter)
        root.addLayout(header)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(separator)

        search_row = QHBoxLayout()
        self.search = SearchField()
        self.search.textChanged.connect(self._refresh_list)
        search_row.addWidget(self.search)
        root.addLayout(search_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(18)

        left = QVBoxLayout()
        list_label = QLabel("Список заметок")
        list_label.setObjectName("section")
        self.note_list = NotesList()
        self.note_list.currentItemChanged.connect(self._select_note)
        left.addWidget(list_label)
        left.addWidget(self.note_list, 1)
        content_row.addLayout(left, 1)

        right = QVBoxLayout()
        form_label = QLabel("Редактор")
        form_label.setObjectName("section")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название заметки")
        self.category = CategoryBox()
        self.editor = NoteEditor()
        self.created_label = QLabel("Новая заметка")
        self.created_label.setObjectName("muted")

        title_label = QLabel("Заголовок")
        category_label = QLabel("Категория")
        body_label = QLabel("Содержание")
        for label in (title_label, category_label, body_label):
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.addWidget(title_label, 0, 0)
        grid.addWidget(self.title_input, 0, 1)
        grid.addWidget(category_label, 1, 0)
        grid.addWidget(self.category, 1, 1)
        grid.addWidget(body_label, 2, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.editor, 2, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(2, 1)

        self.save_button = AppButton("Сохранить")
        self.new_button = AppButton("Новая")
        self.delete_button = AppButton("Удалить")
        self.save_button.clicked.connect(self._save_note)
        self.new_button.clicked.connect(self._new_note)
        self.delete_button.clicked.connect(self._delete_note)

        buttons = QHBoxLayout()
        buttons.addWidget(self.new_button)
        buttons.addWidget(self.delete_button)
        buttons.addStretch(1)
        buttons.addWidget(self.save_button)

        right.addWidget(form_label)
        right.addLayout(grid, 1)
        right.addWidget(self.created_label)
        right.addLayout(buttons)
        content_row.addLayout(right, 2)
        root.addLayout(content_row, 1)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Приложение готово")

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f7fb; color: #20283a;
                                  font-family: Arial; font-size: 14px; }
            QLabel#heading { font-size: 27px; font-weight: 700; color: #17213a; }
            QLabel#section { font-size: 16px; font-weight: 600; }
            QLabel#muted { color: #737d91; font-size: 12px; }
            QLineEdit, QTextEdit, QListWidget, QComboBox {
                background: white; border: 1px solid #dce2ed;
                border-radius: 8px; padding: 9px; selection-background-color: #cddcff;
            }
            QLineEdit:focus, QTextEdit:focus, QListWidget:focus, QComboBox:focus {
                border: 1px solid #6d8fe8;
            }
            QPushButton {
                background: #e6ebf5; border: none; border-radius: 8px;
                padding: 8px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #d7e0f2; }
            QPushButton:pressed { background: #c7d4ed; }
            QPushButton[text="Сохранить"] { background: #345bd6; color: white; }
            QPushButton[text="Сохранить"]:hover { background: #274bbd; }
            QStatusBar { color: #68748a; }
        """)

    def _load_notes(self) -> None:
        if not os.path.exists(DATA_FILE):
            # 10 начальных пользовательских объектов для демонстрации требования.
            examples = [
                ("План на день", "Составить список задач и расставить приоритеты.", "Личное"),
                ("Подготовка к экзамену", "Повторить классы, наследование и методы.", "Учёба"),
                ("Идея проекта", "Сделать приложение простым и удобным.", "Идеи"),
                ("Покупки", "Бумага, ручка, блокнот.", "Личное"),
                ("Вопрос преподавателю", "Уточнить требования к специальным методам.", "Учёба"),
                ("Рабочая задача", "Проверить список текущих задач.", "Работа"),
                ("Не забыть", "Сохранить изменения перед закрытием.", "Важно"),
                ("Идея интерфейса", "Использовать ровные отступы и ясные подписи.", "Идеи"),
                ("Практика Python", "Повторить списки и собственные классы.", "Учёба"),
                ("Цель недели", "Закончить проект и проверить запуск.", "Личное"),
            ]
            for title, body, category in examples:
                self.notes.add(Note(title, body, category))
            self._write_notes()
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                for line in file:
                    parts = line.rstrip("\n").split("|", 3)
                    if len(parts) == 4:
                        title, category, created, body = parts
                        self.notes.add(Note(title, body.replace("\\n", "\n"),
                                            category, created))
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Ошибка чтения", f"Не удалось загрузить заметки:\\n{error}")

    def _write_notes(self) -> None:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                for note in self.notes.all_notes():
                    safe_title = note.title.replace("|", "/").replace("\n", " ")
                    safe_category = note.category.replace("|", "/")
                    safe_body = note.content.replace("\\\\", "\\\\\\\\").replace("\\n", "\\\\n")
                    file.write(f"{safe_title}|{safe_category}|{note.created_at}|{safe_body}\n")
        except OSError as error:
            QMessageBox.critical(self, "Ошибка сохранения", str(error))

    def _refresh_list(self, *_args) -> None:
        selected_key = self.current_key
        self._loading = True
        self.note_list.clear()
        results = self.notes.search(self.search.text())
        for key, note in results:
            item = QListWidgetItem(f"{note.title}\n{note.category} · {note.created_at}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.note_list.addItem(item)
            if key == selected_key:
                self.note_list.setCurrentItem(item)
        self.counter.setText(f"{len(self.notes)} заметок")
        self._loading = False

    def _select_note(self, current: QListWidgetItem | None,
                     _previous: QListWidgetItem | None = None) -> None:
        if self._loading or current is None:
            return
        key = current.data(Qt.ItemDataRole.UserRole)
        note = self.notes.find(key)
        if note is None:
            return
        self.current_key = key
        self.title_input.setText(note.title)
        self.editor.setPlainText(note.content)
        self.category.setCurrentText(note.category)
        self.created_label.setText(f"Создано: {note.created_at}")
        self.statusBar().showMessage(f"Открыта заметка: {note.title}")

    def _new_note(self) -> None:
        self.current_key = None
        self.note_list.clearSelection()
        self.title_input.clear()
        self.editor.clear()
        self.category.setCurrentText("Личное")
        self.created_label.setText("Новая заметка")
        self.title_input.setFocus()
        self.statusBar().showMessage("Создание новой заметки")

    def _save_note(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.information(self, "Нужен заголовок",
                                    "Введите название заметки.")
            self.title_input.setFocus()
            return
        if self.current_key is not None:
            note = self.notes.find(self.current_key)
            if note is not None:
                note.title = title
                note.content = self.editor.toPlainText()
                note.category = self.category.currentText()
        else:
            note = Note(title, self.editor.toPlainText(), self.category.currentText())
            self.current_key = self.notes.add(note)
        self._write_notes()
        self._refresh_list()
        self.created_label.setText(f"Создано: {note.created_at}")
        self.statusBar().showMessage("Заметка сохранена", 3000)

    def _delete_note(self) -> None:
        if self.current_key is None:
            QMessageBox.information(self, "Удаление", "Сначала выберите заметку.")
            return
        answer = QMessageBox.question(
            self, "Удалить заметку", "Вы уверены, что хотите удалить эту заметку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.notes.remove(self.current_key)
            self.current_key = None
            self._write_notes()
            self._new_note()
            self._refresh_list()
            self.statusBar().showMessage("Заметка удалена", 3000)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._write_notes()
        self.session.close_session()
        self.session.write()
        event.accept()


def main() -> None:
    app = QApplication([])
    app.setApplicationName("Заметки")
    window = NoteWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
