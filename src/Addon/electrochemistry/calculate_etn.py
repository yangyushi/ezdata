from collections import OrderedDict
import numpy as np
from scipy.optimize import leastsq
from collections import OrderedDict
from PyQt5.uic import loadUiType
from GUI.plot import refresh_canvas, add_to_canvas
from PyQt5.QtWidgets import QTableWidgetItem, QMenu, QAction
from PyQt5 import QtCore
from IO.Export import export_multiple_data

ui_cal_etn, q_cal_etn = loadUiType("ui/calculate_etn.ui")


class CalculateETN(ui_cal_etn, q_cal_etn):

    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin
        self.data_lsv, self.data_kl, self.data_etn = {}, {}, {}
        self.calc_kl_by_step, self.calc_kl_by_interval = False, True  # assuming calculate kl plot by interval

    def showEvent(self, event):
        event.accept()
        self.data_lsv, self.data_kl, self.data_etn = {}, {}, {}
        self.calc_kl_by_step, self.calc_kl_by_interval = False, True  # assuming calculate kl plot by interval
        self.__init_slot()
        self.__init_canvas()
        self.__init_context()

    def __init_canvas(self):

        for canvas in [self.canvas_lsv, self.canvas_kl]:
            canvas.clear()
            canvas.setBackground('w')

    def __init_slot(self):
        try:
            self.origin.file_list_widget.itemDoubleClicked.disconnect()
        except TypeError:
            pass
        self.button_add_line.clicked.connect(self.accept_data)
        self.button_plot_kl.clicked.connect(self.generate_kl_plot)
        self.button_calculate.clicked.connect(self.calculate_etn)
        self.combo_box_presets.activated[str].connect(self.__on_activate_preset)
        self.combo_box_step_or_interval.activated[str].connect(self.__on_step_or_interval)
        self.origin.file_list_widget.itemDoubleClicked.connect(self.accept_data_db_click)

    def menu_configure(self, widget):
        """
        closure, return a slot poping up menu inside the widget
        """

        def slot(point):
            try:
                self.menu_export.triggered.disconnect()
            except TypeError:
                pass
            self.menu_export.triggered.connect(lambda signal, w=widget: self.export_data(signal, w))
            self.pop_menu.exec_(widget.mapToGlobal(point))

        return slot

    def __init_context(self):
        """
        set up context menu to export data
        """
        self.pop_menu = QMenu(self)
        self.menu_export = QAction("export data to ...", self)
        self.pop_menu.addAction(self.menu_export)

        for widget in [self.canvas_lsv, self.canvas_kl, self.table_result]:
            slot = self.menu_configure(widget)
            widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(slot)

    def __on_activate_preset(self, preset):
        [widget.clear() for widget in [self.line_edit_v, self.line_edit_c0, self.line_edit_d0]]
        if preset == 'Acidic':
            self.line_edit_v.insert('0.01')
            self.line_edit_c0.insert('1.26 * 10 ** -6')
            self.line_edit_d0.insert('1.93 * 10 ** -5')
        if preset == 'Alkaline':
            self.line_edit_v.insert('0.01')
            self.line_edit_c0.insert('1.20 * 10 ** -6')
            self.line_edit_d0.insert('1.90 * 10 ** -5')

    def __on_step_or_interval(self, choice):
        if choice == 'Step':
            self.calc_kl_by_step = True
            self.calc_kl_by_interval = False
        elif choice == 'Interval':
            self.calc_kl_by_step = False
            self.calc_kl_by_interval = True
        else:
            pass

    def accept_data(self):
        """
        accept a single dataset (a line) from the main window (the chosen one)
        insert the data into self.data_lsv dict
        the format: {rotation_speed: (data_x, data_y)}
        :return: 0 if data was accepted; 1 if accept action was not complete
        """
        if self.origin.chosen_file:
            accepted_data = self.origin.data[self.origin.chosen_file]
        else:
            self.origin.warning("Please select a data (line)")
            return 1

        try:
            electrode_area = float(self.line_edit_area.text())
            rotation_speed = float(self.line_edit_speed.text())
        except:
            self.origin.warning("something wrong with the parameters!")
            return 1

        x = accepted_data[0]
        y = [abs(data) * 1000 / electrode_area * (-1) for data in accepted_data[1]]
        self.data_lsv.update({rotation_speed: (x, y)})
        self.refresh_plot()
        return 0

    def export_data(self, signal, widget):
        """
        export the data to a selected folder as .csv files
        :param signal: required by PyQt5
        :param widget: the widget of which the data is to be exported
        :return: 0 if data was exported; 1 if exported was not complete
        """
        if widget == self.canvas_lsv:
            if self.data_lsv:
                prefix = 'LSV-'
                suffix = '.temp'  # add suffix to meet format of the export_multiple_data function
                data = self.data_lsv
                export_multiple_data(self, data, prefix, suffix)
                self.origin.notify("{data} was exported!".format(data='data of the LSV plot'))
                return 0
            else:
                self.origin.warning("no data available")
                return 1
        elif widget == self.canvas_kl:
            if self.data_kl:
                prefix = 'KL'
                suffix = '.temp'  # add suffix to meet format of the export_multiple_data function
                data = self.data_kl
                export_multiple_data(self, data, prefix, suffix)
                self.origin.notify("{data} was exported!".format(data='data of the KL plot'))
                return 0
            else:
                self.origin.warning("no data available")
                return 1
        elif widget == self.table_result:
            if self.data_kl:
                prefix = ''
                suffix = '.temp'  # add suffix to meet format of the export_multiple_data function
                data = self.data_etn
                x, y = [], []
                for p in data:  # change format of the data to export
                    x.append(p)
                    y.append(','.join(data[p][0:]))
                data = {'Fit_result': (x, y)}
                export_multiple_data(self, data, prefix, suffix)
                self.origin.notify("{data} was exported!".format(data='fit result'))
                return 0
            else:
                self.origin.warning("no data available")
                return 1

    def generate_kl_plot(self):
        """
        generate the KL plot based on the rotation speed and the potential range
        insert the calculated data into self.data_kl dict
        the format: {potential: (data_x, data_y)
        :return: 0 if kl plot was generated; 1 if the calculation was terminated
        """

        def find_closest(data_list, target):
            """find the number's index from the data_list whose value is most close to the target"""
            data_list = np.array(data_list)
            target = float(target)
            index, cost = 0, data_list[0]
            for i, temp in enumerate(data_list):
                if abs(temp - target) < cost:
                    cost = abs(temp - target)
                    index = i
            return index

        self.data_kl = OrderedDict()  # re-initialize self.data_kl, the dict is ordered for better output in the table
        try:
            min_num = float(self.line_edit_range_min.text())
            max_num = float(self.line_edit_range_max.text())
            step = float(self.line_edit_step.text())  # how many scatters in each fitting line
            assert step > 0
            if self.calc_kl_by_interval:
                potential_range = []
                while min_num < max_num:
                    potential_range.append(min_num)
                    min_num += step
            elif self.calc_kl_by_step:
                potential_range = np.linspace(min_num, max_num, step)
            else:
                assert 1
        except:
            self.origin.warning("something wrong with the parameters!")
            return 1
        for potential in potential_range:
            x, y = [], []
            for speed in self.data_lsv:
                potential_index = find_closest(self.data_lsv[speed][0], potential)
                current_density = self.data_lsv[speed][1][potential_index]  # self.data_lsv[data][1] - y
                # print("target is %s, result is %s" % (potential, self.data_lsv[speed][0][potential_index]))
                y.append(-1 * current_density ** -1)
                x.append((float(speed) * 2 * np.pi / 60) ** (-0.5))
            self.data_kl.update({"%.4f" % potential: (x, y)})
        self.refresh_plot()
        return 0

    def calculate_etn(self):
        """
        calculate the electron transfer number
        step 1. fit the scatters in the KL plot with linear function
        step 2. use the slope to calculate the etn
        the data structure of self.data_etn is:  {potential: (etn, slope, intercept)}
        :return: 0 if the electron transform number was calculated; 1 if the calculation was terminated
        """
        self.clear_table()

        try:
            c0 = eval(self.line_edit_c0.text())
            d0 = eval(self.line_edit_d0.text())
            v = eval(self.line_edit_v.text())
        except:
            self.origin.warning("something wrong with the parameters!")
            return 1
        if not self.data_kl:
            self.origin.warning("No data available to calculate")
            return 1
        else:  # calculate the electron transfer number if there is kl data available
            self.refresh_plot()
            potentials, slopes, intercepts = [], [], []
            residual = lambda p, x, y: y - (x * p[0] + p[1])  # residual function for linear regression
            for i, potential in enumerate(self.data_kl):
                x = np.array(self.data_kl[potential][0])
                y = np.array(self.data_kl[potential][1])
                fit_result = leastsq(residual, [0, 0], args=(x, y))
                slope = str(fit_result[0][0])
                intercept = str(fit_result[0][1])
                F = 96485  # Faraday constant
                etn = float(slope) ** -1 * (0.62 ** -1) * (F ** -1) * (c0 ** -1) * (d0 ** -(2 / 3)) * v ** (1 / 6) * (
                10 ** -3)
                etn = "%.4f" % etn
                data = (potential, etn, slope, intercept)
                self.insert_data_to_table(data)
                self.data_etn.update({potential: (etn, slope, intercept)})
                potentials.append(potential)
                slopes.append(slope)
                intercepts.append(intercept)
            self.plot_linear_fit(potentials, slopes, intercepts)
            return 0

    def plot_linear_fit(self, potentials, slopes, intercepts):
        # plot the fitting line
        data = OrderedDict()
        for i, potential in enumerate(potentials):
            slope = float(slopes[i])
            intercept = float(intercepts[i])
            x = self.data_kl[potential][0]
            x = np.array(x, dtype=float)
            y = slope * x + intercept
            data.update({potential: (x, y)})
        add_to_canvas(self.canvas_kl, data_line=data)

    def clear_table(self):
        # remove all the rows, leaving a blank line
        row_number = int(self.table_result.rowCount())
        for i in range(row_number):
            if i == 0:
                self.table_result.setItem(i, 0, QTableWidgetItem(''))
                self.table_result.setItem(i, 1, QTableWidgetItem(''))
                self.table_result.setItem(i, 2, QTableWidgetItem(''))
                self.table_result.setItem(i, 3, QTableWidgetItem(''))
            else:
                self.table_result.removeRow(row_number - i)

    def insert_data_to_table(self, data):
        # insert (1x2) data into the table
        row_position = self.table_result.rowCount() - 1
        self.table_result.insertRow(row_position)
        self.table_result.setItem(row_position, 0, QTableWidgetItem(data[0]))
        self.table_result.setItem(row_position, 1, QTableWidgetItem(data[1]))
        self.table_result.setItem(row_position, 2, QTableWidgetItem(data[2]))
        self.table_result.setItem(row_position, 3, QTableWidgetItem(data[3]))

    def refresh_plot(self):
        """
        remove the plot and plot the all datasets in self.data_lsv, self.data_kl again
        set the check state if self.data_lsv and self.data_kl is not blank
        """

        refresh_canvas(self.canvas_lsv, data_line=self.data_lsv)
        refresh_canvas(self.canvas_kl, data_scatter=self.data_kl)
        # add vertical line in canvas_lsv showing the chosen potentials
        for i, potential in enumerate(self.data_kl):
            x = (float(potential), float(potential))
            y = (min([min(self.data_lsv[a][1]) for a in self.data_lsv]),
                 max([max(self.data_lsv[a][1]) for a in self.data_lsv]))
            add_to_canvas(self.canvas_lsv, data_line={'temp': (x, y)})

        if self.data_lsv:
            self.check_lsv.setText("✓︎")
        else:
            self.check_lsv.setText("-")
        if self.data_kl:
            self.check_kl.setText("✓")
        else:
            self.check_kl.setText("-")

    def accept_data_db_click(self, event):
        """
        import the data to self.data_lsv via double click
        """
        self.origin.choose_filename(event)
        self.accept_data()

    def closeEvent(self, event):
        # reset the slot in self.origin, typically the double click in the list widget
        self.origin.file_list_widget.itemDoubleClicked.disconnect()
        self.origin.init_slot()
        event.accept()
