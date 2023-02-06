from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView, QWebEngineSettings
from PyQt5.QtWebEngineCore import (QWebEngineUrlRequestJob,
                                   QWebEngineUrlSchemeHandler)

from themes.main import ChangeThemeDialog, CreateThemeDialog
import main
import json
import os
from PyQt5.QtNetwork import *
import xml.etree.ElementTree as ET


class SmoothySchemeHandler(QWebEngineUrlSchemeHandler):
    def requestStarted(self, job):
        request_method = job.requestMethod()
        if request_method != b"GET":
            job.fail(QWebEngineUrlRequestJob.RequestDenied)
            return

        request_url = job.requestUrl()
        request_path = request_url.path()
        file = QFile(os.path.join(main.html_dir, request_path))
        file.setParent(job)
        job.destroyed.connect(file.deleteLater)
        if not file.exists() or file.size() == 0:
            print(f"resource '{request_path}' not found or is empty")
            job.fail(QWebEngineUrlRequestJob.UrlNotFound)
            return

        file_info = QFileInfo(file)
        mime_database = QMimeDatabase()
        mime_type = mime_database.mimeTypeForFile(file_info)
        job.reply(mime_type.name().encode(), file)

class BrowserEngineView(QWebEngineView):
    def __init__(self, Main, parent=None):
        super(BrowserEngineView, self).__init__(parent)
        self.page().profile().downloadRequested.connect(self.on_downloadRequested)
        self.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self.page().fullScreenRequested.connect(lambda request: request.accept())  
        self.main_window = Main
    
    def on_downloadRequested(self,downloadItem):
        old_path = downloadItem.path()
        suffix = QFileInfo(old_path).suffix()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", old_path, "*."+suffix)
        if path:
            downloadItem.setPath(path)
            downloadItem.accept()
    @pyqtSlot(QUrl, QWebEnginePage.Feature)
    def handleFeaturePermissionRequested(self, securityOrigin, feature):
        title = "Permission Request"
        questionForFeature = {
            QWebEnginePage.Geolocation: "Allow {feature} to access your location information?",
            QWebEnginePage.MediaAudioCapture: "Allow {feature} to access your microphone?",
            QWebEnginePage.MediaVideoCapture: "Allow {feature} to access your webcam?",
            QWebEnginePage.MediaAudioVideoCapture: "Allow {feature} to lock your mouse cursor?",
            QWebEnginePage.DesktopVideoCapture: "Allow {feature} to capture video of your desktop?",
            QWebEnginePage.DesktopAudioVideoCapture: "Allow {feature} to capture audio and video of your desktop?"
        }
        question = questionForFeature.get(feature)
        if question:
            question = question.format(feature=securityOrigin.host())
            if QMessageBox.question(self.view().window(), title, question) == QMessageBox.Yes:
                self.setFeaturePermission(
                    securityOrigin, feature, QWebEnginePage.PermissionGrantedByUser)
            else:
                self.setFeaturePermission(
                    securityOrigin, feature, QWebEnginePage.PermissionDeniedByUser)
                
    def init_signals(self, i):
        self.i = i
        self.loading = QMovie(os.path.join("themes", "%s" % main.settings_data["icons"],"loading.gif"))
        self.loading.frameChanged.connect(lambda: self.main_window.tab_bar.setTabIcon(self.i, QIcon(self.loading.currentPixmap())))
        if (self.loading.loopCount() != -1):
            self.loading.finished.connect(self.loading.start())

        self.loading.start()
        self.titleChanged.connect(lambda title: self.main_window.main_window.setWindowTitle(title + " - Smoothy Browser") if self.main_window.tab_bar.currentIndex() == self.i else None)
        self.titleChanged.connect(lambda title: (self.main_window.tab_bar.setTabText(self.i, title),
                                                        self.main_window.tab_bar.setTabToolTip(self.i, title)))
        self.loadStarted.connect(lambda: self.loading.start())
        self.loadStarted.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).progress_bar.setVisible(True))
        self.loadProgress.connect(self.main_window.navbar_stacked_widget.widget(self.i).progress_bar.setValue)
        self.loadFinished.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).progress_bar.setVisible(False))
        self.loadStarted.connect(lambda: self.main_window.tab_bar.setTabIcon(self.i, QIcon(self.loading.currentPixmap())))  
        self.iconChanged.connect(lambda: self.main_window.tab_bar.setTabIcon(self.i, self.icon()))
        self.loadStarted.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).stop_button.setVisible(True))
        self.loadStarted.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).reload_button.setVisible(False))
        self.page().linkHovered.connect(
            lambda l: self.main_window.status_bar.showMessage(l, 3000)
        )
        self.urlChanged.connect(self.renew_urlbar)
        self.loadFinished.connect(lambda: self.loading.stop())
        self.loadFinished.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).stop_button.setVisible(False))
        self.loadFinished.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).reload_button.setVisible(True))
        self.loadFinished.connect(lambda: self.main_window.updateHistory(self.title(), self.url().toString()))
        self.loadFinished.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).back_button.setEnabled(self.page().history().canGoBack()))
        self.loadFinished.connect(lambda: self.main_window.navbar_stacked_widget.widget(self.i).next_button.setEnabled(self.page().history().canGoForward()))

    def navigate_to_home(self):
        self.load(QUrl(main.settings_data["homeButtonPage"]))

    def renew_urlbar(self, s):
        scheme = s.scheme()
        if s.toString() == "smoothy:home.html":
            self.main_window.navbar_stacked_widget.widget(self.i).url_text_bar.setText('')
            self.main_window.navbar_stacked_widget.widget(self.i).url_text_bar.setFocus()
            self.main_window.navbar_stacked_widget.widget(self.i).ssl_label1.setPixmap(QPixmap("icon.png").scaledToHeight(24))
            self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setText(" This is a Smoothy page ")
            self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setStyleSheet("color:orange;")
        else:
            if scheme == 'https':
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label1.setPixmap(QPixmap(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"safe.png")).scaledToHeight(24))
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setText(" This site is safe ")
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setStyleSheet("color:green;")
            elif scheme == 'smoothy':
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label1.setPixmap(QPixmap("icon.png").scaledToHeight(24))
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setText(" This is a Smoothy page ")
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setStyleSheet("color:orange;")
            else:
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label1.setPixmap(QPixmap(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"unsafe.png")).scaledToHeight(24))
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setText(" This site is unsafe ")
                self.main_window.navbar_stacked_widget.widget(self.i).ssl_label2.setStyleSheet("color:red;")
            self.main_window.navbar_stacked_widget.widget(self.i).url_text_bar.setText(s.toString())
        self.main_window.navbar_stacked_widget.widget(self.i).url_text_bar.setCursorPosition(0)
    
    def navigate_to_url(self):
        in_url = self.main_window.navbar_stacked_widget.widget(self.i).url_text_bar.text()
        url = ""
        """ if the text in the search box endswith one of the domain in the domains tuple, then "http://" will be added
         if the text is pre "http://" or "https://" added, then not"""
        # [0-9A-Za-z]+\.+[A-Za-z0-9]{2}
        if len(str(in_url)) < 1:
            return
        
        if QUrl.fromUserInput(in_url).scheme == "smoothy":
            url = in_url

        elif main.file_pattern.search(in_url):
            file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), in_url))
            local_url = QUrl.fromLocalFile(file_path)
            self.load(local_url)

        elif main.without_http_pattern.search(in_url) and any(
            [i in in_url for i in ["http://", "https://"]]
        ):
            url = in_url

        elif main.pattern.search(in_url) and not any(
            i in in_url for i in ("http://", "https://", "file:///")
        ):
            url = "http://" + in_url

        # this will search google
        elif not "/" in in_url:
            url = self.searchWeb(in_url)

        self.load(QUrl.fromUserInput(url))

    def searchWeb(self, text):
        if text:
            if main.settings_data["defaultSearchEngine"]== "Google":
                return "https://www.google.com/search?q=" + "+".join(text.split())

            elif main.settings_data["defaultSearchEngine"]== "Yahoo":
                return "https://search.yahoo.com/search?q=" + "+".join(text.split())
            elif main.settings_data["defaultSearchEngine"]== "Bing":
                return "https://www.bing.com/search?q=" + "+".join(text.split())

            elif main.settings_data["defaultSearchEngine"]== "DuckDuckGo":
                return "https://duckduckgo.com/?q=" + "+".join(text.split())

    def createWindow(self, windowType):
        webview = BrowserEngineView(self.main_window)
        self.main_window.add_tab(webview)
        return webview

