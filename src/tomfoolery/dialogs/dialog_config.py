#! /usr/bin/env python
import os
from os.path import join
from appdirs import user_config_dir
from PyQt6 import QtWidgets
from tomfoolery.ui.dialog_config import Ui_ConfigDialog


class ConfigDialogUI(QtWidgets.QDialog, Ui_ConfigDialog):
    """
    Set config dialog UI.

    """
    def __init__(self, cfg=None, res=None):

        self.cfg = cfg 
        self.vargs_old = self.cfg.vargs.copy()           
        self.vargs_new = self.cfg.vargs.copy()   

        super().__init__()
        self.setupUi(self, res)       

        self.connectSignalsSlots()

    def checkboxState(self, checkbox):

        state = checkbox.isChecked()
        return state

    def connectSignalsSlots(self):

        state = self.checkboxState(self.checkBoxArtistFolder)               
        self.checkBoxArtistFolder.stateChanged.connect(lambda s = state, obj = 'artistFolder': self.setCfg(obj, s))
        state = self.checkboxState(self.checkBoxAlbumFolder)  
        self.checkBoxAlbumFolder.stateChanged.connect(lambda s = state, obj = 'albumFolder': self.setCfg(obj, s))      

        self.buttonBox.accepted.connect(lambda mode = 'accept': self.save_cfg(mode)) # type: ignore
        self.buttonBox.rejected.connect(lambda mode = 'reject': self.save_cfg(mode)) # type: ignore

        for key in ['albumFolder', 'artistFolder']:                    
            if self.cfg.vargs.get(key):
                checkBox = getattr(self, f'checkBox{key[0].upper() + key[1:]}')
                checkBox.setChecked(True)
                

    def setCfg(self, obj=None, s=None):

        assert obj in self.cfg.vargs        
        self.vargs_new[obj] = bool(s)

    def save_cfg(self, mode=None):

        if mode == 'accept': 
            self.cfg.vargs = self.vargs_new          
            self.cfg.pickle_cfg()
            self.accept()

        elif mode == 'reject':
            self.cfg.vargs = self.vargs_old            
            self.reject()
            
        else:
            raise ValueError  
        