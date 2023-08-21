#! /usr/bin/env python
import demjson3 as demjson
import html
import re
import requests
import sys
import os
from pathlib import Path
from datetime import datetime
from mutagen.mp3 import MP3, EasyMP3
from mutagen.id3 import APIC, WXXX
from mutagen.id3 import ID3 as OldID3
from subprocess import Popen, PIPE
from os.path import exists, join
from os import W_OK

from tomfoolery.utils import (
    console_output, 
    emit_signal, 
    FilenameHandler  
)

if sys.version_info.minor < 4:
    html_unescape = html.parser.HTMLParser().unescape
else:
    html_unescape = html.unescape

class BandcampException(Exception):
    def __init__(self, message, **kwargs):  
       
        super().__init__(message)

        if (exists := kwargs.get('exists')) is not None:      
            self.exists = exists

        if (idx := kwargs.get('idx')) is not None:      
            self.idx = idx

####################################################################
# Bandcamp
####################################################################

class Bandcamp():

    def __init__(self, vargs, cfg):
        
        self.vargs = vargs  
        self.cfg = cfg              

        artist_url = self.vargs['artist_url']
        if 'bandcamp.com' in artist_url or ('://' in artist_url and self.vargs['bandcamp']):
            self.bc_url = artist_url
        else:
            self.bc_url = 'https://' + artist_url + '.bandcamp.com/music'        
              
    def generate_trackinfo(self, **kwargs):  
      
        """
        Read information from Bandcamp embedded JavaScript object notation.
        The method may return a list of URLs (indicating this is probably a "main" page which links to one or more albums),
        or a JSON if we can already parse album/track info from the given url.
        """    
        request = requests.get(self.bc_url)
        output = {}
        try:
            for attr in ['data-tralbum', 'data-embed']:
                output.update(
                    self.extract_embedded_json_from_attribute(
                        request, attr
                    )
                )
        # if the JSON parser failed, we should consider it's a "/music" page,
        # so we generate a list of albums/tracks and return it immediately
        except Exception as e:
            regex_all_albums = r'<a href="(/(?:album|track)/[^>]+)">'
            all_albums = re.findall(regex_all_albums, request.text, re.MULTILINE)
            album_url_list = list()
            for album in all_albums:
                album_url = re.sub(r'music/?$', '', self.bc_url) + album
                album_url_list.append(album_url)
            return album_url_list
        # if the JSON parser was successful, use a regex to get all tags
        # from this album/track, join them and set it as the "genre"
        regex_tags = r'<a class="tag" href[^>]+>([^<]+)</a>'
        tags = re.findall(regex_tags, request.text, re.MULTILINE)
        # make sure we treat integers correctly with join()
        # according to http://stackoverflow.com/a/7323861
        # (very unlikely, but better safe than sorry!)
        output['genre'] = ' '.join(s for s in tags)

        try:
            artUrl = request.text.split("\"tralbumArt\">")[1].split("\">")[0].split("href=\"")[1]
            output['artFullsizeUrl'] = artUrl
        except:
            console_output("Couldn't get full artwork.")
            output['artFullsizeUrl'] = None
        
        # fix artist metadata & mark tracks with attribute 'is_downloadable' 
        for idx, track in enumerate(output.get('trackinfo')):            
            if track.get('artist') is None:
                track['artist'] = output.get('artist')   
            if track.get('is_downloadable') is None:
                emit_signal(kwargs, 'unavailable_for_scraping', [idx]) 

        # get thumbnail
        self.thumbnail_url = output.get('artFullsizeUrl')  
       
        # save metadata
        self.metadata = output        

    def extract_embedded_json_from_attribute(self, request, attribute, debug=False):
        """
        Extract JSON object embedded in an element's attribute value.

        The JSON is "sloppy". The native python JSON parser often can't deal,
        so we use the more tolerant demjson instead.

        Args:
            request (obj:`requests.Response`): HTTP GET response from which to extract
            attribute (str): name of the attribute holding the desired JSON object
            debug (bool, optional): whether to print debug messages

        Returns:
            The embedded JSON object as a dict, or None if extraction failed
        """
        try:
            embed = request.text.split('{}="'.format(attribute))[1]
            embed = html_unescape(
                embed.split('"')[0]
            )
            output = demjson.decode(embed)
            if debug:
                print(
                    'extracted JSON: '
                    + demjson.encode(
                        output,
                        compactly=False,
                        indent_amount=2,
                    )
                )
        except Exception as e:
            output = None
            if debug:
                print(e)
        return output
       

    def execute(self, **kwargs):

        filenames = self.scrape_bandcamp_url(   
            custom_path=self.vargs['path'],
            **kwargs
        )

        if any(isinstance(elem, list) for elem in filenames):        
            filenames = [sub for sub in filenames if sub]        
            filenames = [val for sub in filenames for val in sub]  

    def scrape_bandcamp_url(self, custom_path='', **kwargs):      
        """
        Pull out artist and track info from a Bandcamp URL.

        Returns:
            list: filenames to open
        """    

        filenames = []
        album_data = self.metadata

        artist = album_data.get("artist")
        album_name = album_data.get("album")
            
        if len(album_data["trackinfo"]) > 1:
            console_output("Found a playlist.")  
        else: 
            console_output("Found a track.")  

        for idx, track in enumerate(album_data["trackinfo"]):
                       
            if not track['download_enabled']:
                continue 

            console_output(f'Track n°"{idx}".')                 
            emit_signal(kwargs, 'progress_init', [idx, 100])     
    
            filename = join(custom_path, self.sanitize_filename(f'{artist} - {track.get("title")}.mp3'))

            # Metadata correction          
            fh = FilenameHandler(              
                dir=custom_path, 
                cfg=self.cfg,                 
                filename=filename,
                track_number=idx,
                album=album_data.get("album_title") ,
                metadata_entries = self.metadata['trackinfo'][idx],
                man_metadata_entries=self.vargs.get('man_metadata_entries')                
            )              
            ret = fh.getOutput()
            filename, path =  ret.get('filename'), ret.get('dir')
            title = ret.get('title')   

            if exists(filename):
                emit_signal(kwargs, 'messagebox_set', [idx, f'Track already downloaded: "{title}".']) 
                emit_signal(kwargs, 'resize_window')             
                continue

            if not track['file']: 
                # message box is already set in the tracklist.py
                console_output(f'Track unavailable for scraping: "{title}".')                        
                continue
            
            emit_signal(kwargs, 'messagebox_set', [idx, 'Downloading...'])                   
            emit_signal(kwargs, 'resize_window')                         

            self.download_file(track['file']['mp3-128'], filename, idx, **kwargs)

            emit_signal(kwargs, 'messagebox_set', [idx, 'Setting tags...'])                   
            emit_signal(kwargs, 'resize_window')   

            album_year = album_data['album_release_date']
            if album_year:
                album_year = datetime.strptime(album_year, "%d %b %Y %H:%M:%S GMT").year    

            if track["track_num"]:
                track_number = str(track["track_num"]).zfill(2)
            else:
                track_number = None                
                                
            try:         
                filename = self.tag_file(
                        filename=filename,
                        artist=artist,
                        title=title,
                        album=album_name,
                        year=album_year,
                        genre=album_data['genre'],
                        artwork_url=album_data['artFullsizeUrl'],
                        track_number=track_number,
                        url=album_data['url']                                            
                )                  
            except Exception as e:
                raise BandcampException(f'Problem tagging "{title}".')                              
                                                                                
            filenames.append(filename)
            
            emit_signal(kwargs, 'messagebox_set', [idx, f'Downloaded "{ret.get("title", title)}".'])                 
            emit_signal(kwargs, 'checkbox_set', [idx, False])       
            emit_signal(kwargs, 'resize_window')                
             
        return filenames
    
    def download_file(self, url, filename, track_idx=0, session=None, params=None, **kwargs):
        """
        Download an individual file.
        """      

        if url[0:2] == '//':
            url = 'https://' + url[2:]

        # Use a temporary file so that we don't import incomplete files.
        tmp_path = filename + '.tmp'

        if session and params:
            r = session.get(url, params=params, stream=True )
        elif session and not params:
            r = session.get(url, stream=True )
        else:
            r = requests.get(url, stream=True)
        
        chunk_size = 1024
        total_length = int(r.headers.get('content-length', 0)) 
        pbar_max = int((total_length / chunk_size) + 1)
        emit_signal(kwargs, 'progress_init', [track_idx, pbar_max])  
        
        pbar_current_val = 0
        with open(tmp_path, 'wb') as f:            
            for chunk in r.iter_content(chunk_size=chunk_size):            
                if chunk:  # filter out keep-alive new chunks           
                    pbar_current_val += 1
                    emit_signal(kwargs, 'progress_set', [track_idx, pbar_current_val])  
                    f.write(chunk)
                    f.flush()

        if pbar_current_val < pbar_max:
            raise BandcampException("Connection closed prematurely, download incomplete.", idx=track_idx) 
        try:
            os.rename(tmp_path, filename)   
        except OSError:
            raise BandcampException('Could not rename temp file.')      

    def tag_file(
            self,
            filename=None, artist=None, title=None, 
            year=None, genre=None, artwork_url=None, 
            album=None, track_number=None, url=None            
        ):
        """
        Attempt to put ID3 tags on a file.
       
        """                   
        
        try:                           
            audio = EasyMP3(filename)
            audio.tags = None            
                
            audio["artist"] = artist
            audio["title"] = title 
            
            if year:
                audio["date"] = str(year)
            if album:
                audio["album"] = album
            if track_number:
                audio["tracknumber"] = track_number
            if genre:
                audio["genre"] = genre
            if url: # saves the tag as WOAR
                audio["website"] = url
            audio.save()

            if artwork_url:

                artwork_url = artwork_url.replace('https', 'http')
                mime = 'image/jpeg'
                if '.jpg' in artwork_url:
                    mime = 'image/jpeg'
                if '.png' in artwork_url:
                    mime = 'image/png'

                if '-large' in artwork_url:
                    new_artwork_url = artwork_url.replace('-large', '-t500x500')
                    try:
                        image_data = requests.get(new_artwork_url).content
                    except Exception as e:
                        # No very large image available.
                        image_data = requests.get(artwork_url).content
                else:
                    image_data = requests.get(artwork_url).content

                audio = MP3(filename, ID3=OldID3)
                audio.tags.add(
                    APIC(
                        encoding=3,  # 3 is for utf-8
                        mime=mime,
                        type=3,  # 3 is for the cover image
                        desc='Cover',
                        data=image_data
                    )
                )
                audio.save()

            # because there is software that doesn't seem to use WOAR we save url tag again as WXXX
            if url:
                audio = MP3(filename, ID3=OldID3)
                audio.tags.add( WXXX( encoding=3, url=url ) )
                audio.save()

            return filename                       

        except Exception as e:        
            return None       

    def sanitize_filename(self, filename):
        """
        Make sure filenames are valid paths.

        Returns:
            str:
        """
        sanitized_filename = re.sub(r'[/\\:*?"<>|]', '-', filename)
        sanitized_filename = sanitized_filename.replace('&', 'and')
        sanitized_filename = sanitized_filename.replace('"', '')
        sanitized_filename = sanitized_filename.replace("'", '')
        sanitized_filename = sanitized_filename.replace("/", '')
        sanitized_filename = sanitized_filename.replace("\\", '')

        # Annoying.
        if sanitized_filename[0] == '.':
            sanitized_filename = u'dot' + sanitized_filename[1:]

        return sanitized_filename
                