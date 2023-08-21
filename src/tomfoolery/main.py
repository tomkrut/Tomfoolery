#! /usr/bin/env python
import os
from os.path import join
import sys
from appdirs import user_config_dir
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import QDir

from tomfoolery.scrapers import (
    Bandcamp, 
    Soundcloud, 
    Youtube
)
from tomfoolery.ui import ( 
    ConsoleUI,
    TracklistUI, 
    TomfooleryDirs,
    TomfooleryConfig,
    Completer,
)
from tomfoolery.dialogs import DirsDialogUI, ConfigDialogUI
from tomfoolery.utils import (
    execWorker, 
    initWorker,
    WorkerSlots,
    ImageDownloader, 
    ThumbnailHandler,
    MetadataHandler,
    UnavailableTracksHandler
)


if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(__file__)


class MainUI(ConsoleUI, TracklistUI, MetadataHandler, 
             WorkerSlots, ThumbnailHandler, UnavailableTracksHandler):
    """
    Main.

    """
    def __init__(self):
        
        self.res = join(application_path, 'resources') 
        QDir.addSearchPath('resources', self.res)       

        appname = 'Tomfoolery'          
        self.config_dir = user_config_dir(appname, appauthor=False)  
        # download directories       
        self.ssd = TomfooleryDirs(self.config_dir) 
        # config
        self.cfg = TomfooleryConfig(self.config_dir)
        # autocomplete user url entries
        self.com = Completer(self.config_dir)  
               
        kwargs = {
            'resources': self.res,
            'completer': self.com,            
        }
        super().__init__(**kwargs) 

        # image / thumbnail downloader        
        self.imageDownloader = ImageDownloader(
            label=self.thumbnailLabel
        )      
 
        # init 
        self.vargs = {}  
        self.scraper_type = None 
              
        self.connectSignalsSlots()                    


    def connectSignalsSlots(self):

        self.action_Directories.triggered.connect(self.setDirs) 
        self.action_Config.triggered.connect(self.setConfig) 
        self.scrapeButton.clicked.connect(lambda: self.initScraper()) 
        self.imageDownloader.download_finished.connect(self.handleFinished)
        self.downloadButton.clicked.connect(lambda: self.execScraper()) 
        self.clearButton.clicked.connect(self.clearUI)       
        sys.stdout.textWritten.connect(self.consoleGUI)     
        self.pushButtonDeselectAll.clicked.connect(self.deselectAll)  
        self.pushButtonSelectAll.clicked.connect(self.selectAll)
        self.tableWidget.cellEditingStarted.connect(self.metadata_init) 
        self.tableWidget.itemChanged.connect(self.metadata_changed)             
 

    def handleError(self, error):

        QtWidgets.QMessageBox.about(self, "Error", str(error))           


    def setDirs(self):

        dialog = DirsDialogUI(self.ssd, self.res)
        dialog.exec()
        # overwrite dirs config with the new values
        self.ssd = dialog.ssd


    def setConfig(self):
        
        dialog = ConfigDialogUI(self.cfg, self.res)
        dialog.exec()
        # overwrite misc config with the new values
        self.cfg = dialog.cfg
 

    def clearUI(self):

        self.clearUIContent()  
        self.resetThumbnail(self.thumbnailLabel)       


    def getURL(self):       
      
        txt = self.vargs['artist_url'] = self.lineEditURL.text()     
        if not txt:            
            raise Exception("Please supply an artist\'s username or URL!")            

        if 'soundcloud.com' in txt:
            self.scraper_type = 'soundcloud'  
        elif 'bandcamp.com' in txt:
            self.scraper_type = 'bandcamp'        
        elif any(x in txt for x in ('youtube.com', 'youtu.be')):
            self.scraper_type = 'youtube'         
        else:
            raise Exception('URL format unrecognized.') 
            
        self.com.append_word_bank(txt)
        self.com.pickle_word_bank()        


    def getConfig(self):           

        dirs = {
            key: value for key, value in self.ssd.download_dirs.items()
        }               
        if self.scraper_type == 'soundcloud':
            self.vargs['path'] = dirs.get('soundcloud_dir')        
        elif self.scraper_type == 'bandcamp':
            self.vargs['path'] = dirs.get('bandcamp_dir')       
        elif self.scraper_type == 'youtube':
            self.vargs['path'] = dirs.get('youtube_dir') 

        if self.vargs['path'] is None:
            raise Exception('Please provide the download directory path (Menu "File -> Directories").')     
  
           
    def initScraper(self):

        try:                    
            self.getURL()
            # re-initialize completer (update word bank)
            self.com = Completer(self.config_dir)
            self.lineEditURL.setCompleter(self.com)

            self.getConfig() 
            self.clearUIContent()
            self.clearUIElements()               
           
            if self.scraper_type == 'soundcloud':
                self.scraper = Soundcloud(self.vargs, self.cfg)        
            elif self.scraper_type == 'bandcamp':
                self.scraper = Bandcamp(self.vargs, self.cfg)
            elif self.scraper_type == 'youtube':      
                self.scraper = Youtube(self.vargs, self.cfg) 

        except Exception as e:
            self.handleError(e)
            return

        worker = initWorker(self.scraper.generate_trackinfo)
        worker.signals.unavailable_for_scraping.connect(self.handleUnavailable)
        worker.signals.worker_error.connect(self.handleError)
        worker.signals.worker_finished.connect(self.tracklistUI)
        worker.signals.worker_finished.connect(lambda x=self.thumbnailLabel: self.getThumbnail(x))
  
        self.pool.start(worker)                


    def execScraper(self):

        # drop unchecked tracks from the tracklist
        self.modifyTrackinfo()  

        # execute scraper         
        worker = execWorker(self.scraper.execute)

        worker.signals.progress_set.connect(self.progressBarSet)
        worker.signals.progress_init.connect(self.progressBarInit)
        worker.signals.resize_window.connect(self.resizeWindow)
        worker.signals.checkbox_set.connect(self.checkBoxSet)
        worker.signals.messagebox_set.connect(self.messageBoxSet) 
        worker.signals.worker_error.connect(self.handleError) 
       
        self.pool.start(worker) 


####################################################################
# Main
####################################################################

def main():

    try:    
        app = QtWidgets.QApplication(sys.argv)           
             
        window = MainUI()    
        app.setWindowIcon(QtGui.QIcon(os.path.join(window.res, '512.png')))   
     
        palette = QtGui.QPalette()
        window.setPalette(palette)
        window.show()        

        sys.exit(app.exec())

    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
            