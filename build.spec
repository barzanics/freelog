# PyInstaller: pyinstaller build.spec   (run from the folder containing worktracker/)
a = Analysis(['worktracker/main.py'], pathex=['.'], excludes=['tkinter', 'unittest', 'pydoc', 'PyQt5.QtWebEngine', 'PyQt5.QtMultimedia',
             'PyQt5.QtNetwork', 'PyQt5.QtSql', 'PyQt5.QtQml', 'PyQt5.QtQuick'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name='WorkTracker', console=False, strip=True, upx=True)
