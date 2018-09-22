from collections import OrderedDict
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QAction, QMessageBox, QMenu, QListWidgetItem
from PyQt5.QtGui import QBrush
from PyQt5 import QtCore
from IO.Import import import_multiple_file
from IO.Export import export_multiple_data
from Core import Core_data
from GUI.plot import refresh_canvas, add_to_canvas, configure_canvas, add_legend, autosize
from GUI.import_setting import ImportSetting
from GUI.edit_data import DataEditor
from Addon.electrochemistry.calculate_etn import CalculateETN
from Addon.electrochemistry.current_to_density import CurrentToDensity
from Addon.IR.find_band import FindBand

ui_main_window, q_main_window = loadUiType("ui/main_window.ui")


class Main(q_main_window, ui_main_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.menu_bar.setNativeMenuBar(False)  # for osx to present the menu inside the app
        self.core_data = Core_data.CoreData()
        self.import_set_window = ImportSetting(self)  # import setting window instance
        self.data_editor = DataEditor(self)
        # four features that the addons (may) use
        self.chosen_points = []  # the points chosen by the user, this is convenient for creating a baseline
        self.data = OrderedDict()  # the data to be plotted on the canvas, the format is "filename: (array_x, array_y)"
        self.ax = None  # the axes of the figure, this is useful to plot: self.ax.plot(x, y)
        self.chosen_file = None  # the filename that user chose in the file menu. 
        # initialize the main window
        self.init_menu()
        self.init_canvas()
        self.init_slot()
        self.import_parameters = Core_data.ImportParameters(self) # todo: use this instance

    def instantiate_addons(self):
        """import the addons from addon packages, according to the addon.ini configure file"""
        for package in self.core_data.addon_dict:
            for addon in self.core_data.addon_dict[package]:
                # import addons
                class_name = self.core_data.addon_config[addon]['class']
                file_name = self.core_data.addon_config[addon]['filename']
                package = self.core_data.addon_config[addon]['package']
                comm = "from Addon.{pkg}.{file} import {cls}".format(pkg=package, file=file_name, cls=class_name)
                exec(comm)
                # import on the fly causes crash during compiling
                # instantiate addons
                class_name = self.core_data.addon_config[addon]['class']
                comm = 'self.core_data.addon_instances.update({ "%s": %s(self) })' % (addon, class_name)
                exec(comm)  # add the addon widget into the dict self.core_data.addon_instances

    def init_menu(self):
        # add preset into the Import menu
        self.import_preset_menus = []
        self.import_preset_slots = []
        self.addon_menus = []
        self.addon_slots = []
        self.menu_import_file.clear()
        # generate import_file_as menu
        for preset in self.core_data.import_presets:
            temp = QAction()
            temp.setObjectName("action_preset_{p}".format(p=preset))
            temp.setCheckable(1)
            temp.setText(preset)
            if preset == self.core_data.get_default_preset():
                temp.setChecked(1)
            self.import_preset_slots.append(lambda state, p=preset: self.choose_import_preset(state, p))
            self.import_preset_menus.append(temp)
            self.menu_import_file.addAction(temp)
        # generate addon menu
        for package in self.core_data.addon_dict:
            menu_group = QMenu(self)
            menu_group.setObjectName('action_' + package)
            menu_group.setTitle(package)
            self.menu_addon.addMenu(menu_group)
            for addon_name in self.core_data.addon_dict[package]:
                temp = QAction(self)
                temp.setObjectName("action_addon_{a}".format(a=addon_name))
                temp.setText(addon_name)
                self.addon_menus.append(temp)
                self.addon_slots.append(lambda state, a=addon_name: self.choose_addon(state, a))
                menu_group.addAction(temp)

    def init_slot(self):
        # connect the widget and the slot
        self.file_list_widget.itemPressed.connect(self.choose_filename)
        self.file_list_widget.itemDoubleClicked.connect(self.choose_none)
        self.action_export_data.triggered.connect(self.export_data)
        self.action_edit_data.triggered.connect(self.data_editor.show)
        self.action_remove_data.triggered.connect(self.remove_data)
        self.action_clear_data.triggered.connect(self.clear_data)
        self.action_import_setting.triggered.connect(self.import_set_window.show)
        for widget, slot in zip(self.import_preset_menus, self.import_preset_slots):
            try:
                widget.triggered.disconnect()
            except:
                pass
            widget.triggered.connect(slot)
        for widget, slot in zip(self.addon_menus, self.addon_slots):
            try:
                widget.triggered.disconnect()
            except:
                pass
            widget.triggered.connect(slot)
        self.button_import.pressed.connect(self.import_data)
        self.button_add_legend.pressed.connect(self.add_legend)
        self.button_resize.pressed.connect(lambda: autosize(self.plot_canvas))
        self.button_edit_data.pressed.connect(self.data_editor.show)
        self.button_delete.pressed.connect(self.remove_data)

    def init_canvas(self):
        # todo: add a setting button for the canvas and its setting widget
        self.plot_canvas.setBackground('w')
        configure_canvas(self.plot_canvas)

    def import_data(self):
        # import the data into self.data, format: {filename: (x, y)}
        try:
            imported_data = import_multiple_file(self, **self.core_data.import_parameters)
        except:
            self.warning("Can not read the data, exception raised!")
            imported_data = None
        if imported_data:
            self.data.update(imported_data)
            colors = self.refresh_plot(autorange=True)
            self.refresh_filename_list(colors)
            self.notify("{num} datasets imported".format(num=len(imported_data)))
        else:
            self.warning("No data imported")

    def export_data(self):
        # export the data into a folder at .csv extension
        if not self.data:
            self.warning("No data available to export")
            return 1
        if export_multiple_data(self, self.data):
            self.notify("data exported!")
            return 0
        else:
            self.warning("data not exported!")
            return 1

    def refresh_filename_list(self, color_dict):
        self.file_list_widget.clear()
        for filename in self.data:
            item = QListWidgetItem()
            item.setText(filename)
            brush = QBrush(color_dict[filename])
            item.setForeground(brush)
            self.file_list_widget.addItem(item)

    def refresh_plot(self, **kwargs):
        """
        Refresh the plot, delete everything firstly and plot everything
        if any data changes, you need refresh the plot
        """
        points_xy = ([p[0] for p in self.chosen_points], [p[1] for p in self.chosen_points])  # change format for plot
        color_dict = refresh_canvas(self.plot_canvas,
                                    data_line=self.data,
                                    data_scatter={'chosen': points_xy},
                                    **kwargs)
        if self.chosen_file:
            pen = {'color': (255, 255, 0, 155), 'width': 5}
            add_to_canvas(self.plot_canvas,
                          data_line={self.chosen_file: self.data[self.chosen_file]},
                          pen=pen)
        return color_dict

    def add_legend(self):
        """
        add a legend, remove it if already have one
        """
        add_legend(self.plot_canvas)
        colors = self.refresh_plot()
        self.refresh_filename_list(colors)

    def remove_data(self):
        # remove the item in the file_list_widget and its plot in the canvas
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item and item.text() == self.chosen_file:
                self.file_list_widget.takeItem(i)
                del self.data[self.chosen_file]
                self.chosen_file = None
                colors = self.refresh_plot()
                self.refresh_filename_list(colors)
        self.file_list_widget.setCurrentItem(None)

    def clear_data(self):
        # delete all the data and clear the canvas
        # remove the chosen points
        self.chosen_file = None
        self.data = {}
        self.chosen_points = []
        colors = self.refresh_plot(autorange=True)
        self.refresh_filename_list(colors)
        return 0

    def choose_filename(self, event):
        self.chosen_file = event.text()
        self.refresh_plot()

    def choose_none(self, event):
        self.chosen_file = None
        self.refresh_plot()
        self.file_list_widget.setCurrentItem(None)

    def choose_import_preset(self, state, preset):
        # state wtf??
        # see ---> http://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
        self.core_data.choose_preset_as_default(preset)
        for action in self.menu_import_file.actions():
            if action.text() == preset:
                action.setChecked(1)
            else:
                action.setChecked(0)

    def choose_addon(self, state, addon):
        self.instantiate_addons()
        self.core_data.addon_instances[addon].show()  # pop up the addon widget

    @staticmethod
    def notify(msg):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(msg)
        msg_box.exec_()

    @staticmethod
    def warning(msg):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(msg)
        msg_box.exec_()
