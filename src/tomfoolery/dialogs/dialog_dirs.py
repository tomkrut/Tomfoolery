#! /usr/bin/env python
import os
from os.path import join
from appdirs import user_config_dir
from PyQt6 import QtWidgets
from tomfoolery.ui.dialog_dir import Ui_DirDialog


class DirsDialogUI(QtWidgets.QDialog, Ui_DirDialog):
    """
    Set download dirs dialog UI.

    """
    def __init__(self, ssd=None, res=None):
        
        self.ssd = ssd
        self.download_dirs_old = self.ssd.download_dirs.copy()
        self.download_dirs_new = self.ssd.download_dirs.copy()

        super().__init__()
        self.setupUi(self, res)       

        self.connectSignalsSlots()


    def connectSignalsSlots(self):

        buttons = {}
        lineedits = {}
        for key in self.ssd.download_dirs.keys():

            key_ = key.strip('_').capitalize()[:-4] + 'Dir'            

            buttons[key] = getattr(self, f'button{key_}')
            lineedits[key] = getattr(self, f'lineEdit{key_}')

        for key in self.ssd.download_dirs.keys():  

            lineedit = lineedits[key]
            button = buttons[key]

            button.clicked.connect(lambda _, k = key, le = lineedit: self.change_dir(k, le, 'button_clicked'))
            lineedit.textChanged.connect(lambda _, k = key, le = lineedit: self.change_dir(k, le, 'text_changed'))
        
        self.buttonBox.accepted.connect(lambda mode = 'accept': self.save_dirs(mode)) # type: ignore
        self.buttonBox.rejected.connect(lambda mode = 'reject': self.save_dirs(mode)) # type: ignore
    

    def change_dir(self, key, lineedit, mode):
        
        if mode == 'text_changed':
            self.download_dirs_new[key] = lineedit.text()
        elif mode == 'button_clicked':
            self.download_dirs_new[key] = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                'Select where to save files'
            )
            lineedit.setText(self.download_dirs_new[key])
        else:
            raise ValueError               
        
    def save_dirs(self, mode=None):
        
        if mode == 'accept': 

            for path in self.download_dirs_new.values():
                if not os.path.exists(path) and path:
                    QtWidgets.QMessageBox.about(self, "Error", f"Path {path} is invalid.")
                    self.save_dirs(mode='reject') 
                    return                   

            self.ssd.download_dirs = self.download_dirs_new          
            self.ssd.pickle_dirs()

            self.accept()

        elif mode == 'reject':

            self.ssd.download_dirs = self.download_dirs_old 
            
            self.reject()

        else:
            raise ValueError  
        