class SuggestionModel(QStandardItemModel):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super(SuggestionModel, self).__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._reply = None

    @pyqtSlot(str)
    def search(self, text):
        self.clear()
        if self._reply is not None:
            self._reply.abort()
        if text:
            r = self.create_request(text)
            self._reply = self._manager.get(r)
            self._reply.finished.connect(self.on_finished)
        loop = QEventLoop()
        self.finished.connect(loop.quit)
        loop.exec_()

    def create_request(self, text):
        url = QUrl("http://toolbarqueries.google.com/complete/search")
        query = QUrlQuery()
        query.addQueryItem("q", text)
        query.addQueryItem("output", "toolbar")
        query.addQueryItem("hl", "en")
        url.setQuery(query)
        request = QNetworkRequest(url)
        return request

    @pyqtSlot()
    def on_finished(self):
        reply = self.sender()
        if reply.error() == QNetworkReply.NoError:
            content = reply.readAll().data()
            suggestions = ET.fromstring(content)
            for data in suggestions.iter("suggestion"):
                suggestion = data.attrib["data"]
                self.appendRow(QStandardItem(suggestion))
            self.error.emit("")
        elif reply.error() != QNetworkReply.OperationCanceledError:
            self.error.emit(reply.errorString())
        else:
            self.error.emit("")
        self.finished.emit()
        reply.deleteLater()
        self._reply = None


