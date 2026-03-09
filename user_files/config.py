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
    'monokai': {'accent': '#f92672', 'secondary': '#272822'},
    'dracula': {'accent': '#bd93f9', 'secondary': '#282a36'},
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

JS_KEYWORDS = [
    'break','case','catch','class','const','continue','debugger','default','delete','do','else','export','extends','finally','for','function','if','import','in','instanceof','let','new','return','super','switch','this','throw','try','typeof','var','void','while','with','yield','enum','await','implements','package','protected','static','interface','private','public'
]
TS_KEYWORDS = JS_KEYWORDS + [
    'any','as','async','await','boolean','constructor','declare','get','module','namespace','never','readonly','require','number','set','string','symbol','type','from'
]
C_KEYWORDS = [
    'auto','break','case','char','const','continue','default','do','double','else','enum','extern','float','for','goto','if','inline','int','long','register','restrict','return','short','signed','sizeof','static','struct','switch','typedef','union','unsigned','void','volatile','while','_Alignas','_Alignof','_Atomic','_Bool','_Complex','_Generic','_Imaginary','_Noreturn','_Static_assert','_Thread_local'
]
CPP_KEYWORDS = C_KEYWORDS + [
    'alignas','alignof','and','and_eq','asm','bitand','bitor','bool','catch','char16_t','char32_t','class','compl','constexpr','const_cast','decltype','delete','dynamic_cast','explicit','export','false','friend','mutable','namespace','new','noexcept','not','not_eq','nullptr','operator','or','or_eq','private','protected','public','reinterpret_cast','static_assert','static_cast','template','this','thread_local','throw','true','try','typeid','typename','using','virtual','wchar_t','xor','xor_eq'
]
GO_KEYWORDS = [
    'break','default','func','interface','select','case','defer','go','map','struct','chan','else','goto','package','switch','const','fallthrough','if','range','type','continue','for','import','return','var'
]
RUST_KEYWORDS = [
    'as','break','const','continue','crate','else','enum','extern','false','fn','for','if','impl','in','let','loop','match','mod','move','mut','pub','ref','return','self','Self','static','struct','super','trait','true','type','unsafe','use','where','while','async','await','dyn','abstract','become','box','do','final','macro','override','priv','try','typeof','unsized','virtual','yield'
]
PHP_KEYWORDS = [
    'abstract','and','array','as','break','callable','case','catch','class','clone','const','continue','declare','default','do','echo','else','elseif','empty','enddeclare','endfor','endforeach','endif','endswitch','endwhile','eval','exit','extends','final','finally','for','foreach','function','global','goto','if','implements','include','include_once','instanceof','insteadof','interface','isset','list','namespace','new','or','print','private','protected','public','require','require_once','return','static','switch','throw','trait','try','unset','use','var','while','xor','yield'
]
KOTLIN_KEYWORDS = [
    'as','as?','break','class','continue','do','else','false','for','fun','if','in','!in','interface','is','!is','null','object','package','return','super','this','throw','true','try','typealias','val','var','when','while','by','catch','constructor','delegate','dynamic','field','file','finally','get','import','init','param','property','receiver','set','setparam','where','actual','abstract','annotation','companion','const','crossinline','data','enum','expect','external','final','infix','inline','inner','internal','lateinit','noinline','open','operator','out','override','private','protected','public','reified','sealed','suspend','tailrec','vararg'
]
JAVA_KEYWORDS = [
    'abstract','assert','boolean','break','byte','case','catch','char','class','const','continue',
    'default','do','double','else','enum','extends','final','finally','float','for','goto','if','implements',
    'import','instanceof','int','interface','long','native','new','package','private','protected','public',
    'return','short','static','strictfp','super','switch','synchronized','this','throw','throws','transient',
    'try','void','volatile','while'
]
# Add more if needed