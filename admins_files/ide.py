
from login import *

try:
	import requests
	HAS_REQUESTS = True
except ImportError:
	HAS_REQUESTS = False

try:
	import jedi
	HAS_JEDI = True
except ImportError:
	HAS_JEDI = False

# SyntaxHighlighter and Editor classes (copy from original)
class SyntaxHighlighter(QSyntaxHighlighter):
	def __init__(self, parent, lang='python'):
		super().__init__(parent)
		self.lang = lang
		self._setup_rules()

	def _setup_rules(self):
		self.highlighting_rules = []
		keyword_format = QTextCharFormat()
		keyword_format.setForeground(QColor("#569CD6"))
		keyword_format.setFontWeight(QFont.Bold)

		keywords = PY_KEYWORDS if self.lang == 'python' else []
		if self.lang == 'java':
			keywords = JAVA_KEYWORDS
		# Add more languages as needed

		for word in keywords:
			pattern = r'\b' + re.escape(word) + r'\b'
			self.highlighting_rules.append((re.compile(pattern, re.IGNORECASE), keyword_format))

		# Comments
		comment_format = QTextCharFormat()
		comment_format.setForeground(QColor("#6A9955"))
		self.highlighting_rules.append((re.compile(r'#.*'), comment_format))

		# Strings
		string_format = QTextCharFormat()
		string_format.setForeground(QColor("#CE9178"))
		self.highlighting_rules.append((re.compile(r'".*"'), string_format))
		self.highlighting_rules.append((re.compile(r"'.*'"), string_format))

	def highlightBlock(self, text):
		for pattern, format in self.highlighting_rules:
			for match in pattern.finditer(text):
				self.setFormat(match.start(), match.end() - match.start(), format)

class Editor(QPlainTextEdit):
	focus_in = pyqtSignal()
	focus_out = pyqtSignal()

	def __init__(self, file_path=None, content="", lang='python', palette=None, comments_visible=True, auto_suggest=True, extra_completions=None):
		super().__init__()
		self.file_path = file_path
		self.lang = lang
		self.palette = palette or {'accent': '#7FB4CA', 'secondary': '#0f1112'}
		self.comments_visible = comments_visible
		self.auto_suggest = auto_suggest
		self.extra_completions = extra_completions or []
		self.highlighter = SyntaxHighlighter(self.document(), lang)
		self.setPlainText(content)
		self.setStyleSheet(f"QPlainTextEdit{{background:{self.palette['secondary']};color:#e6eef6;border:none}}")
		self.completer = QCompleter(BASE_AUTOCOMPLETE + self.extra_completions)
		self.completer.setWidget(self)
		self.completer.activated.connect(self.insert_completion)
		self.textChanged.connect(self._update_completions)

	def focusInEvent(self, event):
		super().focusInEvent(event)
		self.focus_in.emit()

	def focusOutEvent(self, event):
		super().focusOutEvent(event)
		self.focus_out.emit()

	def isModifiedContent(self):
		return self.document().isModified()

	def _update_completions(self):
		if not self.auto_suggest:
			return
		cursor = self.textCursor()
		text = self.toPlainText()
		lines = text.split('\n')
		if cursor.blockNumber() < len(lines):
			line = lines[cursor.blockNumber()]
			prefix = line[:cursor.positionInBlock()].strip()
			if prefix in AUTO_SUGGESTIONS:
				suggestion = AUTO_SUGGESTIONS[prefix]
				# Insert suggestion if not already there
				if not text.endswith(suggestion):
					cursor.movePosition(QTextCursor.End)
					cursor.insertText(suggestion)
					self.setTextCursor(cursor)

	def insert_completion(self, completion):
		tc = self.textCursor()
		tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(self.completer.completionPrefix()))
		tc.insertText(completion)
		self.setTextCursor(tc)

	def keyPressEvent(self, event):
		if self.completer.popup().isVisible():
			if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
				event.ignore()
				return
		super().keyPressEvent(event)
		if event.key() == Qt.Key_Tab and self.auto_suggest:
			self._show_completions()
		elif event.key() == Qt.Key_Escape:
			self.completer.popup().hide()

	def _show_completions(self):
		tc = self.textCursor()
		tc.select(QTextCursor.WordUnderCursor)
		prefix = tc.selectedText()
		if prefix:
			self.completer.setCompletionPrefix(prefix)
			popup = self.completer.popup()
			cr = self.cursorRect()
			cr.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
			self.completer.complete(cr)

