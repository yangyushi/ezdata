import re
from PyQt5.QtWidgets import *


def save_xy(folder, filename, x, y):
    # write data in different files to the folder
    content = [('{data_x},{data_y}'.format(data_x=x[i], data_y=y[i])) for i in range(len(x))]
    content = "\n".join(content)
    print("exporting to filename: %s" % filename)
    filename += '.csv'
    filename = folder + '/' + filename
    with open(filename, 'w') as f:
        f.write(content)
    f.close()


def export_multiple_data(root, data, prefix='', suffix=''):
    folder = QFileDialog.getExistingDirectory(root)
    if folder:
        for filename in data:
            xy = data[filename]
            save_name = "{p}{f}{s}".format(p=prefix, f=filename, s=suffix)
            save_xy(folder, save_name, xy[0], xy[1])
        return True
    else:
        return False


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QMainWindow, QApplication

    app = QApplication(sys.argv)
    main = QMainWindow()
    export_multiple_data(main, {'test.txt': ([1, 2], [3, 4])})
    app.exec_()
