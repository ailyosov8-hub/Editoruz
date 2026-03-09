import os
import json
import hashlib
import subprocess
from user_files.config import BASE_DATA_DIR, HASH_STORE, CREDS_FILE, UPDATE_CHECK_URL

try:
	import requests
	HAS_REQUESTS = True
except ImportError:
	HAS_REQUESTS = False

def compute_sha256(path):
	try:
		h = hashlib.sha256()
		with open(path, 'rb') as f:
			for chunk in iter(lambda: f.read(8192), b''):
				h.update(chunk)
		return h.hexdigest()
	except Exception:
		return None

def save_hashes(hashes):
	try:
		os.makedirs(BASE_DATA_DIR, exist_ok=True)
		with open(HASH_STORE, 'w', encoding='utf8') as f:
			json.dump(hashes, f, ensure_ascii=False, indent=2)
	except Exception:
		pass

def load_hashes():
	if not os.path.exists(HASH_STORE):
		return {}
	try:
		with open(HASH_STORE, 'r', encoding='utf8') as f:
			return json.load(f)
	except Exception:
		return {}

def hash_secret(secret: str) -> str:
	return hashlib.sha256(secret.encode('utf8')).hexdigest()

def save_credentials(info: dict):
	try:
		os.makedirs(BASE_DATA_DIR, exist_ok=True)
		with open(CREDS_FILE, 'w', encoding='utf8') as f:
			json.dump(info, f, ensure_ascii=False, indent=2)
	except Exception:
		pass

def load_credentials() -> dict:
	if not os.path.exists(CREDS_FILE):
		return {}
	try:
		with open(CREDS_FILE, 'r', encoding='utf8') as f:
			return json.load(f)
	except Exception:
		return {}

# password handling ---------------------------------------------------------
PASSWORD_FILE = os.path.join(BASE_DATA_DIR, 'passwords.json')

def load_passwords() -> dict:
	if not os.path.exists(PASSWORD_FILE):
		return {}
	try:
		with open(PASSWORD_FILE, 'r', encoding='utf8') as f:
			return json.load(f)
	except Exception:
		return {}

def save_passwords(info: dict):
	try:
		os.makedirs(BASE_DATA_DIR, exist_ok=True)
		with open(PASSWORD_FILE, 'w', encoding='utf8') as f:
			json.dump(info, f, ensure_ascii=False, indent=2)
	except Exception:
		pass

def verify_password(role: str, password: str) -> bool:
	pw = load_passwords().get(role)
	if not pw:
		return False
	return hash_secret(password) == pw

def set_password(role: str, password: str):
	pw = load_passwords()
	pw[role] = hash_secret(password)
	save_passwords(pw)

# data integrity helpers ----------------------------------------------------
CHECKSUM_FILE = os.path.join(BASE_DATA_DIR, 'checksums.json')

def save_checksums(checks: dict):
	try:
		os.makedirs(BASE_DATA_DIR, exist_ok=True)
		with open(CHECKSUM_FILE, 'w', encoding='utf8') as f:
			json.dump(checks, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


def load_checksums() -> dict:
	if not os.path.exists(CHECKSUM_FILE):
		return {}
	try:
		with open(CHECKSUM_FILE, 'r', encoding='utf8') as f:
			return json.load(f)
	except Exception:
		return {}


def verify_data_integrity() -> bool:
	"""Return True if stored checksum matches actual files. False indicates tamper."""
	checks = load_checksums()
	current = {}
	for fname in ['hashes.json', 'credentials.json']:
		path = os.path.join(BASE_DATA_DIR, fname)
		if os.path.exists(path):
			h = compute_sha256(path)
			if h:
				current[fname] = h
	if checks != current:
		# if mismatch, update stored values but signal failure
		save_checksums(current)
		return False
	return True

def tr(lang, uz, ru, en):
	if lang == 'ru':
		return ru
	if lang == 'en':
		return en
	return uz

def export_main_to_role(role: str) -> bool:
	"""Copy main.py into the appropriate role folder and return success."""
	try:
		src = os.path.join(os.getcwd(), 'main.py')
		dest_dir = os.path.join(os.getcwd(), 'admin_files' if role == 'admin' else 'user_files')
		os.makedirs(dest_dir, exist_ok=True)
		dst = os.path.join(dest_dir, 'main.py')
		shutil.copy(src, dst)
		return True
	except Exception:
		return False


def check_for_updates(last_folder, logged_in, identifier, logged_in_provider):
	if not last_folder:
		return
	try:
		subprocess.run(['git', '-C', last_folder, 'fetch', 'origin'], check=True)
		local = subprocess.check_output(['git', '-C', last_folder, 'rev-parse', 'HEAD']).strip().decode()
		remote = subprocess.check_output(['git', '-C', last_folder, 'rev-parse', 'origin/main']).strip().decode()
		if local != remote:
			return "Update available: Remote repo has new commits. Run 'git pull'."
	except Exception:
		pass
	if HAS_REQUESTS and logged_in:
		try:
			requests.post(UPDATE_CHECK_URL, json={'user': identifier, 'provider': logged_in_provider})
		except Exception:
			pass
	return None
