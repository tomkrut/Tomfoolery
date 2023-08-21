#! /usr/bin/env python
from pytube import YouTube, Playlist
from pytube.exceptions import *
import subprocess
import re
import os
import requests
from pathlib import Path
from pathvalidate import sanitize_filename
import shutil
from tomfoolery.utils import (
    console_output, 
    emit_signal, 
    FilenameHandler
)

class YoutubeException(Exception):
    def __init__(self, message, **kwargs):  

        super().__init__(message)

        if (idx := kwargs.get('idx')) is not None:      
            self.idx = idx

ffmpeg = shutil.which('ffmpeg')
if not ffmpeg: 
    raise Exception("ffmpeg is not installed.")
os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg
from moviepy.editor import  VideoFileClip


class Youtube():

    def __init__(self, vargs=None, cfg=None):
        
        self.vargs = vargs  
        self.cfg = cfg
        self.metadata = {}  

        self.download_path = self.vargs['path']
        self.url = self.vargs['artist_url']         

        self.default_filename = None
        self.filename = None   
              
        self.playlist_title = None
        self.videos = []           
        if 'list' in self.url:
            self.type = 'playlist'     
            console_output("Found a playlist.")          
        else:
            self.type = 'single_track'    
            console_output("Found a track.")

    def pytube_init(self, url):

        if self.type == 'single_track':            
            try:
                video = YouTube(url)
                self.videos.append(video)       
            except VideoRegionBlocked:
                raise YoutubeException(f'Video {url} is blocked in your region, skipping.')   
            except VideoPrivate:
                raise YoutubeException(f'Video {url} is private, skipping.')
            except RegexMatchError:
                raise YoutubeException(f'Regex pattern did not return any matches, skipping.')
            except RecordingUnavailable:
                raise YoutubeException(f'Video {url} is private, skipping.')
            except MembersOnly:
                raise YoutubeException(f'Video {url} is available only to users who have subscribed to a content creator, skipping.')
            except MaxRetriesExceeded:
                raise YoutubeException(f'Maximum number of retries exceeded, skipping.')
            except LiveStreamError:
                raise YoutubeException('Video is a live stream.')
            except HTMLParseError:
                raise YoutubeException('HTML could not be parsed')
            except ExtractError:
                raise YoutubeException('Data extraction based exception.')
            except AgeRestrictedError:
                raise YoutubeException('Video is age restricted, and cannot be accessed without OAuth.')
            except VideoUnavailable:
                raise YoutubeException(f'Video {url} is unavailable, skipping.')
            
        else:                    
            try:
                p = Playlist(url)
                self.playlist_title = p.title
                for video in p.videos:
                    self.videos.append(video)
            except VideoRegionBlocked:
                raise YoutubeException(f'Video {url} is blocked in your region, skipping.')   
            except VideoPrivate:
                raise YoutubeException(f'Video {url} is private, skipping.')
            except RegexMatchError:
                raise YoutubeException(f'Regex pattern did not return any matches, skipping.')
            except RecordingUnavailable:
                raise YoutubeException(f'Video {url} is private, skipping.')
            except MembersOnly:
                raise YoutubeException(f'Video {url} is available only to users who have subscribed to a content creator, skipping.')
            except MaxRetriesExceeded:
                raise YoutubeException(f'Maximum number of retries exceeded, skipping.')
            except LiveStreamError:
                raise YoutubeException('Video is a live stream.')
            except HTMLParseError:
                raise YoutubeException('HTML could not be parsed')
            except ExtractError:
                raise YoutubeException('Data extraction based exception.')
            except AgeRestrictedError:
                raise YoutubeException('Video is age restricted, and cannot be accessed without OAuth.')
            except VideoUnavailable:
                raise YoutubeException(f'Video {url} is unavailable, skipping.')

        
    def generate_trackinfo(self, **kwargs):

        self.pytube_init(self.url)
        try:
            self.thumbnail_url = self.videos[0].thumbnail_url 
        except KeyError:
            raise YoutubeException('Found no video, check URL.') 

        self.metadata['trackinfo'] = []
        
        for idx, vid in enumerate(self.videos):                

            if '-' in vid.title:   

                pattern_text = r'(?P<artist>.*)(\s+-\s+)(?P<title>.*)'
                pattern = re.compile(pattern_text)
                match = pattern.match(vid.title)
                if match:
                    artist = match.group('artist')
                    title = match.group('title')    

            elif '"' in vid.title:

                pattern_text = r'(?P<artist>.*)(\b.*)"(?P<title>.*)"'
                pattern = re.compile(pattern_text)
                match = pattern.match(vid.title)
                if match:
                    artist = match.group('artist')
                    title = match.group('title') 

            elif "'" in vid.title:

                pattern_text = r"(?P<artist>.*)(\b.*)'(?P<title>.*)'"
                pattern = re.compile(pattern_text)
                match = pattern.match(vid.title)
                if match:
                    artist = match.group('artist')
                    title = match.group('title') 

            else:

                artist = vid.author
                title = vid.title
                 
            self.metadata['trackinfo'].append(
                {    
                    'artist': artist,                
                    'track_num': idx + 1,
                    'title': title
                }
            )     

    def execute(self, **kwargs):        
      
        for idx, vid in enumerate(self.videos):            
      
            if not self.metadata['trackinfo'][idx].get('download_enabled'):                   
                continue

            console_output(f'Track n°"{idx + 1}".') 

            if (audio_streams := vid.streams.filter(only_audio=True)) is not None:
                sorted_streams = audio_streams.order_by('abr').desc()        
                file = sorted_streams.first()                
            else:          
                if (video_streams := vid.streams.filter(only_audio=False)) is not None:
                    sorted_streams = video_streams.order_by('fps').desc()        
                    file = sorted_streams.first()

            filename = sanitize_filename(file.default_filename)
            self.default_filename = Path(self.download_path).joinpath(filename)      
            self.filename = Path(self.download_path).joinpath(filename).with_suffix('.mp3')  

            # Metadata correction          
            fh = FilenameHandler(              
                dir=self.download_path, 
                cfg=self.cfg,                 
                filename=self.filename,
                track_number=idx,
                album=self.playlist_title,
                metadata_entries = self.metadata['trackinfo'][idx],
                man_metadata_entries=self.vargs.get('man_metadata_entries')                
            )              
            ret = fh.getOutput()
            self.filename, self.download_path, metadata = ret.get('filename'), ret.get('dir'), ret.get('metadata') 
            title = ret.get('title')  
         
            if os.path.isfile(self.filename):
                stem = Path(self.filename).stem
                emit_signal(kwargs, 'messagebox_set', [idx, f'Track already downloaded: "{stem}".'])    
                continue
            else: 
                emit_signal(kwargs, 'messagebox_set', [idx, 'Downloading...']) 
                emit_signal(kwargs, 'progress_init', [idx, 100]) 
                emit_signal(kwargs, 'resize_window')  

                file = file.download(output_path=self.download_path)   
            
                emit_signal(kwargs, 'progress_set', [idx, 50])  
                emit_signal(kwargs, 'resize_window')  

                if audio_streams:
                    ffmpeg_proc = f'{ffmpeg} -y -i "{self.default_filename}" "{self.filename}"'
                    subprocess.run(ffmpeg_proc, shell=True)
                elif video_streams:
                    video = VideoFileClip(file)
                    audio = video.audio
                    audio.write_audiofile(self.filename)
                    audio.close()
                    video.close()
                else:
                    raise Exception('No audio or video streams found.')

                emit_signal(kwargs, 'progress_set', [idx, 75])  
                emit_signal(kwargs, 'resize_window')  
                try:
                    os.remove(file) 
                except OSError:
                    raise YoutubeException('Could not remove temp file.')                        
                            
            emit_signal(kwargs, 'progress_set', [idx, 85]) 
            emit_signal(kwargs, 'resize_window')  

            self.embed_art(vid.thumbnail_url)

            emit_signal(kwargs, 'messagebox_set', [idx, 'Setting tags...']) 
            emit_signal(kwargs, 'progress_set', [idx, 95]) 
            emit_signal(kwargs, 'resize_window')  
                    
            self.add_tags(metadata)   
            
            emit_signal(kwargs, 'messagebox_set', [idx, f'Downloaded {title}.'])  
            emit_signal(kwargs, 'progress_set', [idx, 100])            
            emit_signal(kwargs, 'resize_window')  

            emit_signal(kwargs, 'checkbox_set', [idx, False])   


    def add_tags(self, metadata=None):          

        root = Path(self.download_path)        
        temp_audio_path = root.joinpath('temp.mp3')                 
       
        # overwrite track title with a new value        
        artist = metadata.get('artist')
        title = metadata.get('title')           
        track = metadata.get('track_num')

        if self.playlist_title is not None:
            album = self.playlist_title 
        else:
            album = "-"
        
        ffmpeg_proc = f'{ffmpeg} -i "{self.filename}"'
        ffmpeg_proc += f' -metadata artist="{artist}"'
        ffmpeg_proc += f' -metadata title="{title}"' 
        ffmpeg_proc += f' -metadata track="{track}"'
        ffmpeg_proc += f' -metadata album="{album}"'
        ffmpeg_proc += f' "{temp_audio_path}"' 

        subprocess.run(ffmpeg_proc, shell=True)                            
    
        try:
            os.rename(temp_audio_path, self.filename)  
        except OSError:
            raise YoutubeException('Could not remove temp file.') 
                     
    
    def embed_art(self, thumbnail_url):
        
        root = Path(self.download_path)
        temp_cover_path = root.joinpath('cover.png')
        temp_audio_path = root.joinpath('temp.mp3')
        try:
            r = requests.get(thumbnail_url)  
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise YoutubeException(e)
        except requests.exceptions.ConnectionError as e:
            raise YoutubeException(e)   
        except requests.exceptions.Timeout as e:
            raise YoutubeException(e) 
        except requests.exceptions.TooManyRedirects:
            raise YoutubeException(e) 
        except requests.exceptions.RequestException as e:
            raise YoutubeException(e) 
            raise SystemExit(e)
        
        with open(temp_cover_path, 'wb') as f:
            f.write(r.content)

        ffmpeg_proc = f'{ffmpeg} -i "{self.filename}" -i "{temp_cover_path}" -c copy -map 0 -map 1 "{temp_audio_path}"'        
        subprocess.run(ffmpeg_proc, shell=True)

        try:
            os.rename(temp_audio_path, self.filename)
        except OSError:
            raise YoutubeException('Could not rename temp audio file.')
        try:
            os.remove(temp_cover_path)
        except OSError:
            raise YoutubeException('Could not delete temp conver image file.')
                