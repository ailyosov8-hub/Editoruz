import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QFileDialog, QTextEdit
)
from user_files.utils import (
    load_passwords, save_passwords, hash_secret,
    verify_password, set_password
)
import subprocess

# defaults
DEFAULT_USER_PW = '1234'
DEFAULT_ADMIN_PW = '1928'  # admin default password now 1928
MAGIC_ADMIN_CODE = '1928'  # magic code remains same

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter password:"))
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pw)
        btn = QPushButton("OK")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_password(self):
        return self.pw.text()

class AuthSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Settings")
        self.file_path = None
        v = QVBoxLayout()
        # password section
        v.addWidget(QLabel("Change user password:"))
        self.user_pw = QLineEdit()
        self.user_pw.setEchoMode(QLineEdit.Password)
        v.addWidget(self.user_pw)
        btn_user = QPushButton("Save user password")
        btn_user.clicked.connect(self.save_user_pw)
        v.addWidget(btn_user)

        v.addWidget(QLabel("\nChange admin password:"))
        self.admin_pw = QLineEdit()
        self.admin_pw.setEchoMode(QLineEdit.Password)
        v.addWidget(self.admin_pw)
        btn_admin = QPushButton("Save admin password")
        btn_admin.clicked.connect(self.save_admin_pw)
        v.addWidget(btn_admin)

        # code editing section
        v.addWidget(QLabel("\nEdit a code file:"))
        file_h = QHBoxLayout()
        self.open_btn = QPushButton("Open file")
        self.open_btn.clicked.connect(self.open_file)
        file_h.addWidget(self.open_btn)
        self.save_btn = QPushButton("Save file")
        self.save_btn.clicked.connect(self.save_file)
        file_h.addWidget(self.save_btn)
        v.addLayout(file_h)
        self.code_editor = QTextEdit()
        v.addWidget(self.code_editor)

        # git push button
        self.push_btn = QPushButton("Commit & Push changes to GitHub")
        self.push_btn.clicked.connect(self.git_push)
        v.addWidget(self.push_btn)

        self.setLayout(v)

    def save_user_pw(self):
        pw = self.user_pw.text().strip()
        if pw:
            set_password('user', pw)
            QMessageBox.information(self, "Settings", "User password updated")
            self.user_pw.clear()

    def save_admin_pw(self):
        pw = self.admin_pw.text().strip()
        if pw:
            set_password('admin', pw)
            QMessageBox.information(self, "Settings", "Admin password updated")
            self.admin_pw.clear()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open code file", os.getcwd(), "All Files (*.*)")
        if path:
            try:
                with open(path, 'r', encoding='utf8') as f:
                    txt = f.read()
                self.code_editor.setPlainText(txt)
                self.file_path = path
            except Exception as e:
                QMessageBox.warning(self, "Open file", f"Cannot open {path}: {e}")

    def save_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "Save file", "No file selected")
            return
        try:
            with open(self.file_path, 'w', encoding='utf8') as f:
                f.write(self.code_editor.toPlainText())
            QMessageBox.information(self, "Save file", "File saved")
        except Exception as e:
            QMessageBox.warning(self, "Save file", f"Failed to save: {e}")

    def git_push(self):
        # commit any changed files and push
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'admin update'], check=True)
            subprocess.run(['git', 'push'], check=True)
            QMessageBox.information(self, "Git", "Changes pushed to GitHub")
        except Exception as e:
            QMessageBox.warning(self, "Git", f"Git push failed: {e}")


def ensure_login(parent=None):
    """Prompt for password. Returns (success:bool, is_admin:bool).
    If parent is provided it is used as the dialog parent; otherwise None.
    """
    # ensure password file exists with defaults
    pw = load_passwords()
    changed = False
    if 'user' not in pw:
        pw['user'] = hash_secret(DEFAULT_USER_PW)
        changed = True
    if 'admin' not in pw:
        pw['admin'] = hash_secret(DEFAULT_ADMIN_PW)
        changed = True
    if changed:
        save_passwords(pw)

    while True:
        dlg = PasswordDialog(parent)
        if dlg.exec_():
            pwd = dlg.get_password()
            # magic code should open settings only if not actually the admin password
            if pwd == MAGIC_ADMIN_CODE and parent is not None and not verify_password('admin', pwd):
                SettingsDialog(parent).exec_()
                continue
            # check admin first so they aren't treated as regular user when passwords coincide
            if verify_password('admin', pwd):
                # do not automatically pop settings; allow admin to click button
                return True, True
            if verify_password('user', pwd):
                return True, False
            QMessageBox.warning(parent, "Login", "Incorrect password")
            continue
        return False, False
