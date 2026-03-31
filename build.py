import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--name=freerdp-gui',
    '--onefile',
    '--windowed',
    '--add-data=assets:assets',
    '--icon=assets/icon.png',
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtGui',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=cryptography'
])