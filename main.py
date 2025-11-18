import sys
import json

from PySide6 import QtCore

import password as ps
import os
from PySide6.QtGui import QGuiApplication

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget, QListWidget, QLineEdit,
)

from password import hash_master_password


def first_time():
    if not os.path.exists("salt.bin"):
        with open("salt.bin", "x") as salt_file:
            ps.generate_salt()
            return True
    else:
        try:
            with open("vault.json", "r") as vault_file:
                vault_data = json.load(vault_file)
                if vault_data is None or "master" not in vault_data.get("vault", {}):
                    return True
        except (json.JSONDecodeError, FileNotFoundError):
            return True
    return False

def center_widget(widget):
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return
    screen_geo = screen.availableGeometry()
    widget.adjustSize()
    geom = widget.frameGeometry()
    geom.moveCenter(screen_geo.center())
    widget.move(geom.topLeft())

class AddWindow(QWidget):
    def __init__(self, list_widget: QListWidget):
        super().__init__()

        self.setWindowTitle("Add Site")

        self.list_widget = list_widget

        self.lineedit = QLineEdit()
        self.lineedit.setPlaceholderText("Type your site")
        self.lineedit.returnPressed.connect(self.return_pressed)

        layout = QVBoxLayout()
        layout.addWidget(self.lineedit)
        self.setLayout(layout)

        center_widget(self)

    def return_pressed(self):
        site = self.lineedit.text()
        if site:
            if ps.add_to_vault(site, ps.generate_password()):
                self.list_widget.addItem(site)
            self.close()

class SetupWindow(QWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__()

        layout = QVBoxLayout()
        self.main = main_window
        self.label = QLabel()
        self.label.setText("Type your new mater password, you MUST remember it otherwise you will lose the data")
        layout.addWidget(self.label)

        self.setWindowTitle("Setup")

        self.lineedit = QLineEdit()
        self.lineedit.setPlaceholderText("Type your new master Password")
        self.lineedit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.lineedit)

        self.lineeditconfirm = QLineEdit()
        self.lineeditconfirm.setEchoMode(QLineEdit.EchoMode.NoEcho)
        self.lineeditconfirm.setPlaceholderText("Confirm your new password")
        self.lineeditconfirm.returnPressed.connect(self.return_pressed)
        layout.addWidget(self.lineeditconfirm)

        self.setLayout(layout)
        center_widget(self)

    def return_pressed(self):
        if self.lineedit.text() == self.lineeditconfirm.text():
            ps.add_to_vault("master", hash_master_password(self.lineedit.text()))
            ps.master_password = self.lineedit.text()
            self.main.show()
            self.close()
        else:
            self.lineedit.setPlaceholderText("The two passwords are not the same")
            self.lineeditconfirm.clear()
            self.lineedit.clear()

class RenameWindow(QWidget):
    def __init__(self, old_name: str, list_widget: QListWidget):
        super().__init__()

        self.old_name = old_name
        self.list_widget = list_widget

        self.setWindowTitle("Rename Site")

        self.lineedit = QLineEdit()
        self.lineedit.setPlaceholderText("Type the new site name")
        self.lineedit.returnPressed.connect(self.return_pressed)

        layout = QVBoxLayout()
        layout.addWidget(self.lineedit)
        self.setLayout(layout)

        center_widget(self)

    def return_pressed(self):
        new_name = self.lineedit.text()
        if new_name:
            self.rename_site(self.old_name, new_name)
            items = self.list_widget.findItems(self.old_name, QtCore.Qt.MatchExactly)
            if items:
                item = items[0]
                item.setText(new_name)
            self.close()

    def rename_site(self, old_name: str, new_name: str):
        with open("vault.json", "r") as vault_file:
            vault_data = json.load(vault_file)

        if old_name in vault_data["vault"]:
            vault_data["vault"][new_name] = vault_data["vault"].pop(old_name)

            with open("vault.json", "w") as vault_file:
                json.dump(vault_data, vault_file, indent=4)

class MainWindow(QMainWindow):
    def __init__(self, FT: bool):
        super().__init__()
        if FT:
            self.set_password_window = SetupWindow(self)
            self.set_password_window.show()
        else:
            self.login = LoginWindow(self)
            self.login.show()
            ps.init_vault()

        self.setWindowTitle("PassManager")
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.copylabel = QLabel("Double click an item to copy the password to clipboard")
        layout.addWidget(self.copylabel)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_box)

        self.list_widget = QListWidget()
        self.list_widget.addItems(ps.sites)
        self.list_widget.itemDoubleClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        self.label = QLabel("Selected Passwords")
        layout.addWidget(self.label)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.show_add_window)
        layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_button_clicked)
        layout.addWidget(self.remove_button)

        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self.rename_button_clicked)
        layout.addWidget(self.rename_button)
        self.setLayout(layout)
        center_widget(self)

    def on_item_clicked(self, item):
        self.label.setText(ps.get_password_from_vault(item.text()))
        clipboard = QApplication.clipboard()
        clipboard.setText(self.label.text())

    def remove_button_clicked(self):
        item = self.list_widget.currentItem()
        if item is None:
            return

        with open("vault.json", "r") as vault_file:
            vault_data = json.load(vault_file)

        if item.text() in vault_data["vault"]:
            if item.text() == "master":
                return
            vault_data["vault"].pop(item.text())

            with open("vault.json", "w") as vault_file:
                json.dump(vault_data, vault_file, indent=4)

            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def show_add_window(self):
        self.w = AddWindow(self.list_widget)
        self.w.show()

    def rename_button_clicked(self):
        item = self.list_widget.currentItem()
        if item is None:
            return
        self.w = RenameWindow(item.text(), self.list_widget)
        self.w.show()

    def filter_list(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

class LoginWindow(QListWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window

        self.lineedit = QLineEdit()
        self.lineedit.setPlaceholderText("Type your master Password")
        self.lineedit.returnPressed.connect(self.check_password)
        self.setWindowTitle("Login")

        layout = QVBoxLayout()
        layout.addWidget(self.lineedit)
        self.setLayout(layout)
        center_widget(self)

    def check_password(self):
        password = self.lineedit.text()

        if ps.check_master_password(self.lineedit.text(), ps.get_master_password()):
            ps.master_password = password  # Set global variable
            self.main_window.show()
            self.close()
        else:
            self.lineedit.clear()
            self.lineedit.setPlaceholderText("Wrong Password")


def cleanup():
    ps.master_password = None

lebool = first_time()
app = QApplication(sys.argv)
window = MainWindow(lebool)
app.aboutToQuit.connect(cleanup)
app.exec()