class Completer(QCompleter):
    def splitPath(self, path):
        self.model().search(path)
        return super(Completer, self).splitPath(path)

class NavBar(QToolBar):
    def __init__(self, parent):
        super(NavBar,self).__init__(parent)
        self.setIconSize(QSize(16, 16))
        self.setFixedHeight(36)
        self.setMovable(False)
        self.main_window = parent
        self.back_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"back.png")), 'Back', self)
        self.next_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"forward.png")), 'Forward', self)
        self.reload_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"reload.png")), 'Refresh', self)
        self.stop_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"close.png")), 'Stop loading', self)
        self.home_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"home.png")), 'Go home', self)
        self.enter_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"search.png")), 'Search', self)
        self.ssl_label1 = QLabel(self)
        self.ssl_label2 = QLabel(self)
        self.url_text_bar = QLineEdit(self)
        self.url_text_bar.setSizePolicy(QSizePolicy.Expanding, self.url_text_bar.sizePolicy().verticalPolicy())
        self.url_text_bar.setPlaceholderText("Search with DuckDuckGo or enter a url")
        # Adding Completer.
        self._model = SuggestionModel(self)
        self.completer = Completer(self, caseSensitivity=Qt.CaseInsensitive)
        self.completer.setModel(self._model)
        self._model.error.connect(self.main_window.status_bar.showMessage)
        self.url_text_bar.setCompleter(self.completer)
        self.progress_bar = QProgressBar()
        
        self.favorite_button = QToolButton(self)
        self.favorite_button.setIcon(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"bookmark.png")))

        self.history_action = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"history.png")), 'History', self)
        self.history_action.setCheckable(True)

        self.find_action = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"find.png")), 'Find', self)
        self.find_action.setCheckable(True)

        self.theme_action = QAction("Change Theme")

        self.addAction(self.back_button)
        self.addAction(self.reload_button)
        self.addAction(self.stop_button)
        self.addAction(self.next_button)
        self.addAction(self.home_button)
        self.addSeparator()
        self.addWidget(self.ssl_label1)
        self.addWidget(self.ssl_label2)
        self.addWidget(self.url_text_bar)
        self.addAction(self.enter_button)
        self.addSeparator()
        self.addWidget(self.favorite_button)
        self.addAction(self.history_action)
        self.addAction(self.find_action)
        self.addAction(self.theme_action)
        self.addSeparator()
        self.addWidget(self.progress_bar)

    def init_signals(self, i):
        self.i = i
        self.favorite_button.clicked.connect(self.addFavoriteClicked)
        self.back_button.triggered.connect(self.main_window.browser_stacked_widget.widget(self.i).back)        
        self.next_button.triggered.connect(self.main_window.browser_stacked_widget.widget(self.i).forward)              
        self.reload_button.triggered.connect(self.main_window.browser_stacked_widget.widget(self.i).reload)              
        self.stop_button.triggered.connect(self.main_window.browser_stacked_widget.widget(self.i).stop)            
        self.home_button.triggered.connect(self.main_window.browser_stacked_widget.widget(self.i).navigate_to_home)
        self.url_text_bar.returnPressed.connect(self.main_window.browser_stacked_widget.widget(self.i).navigate_to_url)
        self.history_action.toggled.connect(self.main_window.reset_history_action)
        self.history_action.toggled.connect(self.main_window.history_dock.setVisible)
        self.find_action.toggled.connect(self.main_window.reset_find_action)
        self.find_action.toggled.connect(self.main_window.find_bar.setVisible)
        self.theme_action.triggered.connect(lambda: self.open_theme_dialog())

    def open_theme_dialog(self):
        self.change_theme_dialog = ChangeThemeDialog(self.main_window)
        self.change_theme_dialog.combo_box.currentTextChanged.connect(self.change_theme)
        self.change_theme_dialog.exec_()
    def change_theme(self, text):
        if text != "Create new theme":
            with open(os.path.join("themes","qss","%s" % text),"r") as fh:
                self.main_window.setStyleSheet(fh.read())
        else:
            self.create_theme_dialog = CreateThemeDialog(self.main_window)
            self.create_theme_dialog.accepted.connect(self.create_theme)
            self.create_theme_dialog.exec_()
    def create_theme(self):
        if self.create_theme_dialog.main_color and self.create_theme_dialog.accent_color and self.create_theme_dialog.border_color:
            content = '''QMainWindow {{
                            border: {border_color};
                            color: {accent_color};
                            background-color: {main_color};
                            margin: 0;
                            padding: 0;
                        }}
                        QMessageBox {{
                            color: {accent_color};
                        }}
                        QWidget {{
                                color: {accent_color};
                            background-color: {main_color};
                        }}
                        QTabWidget::tab-bar {{
                            background: {main_color};
                        }}

                        /* Style the tab using the tab sub-control. Note that
                            it reads QTabBar _not_ QTabWidget */
                        QTabBar::tab {{
                            background: {main_color};
                            min-width: 10ex;
                            padding: 5px;
                            color: {accent_color};
                            border: 0px 1px solid {accent_color};
                        }}
                        QTabBar::tab:hover {{
                            background-color: {accent_color};
                            color: {main_color};
                        }}
                        QTabBar::tab:selected {{
                            background: {accent_color};
                            border: 2px solid {border_color};
                            color: {main_color};
                            border-radius: 4px;
                            padding: 5px;
                        }}
                        QTabBar::tab:first:!selected {{
                            border-left: none;
                        }}

                        QTabBar::tab:last:!selected {{
                            border-right: none;
                        }}

                        QTabBar::scroller {{ /* the width of the scroll buttons */
                            width: 40px;
                        }}

                        QTabBar QToolButton {{ /* the scroll buttons are tool buttons */
                            background: {main_color};
                        }}

                        QToolBar {{
                            background: {main_color};
                            spacing: 3px;
                            border: 1px solid {border_color};
                        }}
                        QAbstractButton {{
                            background-color: {main_color};
                            color: {accent_color};
                            padding: 5px;
                        }}
                        QAbstractButton:hover {{
                            background: {accent_color};
                            color: {main_color};
                        }}                                                             
                        QToolTip {{
                            border: 1px solid {border_color};
                            border-radius: 5px;
                            color: {accent_color};
                            background-color: {main_color};
                        }}
                        QLineEdit {{
                            border: none;
                            background: {main_color};
                            color: {accent_color};
                        }}
                        QStatusBar {{
                            background: {main_color};
                            color: {accent_color};
                            border: 2px solid {border_color};
                        }}
                        QLabel {{
                            color: {accent_color};
                        }}
                        QProgressBar {{
                            border: 2px solid {border_color};
                            border-radius: 5px;
                            color: {accent_color};
                            text-align: center;
                            /*height: 0.1px;*/
                            background-color: {main_color};
                        }}

                        QProgressBar::chunk {{
                            background-color: {accent_color};
                            width: 20px;
                        }}
                        QMenu {{
                            background-color: {main_color}; /* sets background of the menu */
                            border: 1px solid {border_color};
                            color: {accent_color};
                        }}

                        QMenu::item {{
                            /* sets background of menu item. set this to something non-transparent
                                if you want menu color and menu item color to be different */
                            background-color: {main_color};
                        }}

                        QMenu::item:selected {{ /* when user selects item using mouse or keyboard */
                            background-color: {accent_color};
                            color: {main_color};
                        }}
                        QDockWidget {{
                            background-color: {main_color};
                            border: 1px solid {border_color};
                            color: {accent_color};
                        }}
                        QListWidget, QListView{{
                            background-color: {main_color};
                            color: {accent_color};
                        }}
                        QListWidget::item:hover, QListView::item:hover{{
                            background-color: {accent_color};
                            color: {main_color};
                        }}'''
            self.main_window.setStyleSheet(content.format(border_color = self.create_theme_dialog.border_color, accent_color = self.create_theme_dialog.accent_color, main_color = self.create_theme_dialog.main_color))
            with open(os.path.join("themes","qss", "%s.qss" % self.create_theme_dialog.title_line_edit.text()), "xt") as w:
                w.write(content.format(border_color = self.create_theme_dialog.border_color, accent_color = self.create_theme_dialog.accent_color, main_color = self.create_theme_dialog.main_color))
        else:
            print("error")
    def addFavoriteClicked(self):
        self.title = self.main_window.browser_stacked_widget.widget(self.i).title()  
        self.url = self.main_window.browser_stacked_widget.widget(self.i).url()     
        self.main_window.bookmarks_bar.addBookMarkAction(self.title, self.url.toString())


