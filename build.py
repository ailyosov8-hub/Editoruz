# build.py
import subprocess
import sys

def cleanup_workspace():
    """Remove unwanted files/folders before packaging."""
    import shutil
    paths = [
        '__pycache__',
        r'user_files\ide_old.py',
        r'user_files\data\passwords.json',
        r'data\*.json',
    ]
    for p in paths:
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)
            else:
                # wildcard patterns
                import glob
                for f in glob.glob(p):
                    if os.path.isdir(f):
                        shutil.rmtree(f)
                    else:
                        os.remove(f)
        except Exception:
            pass


def build_exe():
    # cleanup before building
    cleanup_workspace()

    # Install requirements
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

    # Install pyinstaller if not installed
    try:
        import PyInstaller
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # Build the exe
    subprocess.check_call([
        sys.executable, '-m', 'PyInstaller',
        '--onedir',  # Folder with exe and data
        # '--windowed',  # No console window - commented for debugging
        '--icon', 'icon.ico',
        '--add-data', 'data;data',  # Include data folder
        '--add-data', 'user_files;user_files',
        '--add-data', 'admin_files;admin_files',
        '--add-data', 'docs;docs',
        '--add-data', 'plugins;plugins',
        '--hidden-import', 'PyQt5.QtCore',
        '--hidden-import', 'PyQt5.QtGui',
        '--hidden-import', 'PyQt5.QtWidgets',
        '--hidden-import', 'jedi',
        '--hidden-import', 'requests',
        '--name', 'Editor',
        'main.py'
    ])

    print("Exe built successfully. Find it in dist/ folder.")

if __name__ == '__main__':
    build_exe()