# AiManager class
class AiManager:
	def __init__(self, parent=None):
		self.parent = parent

	def ready(self):
		if not HAS_REQUESTS:
			return False
		if getattr(self.parent, 'openai_key', None):
			return True
		return False

	def ensure_ready(self):
		if not HAS_REQUESTS:
			QMessageBox.warning(self.parent, "AI unavailable", "Python package 'requests' is not installed.")
			return False
		if not self.ready():
			QMessageBox.information(self.parent, "AI key needed", "Provide an OpenAI key via Settings.")
			return False
		return True

	def query(self, prompt):
		if not self.ensure_ready():
			return "(AI not configured)"
		key = getattr(self.parent, 'openai_key', '')
		if not key:
			return "(OpenAI key missing)"
		try:
			res = requests.post(
				"https://api.openai.com/v1/chat/completions",
				headers={"Authorization": f"Bearer {key}"},
				json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}], "max_tokens":800}
			)
			if res.status_code == 200:
				return res.json()['choices'][0]['message']['content']
			else:
				return f"AI error: {res.status_code}"
		except Exception as e:
			return f"AI request failed: {e}"

# PluginManager (simplified)
class PluginManager:
	def __init__(self, parent):
		self.parent = parent
		self.plugins = []

	def load_plugins(self):
		# Simplified, no actual loading
		pass

# The main IDE class (simplified version)
class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self.tree = QTreeView()
		self.fsmodel = QFileSystemModel()
		self.fsmodel.setReadOnly(False)
		self.tree.setModel(self.fsmodel)
		self.tree.clicked.connect(self.onTreeClicked)

		right_split = QSplitter(Qt.Vertical)
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.closeTab)
		self.tabs.currentChanged.connect(self.onTabChanged)

		self.terminal = QListWidget()
		self.terminal_input = QLineEdit()
		self.terminal_input.returnPressed.connect(self.runCommandFromInput)

		right_split.addWidget(self.tabs)
		right_split.addWidget(self.terminal)
		right_split.addWidget(self.terminal_input)

		main_split.addWidget(self.tree)
		main_split.addWidget(right_split)
		self.setCentralWidget(main_split)

		# Toolbar
		tb = QToolBar()
		self.addToolBar(tb)
		self.act_run = QAction('Run', self)
		self.act_run.triggered.connect(self.runCode)
		tb.addAction(self.act_run)

		self.loadConfig()
		ensure_login(self)

		if self.tabs.count() == 0:
			ed = Editor()
			self.tabs.addTab(ed, 'Welcome')

		self.statusBar().showMessage('Ready')

	def loadConfig(self):
		if os.path.exists(APP_CONFIG):
			try:
				with open(APP_CONFIG, 'r', encoding='utf8') as f:
					cfg = json.load(f)
				self.last_folder = cfg.get('folder')
				self.openai_key = cfg.get('openai_key', '')
				if self.last_folder and os.path.isdir(self.last_folder):
					self.fsmodel.setRootPath(self.last_folder)
					self.tree.setRootIndex(self.fsmodel.index(self.last_folder))
			except Exception:
				pass

	def saveConfig(self):
		data = {'folder': self.last_folder, 'openai_key': self.openai_key}
		try:
			with open(APP_CONFIG, 'w', encoding='utf8') as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def onTreeClicked(self, index):
		path = self.fsmodel.filePath(index)
		if os.path.isfile(path):
			with open(path, 'r', encoding='utf8') as f:
				content = f.read()
			lang = self._lang(path)
			ed = Editor(file_path=path, content=content, lang=lang, palette=self.palette)
			self.tabs.addTab(ed, os.path.basename(path))
			self.tabs.setCurrentWidget(ed)

	def _lang(self, path):
		ext = os.path.splitext(path)[1].lower()
		ext_lang = {
			'.py': 'python', '.java': 'java', '.js': 'javascript', '.ts': 'typescript',
			'.cpp': 'cpp', '.c': 'c', '.go': 'go', '.rs': 'rust', '.php': 'php', '.kt': 'kotlin'
		}
		return ext_lang.get(ext, 'python')

	def closeTab(self, idx):
		self.tabs.removeTab(idx)

	def onTabChanged(self, idx):
		if idx >= 0:
			w = self.tabs.widget(idx)
			if isinstance(w, Editor) and w.file_path:
				self.setWindowTitle(f"Editor - {os.path.basename(w.file_path)}")

	def runCode(self):
		current = self.tabs.currentWidget()
		if isinstance(current, Editor) and current.file_path and current.file_path.endswith('.py'):
			subprocess.run([sys.executable, current.file_path])

	def runCommandFromInput(self):
		cmd = self.terminal_input.text()
		if cmd:
			result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
			self.terminal.addItem(f"> {cmd}")
			self.terminal.addItem(result.stdout)
			if result.stderr:
				self.terminal.addItem(result.stderr)
			self.terminal_input.clear()

	# Hash project methods
	def _hash_project(self):
		if not self.last_folder or not os.path.isdir(self.last_folder):
			return
		hashes = {}
		for root, dirs, files in os.walk(self.last_folder):
			for fn in files:
				p = os.path.join(root, fn)
				rel = os.path.relpath(p, self.last_folder)
				h = compute_sha256(p)
				if h:
					hashes[rel] = h
		save_hashes(hashes)
		if HAS_REQUESTS and self.logged_in:
			try:
				requests.post(UPDATE_CHECK_URL, json={'user': self.identifier, 'provider': self.logged_in_provider})
			except Exception:
				pass

	def verify_project_hashes(self):
		if not self.last_folder:
			return True
		stored = load_hashes()
		for rel, expected in stored.items():
			p = os.path.join(self.last_folder, rel)
			if os.path.isfile(p) and compute_sha256(p) != expected:
				return False
		return True

