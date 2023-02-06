import os
import sys
import re
import json
import sqlite3
from PyQt5.QtGui import QIcon
import mainWindow

application_path = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(__file__)
)
html_dir = os.path.join(application_path, "html")


pattern = re.compile(
    r"^(http|https)?:?(\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
)
without_http_pattern = re.compile(
    r"[\-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
)
file_pattern = re.compile(r"^file://")
# DB to open
connection = sqlite3.connect("BrowserLocalDB.db", isolation_level=None, check_same_thread=False)
# connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS "history" (
        "id"	INTEGER,
        "title"	TEXT,
        "url"	TEXT,
        "date"	TEXT,
        "time"	TEXT,
        PRIMARY KEY("id")
    )"""
)

if os.path.isfile("bookmarks.json") == False:
    with open("bookmarks.json", "x") as f:
        f.write(json.dumps([]))


if os.path.isfile("settings.json"):  # If settings file exists, then open it
    with open("settings.json", "r") as f:
        settings_data = json.load(f)
else:  # If settings not exists, then create a new file with default settings
    json_data = json.loads(
    """
    {
        "defaultSearchEngine": "DuckDuckGo",
        "startupPage": "https://browser-new-tab.netlify.app",
        "newTabPage": "https://browser-new-tab.netlify.app",
        "homeButtonPage": "https://browser-new-tab.netlify.app"
        "theme": "dark"
    }
    """
    )
    with open("settings.json", "w") as f:
        json.dump(json_data, f, indent=2)
    with open("settings.json", "r") as f:
        settings_data = json.load(f)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    mainWindow.app.setWindowIcon(QIcon('icon.png'))
    window = mainWindow.MainWindow()
    window.showMaximized()
    sys.exit(mainWindow.app.exec_())