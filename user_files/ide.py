import sys, os, json, re, subprocess, tempfile, importlib.util
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QFileDialog, QToolBar, QAction, QSplitter, QTreeView, QFileSystemModel,
    QTabWidget, QLabel, QLineEdit, QPushButton, QWidget, QTextEdit, QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox,
    QListWidget, QInputDialog, QMessageBox, QDockWidget, QShortcut, QCompleter, QMenu
)
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QIcon, QKeySequence, QTextCursor
from PyQt5.QtCore import Qt

APP_CONFIG = os.path.join(os.getcwd(), 'data', 'mini_ide_config_improved.json')
THEMES = {
    # editor/background color plus UI secondary color and an accent for the
    # sidebar/file tree to mimic VSCode-style theme switching.
    'Light': {
        'background': '#ffffff',
        'secondary': '#f0f0f0',
        'foreground': '#222222',
        'keyword': '#0057b7',
        'string': '#008000',
        'comment': '#888888',
        'accent': '#0057b7'
    },
    'Dark': {
        'background': '#23272e',
        'secondary': '#1e1e1e',
        'foreground': '#e6e6e6',
        'keyword': '#569CD6',
        'string': '#98C379',
        'comment': '#6A9955',
        'accent': '#569CD6'
    },
    'Monokai': {
        'background': '#272822',
        'secondary': '#3e3d32',
        'foreground': '#f8f8f2',
        'keyword': '#f92672',
        'string': '#e6db74',
        'comment': '#75715e',
        'accent': '#f92672'
    },
}
DEFAULT_THEME = 'Dark'
PY_KEYWORDS = [
    'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'import', 'from', 'as', 'return', 'try', 'except', 'with', 'pass',
    'break', 'continue', 'in', 'is', 'not', 'and', 'or', 'lambda', 'yield', 'global', 'nonlocal', 'assert', 'del', 'raise',
    'finally', 'True', 'False', 'None'
]
# very small set for C/CPP/Java/JS
C_KEYWORDS = ['int','float','double','char','long','short','for','while','if','else','return','void','static','struct']

EXT_LANG_MAP = {
    '.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
    '.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
}

# ---------- helpers ---------------------------------------------------------

def _get_config_value(key, default=None):
    if os.path.exists(APP_CONFIG):
        try:
            with open(APP_CONFIG, 'r', encoding='utf8') as f:
                cfg = json.load(f)
            return cfg.get(key, default)
        except Exception:
            pass
    return default

