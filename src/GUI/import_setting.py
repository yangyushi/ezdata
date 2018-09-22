import re
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QRadioButton, QLineEdit, QPlainTextEdit

ui_import_setting, q_import_setting = loadUiType("ui/import_setting.ui")
ui_import_setting_save_preset, q_import_setting_save_preest = loadUiType("ui/import_setting_save_preset.ui")
ui_import_setting_delete_preset, q_import_setting_delete_preest = loadUiType("ui/import_setting_delete_preset.ui")


class ImportSetting(q_import_setting, ui_import_setting):
    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin
        self.parameter_widgets = {"file_code": self.line_edit_decode,
                                  "xy_format": self.text_edit_regular_expression,
                                  "head_ignore": self.line_edit_ignore_line,
                                  "no_segment": self.radio_button_no_segment,
                                  "delimiter": self.line_edit_segment_separate,
                                  "split_segment": self.radio_button_split}
        self.read_import_parameter()
        self.save_preset_widget = SavePreset(self)
        self.delete_preset_widget = DeletePreset(self)
        self.__setup_combo_box()
        self.__init_slot()

    def __setup_combo_box(self):
        """set the combo box containing all the saved presets"""
        self.combo_box_presets.clear()
        self.origin.core_data.__init__()
        for preset in self.origin.core_data.import_presets:
            self.combo_box_presets.addItem(preset)

    def __init_slot(self):
        self.combo_box_presets.activated[str].connect(self.on_activate_preset)
        self.button_import.clicked.connect(self.open_import_data_window)
        self.button_delete.clicked.connect(self.open_delete_window)
        self.button_save_as.clicked.connect(self.open_save_as_window)
        self.button_test_regular_expression.clicked.connect(self.test_regular_expression)

    def on_activate_preset(self, preset):
        """
        refresh the parameters when choosing a preset
        also change the import preset in the Main()
        """
        self.clear_widgets()
        self.origin.core_data.choose_preset_as_default(preset)
        self.read_import_parameter()

    def clear_widgets(self):
        for par in self.parameter_widgets:
            widget = self.parameter_widgets[par]
            if type(widget) == QRadioButton:
                pass
            else:
                widget.clear()

    def read_import_parameter(self):
        """ read from the inner dict, presenting on the setting window """
        self.clear_widgets()
        for par in self.parameter_widgets:
            widget = self.parameter_widgets[par]
            if type(widget) == QLineEdit:
                widget.insert(self.origin.core_data.import_parameters[par])
            if type(widget) == QPlainTextEdit:
                widget.insertPlainText(self.origin.core_data.import_parameters[par])
            if type(widget) == QRadioButton:
                choice = self.origin.core_data.import_parameters[par]
                choice = True if choice == 'True' else False
                if choice:
                    widget.setChecked(choice)

    def upload_import_parameter(self):
        """ change the import parameters with the widget content """
        for par in self.parameter_widgets:
            content = ""
            widget = self.parameter_widgets[par]
            if type(widget) == QLineEdit:
                content = widget.text()
            if type(widget) == QPlainTextEdit:
                content = widget.toPlainText()
            if type(widget) == QRadioButton:
                content = widget.isChecked()
            self.origin.core_data.import_parameters[par] = str(content)

    def save_parameter_as_preset(self, name):
        """ save the current import parameter to the import.ini file """
        self.origin.core_data.import_config[
            name] = self.origin.core_data.import_parameters  # add new entry to the configure parser
        with open('config/import.ini', 'w') as f:
            self.origin.core_data.import_config.write(f)
        self.__setup_combo_box()  # refresh the combo box
        self.origin.init_menu()  # refresh the menu item in the main window
        self.origin.init_slot()  # reconnect the slot and signal

    def delete_preset(self, preset):
        del (self.origin.core_data.import_config[preset])
        with open('config/import.ini', 'w') as f:
            self.origin.core_data.import_config.write(f)
        self.__setup_combo_box()  # refresh the combo box
        self.origin.init_menu()  # refresh the menu item in the main window
        self.origin.init_slot()  # reconnect the slot and signal

    def open_import_data_window(self):
        self.hide()
        self.upload_import_parameter()
        self.origin.import_data()

    def open_save_as_window(self):
        self.hide()
        self.save_preset_widget.show()

    def open_delete_window(self):
        self.hide()
        self.delete_preset_widget.__init__(self)
        self.delete_preset_widget.show()

    def test_regular_expression(self):
        self.line_edit_result_x.clear()
        self.line_edit_result_y.clear()
        sample_text = self.line_edit_sample.text()
        regular_expression = self.text_edit_regular_expression.toPlainText()
        result = re.search(regular_expression, sample_text)
        if result:
            x = result.group(1)
            y = result.group(2)
            self.line_edit_result_x.insert(x)
            self.line_edit_result_y.insert(y)


class SavePreset(q_import_setting_save_preest, ui_import_setting_save_preset):
    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin
        self.__init_slot()

    def __init_slot(self):
        self.button_save.clicked.connect(self.on_save_preset)
        self.button_cancel.clicked.connect(self.on_cancel)

    def on_save_preset(self):
        # write the current preset to the import.ini file
        self.hide()
        self.origin.show()
        self.origin.upload_import_parameter()
        if self.line_edit_name.text():
            self.origin.save_parameter_as_preset(self.line_edit_name.text())

    def on_cancel(self):
        self.hide()
        self.origin.show()
        pass


class DeletePreset(q_import_setting_delete_preest, ui_import_setting_delete_preset):
    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin
        self.__init_slot()
        self.preset = self.origin.combo_box_presets.currentText()
        print("preset is: ", self.preset)
        self.label_confirm.setText("Deleting [{}]".format(self.preset))

    def __init_slot(self):
        self.button_delete.clicked.connect(self.on_delete_preset)
        self.button_cancel.clicked.connect(self.on_cancel)

    def on_delete_preset(self):
        # write the current preset to the import.ini file
        self.hide()
        self.origin.show()
        self.origin.upload_import_parameter()
        self.origin.delete_preset(self.preset)

    def on_cancel(self):
        self.hide()
        self.origin.show()
        pass
