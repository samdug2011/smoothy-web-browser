from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMainWindow, QStatusBar, QSplitter, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineCore import QWebEngineUrlScheme
from widgets import BookMarkToolBar, HistoryWindow, BrowserEngineView, NavBar, SmoothySchemeHandler, TabBarPlus, FindPanel
import main
import os
import sys
import datetime

app = QApplication(sys.argv)

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)

    def closeEvent(self, event):
        if self.main_widget.tab_bar.count() > 5:
            reply = QMessageBox.question(self, 'Window Close', 'Are you sure that you want to close %x tabs?'%self.main_widget.tab_bar.count(), QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
                for i in range(self.main_widget.tab_bar.count()):
                    self.main_widget.browser_stacked_widget.widget(i).deleteLater()
                print('Window closed')
            else:
                event.ignore()
        else:
            for i in range(self.main_widget.tab_bar.count()):
                self.main_widget.browser_stacked_widget.widget(i).deleteLater()
            event.accept()
class MainWidget(QWidget):
    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)

        with open(os.path.join("themes","qss","%s.qss" % main.settings_data["theme"]),"r") as fh:
            self.setStyleSheet(fh.read())


        self.first_tab = True
        self.main_window = parent
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.browser_stacked_widget = QStackedWidget()
        self.navbar_stacked_widget = QStackedWidget()

        scheme = QWebEngineUrlScheme(b"smoothy")
        QWebEngineUrlScheme.registerScheme(scheme)

        #Widgets
        self.bookmarks_bar = BookMarkToolBar()
        self.history_dock = HistoryWindow(self)
        self.history_dock.setVisible(False)
        self.tab_bar = TabBarPlus()
        self.status_bar = QStatusBar(self)
        self.find_bar = FindPanel(self)
        self.find_bar.setVisible(False)

        #Signals and Slots
        self.tab_bar.tabCloseRequested.connect(self.on_close_tab)
        self.tab_bar.plus_clicked.connect(self.add_new_tab)
        self.tab_bar.currentChanged.connect(self.current_changed)
        self.find_bar.searched.connect(self.on_finded)
        self.bookmarks_bar.bookmarkClicked.connect(self.add_bookmark_tab)
        
        #Add Widgets to layouts
        self.splitter.addWidget(self.history_dock)
        self.splitter.addWidget(self.browser_stacked_widget)
        self.main_layout.addWidget(self.tab_bar, 0)
        self.main_layout.addWidget(self.navbar_stacked_widget, 0)
        self.main_layout.addWidget(self.bookmarks_bar, 0)
        self.main_layout.addWidget(self.splitter, 1)
        self.main_layout.addWidget(self.find_bar, 0)
        self.main_layout.addWidget(self.status_bar, 0)

        self.add_new_tab()

    def on_finded(self, text, flag):
        def callback(found):
            if text and not found:
                self.status_bar.showMessage('Not found')
        self.browser_stacked_widget.currentWidget().findText(text, flag, callback)

    def updateHistory(self, title, url):
        time = datetime.datetime.now().strftime("%X")
        date = datetime.datetime.now().strftime("%x")
        main.cursor.execute(
            "INSERT INTO history (title,url,date,time) VALUES (:title,:url,:date,:time)",
            {"title": title, "url": url, "date": date, "time": time},
        )
        text = title + " - " + url + " - " + date + " - " + time
        self.history_dock.history_list.addItem(text)

    def reset_find_action(self, state):
        for i in range(self.navbar_stacked_widget.count()):
            self.navbar_stacked_widget.widget(i).find_action.setChecked(state)

    def reset_history_action(self, state):
        for i in range(self.navbar_stacked_widget.count()):
            self.navbar_stacked_widget.widget(i).history_action.setChecked(state)
    
    def add_new_tab(self):
        i = self.add_tab(None, QUrl(main.settings_data["newTabPage"]))
        self.tab_bar.setCurrentIndex(i)

    def add_bookmark_tab(self, url = None, label = 'Blank'):
        self.add_tab(None, QUrl(url), label)
    def add_tab(self, browser = None, qurl = None, label = 'Blank'):
        if qurl:
            browser = BrowserEngineView(self)
            browser.load(qurl)
        navbar = NavBar(self)
        self.navbar_stacked_widget.addWidget(navbar)
        self.browser_stacked_widget.addWidget(browser)
        if self.first_tab == True:
            self.scheme_handler = SmoothySchemeHandler()
            browser.page().profile().installUrlSchemeHandler(b"smoothy", self.scheme_handler)
            self.first_tab = False
        i = self.tab_bar.addTab(label)
        navbar.init_signals(i)
        browser.init_signals(i)
        return i
    
    def on_close_tab(self, i):
        if self.tab_bar.count() > 1:
            self.tab_bar.removeTab(i)
            navbar = self.navbar_stacked_widget.widget(i)
            self.navbar_stacked_widget.removeWidget(navbar)
            navbar.deleteLater();
            view = self.browser_stacked_widget.widget(i)
            view.loading.stop()
            self.browser_stacked_widget.removeWidget(view)
            view.deleteLater();
            for i in range(self.tab_bar.count() - 1):
                self.browser_stacked_widget.widget(i).i = i
                self.navbar_stacked_widget.widget(i).i = i
                

        else:
            self.main_window.close()

    def current_changed(self, i):
        self.main_window.setWindowTitle(self.tab_bar.tabText(i) + " - Smoothy Browser")
        self.browser_stacked_widget.setCurrentIndex(i)
        self.navbar_stacked_widget.setCurrentIndex(i)