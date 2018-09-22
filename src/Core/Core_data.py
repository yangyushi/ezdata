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
        self.master = {section: self.parser[section] for section in self.parser if section != 'DEFAULT'}

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
            if type(form) == QLineEdit:
                form.insert(self.master[parameter])
            if type(form) == QPlainTextEdit:
                form.insertPlainText(self.master[parameter])
            if type(form) == QRadioButton:
                choice = self.master[parameter]
                choice = True if choice == 'True' else False
                if choice:
                    form.setChecked(choice)


class ImportParameters(Property):
    def __init__(self, origin):
        super().__init__()
        self.file = ConfigureFile('config/import.ini', self)
        self.form = ImportSettingForm(origin.import_set_window, self)


class CoreData(object):
    # this class contains some nasty parameters needed by the GUI.main.Main class
    def __init__(self):
        self.import_config, self.addon_config = self.read_config()
        self.import_presets = {name: self.import_config[name] for name in self.import_config if name != 'DEFAULT'}
        self.import_parameters = self.import_presets[self.get_default_preset()]  # The chosen parameters for import data
        self.addon_dict = self.generate_addon_dict(self.addon_config)  # {package_name: addon_name}, used for the menu
        self.addon_instances = {}  # {addon_name: addon_instance}, instances injected by main.py

    def get_default_preset(self):
        for preset in self.import_presets:
            if self.import_presets[preset]['is_default']:
                return preset
        raise AttributeError

    def choose_preset_as_default(self, preset):
        self.import_parameters = self.import_presets[preset]
        self.import_presets[preset]['is_default'] = "True"
        for other_preset in self.import_presets:
            if other_preset != preset:
                self.import_presets[other_preset]['is_default'] = "False"

    @staticmethod
    def read_config():
        import_config = configparser.ConfigParser()
        addon_config = configparser.ConfigParser()
        import_config.read_file(open('config/import.ini'))
        addon_config.read_file(open('config/addon.ini'))
        return import_config, addon_config

    @staticmethod
    def generate_addon_dict(addon_config):
        addon_dict = {}
        addon_names = [item for item in addon_config if item != 'DEFAULT']
        packages = list(set([addon_config[addon]['package'] for addon in addon_names]))
        for package in packages:
            addon_dict.update({package: []})
        for name in addon_names:
            addon_dict[addon_config[name]['package']].append(name)
        return addon_dict


if __name__ == '__main__':
    data = CoreData()
    print(data.import_presets)
    print(data.addon_dict)
