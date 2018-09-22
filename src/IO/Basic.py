import configparser
import abc
from PyQt5.QtWidgets import QRadioButton, QLineEdit, QPlainTextEdit


class BasicIOElement(object):
    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def write(self):
        pass


class Property(dict):
    def __init__(self):
        super().__init__()
        self.file = BasicIOElement()
        self.form = BasicIOElement()

    def read(self):
        self.file.read()
        self.form.write()

    def upload(self):
        self.form.read()

    def save(self):
        self.form.read()
        self.file.write()


class ConfigureFile(BasicIOElement):
    def __init__(self, filename, master):
        self.filename = filename
        self.parser = configparser.ConfigParser()
        self.master = master

    def read(self):
        with open(self.filename, 'r') as f:
            self.parser.read_file(f)
        config_dict = {section: dict(self.parser[section]) for section in self.parser if section != 'DEFAULT'}
        self.master.update(config_dict)

    def write(self):
        for section in self.master:
            for entry in section:
                self.parser[section][entry] = self.master[section][entry]
        with open(self.filename, 'w') as f:
            self.parser.write(f)


class ImportSettingForm(BasicIOElement):
    def __init__(self, gui, master):
        self.gui = gui
        self.master = master

    def read(self):
        for parameter in self.gui.parameter_widgets:
            form = self.gui.parameter_widgets[parameter]
            if type(form) == QLineEdit:
                content = form.text()
            if type(form) == QPlainTextEdit:
                content = form.toPlainText()
            if type(form) == QRadioButton:
                content = form.isChecked()
            self.master[parameter] = str(content)

    def write(self):
        for parameter in self.gui.parameter_widgets:
            form = self.gui.parameter_widgets[parameter]
            print(parameter)
            print(self.master)
            if type(form) == QLineEdit:
                form.insert(self.master[parameter])
            elif type(form) == QPlainTextEdit:
                form.insertPlainText(self.master[parameter])
            elif type(form) == QRadioButton:
                choice = self.master[parameter]
                choice = True if choice == 'True' else False
                if choice:
                    form.setChecked(choice)
            else:
                pass


class ImportParameters(Property):
    def __init__(self, origin):
        super().__init__()
        self.file = ConfigureFile('config/import.ini', self)
        self.form = ImportSettingForm(origin.import_set_window, self)
