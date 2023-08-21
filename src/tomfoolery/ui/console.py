#! /usr/bin/env python
import sys
from PyQt6 import QtGui, QtCore
from .base import BaseUI

class EmittingStream(QtCore.QObject):

    textWritten = QtCore.pyqtSignal(str)
    
    def write(self, text):
        self.textWritten.emit(str(text))

class ConsoleUI(BaseUI):
    def __init__(self, **kwargs):

        super().__init__(**kwargs)
       
        # setup custom output stream
        sys.stdout = EmittingStream()

    def closeEvent(self, a0: QtGui.QCloseEvent):              

        # restore sys.stdout
        sys.stdout = sys.__stdout__

    def consoleGUI(self, text):

        if not text or text == '\n':
            return

        cursor = self.textEdit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        self.textEdit.setTextCursor(cursor)
        if len(self.textEdit.toPlainText()):            
            text = "<br>" + text + "</br>"      
        cursor.insertHtml(text)        
        self.textEdit.ensureCursorVisible()
        