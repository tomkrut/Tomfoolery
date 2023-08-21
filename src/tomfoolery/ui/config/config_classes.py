#! /usr/bin/env python
import pickle
from glob import glob
from os.path import exists, join
from os import mkdir, W_OK


class TomfooleryDirs():

    def __init__(self, config_dir):
        
        self.filename = 'config_dir.pkl' 
        self.config_dir = config_dir
        self.download_dirs = {
            'soundcloud_dir': None,
            'bandcamp_dir': None,      
            'youtube_dir': None,
        }
  
        self.get_pkl() 

    def get_pkl(self):

        if not exists(self.config_dir):
            mkdir(self.config_dir)            
            return

        for f in glob(join(self.config_dir, self.filename)):
            with open(f, 'rb') as handle:                
                pkl = pickle.load(handle)
                for key in self.download_dirs:
                    self.download_dirs[key] = pkl.get(key)
                return
                          
    def pickle_dirs(self):
        
        path = join(self.config_dir, self.filename)        
        with open(path, 'wb') as handle:
            pickle.dump(self.download_dirs, handle, protocol=pickle.HIGHEST_PROTOCOL)


class TomfooleryConfig():

    def __init__(self, config_dir):
        
        self.filename = 'config_misc.pkl'   
        self.config_dir = config_dir
        self.vargs = {
            'artistFolder': None,
            'albumFolder': None,            
        }

        self.load_pkl()
    
    def load_pkl(self):       

        if not exists(self.config_dir):
            mkdir(self.config_dir)            
            return

        for f in glob(join(self.config_dir, self.filename)):
            with open(f, 'rb') as handle:                
                pkl = pickle.load(handle)
                for key in self.vargs:
                    self.vargs[key] = pkl.get(key)
                return

    def pickle_cfg(self):

        path = join(self.config_dir, self.filename)     
        with open(path, 'wb') as handle:          
            pickle.dump(self.vargs, handle, protocol=pickle.HIGHEST_PROTOCOL)            
