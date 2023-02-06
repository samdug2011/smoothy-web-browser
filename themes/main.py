from PyQt5.QtWidgets import QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QColorDialog, QDialog, QDialogButtonBox, QLabel, QComboBox
from PyQt5.QtCore import *
import os
class CreateThemeDialog(QDialog):
    def __init__(self, parent = None):
        super(CreateThemeDialog, self).__init__(parent)

        self.setWindowTitle("New Theme")

        btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.button_box = QDialogButtonBox(btn)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.main_color_button = QPushButton("Open color dialog...")
        self.accent_color_button = QPushButton("Open color dialog...")
        self.border_color_button = QPushButton("Open color dialog...")
        self.main_color_label = QLabel()
        self.accent_color_label = QLabel()
        self.border_color_label = QLabel()
        self.title_line_edit = QLineEdit()
        

        self.main_color_dialog = QColorDialog(self)
        self.accent_color_dialog = QColorDialog(self)
        self.border_color_dialog = QColorDialog(self)
        self.border_color_dialog.colorSelected.connect(self.set_border_color)
        self.main_color_dialog.colorSelected.connect(self.set_main_color)
        self.accent_color_dialog.colorSelected.connect(self.set_accent_color)
        self.main_color_button.clicked.connect(lambda: self.main_color_dialog.show())
        self.accent_color_button.clicked.connect(lambda: self.accent_color_dialog.show())
        self.border_color_button.clicked.connect(lambda: self.border_color_dialog.show())

        self.hbox_text_edit = QHBoxLayout()
        self.hbox_text_edit.addWidget(QLabel("Theme title:"))
        self.hbox_text_edit.addWidget(self.title_line_edit)
        self.layout.addLayout(self.hbox_text_edit)

        self.hbox_main_color = QHBoxLayout()
        self.hbox_main_color.addWidget(QLabel("Main color:"))
        self.hbox_main_color.addWidget(self.main_color_label)
        self.hbox_main_color.addWidget(self.main_color_button)
        self.layout.addLayout(self.hbox_main_color)

        self.hbox_accent_color = QHBoxLayout()
        self.hbox_accent_color.addWidget(QLabel("Accent color:"))
        self.hbox_accent_color.addWidget(self.accent_color_label)
        self.hbox_accent_color.addWidget(self.accent_color_button)
        self.layout.addLayout(self.hbox_accent_color)

        self.hbox_border_color = QHBoxLayout()
        self.hbox_border_color.addWidget(QLabel("Border color:"))
        self.hbox_border_color.addWidget(self.border_color_label)
        self.hbox_border_color.addWidget(self.border_color_button)
        self.layout.addLayout(self.hbox_border_color)

        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def set_main_color(self, dialog):
        self.main_color = dialog.name()
        self.main_color_label.setText(dialog.name())
    def set_accent_color(self, dialog):
        self.accent_color = dialog.name()
        self.accent_color_label.setText(dialog.name())
    def set_border_color(self, dialog):
        self.border_color = dialog.name()
        self.border_color_label.setText(dialog.name())

class ChangeThemeDialog(QDialog):
    def __init__(self, parent = None):
        super(ChangeThemeDialog, self).__init__(parent)
        self.setWindowTitle("Change Theme")
        self.main_layout = QVBoxLayout(self)

        self.combo_box = QComboBox()
        self.main_layout.addWidget(self.combo_box)

        btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.button_box = QDialogButtonBox(btn)
        self.main_layout.addWidget(self.button_box)

        self.fill_combo_box()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def fill_combo_box(self):
        self.combo_box.addItem("Create new theme")
        dir = os.path.join("themes","qss")
        
        files = os.listdir(dir)
        files = [f for f in files if os.path.isfile(dir+'/'+f)] #Filtering only the files.
        self.combo_box.addItems(files)
    
