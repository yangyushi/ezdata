from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QTableWidgetItem, QMenu, QAction
from PyQt5 import QtCore

ui_cur_2_den, q_cur_2_den = loadUiType("ui/current_to_density.ui")


class CurrentToDensity(ui_cur_2_den, q_cur_2_den):
    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin
        self.x_axis = 'Current'
        self.origin_data = self.origin.data.copy()
        self.refresh_ui()

    def refresh_ui(self):
        unit = 'A' if self.x_axis == 'Current' else 'mA·cm<sup>-2</sup>'
        label = "%s (%s)" % (self.x_axis, unit)
        self.label_unit.setText(label)
        self.label_unit.setStyleSheet('color: blue; font: 20pt; font-family: courier')
        try:
            self.button_to_density.clicked.disconnect()
            self.button_to_current.clicked.disconnect()
        except TypeError:
            pass
        if self.x_axis == 'Current':
            self.button_to_density.clicked.connect(self.c2d)
            self.button_to_current.clicked.connect(lambda: self.origin.warning("Unable to transform!"))
        if self.x_axis == 'Density':
            self.button_to_density.clicked.connect(lambda: self.origin.warning("Unable to transform!"))
            self.button_to_current.clicked.connect(self.d2c)

    def __read_parameters(self):
        try:
            self.area = float(self.line_edit_area.text())
            self.negative = -1 if bool(self.check_box_negative.checkState()) else 1
            return 0
        except:
            return 1

    def c2d(self):
        # current to density
        if self.__read_parameters():
            self.origin.warning("Something wrong with the parameters!")
            return 1
        for data_name in self.origin.data:
            x = self.origin.data[data_name][0]
            y = self.origin.data[data_name][1]
            y = [data * 1000 / self.area * self.negative for data in y]
            self.origin.data.update({data_name: (x, y)})
        self.x_axis = 'Density'
        self.refresh_ui()
        colors = self.origin.refresh_plot(autorange=True)
        self.origin.refresh_filename_list(colors)
        return 0

    def d2c(self):
        # density to current
        if self.__read_parameters():
            self.origin.warning("Something wrong with the parameters!")
            return 1
        for data_name in self.origin.data:
            x = self.origin.data[data_name][0]
            y = self.origin.data[data_name][1]
            y = [data / 1000 * self.area * self.negative for data in y]
            self.origin.data.update({data_name: (x, y)})
        self.x_axis = 'Current'
        self.refresh_ui()
        colors = self.origin.refresh_plot(autorange=True)
        self.origin.refresh_filename_list(colors)
        return 0

    def closeEvent(self, event):
        self.origin.data = self.origin_data.copy()
        colors = self.origin.refresh_plot(autorange=True)
        self.origin.refresh_filename_list(colors)
        event.accept()
