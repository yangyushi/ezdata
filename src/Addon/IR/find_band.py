import numpy as np
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5 import QtCore
from IO.Export import export_multiple_data

ui_find_band, q_find_band = loadUiType("ui/ir_find_band.ui")

class FindBand(ui_find_band, q_find_band):

    def __init__(self, origin):
        super().__init__()
        self.setupUi(self)
        self.origin = origin

    def showEvent(self, event):
        self.smooth_range = [0, 20]
        self.threshold_range = [0, 100]
        self.threshold = 100 
        self.smooth = 0
        self.band_positions = {}
        self.band_positions = {}
        self.refresh_ui()

    def refresh_ui(self):
        self.slider_smooth.setMinimum(self.smooth_range[0])
        self.slider_smooth.setMaximum(self.smooth_range[1])
        self.slider_threshold.setMinimum(self.threshold_range[0])
        self.slider_threshold.setMaximum(self.threshold_range[1])
        self.slider_smooth.valueChanged[int].connect(self.change_smooth_value)
        self.slider_threshold.valueChanged[int].connect(self.change_threshold_value)
        self.button_find_band.clicked.connect(self.find_band)
        self.button_export_data.clicked.connect(self.export_data)

    def change_smooth_value(self, value):
        self.smooth = value
        value = str(value)
        self.line_edit_smooth.setText(value)

    def change_threshold_value(self, value):
        self.threshold = value
        value = str(value)
        self.line_edit_threshold.setText(value)

    def find_band(self):
        if not self.origin.chosen_file:
            self.origin.warning("Please choose an IR spectrum!")
            return 1
        chosen_file = self.origin.chosen_file
        x, y = self.origin.data[chosen_file]
        smooth = self.line_edit_smooth.text()
        threshold = self.line_edit_threshold.text()
        smooth, threshold = int(smooth), float(threshold)  # str --> number
        max_x, max_y = self.local_minimum(x, y, smooth, threshold)
        self.band_positions.update({chosen_file: (max_x, max_y)})
        self.origin.chosen_points = []
        for spectrum in self.band_positions:
            x, y = self.band_positions[spectrum]
            points = [(x[i], y[i]) for i in range(len(x))]
            for point in points:
                self.origin.chosen_points.append(point)
        self.origin.refresh_plot()

    def export_data(self):
        export_multiple_data(self.origin, self.band_positions, prefix='IR_bands_', suffix='.csv')

    @staticmethod
    def simple_smooth(data, smooth_range):
        result = []
        for i in range(len(data)):
            if i >= smooth_range and i + smooth_range < len(data):
                temp = 0
                for j in data[i-smooth_range : i+smooth_range]:
                    temp += j
                temp = temp / (2 * smooth_range + 1)
                result.append(temp)
        for i in range(smooth_range):  # fill the data missed
            result.insert(0, result[0])
            result.insert(-1, result[-1])
        return result

    def local_minimum(self, x, y, smooth=0, threshold=0):
        # find the local minimum
        data = y.copy()
        if smooth:
            data = self.simple_smooth(data, smooth)
        indice = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0]  # this is the indice of local minimum
        if smooth:  # compensate for the position shift due to the smooth
            for ioi, i in enumerate(indice):
                    for j in range(i-smooth, i+smooth):
                        try:
                            if y[j] < y[i]:
                                indice[ioi] = j
                        except:
                            pass
        if threshold:  # ignore the mininum above the threshold
            f = lambda i: True if y[i] < threshold else False
            indice = list(filter(f, indice))
        max_x = [x[i] for i in indice]
        max_y = [y[i] for i in indice]
        return max_x, max_y
