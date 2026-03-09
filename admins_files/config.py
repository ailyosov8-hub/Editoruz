# config.py
import os
import sys

if getattr(sys, 'frozen', False):
	BASE_DATA_DIR = os.path.join(os.path.dirname(sys.executable), 'data')
else:
	BASE_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
HASH_STORE = os.path.join(BASE_DATA_DIR, 'hashes.json')
CREDS_FILE = os.path.join(BASE_DATA_DIR, 'credentials.json')
UPDATE_CHECK_URL = 'https://your-server.example.com/update'  # Replace with your server URL
APP_CONFIG = os.path.join(BASE_DATA_DIR, 'mini_ide_config_improved.json')
PROJECT_SETTINGS = '.mini_ide_settings.json'

# GitHub OAuth
GITHUB_CLIENT_ID = 'Iv1.0123456789abcdef'  # Replace with real client ID

# Themes
THEMES = {
	'dark': {'accent': '#61DAFB', 'secondary': '#282C34'},
	'light': {'accent': '#007acc', 'secondary': '#ffffff'},
	'solarized': {'accent': '#b58900', 'secondary': '#002b36'},
}
DEFAULT_THEME = 'dark'

# Auto suggestions
AUTO_SUGGESTIONS = {
	'main': 'if __name__ == "__main__":\n    main()\n',
	'try': 'try:\n    \nexcept Exception as e:\n    print(e)\n',
	'class': 'class ClassName(object):\n    def __init__(self, args):\n        pass\n',
}

# Keywords
PY_KEYWORDS = [
	'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
]
PY_BUILTINS = [name for name in dir(__builtins__) if not name.startswith('_')]
BASE_AUTOCOMPLETE = sorted(set(PY_KEYWORDS + PY_BUILTINS))

# Other language keywords (add as needed)
JAVA_KEYWORDS = [
	'abstract','assert','boolean','break','byte','case','catch','char','class','const','continue',
	'default','do','double','else','enum','extends','final','finally','float','for','goto','if','implements',
	'import','instanceof','int','interface','long','native','new','package','private','protected','public',
	'return','short','static','strictfp','super','switch','synchronized','this','throw','throws','transient',
	'try','void','volatile','while'
]
# Add more if needed
