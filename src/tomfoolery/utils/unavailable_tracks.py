#! /usr/bin/env python

class UnavailableTracksHandler:

    def __init__(self):
        
        # list of unavailable tracks to skip
        self.unavailable_tracks = []  

    def handleUnavailable(self, idx):
        
        # add index to the list
        self.unavailable_tracks.append(idx)  
