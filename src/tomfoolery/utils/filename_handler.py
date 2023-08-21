#! /usr/bin/env python
import re
from os.path import join, exists
from os import mkdir, rename
from pathlib import Path
from pathvalidate import sanitize_filename
from .scrape_common import console_output

class FilenameHandler:

    def __init__(
            self, 
            dir: str, 
            cfg: dict,             
            filename: str,
            track_number: int,
            album: str,
            metadata_entries: dict,
            man_metadata_entries: dict,         
        ):
        
        # config
        self.dir = dir
        self.cfg = cfg

        # metadata        
        self.metadata = metadata_entries
        self.artist = metadata_entries.get('artist')
        self.title = metadata_entries.get('title')
        self.album = album if album is not None else metadata_entries.get('title')
        self.track_number = track_number        
        self.man_metadata_entries = man_metadata_entries 

        self.albumFolder = self.cfg.vargs.get('albumFolder')
        self.artistFolder = self.cfg.vargs.get('artistFolder')  

        self.filename = self.getFilename(filename)     
         
        if self.artistFolder:
            self.makeArtistFolder()        
        if self.albumFolder:
            self.makeAlbumFolder()


    def getFilename(self, filename):
               
        # Check for manual metadata entries   
        if self.man_metadata_entries is not None:             
            man_metadata_track = [v for k, v in self.man_metadata_entries.items() if k[0] == self.track_number]
            for entry in man_metadata_track:      
                if entry.get('header') == 'Artist':
                    self.metadata['artist'] = self.artist = entry.get('text')
                    console_output(f"Changing artist to {self.artist}.")
                elif entry.get('header') == 'Title':
                    self.metadata['title'] = self.title = entry.get('text')
                    console_output(f"Changing title to {self.title}.")                 

        # format: <title>
        if self.albumFolder:
            stem = sanitize_filename(f'{self.title}')
            filename_new = str(Path(filename).with_stem(stem))
        # format: <artist - title>
        else: 
            stem = sanitize_filename(f'{self.artist} - {self.title}')
            filename_new = str(Path(filename).with_stem(stem))

        return filename_new
       

    def makeArtistFolder(self):                 
     
        directory = self.artist
        directory = sanitize_filename(directory)
        directory = join(self.dir, directory)
        if not exists(directory):
            mkdir(directory)   
        # overwrite current directory  
        self.dir = directory     
    

    def makeAlbumFolder(self):

        if self.artistFolder:         
            directory = self.album
        else:
            directory = self.artist + " - " + self.title
        directory = sanitize_filename(directory)
        directory = join(self.dir, directory)
        if not exists(directory):
            mkdir(directory)   
        # overwrite current directory  
        self.dir = directory


    def getOutput(self):

        return {
            'artist': self.artist,
            'title': self.title,
            'metadata': self.metadata,
            'dir': self.dir,
            'filename': self.filename,       
        }   
        