class BookMarkToolBar(QToolBar):
    bookmarkClicked = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(BookMarkToolBar, self).__init__(parent)
        self.setFixedHeight(36)
        self.setMovable(False)
        self.actionTriggered.connect(self.onActionTriggered)
        if os.path.exists("bookmarks.json")
            with open("bookmarks.json", "r") as file:
                self.bookmark_list = json.load(file)
        else:
            self.bookmark_list = []
        self.setBookMarks(self.bookmark_list)

    def setBookMarks(self, bookmarks):
        for bookmark in bookmarks:
            self.addBookMarkAction(bookmark["title"], bookmark["url"],verify = True)

    def addBookMarkAction(self, title, url, verify=None):
        bookmark = {
            "title": title,
            "url": url
        }
        fm = QFontMetrics(self.font())
        if verify == None:
            if bookmark not in self.bookmark_list:
                text = fm.elidedText(title, Qt.ElideRight, 150)
                action = self.addAction(text)
                action.setData(bookmark)
                with open("bookmarks.json", "r") as read_file:
                    self.bookmark_list = json.load(read_file)
                    self.bookmark_list.append(bookmark)
                with open("bookmarks.json", "w") as write_file:
                    json.dump(self.bookmark_list, write_file, indent=4)
        else:
            text = fm.elidedText(title, Qt.ElideRight, 150)
            action = self.addAction(text)
            action.setData(bookmark)


    @pyqtSlot(QAction)
    def onActionTriggered(self, action):
        bookmark = action.data()
        self.bookmarkClicked.emit(bookmark["url"], bookmark["title"])