class SettingsDialog(QDialog):
    def __init__(self, parent=None, theme=DEFAULT_THEME, font_size=12, ai_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Sozlamalar")
        v = QVBoxLayout()
        # Theme
        v.addWidget(QLabel("Mavzuni tanlash:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(theme)
        v.addWidget(self.theme_combo)
        # Font size
        v.addWidget(QLabel("Shrift o'lchami:"))
        self.font_size = QLineEdit(str(font_size))
        v.addWidget(self.font_size)
        # AI
        self.ai_checkbox = QPushButton("AI yordam yoqilgan" if ai_enabled else "AI yordam o'chirilgan")
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setChecked(ai_enabled)
        self.ai_checkbox.clicked.connect(self._toggle_ai)
        v.addWidget(self.ai_checkbox)
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        self.setLayout(v)
        self.setFixedWidth(350)
        self.setFixedHeight(250)
    def _toggle_ai(self):
        checked = self.ai_checkbox.isChecked()
        self.ai_checkbox.setText("AI yordam yoqilgan" if checked else "AI yordam o'chirilgan")
    def get_settings(self):
        return {
            'theme': self.theme_combo.currentText(),
            'font_size': int(self.font_size.text()),
            'ai_enabled': self.ai_checkbox.isChecked()
        }

class HelpPanel(QDockWidget):
    def __init__(self, parent=None, lang='uz'):
        super().__init__("Qo‘llanma / Help / Справка", parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.setWidget(self.text)
        self.setMinimumWidth(400)
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

class IDE(QMainWindow):
	def __init__(self):
		super().__init__()
		self.lang = self._load_user_lang()
		self.setWindowTitle("Editor")
		self.resize(1200, 800)
		self.last_folder = None
		self.sidebar_visible = True
		self.palette = THEMES[DEFAULT_THEME]
		self.openai_key = ''
		self.logged_in = False
		self.logged_in_provider = None
		self.identifier = None

		self.ai_manager = AiManager(self)
		self.plugin_manager = PluginManager(self)

		# UI setup (simplified)
		main_split = QSplitter(Qt.Horizontal)
		self