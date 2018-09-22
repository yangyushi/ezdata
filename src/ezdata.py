#!/usr/bin/env python3

import sys
sys.path.append('./ui')
sys.path.append('./src')
from GUI import main
from PyQt5 import QtWidgets

'''
QtWidgets.QApplication.oldinit = QtWidgets.QApplication.__init__
def newAppInit(self, *args):
    QtWidgets.QApplication.oldinit(self, *args)
    if hasattr(sys, 'frozen'):
        print('Removing /Users/yangyushi/Qt5.7.0/5.7/clang_64/plugins from path')
        self.removeLibraryPath('/Users/yangyushi/Qt5.7.0/5.7/clang_64/plugins')
        self.addLibraryPath('src/config')
        print('Library paths:')
        for aPath in self.libraryPaths():
            print(aPath)
    else:
        print('App runs within py interpreter')
QtWidgets.QApplication.__init__ = newAppInit
'''

if __name__ == '__main__':
    ezdata = QtWidgets.QApplication(sys.argv)
    main_window = main.Main()
    main_window.show()
    sys.exit(ezdata.exec_())
