#! /usr/bin/env python
import re
from os.path import join, exists
from os import mkdir
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
        self.man_metadata_entries = man_metadata_entries 

        self.metadata['album'] = self.metadata.get('title') if album is None else album

        self.track_number = track_number    

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
                    if self.metadata.get('artist') and self.metadata['artist'] != entry.get('text'):
                        console_output(f'Changing artist to "{entry.get("text")}".')
                        self.metadata['artist'] = entry.get('text')
                elif entry.get('header') == 'Title':
                    if self.metadata.get('title') and self.metadata['title'] != entry.get('text'):
                        console_output(f'Changing title to "{entry.get("text")}".')
                        self.metadata['title'] = entry.get('text')
                elif entry.get('header') == 'Album':
                    if self.metadata.get('album') and self.metadata['album'] != entry.get('text'):
                        console_output(f'Changing album to "{entry.get("text")}".')
                        self.metadata['album'] = entry.get('text')

        if self.albumFolder:
            stem = sanitize_filename(f'{self.metadata["title"]}')
            filename_new = str(Path(filename).with_stem(stem))
        # format: <artist - title>
        else: 
            stem = sanitize_filename(f'{self.metadata["artist"]} - {self.metadata["title"]}')
            filename_new = str(Path(filename).with_stem(stem))

        return filename_new

    def makeArtistFolder(self):                 
     
        directory = self.metadata['artist']
        directory = sanitize_filename(directory)
        self.dir = join(self.dir, directory)
        if not exists(self.dir):
            mkdir(self.dir)      

    def makeAlbumFolder(self):

        if self.artistFolder:         
            directory = self.metadata['album']
        else:
            directory = self.metadata['artist'] + " - " + self.metadata['title']
        directory = sanitize_filename(directory)
        self.dir = join(self.dir, directory)
        if not exists(self.dir):
            mkdir(self.dir)   

    def getOutput(self):

        return {
            'artist': self.metadata['artist'],
            'title': self.metadata['title'],
            'metadata': self.metadata,
            'dir': self.dir,
            'filename': self.filename,
            'album': self.metadata['album']
        }   
        