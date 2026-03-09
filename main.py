import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import QApplication

# choose IDE implementation based on role later after login
# we will import inside __main__ since we don't yet know admin status
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from user_files.auth import ensure_login
# configuration path for theme retrieval
from user_files.config import APP_CONFIG

def check_for_app_update():
    """Lightweight update check: warn if git remote heads differ."""
    try:
        subprocess.run(['git', 'fetch'], check=True)
        local = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
        remote = subprocess.check_output(['git', 'rev-parse', 'origin/main']).strip()
        if local != remote:
            QMessageBox.information(None, "Update available",
                                    "Masofadagi repoda yangi commit bor. git pull qiling.")
    except Exception:
        pass

def check_required_files():
    required = [
        os.path.join('user_files', 'config.py'),
        os.path.join('user_files', 'ide.py'),
        os.path.join('user_files', 'utils.py'),
        os.path.join('user_files', 'auth.py')
    ]
    missing = [f for f in required if not os.path.exists(os.path.join(os.getcwd(), f))]
    return missing


def fetch_repository(role):
    """Ensure local copy of GitHub repo is present; pull or clone as needed.
    role is either True (admin) or False (user) but currently ignored.
    """
    repo_url = 'https://github.com/ailyosov8-hub/Editoruz.git'
    cwd = os.getcwd()
    try:
        if not os.path.isdir(os.path.join(cwd, '.git')):
            subprocess.run(['git', 'clone', repo_url, cwd], check=True)
        else:
            subprocess.run(['git', '-C', cwd, 'pull', 'origin', 'main'], check=True)
    except Exception:
        # fallback download zip via requests
        try:
            import requests, zipfile, io
            zurl = 'https://github.com/ailyosov8-hub/Editoruz/archive/refs/heads/main.zip'
            r = requests.get(zurl)
            if r.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(cwd)
        except Exception:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # apply a simple stylesheet to message/dialog boxes based on the saved theme
    try:
        # import theme definitions from the IDE module
        from user_files.ide import THEMES, DEFAULT_THEME
        theme_key = DEFAULT_THEME
        if os.path.exists(APP_CONFIG):
            try:
                with open(APP_CONFIG, 'r', encoding='utf8') as f:
                    cfg = json.load(f)
                theme_key = cfg.get('theme', theme_key)
            except Exception:
                pass
        theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
        bg = theme.get('background', '#fff')
        fg = theme.get('foreground', '#000')
        # dialogs and file choosers
        app.setStyleSheet(f"QMessageBox, QFileDialog, QInputDialog {{ background:{bg}; color:{fg}; }}")
    except Exception:
        pass

    missing = check_required_files()
    if missing:
        QMessageBox.warning(None, "Fayllar yetishmayapti",
                            f"Quyidagi fayllar mavjud emas: {', '.join(missing)}")
        sys.exit(1)

    def fetch_core_files():
        required = ['ide.py','utils.py','config.py','auth.py']
        missing = [f for f in required if not os.path.exists(os.path.join('user_files', f))]
        if not missing:
            return
        resp = QMessageBox.question(None, "Fayllarni yuklash",
            f"Asosiy fayllar yetishmayapti: {', '.join(missing)}. GitHub'dan yuklashni xohlaysizmi?",
            QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        dest = QFileDialog.getExistingDirectory(None, "Fayllar saqlanadigan papkani tanlang")
        if not dest:
            return
        base = 'https://raw.githubusercontent.com/uzlegen290/Editor/main/user_files/'
        try:
            import requests
        except ImportError:
            QMessageBox.warning(None, "Yuklab olish xatosi", "Python uchun 'requests' paketi kerak.")
            return
        for f in missing:
            try:
                r = requests.get(base + f)
                if r.status_code == 200:
                    with open(os.path.join('user_files', f), 'w', encoding='utf8') as out:
                        out.write(r.text)
            except Exception as e:
                QMessageBox.warning(None, "Yuklab olish xatosi", f"{f} faylini yuklab bo'lmadi: {e}")

    fetch_core_files()

    check_for_app_update()

    ok, is_admin = ensure_login(None)
    if not ok:
        sys.exit(0)
    QMessageBox.information(None, "Kirish", "Tizimga kirdingiz")
    # ensure directories exist
    admin_dir = os.path.join(os.getcwd(), 'admin_files')
    user_dir = os.path.join(os.getcwd(), 'user_files')
    try:
        os.makedirs(admin_dir, exist_ok=True)
        os.makedirs(user_dir, exist_ok=True)
    except Exception:
        pass

    # synchronize repository files for the role (admin/user)
    fetch_repository(is_admin)

    # after successful login import the IDE class (it may depend on is_admin)
    from user_files.ide import IDE
    ide = IDE(is_admin=is_admin)
    # ask for language/theme immediately after login
    ide.open_settings()
    ide.show()
    sys.exit(app.exec_())