def _set_config_value(key, value):
    cfg = {}
    if os.path.exists(APP_CONFIG):
        try:
            with open(APP_CONFIG, 'r', encoding='utf8') as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg[key] = value
    try:
        os.makedirs(os.path.dirname(APP_CONFIG), exist_ok=True)
        with open(APP_CONFIG, 'w', encoding='utf8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ---------- syntax highlighting ------------------------------------------------

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, theme, lang='python'):
        super().__init__(parent)
        self.theme = theme
        self.lang = lang
        self._setup_rules()

    def _setup_rules(self):
        self.highlighting_rules = []
        keyword_format = QTextCharFormat(); keyword_format.setForeground(QColor(self.theme['keyword'])); keyword_format.setFontWeight(QFont.Bold)
        keywords = []
        if self.lang == 'python':
            keywords = PY_KEYWORDS
            comment_pattern = r'#.*'
            string_patterns = [r'(".*?"|.*?)', r"'.*?'"]
        else:
            # simple C-like rules
            keywords = C_KEYWORDS
            comment_pattern = r'//.*|/\*.*?\*/'
            string_patterns = [r'".*?"', r"'.*?'"]
        for word in keywords:
            pattern = r'\b' + re.escape(word) + r'\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        string_format = QTextCharFormat(); string_format.setForeground(QColor(self.theme['string']))
        for pat in string_patterns:
            self.highlighting_rules.append((re.compile(pat), string_format))
        comment_format = QTextCharFormat(); comment_format.setForeground(QColor(self.theme['comment']))
        self.highlighting_rules.append((re.compile(comment_pattern), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

# ---------- editor widget ----------------------------------------------------

class Editor(QPlainTextEdit):
    def __init__(self, file_path=None, content='', lang='python', theme=THEMES[DEFAULT_THEME], parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.lang = lang
        self.theme = theme
        self.setPlainText(content)
        self.setFont(QFont('Consolas', 12))
        self.setStyleSheet(f'background:{theme["background"]};color:{theme["foreground"]};')
        self.highlighter = SyntaxHighlighter(self.document(), theme, lang)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['python','cpp','c','javascript','txt'])
        self.lang_combo.setCurrentText(lang)
        self.lang_combo.currentTextChanged.connect(self.set_language)
        self.run_btn = QPushButton('Ishga tushirish / Kompilyatsiya')
        self.run_btn.clicked.connect(self.run_code)
        self.output_box = QTextEdit(); self.output_box.setReadOnly(True)

    def set_language(self, lang):
        self.lang = lang
        self.highlighter.lang = lang
        self.highlighter._setup_rules()

    def run_code(self):
        code = self.toPlainText()
        lang = self.lang_combo.currentText()
        self.output_box.clear()
        try:
            if lang == 'python':
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py', encoding='utf8') as f:
                    f.write(code); fname = f.name
                proc = subprocess.run([sys.executable, fname], capture_output=True, text=True)
                self.output_box.setPlainText(proc.stdout + ("\n" + proc.stderr if proc.stderr else ''))
            elif lang in ('cpp','c'):
                ext = '.cpp' if lang == 'cpp' else '.c'
                with tempfile.NamedTemporaryFile('w', delete=False, suffix=ext, encoding='utf8') as f:
                    f.write(code); src = f.name
                exe = src + '.exe'
                compile_res = subprocess.run(['g++', src, '-o', exe], capture_output=True, text=True)
                if compile_res.returncode != 0:
                    self.output_box.setPlainText('Kompilyatsiya xatosi:\n' + compile_res.stderr)
                else:
                    run_res = subprocess.run([exe], capture_output=True, text=True)
                    self.output_box.setPlainText(run_res.stdout + ("\n" + run_res.stderr if run_res.stderr else ''))
            elif lang == 'javascript':
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.js', encoding='utf8') as f:
                    f.write(code); fname = f.name
                proc = subprocess.run(['node', fname], capture_output=True, text=True)
                self.output_box.setPlainText(proc.stdout + ("\n" + proc.stderr if proc.stderr else ''))
            else:
                self.output_box.setPlainText('Bu til uchun kompilyatsiya/ishga tushirish yo‘q yetkazilmagan yetkazilgan.')
        except Exception as e:
            self.output_box.setPlainText(f'Xatolik: {e}')

# ---------- AI manager ------------------------------------------------------

class AiManager:
    def __init__(self, parent=None):
        self.parent = parent

    def ready(self):
        try:
            import requests
        except ImportError:
            return False
        key = getattr(self.parent, 'openai_key', '')
        return bool(key)

    def ensure_ready(self):
        import requests
        if not self.ready():
            QMessageBox.information(self.parent, "AI sozlanmagan", "Iltimos Settings orqali OpenAI kalitini kiriting va 'requests' paketini o'rnating.")
            return False
        return True

    def query(self, prompt):
        if not self.ensure_ready():
            return "(AI tayyor emas)"
        import requests
        key = self.parent.openai_key
        try:
            res = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}], "max_tokens":600}
            )
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            return f"AI xato: {res.status_code}"
        except Exception as e:
            return f"AI so‘rovida xato: {e}"

# ---------- plugin manager --------------------------------------------------

class PluginManager:
    def __init__(self, ide):
        self.ide = ide
        self.plugins = []

    def load_plugins(self):
        folders = ['plugins']
        if getattr(self.ide, 'is_admin', False):
            folders.append('admin_plugins')
        for folder in folders:
            if not os.path.isdir(folder):
                continue
            for name in os.listdir(folder):
                if name.endswith('.py'):
                    path = os.path.join(folder, name)
                    try:
                        spec = importlib.util.spec_from_file_location(name[:-3], path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'register'):
                            module.register(self.ide)
                        self.plugins.append(module)
                    except Exception as e:
                        print('plugin error', name, e)

# ---------- library manager -------------------------------------------------

class LibraryManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Kutubxonalar boshqaruvi')
        v = QVBoxLayout()
        self.list_widget = QListWidget()
        v.addWidget(self.list_widget)
        h = QHBoxLayout()
        install_btn = QPushButton('Yangi o‘rnatish')
        install_btn.clicked.connect(self.add_package)
        uninstall_btn = QPushButton('O‘chirish')
        uninstall_btn.clicked.connect(self.remove_package)
        h.addWidget(install_btn); h.addWidget(uninstall_btn)
        v.addLayout(h)
        self.setLayout(v)
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        try:
            import pkg_resources
            for d in pkg_resources.working_set:
                self.list_widget.addItem(f"{d.project_name}=={d.version}")
        except Exception:
            pass

    def add_package(self):
        name, ok = QInputDialog.getText(self, 'O‘rnatish', 'Paket nomi:')
        if ok and name:
            subprocess.run([sys.executable, '-m', 'pip', 'install', name])
            self.refresh()

    def remove_package(self):
        name, ok = QInputDialog.getText(self, 'O‘chirish', 'Paket nomi:')
        if ok and name:
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', name])
            self.refresh()

# ---------- helper widgets --------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None, lang='uz', theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        v.addWidget(QLabel("Tilni tanlash:"))
        self.lang_combo = QComboBox(); self.lang_combo.addItems(['uz','ru','en']); self.lang_combo.setCurrentText(lang)
        v.addWidget(self.lang_combo)
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox(); self.theme_combo.addItems(list(THEMES.keys())); self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size)); v.addWidget(self.font_size)
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True); self.ai_checkbox.setChecked(ai_enabled);
        self.ai_checkbox.clicked.connect(self._toggle_ai); v.addWidget(self.ai_checkbox)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v); self.setFixedWidth(350); self.setFixedHeight(300)

    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")

    def get_settings(self):
        return {'lang': self.lang_combo.currentText(),
                'theme': self.theme_combo.currentText(),
                'font_size': int(self.font_size.text()),
                'ai_enabled': self.ai_checkbox.isChecked()}

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit(); self.text.setReadOnly(True)
        self.setWidget(self.text); self.setMinimumWidth(400)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.update_help(lang)

    def update_help(self, lang):
        doc_path = os.path.join(os.getcwd(), 'docs', f'README_{lang}.md')
        if not os.path.exists(doc_path):
            doc_path = os.path.join(os.getcwd(), 'docs', 'README_uz.md')
        try:
            with open(doc_path, 'r', encoding='utf8') as f:
                self.text.setPlainText(f.read())
        except Exception:
            self.text.setPlainText("Qo‘llanma topilmadi.")

# ---------- main IDE --------------------------------------------------------

