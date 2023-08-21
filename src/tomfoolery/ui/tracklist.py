#! /usr/bin/env python
from PyQt6 import QtWidgets, QtCore
from .base import BaseUI

class TracklistUI(BaseUI):   

    def __init__(self, **kwargs):  

        super().__init__(**kwargs)

        self.scraper = None
        self.imageDownloader = None

        # init GUI elements lists
        self.checkboxes = []
        self.progressbars = []
        self.messageboxes = []

        self.unavailable_tracks = []

    def resizeWindow(self):

        self.tableWidget.resize(
            self.tableWidget.sizeHint().width(), 
            self.tableWidget.sizeHint().height()
        )   

    def prepareTracklist(self):

        labels = {            
            'Track nr.': [],
            'Title': [],
            'Artist': [],
        }

        for item in self.scraper.metadata.get('trackinfo') :
            labels['Track nr.'] += [str(item.get('track_num'))]
            labels['Title'] += [str(item.get('title'))]
            labels['Artist'] += [str(item.get('artist'))] 
            
        return labels
        
    def tracklistUI(self):

        labels = self.prepareTracklist()

        tablewidget = self.tableWidget        
               
        header_keys = list(labels.keys()) + ["Download", "Progress", "Message"]        
        tablewidget.verticalHeader().setVisible(False)

        labels = [dict(zip(labels, t)) for t in zip(*labels.values())]

        tablewidget.setRowCount(len(labels))
        tablewidget.setColumnCount(len(header_keys))        
        for row, label in enumerate(labels):
            
            for col, (k, v) in enumerate(label.items()):
                item = QtWidgets.QTableWidgetItem(v)       
                if k != 'Track nr.':
                    item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                tablewidget.setItem(row, col, item)

            # add checkbox          
            checkbox = QtWidgets.QCheckBox()            
            checkbox.setObjectName(f'checkboxRow{row}')
            self.checkboxes.append(checkbox)

            cellwidget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(cellwidget)
            layout.addWidget(checkbox)
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            cellwidget.setLayout(layout)

            tablewidget.setCellWidget(row, col + 1, cellwidget)

            # add progressbar
            progressbar = QtWidgets.QProgressBar()            
            progressbar.setObjectName(f'progressbarRow{row}')
            self.progressbars.append(progressbar)

            cellwidget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(cellwidget)
            layout.addWidget(progressbar)
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            cellwidget.setLayout(layout)       

            self.tableWidget.setCellWidget(row, col + 2, cellwidget)     

            # add messagebox label
            messagebox = QtWidgets.QLabel()           
            messagebox.setObjectName(f'messageboxRow{row}')
            messagebox.setStyleSheet(
            f'''
            QLabel#messageboxRow{row} {{                
                background-color: rgba(0,0,0,0%);
                border-radius: 0px;
                border-width: 0px;
                padding-right: 0px;
                padding-left: 0px;      
            }}	                                    
            '''         
            )
            self.messageboxes.append(messagebox)

            cellwidget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(cellwidget)
            layout.addWidget(messagebox)
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            layout.setContentsMargins(0,0,0,0)
            cellwidget.setLayout(layout)

            tablewidget.setCellWidget(row, col + 3, cellwidget)

            if row in self.unavailable_tracks:       
                checkbox.setEnabled(False)
                messagebox.setText("Track unavailable for scraping.") 

        tablewidget.setHorizontalHeaderLabels(header_keys)
        hheader = tablewidget.horizontalHeader()       
        hheader.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hheader.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hheader.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        hheader.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
        hheader.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
        hheader.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        tablewidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)   
        
        self.pushButtonDeselectAll.setDisabled(False)       
        self.pushButtonSelectAll.setDisabled(False) 

        self.resizeWindow()         

    def modifyTrackinfo(self):
        
        trackinfo = self.scraper.metadata.get('trackinfo')     
        assert len(self.checkboxes) == len(trackinfo)       
        for i, track in enumerate(trackinfo):
            if self.checkboxes[i].isChecked():
                trackinfo[i]['download_enabled'] = True
            else:
                trackinfo[i]['download_enabled'] = False

        self.scraper.metadata['trackinfo'] = trackinfo

    def selectAll(self):

        for cbox in self.checkboxes:
            cbox.setChecked(True)

    def deselectAll(self):

        for cbox in self.checkboxes:
            cbox.setChecked(False)
 
    def clearUIContent(self):    

        self.tableWidget.clearContents()  
        self.textEdit.clear()   
        self.pushButtonDeselectAll.setDisabled(True)        
        self.pushButtonSelectAll.setDisabled(True)  
    
    def clearUIElements(self):

        self.progressbars = []
        self.checkboxes = []
        self.messageboxes = []  
