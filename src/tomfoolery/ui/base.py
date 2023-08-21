#! /usr/bin/env python
from PyQt6 import QtWidgets, QtCore
from .main_window import Ui_TomfooleryWindow

class BaseUI(QtWidgets.QMainWindow, Ui_TomfooleryWindow):

    def __init__(self, resources, completer, **kwargs):

        super().__init__()
  
        self.setupUi(
            self, 
            resources, 
            completer
        ) 

        # setup multithreading    
        self.pool = QtCore.QThreadPool.globalInstance()
