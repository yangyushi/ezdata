import pyqtgraph

color_maps = {
    # todo: enable more color maps
    'red-violet-blue': pyqtgraph.ColorMap(
        pos=(0, 0.4, 1),
        color=((255, 0, 0, 255),
               (255, 102, 255, 255),
               (0, 0, 255, 255))
    )
}


def decompose_canvas(canvas):
    """
    Extract components from the canvas, enabling better control of the plot
    :param canvas: a PlotWidget instance, in EZData such instance can be found in src/ui/main_window.ui
    :return:
    """
    plot_item = canvas.getPlotItem()
    view_box = plot_item.getViewBox()
    axes = {'left': plot_item.getAxis('left'),
            'right': plot_item.getAxis('right'),
            'top': plot_item.getAxis('top'),
            'bottom': plot_item.getAxis('bottom')}
    return (plot_item, view_box, axes)


def configure_canvas(canvas):
    plot_item, view_box, axes = decompose_canvas(canvas)
    for axis in axes:
        plot_item.showAxis(axis, show=True)
        if axis in ['top', 'right']:
            axes[axis].showLabel(False)
            axes[axis].setStyle(showValues=False)
    plot_item.disableAutoRange()


def add_to_canvas(canvas, data_line=None, data_scatter=None, **kwargs):
    """
    Plot data on a canvas
    :param canvas: The canvas that data sets were plotted on
    :param data_line: Data sets will be plotted as line, the data sets have this structure:
        {data_name_1: ((x1, x2, ...), (y1, y2, ...))}
    :param data_scatter: Data sets will be plotted as scatter, the data sets have this structure
        {data_name_1: ((x1, x2, ...), (y1, y2, ...))}
    :param kwargs: Other parameters
    :return: {filename: color}
    """

    color_map = color_maps['red-violet-blue']
    plot_item, view_box, axes = decompose_canvas(canvas)
    color_dict = {}

    if data_line:
        if kwargs.get('pen'):
            try:
                for name in data_line:
                    pen = kwargs.get('pen')
                    width = pen['width']
                    color = pyqtgraph.mkColor(*pen['color'])
                    pen = pyqtgraph.mkPen(color, width=width, cosmetic=True)
                    data = data_line[name]
                    plot_item.plot(data[0], data[1], pen=pen, name=name)
                    color_dict.update({name: color})
            except ValueError:  # when the given pen is not good
                add_to_canvas(canvas, data_line=data_line)
        else:  # using default pens
            for index, name in enumerate(data_line):
                data = data_line[name]
                color = tuple(color_map.map(index / len(data_line)))  # generate color according to the index
                color = pyqtgraph.mkColor(*color)
                pen = pyqtgraph.mkPen(color=color, width=2, cosmetic=True)
                plot_item.plot(data[0], data[1], pen=pen, name=name)
                color_dict.update({name: color})

    if data_scatter:
        for index, name in enumerate(data_scatter):
            data = data_scatter[name]
            color = tuple(color_map.map(index / len(data_scatter)))  # generate color according to the index
            color = pyqtgraph.mkColor(*color)
            plot_item.plot(data[0], data[1],
                           pen=None, symbol='o', symbolPen=None, symbolSize=10, symbolBrush=color)

    if kwargs.get('autorange'):
        plot_item.autoRange()

    return color_dict


def refresh_canvas(canvas, data_line=None, data_scatter=None, **kwargs):
    """
    Refresh the plot, delete everything firstly and plot everything
    """
    # todo: enable user to store previous plot configurations
    plot_item, view_box, axes = decompose_canvas(canvas)
    if plot_item.legend != None:
        plot_item.legend.scene().removeItem(plot_item.legend)
        plot_item.addLegend()
    plot_item.clear()
    return add_to_canvas(canvas, data_line, data_scatter, **kwargs)


def add_legend(canvas):
    plot_item, view_box, axes = decompose_canvas(canvas)
    if plot_item.legend:
        plot_item.legend.scene().removeItem(plot_item.legend)
        plot_item.legend = None
    else:
        plot_item.addLegend()


def autosize(canvas):
    plot_item, view_box, axes = decompose_canvas(canvas)
    plot_item.autoRange()
