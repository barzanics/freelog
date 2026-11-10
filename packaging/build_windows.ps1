# Run on Windows from the folder that CONTAINS worktracker\  (needs: py -m pip install pyinstaller PyQt5 openpyxl reportlab cryptography tzdata)
py -m PyInstaller --noconfirm --clean --windowed --name WorkTracker --paths . --exclude-module tkinter --exclude-module PyQt5.QtWebEngine worktracker\main.py
# Optional installer: install Inno Setup, then:  iscc packaging\installer.iss
