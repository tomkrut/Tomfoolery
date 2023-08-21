#! /usr/bin/env python
from PyQt6 import QtWidgets, QtCore
from os.path import exists, join
from os import mkdir, W_OK
import pickle
from glob import glob
import urllib

WORD_BANK_MAX_SIZE = 5
COMPLETER_MAX_VISIBLE_ITEMS = 5


def url_validator(url):
    try:
        result = urllib.parse.urlparse(url)
        components = [result.scheme, result.path]
        if result.netloc != "":
            components.append(result.netloc)
        if result.scheme not in ['http', 'https']:
            raise Exception
        return all(components)
    except:
        return False


class Completer(QtWidgets.QCompleter):

    def __init__(self, config_dir):  
       
        self.word_bank = []
        self.word_bank_esc = []

        self.config_dir = config_dir
        self.filename = 'word_bank.pkl'     
                 
        self.word_bank_esc = self.unpickle_word_bank()  
        
        self.word_bank = [
            urllib.parse.unquote(el, encoding='utf-8', errors='replace')
            for el in self.word_bank_esc
        ]

        super().__init__(self.word_bank)    

        self.setMaxVisibleItems(COMPLETER_MAX_VISIBLE_ITEMS)  
        self.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

    def unpickle_word_bank(self):

        if not exists(self.config_dir):
            mkdir(self.config_dir)            
            return

        for f in glob(join(self.config_dir, self.filename)):
            with open(f, 'rb') as handle:                
                pkl = pickle.load(handle)
                return pkl
            
        return []

    def pickle_word_bank(self):

        path = join(self.config_dir, self.filename)     
        with open(path, 'wb') as handle:          
            pickle.dump(self.word_bank_esc, handle, protocol=pickle.HIGHEST_PROTOCOL)                

    def append_word_bank(self, url):

        if not url_validator(url):            
            raise Exception('Please provide a valid URL.') 
        
        url_ = urllib.parse.quote(url, safe=':/') 
        if url_ not in self.word_bank_esc:
            self.word_bank_esc.append(url_)
        
        self.limit_word_bank()
    
    def limit_word_bank(self):

        if len(self.word_bank_esc) > WORD_BANK_MAX_SIZE:
            self.word_bank_esc  = self.word_bank_esc[-WORD_BANK_MAX_SIZE:]
            