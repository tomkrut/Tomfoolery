#! /usr/bin/env python


class MetadataHandler:

    def __init__(self, **kwargs):

        super().__init__(**kwargs)  
        
        # manual metadata entries are saved to temp variable
        # they are only propagated forward if they differ from the downloaded metadata            
        self.temp_metadata = {}  

    def metadata_init(self, item): 

        row = item.row()
        col = item.column()
        try:
            header = self.tableWidget.horizontalHeaderItem(col).text()  
        except AttributeError as e:  
            return
        if not hasattr(self, 'temp_metadata'):
            self.temp_metadata = {} 
        self.temp_metadata[(row, col)] = {                
                'text': item.text(), 
                'header': header,           
        }
        
    def metadata_changed(self, item): 
    
        row = item.row()
        col = item.column()
        try:
            header = self.tableWidget.horizontalHeaderItem(col).text()
        except AttributeError:
            return
        # if metadata is not equal to initial metadata, remember the manual entry
        try:
            if not hasattr(self, 'temp_metadata'):
                return
            entry = self.temp_metadata[(row, col)]
            if ((entry.get('text') != item.text()) and (entry.get('header') == header)): 
                if 'man_metadata_entries' not in self.vargs.keys():
                    self.vargs['man_metadata_entries'] = {}             
                self.vargs['man_metadata_entries'][(row, col)] = {                
                    'text': item.text(), 
                    'header': header,           
                }    
        except KeyError:
            return 
                          