class TabBarPlus(QTabBar):
    """Tab bar that has a plus button floating to the right of the tabs."""

    plus_clicked = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setExpanding(False)
        self.setTabsClosable(True)

        # Plus Button
        self.button = QToolButton(self)
        self.button.setText("+")  # Set Text
        self.button.clicked.connect(self.plus_clicked.emit)
        self.movePlusButton() # Move to the correct location


    def sizeHint(self):
        """Return the size of the TabBar with increased width for the plus button."""
        sizeHint = QTabBar.sizeHint(self) 
        width = sizeHint.width()
        height = sizeHint.height()
        return QSize(width+25, height)

    def resizeEvent(self, event):
        """Resize the widget and make sure the plus button is in the correct location."""
        super().resizeEvent(event)

        self.movePlusButton()

    def tabLayoutChange(self):
        """This virtual handler is called whenever the tab layout changes.
        If anything changes make sure the plus button is in the correct location.
        """
        super().tabLayoutChange()

        self.movePlusButton()

    def movePlusButton(self):
        """Move the plus button to the correct location."""
        # Find the width of all of the tabs
        size = sum([self.tabRect(i).width() for i in range(self.count())])
        # size = 0
        # for i in range(self.count()):
        #     size += self.tabRect(i).width()

        # Set the plus button location in a visible area
        h = self.geometry().top() + 3
        w = self.width()
        if size > w: # Show just to the left of the scroll buttons
            self.button.move(w-50, h)
        else:
            self.button.move(size, h)

class HistoryWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.main = main_window

        self.titleLbl = QLabel("History")
        self.titleLbl.setFont(QFont('Arial', 30))

        self.clearBtn = QPushButton("Clear")
        self.clearBtn.clicked.connect(self.clear)

        self.close_bnt = QToolButton(self)
        self.close_bnt.setIcon(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"],"close.png")))
        self.close_bnt.setAutoRaise(True)

        self.close_bnt.clicked.connect(lambda: self.main.reset_history_action(False))
        self.close_bnt.clicked.connect(lambda: self.hide())

        self.history_list = QListWidget()

        self.fill_history_list()

        self.history_list.itemClicked.connect(self.go_clicked_link)

        layout = QGridLayout()

        layout.addWidget(self.titleLbl, 0, 0)
        layout.addWidget(self.clearBtn, 0, 1)
        layout.addWidget(self.close_bnt, 0, 2)
        layout.addWidget(self.history_list, 1, 0, 1, 3)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def fill_history_list(self):
        data = main.cursor.execute("SELECT * FROM history ORDER BY id DESC")
        siteInfoList = data.fetchall()
        for i in range(len(siteInfoList) - 1, -1, -1):
            siteInfo = siteInfoList[i][1] + " - " + siteInfoList[i][2] + " - " + siteInfoList[i][3] + " - " + siteInfoList[i][4]
            self.history_list.addItem(siteInfo)

    def clear(self):
        main.cursor.execute("DELETE FROM history")
        main.connection.commit()
        self.history_list.clear()

    def go_clicked_link(self, index):
        text = index.text()
        splited_text = text.split(" - ")
        history_info = main.cursor.execute("SELECT title, url FROM history WHERE date = ? AND time = ?", (splited_text[-2],splited_text[-1],)).fetchone()
        url = history_info[1]
        title = history_info[0]
        self.main.add_tab(None, QUrl.fromUserInput(url), title)  # open selected url

class SearchCompleter(QCompleter):
    def __init__(self, input, parent=None):
        super(SearchCompleter, self).__init__(parent)
        self.search = input
        self.highlighted.connect(self.update_url)
        self.complete()
        self.model = QStringListModel()
        self.model.setStringList(self.list)
        self.setModel(self.model)
    def complete(self):
        data = main.cursor.execute("SELECT * FROM history ORDER BY date DESC;")
        siteInfoList = data.fetchall()
        self.list = []
        for i in range(len(siteInfoList) - 1, -1, -1):
            self.list.append(siteInfoList[i][1])
            self.list.append(siteInfoList[i][2])
    def update_url(self, text):
        main.cursor.execute("SELECT url FROM history WHERE title='%s'" %text)
        rows = main.cursor.fetchall()
        self.search.setText(rows[0][0])
class FindPanel(QToolBar):
    searched = pyqtSignal(str, QWebEnginePage.FindFlag)

    def __init__(self, parent):
        super(FindPanel, self).__init__(parent)
        self.main_window = parent
        self.setIconSize(QSize(16, 16))
        self.close_button = QAction(QIcon(os.path.join("themes","icons", "%s" % main.settings_data["icons"], "close.png")), 'Close', self)
        self.close_button.setShortcut(Qt.Key_Escape)
        self.close_button.triggered.connect(lambda: self.main_window.reset_find_action(False))
        self.case_button = QAction('Match Case', self)
        self.case_button.setCheckable(True)
        self.next_button = QAction('Next', self)
        self.next_button.setShortcut(QKeySequence.FindNext)
        self.prev_button = QAction('Previous', self)
        self.next_button.setShortcut(QKeySequence.FindPrevious)
        self.search_le = QLineEdit()
        self.setFocusProxy(self.search_le)
        self.close_button.triggered.connect(self.hide_search_tb)
        self.next_button.triggered.connect(self.update_searching)
        self.prev_button.triggered.connect(self.on_preview_find)
        self.case_button.triggered.connect(self.update_searching)
        self.addWidget(self.search_le)
        self.addAction(self.prev_button)
        self.addAction(self.next_button)
        self.addSeparator()
        self.addAction(self.case_button)
        self.addAction(self.close_button)
        self.search_le.textChanged.connect(self.update_searching)
    def hide_search_tb(self):
        self.hide()
        self.search_le.clear()

    @pyqtSlot()
    def on_preview_find(self):
        self.update_searching(QWebEnginePage.FindBackward)

    @pyqtSlot()
    def update_searching(self, direction=QWebEnginePage.FindFlag()):
        flag = direction
        if self.case_button.isChecked():
            flag |= QWebEnginePage.FindCaseSensitively
        self.searched.emit(self.search_le.text(), flag)

    def showEvent(self, event):
        super(FindPanel, self).showEvent(event)
        self.setFocus(True)
