#! /usr/bin/env python
from PyQt6 import QtCore, QtGui, QtWidgets
import os

class QTableWidget_(QtWidgets.QTableWidget):

    cellEditingStarted = QtCore.pyqtSignal(object)
  
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.rowCount() != 0:         
            height = self.horizontalHeader().height()
            for row in range(self.model().rowCount()):
                height += self.rowHeight(row)

            if self.horizontalScrollBar().isVisible():
                height += self.horizontalScrollBar().height()
            self.setMaximumHeight(height + 2)
    
    def edit(self, index, trigger, event):
        result = super().edit(index, trigger, event)
        if result:
            self.cellEditingStarted.emit(self.item(index.row(), index.column()))
        return result


class Ui_TomfooleryWindow(object):    

    def setupUi(self, TomfooleryWindow, resources=None, completer=None):             
        TomfooleryWindow.setObjectName("TomfooleryWindow")      
        TomfooleryWindow.resize(800, 500)       
        self.centralwidget = QtWidgets.QWidget(parent=TomfooleryWindow)        
        self.centralwidget.setObjectName("centralwidget")        
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.urlLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.urlLabel.setObjectName("urlLabel")
        self.horizontalLayout.addWidget(self.urlLabel)
        self.lineEditURL = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.lineEditURL.setObjectName("lineEditURL")    
        self.completer = completer   
        self.lineEditURL.setCompleter(self.completer)     
        self.horizontalLayout.addWidget(self.lineEditURL)
        self.scrapeButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.scrapeButton.setObjectName("scrapeButton")
        self.horizontalLayout.addWidget(self.scrapeButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.pushButtonSelectAll = QtWidgets.QPushButton(parent=self.centralwidget)
        self.pushButtonSelectAll.setObjectName("pushButtonSelectAll")
        self.pushButtonSelectAll.setDisabled(True)
        self.horizontalLayout_5.addWidget(self.pushButtonSelectAll)
        self.pushButtonDeselectAll = QtWidgets.QPushButton(parent=self.centralwidget)
        self.pushButtonDeselectAll.setObjectName("pushButtonDeselectAll")
        self.pushButtonDeselectAll.setDisabled(True)
        self.horizontalLayout_5.addWidget(self.pushButtonDeselectAll)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.tableWidget = QTableWidget_(parent=self.centralwidget)
        self.tableWidget.setObjectName("tableWidget")
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.textEdit = QtWidgets.QTextEdit(parent=self.centralwidget)      
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.textEdit.setMaximumHeight(100)
        self.textEdit.setStyleSheet("background-color: black; color: white;")
        self.horizontalLayout_3.addWidget(self.textEdit)        
        self.thumbnailLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.thumbnailLabel.setObjectName("thumbnailLabel")   
        pixmap = QtGui.QPixmap(os.path.join(resources, 'missing_image.png'))
        self.thumbnailLabel.setPixmap(
            pixmap.scaled(
            self.horizontalLayout_3.maximumSize().height(),
            self.horizontalLayout_3.maximumSize().height()
            )
        )
        self.horizontalLayout_3.addWidget(self.thumbnailLabel)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)        
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.clearButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.clearButton.setObjectName("clearButton")
        self.horizontalLayout_2.addWidget(self.clearButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.downloadButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.downloadButton.setObjectName("downloadButton")
        self.horizontalLayout_2.addWidget(self.downloadButton)        
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 6)
        self.verticalLayout_2.setStretch(2, 2)
        self.verticalLayout_2.setStretch(3, 1)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)
        TomfooleryWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=TomfooleryWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 654, 19))
        self.menubar.setObjectName("menubar")
        self.menu_File = QtWidgets.QMenu(parent=self.menubar)
        self.menu_File.setObjectName("menu_File")
        TomfooleryWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=TomfooleryWindow)
        self.statusbar.setObjectName("statusbar")
        TomfooleryWindow.setStatusBar(self.statusbar)
        self.action_Directories = QtGui.QAction(parent=TomfooleryWindow)
        self.action_Directories.setObjectName("action_Directories")
        self.action_Directories.setMenuRole(QtGui.QAction.MenuRole.NoRole)
        self.action_Config = QtGui.QAction(parent=TomfooleryWindow)
        self.action_Config.setObjectName("action_Config")
        self.action_Config.setMenuRole(QtGui.QAction.MenuRole.NoRole)           
        self.menu_File.addAction(self.action_Directories)
        self.menu_File.addAction(self.action_Config)
        self.menubar.addAction(self.menu_File.menuAction())

        style_dir = os.path.join(resources, 'stylesheet.qss')    
        with open(style_dir, mode='r') as f:
            TomfooleryWindow.setStyleSheet(f.read()) 

        self.retranslateUi(TomfooleryWindow)
        QtCore.QMetaObject.connectSlotsByName(TomfooleryWindow)

    def retranslateUi(self, TomfooleryWindow):
        _translate = QtCore.QCoreApplication.translate
        TomfooleryWindow.setWindowTitle(_translate("TomfooleryWindow", "Tomfoolery"))
        self.pushButtonSelectAll.setText(_translate("TomfooleryWindow", "Select All"))
        self.pushButtonDeselectAll.setText(_translate("TomfooleryWindow", "Deselect All"))
        self.urlLabel.setText(_translate("TomfooleryWindow", "URL"))
        self.scrapeButton.setText(_translate("TomfooleryWindow", "Scrape"))
        self.clearButton.setText(_translate("TomfooleryWindow", "Clear"))
        self.downloadButton.setText(_translate("TomfooleryWindow", "Download"))
        self.menu_File.setTitle(_translate("TomfooleryWindow", "&File"))
        self.action_Directories.setText(_translate("TomfooleryWindow", "&Directories"))
        self.action_Config.setText(_translate("TomfooleryWindow", "&Config"))
            