class IDE(QMainWindow):
    def __init__(self, is_admin=False):
        super().__init__()
        self.is_admin = is_admin
        self.lang = _get_config_value('lang','uz')
        theme_key = _get_config_value('theme', DEFAULT_THEME)
        self.theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
        self.font_size = _get_config_value('font_size', 12)
        # folder to show in tree; remember between runs
        self.last_folder = _get_config_value('folder', os.getcwd())
        self.openai_key = _get_config_value('openai_key', '')

        self.plugin_manager = PluginManager(self)
        self.ai_manager = AiManager(self)
        # start with sidebar hidden; only reveal after user opens a folder or
        # presses the logo/button.  ignore stored preference on startup.
        self.sidebar_visible = False

        self._setup_ui()
        self.plugin_manager.load_plugins()
        # apply theme immediately
        self._apply_theme_to_ui()
        self.statusBar().showMessage('Ready')

    def _setup_ui(self):
        self.setWindowTitle("Editor")
        self.resize(1200,800)
        sidebar = QWidget(); sidebar.setFixedWidth(60)
        sb_layout = QVBoxLayout(); sb_layout.setContentsMargins(0,0,0,0)
        # use a clickable button instead of static label for the logo so we can
        # toggle the sidebar by clicking it.
        logo = QPushButton("A")
        logo.setFlat(True)
        logo.setStyleSheet("font-size:24px; font-weight:bold;")
        logo.clicked.connect(self.toggle_sidebar)
        logo.setCursor(Qt.PointingHandCursor)
        sb_layout.addWidget(logo); sb_layout.addStretch(); sidebar.setLayout(sb_layout)

        self.tree = QTreeView(); self.fsmodel = QFileSystemModel()
        self.fsmodel.setRootPath(self.last_folder); self.tree.setModel(self.fsmodel)
        self.tree.setRootIndex(self.fsmodel.index(self.last_folder)); self.tree.clicked.connect(self.on_tree_clicked)
        # remember folder when changed
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_context_menu)

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.terminal = QListWidget()
        self.terminal.setVisible(False)  # hide until there is output
        self.terminal_input = QLineEdit(); self.terminal_input.returnPressed.connect(self.run_command)

        # store sidebar widget for toggling
        self.sidebar = sidebar
        left_split = QSplitter(Qt.Vertical); left_split.addWidget(self.tree); 
        term_widget = QWidget(); tbox = QVBoxLayout(); tbox.addWidget(self.terminal); tbox.addWidget(self.terminal_input);
        term_widget.setLayout(tbox); left_split.addWidget(term_widget)

        main_split = QSplitter(Qt.Horizontal); main_split.addWidget(sidebar); main_split.addWidget(left_split); main_split.addWidget(self.tabs)
        self.main_split = main_split
        self.setCentralWidget(main_split)
        # apply visibility state; start hidden regardless of config
        self.sidebar.setVisible(self.sidebar_visible)
        if not self.sidebar_visible:
            self.main_split.setSizes([0,1,4])

        tb = QToolBar(); self.addToolBar(tb)
        tb.addAction(self._tr('Yangi'), self.new_file)
        # add shortcut for sidebar toggle
        self.shortcut_toggle = QShortcut(QKeySequence("Ctrl+B"), self)
        self.shortcut_toggle.activated.connect(self.toggle_sidebar)
        tb.addAction(self._tr('Ochish'), self.open_file)
        tb.addAction(self._tr('Saqlash'), self.save_file)
        # folder action shown only when a folder has been opened
        self.act_open_folder = tb.addAction('Folder ochish', self.open_folder)
        if not self.last_folder or not os.path.isdir(self.last_folder):
            self.act_open_folder.setVisible(False)
        tb.addAction('Fayl qo‘shish', self.add_file)
        tb.addAction('Papka qo‘shish', self.add_folder)
        tb.addAction('O‘chirish', self.delete_selected)
        tb.addAction('Nomini o‘zgartirish', self.rename_selected)
        tb.addAction('Qidiruv', self.open_search)
        tb.addAction(self._tr('Sozlamalar'), self.open_settings)
        tb.addAction('Toggle sidebar', self.toggle_sidebar)
        # add explicit button to toggle terminal visibility
        tb.addAction('Toggle terminal', self.toggle_terminal)
        if self.is_admin:
            tb.addAction('Kutubxonalar', self.open_library_manager)
            tb.addAction('GitHub’dan yuklash', self.github_download)
            tb.addAction('Admin sozlamalar', self.open_admin_settings)
        tb.addAction('Help', lambda: HelpPanel(self, self.lang).show())
        self.toolbar = tb

        # open welcome tab
        self.new_file(welcome=True)
        # set window icon if available
        icon_path = os.path.join(os.getcwd(), 'icon.ico')
        if os.path.exists(icon_path):
            try:
                self.setWindowIcon(QIcon(icon_path))
            except Exception as e:
                print('icon load failed', e)

    # utility methods
    def _tr(self, text):
        uz = {'Yangi':'Yangi','Ochish':'Fayl ochish','Saqlash':'Saqlash','Sozlamalar':'Sozlamalar','Tayyor':'Tayyor','Xush kelibsiz':'Xush kelibsiz'}
        en = {'Yangi':'New','Ochish':'Open','Saqlash':'Save','Sozlamalar':'Settings','Tayyor':'Ready','Xush kelibsiz':'Welcome'}
        return uz.get(text,text) if self.lang=='uz' else en.get(text,text)

    def _apply_theme_to_ui(self):
        # apply stylesheet to main window and set default fg/bg on root
        # use explicit secondary color if provided, otherwise fall back to
        # the standard background value so that existing themes continue to
        # work.  Many widget types are styled here so that changing the theme
        # affects the entire interface, not just editors and dialogs.
        sec = self.theme.get('secondary', self.theme.get('background', ''))
        bg = self.theme.get('background', sec)
        fg = self.theme.get('foreground', '#000')
        # build a comprehensive stylesheet; order matters because later rules
        # override earlier ones if they overlap.  the intent is to make the
        # *editor content* use `background` while the rest of the UI uses
        # `secondary` so that panels/toolbars/menus are distinct like in VSCode.
        style = f"""
QMainWindow {{ background:{sec}; color:{fg}; }}
QToolBar, QMenuBar, QMenu, QTabBar, QTabWidget, QDockWidget {{ background:{sec}; color:{fg}; }}
QWidget {{ background:{sec}; color:{fg}; }}
QLabel, QMenu, QToolButton, QPushButton {{ color:{fg}; }}
QLineEdit, QComboBox, QListWidget, QTreeView, QTableView, QSpinBox, QTextEdit, QPlainTextEdit {{
    background:{bg}; color:{fg}; }}
QPlainTextEdit {{ background:{bg}; color:{fg}; }}
"""
        try:
            self.setStyleSheet(style)
        except Exception:
            pass
        # update toolbar button texts if language changed
        for action in self.toolbar.actions():
            txt = action.text()
            if txt in ['Yangi','New','Ochish','Open','Saqlash','Save','Sozlamalar','Settings','Help']:
                action.setText(self._tr(txt))
        # reapply sidebar style as colours may rely on theme
        self._apply_sidebar_style()
        # propagate colours to any dialog-like widgets created by the global app
        try:
            app = QApplication.instance()
            if app:
                app.setStyleSheet(f"QMessageBox, QFileDialog, QInputDialog {{ background:{sec}; color:{fg}; }}")
        except Exception:
            pass
        # update all open editors with new theme
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w is None:
                continue
            ed = w.findChild(Editor)
            if ed:
                ed.theme = self.theme
                ed.setStyleSheet(f'background:{self.theme.get("background","")};color:{self.theme.get("foreground",
                    "")}')
                try:
                    ed.highlighter.theme = self.theme
                    ed.highlighter._setup_rules()
                except Exception:
                    pass
        # style tab widget area
        try:
            tab_bg = self.theme.get('secondary', '')
            tab_fg = self.theme.get('foreground', '')
            self.tabs.setStyleSheet(f'QTabWidget {{background:{tab_bg}; color:{tab_fg};}}')
        except Exception:
            pass
        # optionally style terminal widget
        try:
            term_bg = self.theme.get('background', '')
            term_fg = self.theme.get('foreground', '')
            self.terminal.setStyleSheet(f'background:{term_bg};color:{term_fg};')
        except Exception:
            pass

    def _lang(self,path):
        return EXT_LANG_MAP.get(os.path.splitext(path)[1].lower(),'python')

    # file operations (new, open, save) similar to previous code
    def new_file(self, welcome=False):
        ed = Editor(theme=self.theme)
        w = QWidget(); vbox=QVBoxLayout(); hbox=QHBoxLayout(); hbox.addWidget(ed.lang_combo); hbox.addWidget(ed.run_btn)
        vbox.addLayout(hbox); vbox.addWidget(ed); vbox.addWidget(QLabel('Natija:')); vbox.addWidget(ed.output_box)
        w.setLayout(vbox);
        title = self._tr('Xush kelibsiz') if welcome else self._tr('Yangi')
        self.tabs.addTab(w, title); self.tabs.setCurrentWidget(w)

    def open_file(self):
        path,_ = QFileDialog.getOpenFileName(self,self._tr('Ochish'), self.last_folder,'All Files (*)')
        if not path: return
        # remember folder
        self.last_folder = os.path.dirname(path)
        _set_config_value('folder', self.last_folder)
        try:
            with open(path,'r',encoding='utf8') as f: content=f.read()
            lang=self._lang(path)
            ed = Editor(file_path=path, content=content, lang=lang, theme=self.theme)
            w=QWidget(); vbox=QVBoxLayout(); hbox=QHBoxLayout(); hbox.addWidget(ed.lang_combo); hbox.addWidget(ed.run_btn)
            vbox.addLayout(hbox); vbox.addWidget(ed); vbox.addWidget(QLabel('Natija:')); vbox.addWidget(ed.output_box)
            w.setLayout(vbox)
            self.tabs.addTab(w, os.path.basename(path)); self.tabs.setCurrentWidget(w)
        except Exception:
            pass

    def save_file(self):
        w = self.tabs.currentWidget()
        if not w: return
        ed = w.findChild(Editor)
        if not ed: return
        path = ed.file_path
        if not path:
            path,_ = QFileDialog.getSaveFileName(self,self._tr('Saqlash'), self.last_folder,'All Files (*)')
            if not path: return
            ed.file_path = path
        # remember folder after saving
        self.last_folder = os.path.dirname(path)
        _set_config_value('folder', self.last_folder)
        try:
            with open(path,'w',encoding='utf8') as f: f.write(ed.toPlainText())
        except Exception:
            pass

    def add_file(self):
        idx = self.tree.currentIndex();
        dir_path = self.fsmodel.filePath(idx) if self.fsmodel.isDir(idx) else os.path.dirname(self.fsmodel.filePath(idx))
        name,ok = QInputDialog.getText(self,'Fayl qo‘shish','Fayl nomi:')
        if ok and name:
            try:
                with open(os.path.join(dir_path,name),'w',encoding='utf8'):
                    pass
            except Exception:
                pass

    def add_folder(self):
        idx = self.tree.currentIndex();
        dir_path = self.fsmodel.filePath(idx) if self.fsmodel.isDir(idx) else os.path.dirname(self.fsmodel.filePath(idx))
        name,ok = QInputDialog.getText(self,'Papka qo‘shish','Papka nomi:')
        if ok and name:
            try:
                os.makedirs(os.path.join(dir_path,name), exist_ok=True)
            except Exception:
                pass

    def delete_selected(self):
        idx = self.tree.currentIndex(); path = self.fsmodel.filePath(idx)
        if not path: return
        confirm = QMessageBox.question(self,'O‘chirish',f'{path}ni o‘chirilsinmi?',QMessageBox.Yes|QMessageBox.No)
        if confirm==QMessageBox.Yes:
            try:
                if os.path.isdir(path): import shutil; shutil.rmtree(path)
                else: os.remove(path)
            except Exception:
                pass

    def rename_selected(self):
        idx=self.tree.currentIndex(); path=self.fsmodel.filePath(idx)
        if not path: return
        new,ok=QInputDialog.getText(self,'Nomini o‘zgartirish','Yangi nom:')
        if ok and new:
            try: os.rename(path, os.path.join(os.path.dirname(path),new))
            except Exception:
                pass

    def open_search(self):
        text,ok=QInputDialog.getText(self,'Qidiruv','Qidiriladigan matn:')
        if not ok or not text: return
        results=[]
        for root,dirs,files in os.walk(self.last_folder):
            for fn in files:
                p=os.path.join(root,fn)
                try:
                    with open(p,'r',encoding='utf8') as f:
                        for i,line in enumerate(f,1):
                            if text in line: results.append(f'{p} ({i}): {line.strip()}')
                except Exception:
                    continue
        QMessageBox.information(self,'Qidiruv natijasi','\n'.join(results) if results else 'Hech narsa topilmadi.')

    def open_settings(self):
        theme_key = [k for k,v in THEMES.items() if v == self.theme][0]
        dlg = SettingsDialog(self, self.lang, theme_key, self.font_size, _get_config_value('ai_enabled',True))
        if dlg.exec_()==QDialog.Accepted:
            s=dlg.get_settings()
            self.lang=s['lang']; _set_config_value('lang',self.lang)
            _set_config_value('theme',s['theme']);
            self.theme=THEMES[s['theme']]
            self.font_size=s['font_size']; _set_config_value('font_size',self.font_size)
            _set_config_value('ai_enabled', s['ai_enabled'])
            # reapply theme and sidebar style after theme change
            self._apply_theme_to_ui()


    def on_tree_clicked(self,index):
        if os.path.isfile(self.fsmodel.filePath(index)):
            self.open_file()

    def close_tab(self,idx): self.tabs.removeTab(idx)
    def on_tab_changed(self,idx):
        w=self.tabs.widget(idx)
        ed=w.findChild(Editor)
        if ed and ed.file_path:
            self.setWindowTitle(f"Editor - {os.path.basename(ed.file_path)}")

    def run_command(self):
        cmd=self.terminal_input.text()
        if not cmd: return
        # show terminal when executing anything
        if not self.terminal.isVisible():
            self.terminal.setVisible(True)
        try:
            res=subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.terminal.addItem(f"> {cmd}")
            self.terminal.addItem(res.stdout)
            if res.stderr: self.terminal.addItem(res.stderr)
        except Exception as e:
            self.terminal.addItem(str(e))
        self.terminal_input.clear()
        # hide terminal again if it has no meaningful content
        self.update_terminal_visibility()

    def open_library_manager(self):
        dlg=LibraryManager(self); dlg.exec_()

    def toggle_terminal(self):
        # simple show/hide with state tracking
        vis = self.terminal.isVisible()
        self.terminal.setVisible(not vis)
        if not vis and self.terminal.count() == 0:
            # if showing empty terminal, keep hidden until something added
            self.terminal.setVisible(False)

    def update_terminal_visibility(self):
        # ensure terminal visible only when it has at least one item
        if self.terminal.count() == 0:
            self.terminal.setVisible(False)
        else:
            self.terminal.setVisible(True)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Folder ochish', self.last_folder or os.getcwd())
        if folder:
            self.last_folder = folder
            self.fsmodel.setRootPath(folder)
            self.tree.setRootIndex(self.fsmodel.index(folder))
            _set_config_value('folder', folder)
            # reveal sidebar automatically when a folder is selected
            if not self.sidebar_visible:
                self.sidebar_visible = True
                _set_config_value('sidebar_visible', True)
                self.sidebar.setVisible(True)
                self.main_split.setSizes([1,3,5])
            # make sure toolbar button is visible once a folder exists
            if hasattr(self, 'act_open_folder'):
                self.act_open_folder.setVisible(True)

    def _tree_context_menu(self, pos):
        # simple context menu for tree: open folder or copy path
        idx = self.tree.indexAt(pos)
        menu = QMenu(self)
        open_folder_action = menu.addAction('Bu papkani ochish')
        action = menu.exec_(self.tree.viewport().mapToGlobal(pos))
        if action == open_folder_action:
            path = self.fsmodel.filePath(idx)
            if os.path.isdir(path):
                self.last_folder = path
                self.fsmodel.setRootPath(path)
                self.tree.setRootIndex(self.fsmodel.index(path))
                _set_config_value('folder', path)

    def _apply_sidebar_style(self):
        # style sidebar using accent color with a little polish
        accent = None
        if isinstance(self.theme, dict):
            accent = self.theme.get('accent') or self.theme.get('keyword')
        if not accent:
            accent = '#444'  # fallback dark grey
        # use a subtle gradient and a border to mimic a modern sidebar
        self.sidebar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {accent}, stop:1 {accent}CC);
            border-right: 1px solid {self.theme.get('foreground', '#fff')};
        """)
        # also color the file tree similarly and ensure text remains readable
        try:
            fg = self.theme.get('foreground', '#fff')
            self.tree.setStyleSheet(f"""
                background:{accent};
                color:{fg};
                selection-background-color:{self.theme.get('background','')};
            """)
        except Exception:
            pass

    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        _set_config_value('sidebar_visible', self.sidebar_visible)
        self.sidebar.setVisible(self.sidebar_visible)
        if not self.sidebar_visible:
            # collapse to zero width
            self.main_split.setSizes([0,1,4])
        else:
            self.main_split.setSizes([1,3,5])

    def open_admin_settings(self):
        # reuse auth module's settings dialog
        try:
            from user_files.auth import AuthSettingsDialog
            dlg = AuthSettingsDialog(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.warning(self, 'Admin', f'Settings ochilmadi: {e}')

    def github_download(self):
        url,ok = QInputDialog.getText(self,'GitHub','Repo URL:')
        if not ok or not url: return
        dest = QFileDialog.getExistingDirectory(self,'Saqlanish papkasi')
        if not dest: return
        try:
            subprocess.run(['git','clone',url,dest], check=True)
            QMessageBox.information(self,'GitHub','Yuklandi')
        except Exception as e:
            QMessageBox.warning(self,'GitHub',f'Xato: {e}')

# end of file
