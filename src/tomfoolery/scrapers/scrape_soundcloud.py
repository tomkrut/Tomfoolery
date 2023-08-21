#!/usr/bin/env python3
import re
import cgi
import itertools
import logging
import mimetypes
mimetypes.init()
import os
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import warnings
import sys
from dataclasses import asdict
import mutagen
from mutagen.easymp4 import EasyMP4
EasyMP4.RegisterTextKey("website", "purl")
import requests
from clint.textui import progress
from pathlib import Path
from pathvalidate import sanitize_filename
from soundcloud import (
    BasicAlbumPlaylist, 
    BasicTrack, 
    MiniTrack, 
    SoundCloud,
    Transcoding
)
from tomfoolery.utils import (
    console_output, 
    emit_signal, 
    FilenameHandler,
    FfmpegProcess, 
    handle_progress_info
)

CLIENT_ID = 'a3e059563d7fd3372b49b37f00a00bcf'
AUTH_TOKEN = None
NAME_FORMAT = '{title}'
PLAYLIST_NAME_FORMAT = '{playlist[title]}_{title}'

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("requests").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fileToKeep = []

class SoundCloudException(Exception):
    def __init__(self, message, **kwargs):  

        super().__init__(message)

        if (idx := kwargs.get('idx')) is not None:      
            self.idx = idx

class Soundcloud():

    def __init__(self, vargs=None, cfg=None):  

        self.vargs = vargs  
        self.cfg = cfg        

        self.metadata = {}
        self.python_args = {}
        self.arguments = None

        self.thumbnail_url = None

        self.setup_args()              
    
    def generate_trackinfo(self, **kwargs):

        kwargs = self.python_args
        self.metadata['trackinfo'] = []

        url = kwargs.get("l")
        item = self.client.resolve(url)
        logger.debug(item)
     
        if not item: 
            raise SoundCloudException("URL is not valid.")                      
        elif item.kind == "track":   
            self.metadata = get_track_info(
                item, 
                metadata=self.metadata
            )
        elif item.kind == "playlist":     
            self.metadata = get_playlist_info(
                item,            
                metadata=self.metadata, 
                **kwargs
            ) 
        else:
            raise SoundCloudException("Unknown item type: {item.kind}.")           
    
        # remember artwork reference
        self.thumbnail_url = item.artwork_url

        # save metadata to kwargs, used when out of the class scope
        self.python_args['metadata'] = self.metadata          
    
    def setup_args(self):
        """
        Main function, parses the URL from command line arguments
        """

        # exit if ffmpeg not installed
        if not is_ffmpeg_available():
            raise SoundCloudException("ffmpeg is not installed.")                   

        # Parse arguments
        self.arguments = {}

        # main arguments
        self.arguments["-l"] = self.vargs['artist_url']  
        self.arguments["--path"] = self.vargs['path']
        self.arguments["-c"] = True
        self.arguments["--no-playlist-folder"] = True

        if self.arguments.get("--debug"):
            logger.level = logging.DEBUG
        elif self.arguments.get("--error"):
            logger.level = logging.ERROR                   
        
        logger.info("Soundcloud Downloader")
        logger.debug(self.arguments)
            
        client_id = self.arguments.get("--client-id") or CLIENT_ID
        token = self.arguments.get("--auth-token") or AUTH_TOKEN
        
        self.client = SoundCloud(client_id, token if token else None)
        
        if not self.client.is_client_id_valid():
            if self.arguments.get("--client-id"):
                logger.error(f"Invalid client_id specified by --client-id argument. Using a dynamically generated client_id.")
            elif CLIENT_ID:
                logger.error(f"Invalid client_id. Using a dynamically generated client_id.")
            self.client = SoundCloud(None, token if token else None)
            if not self.client.is_client_id_valid():
                raise SoundCloudException("Dynamically generated client_id is not valid.")                
        
        if token or self.arguments.get("me") and not self.client.is_auth_token_valid():
            if self.arguments.get("--auth-token"):
                raise SoundCloudException(f"Invalid auth_token specified by --auth-token argument.")
            else:
                raise SoundCloudException(f"Invalid auth_token.")          
       
        if self.arguments.get("--hidewarnings"):
            warnings.filterwarnings("ignore")
        
        if not self.arguments.get("--name-format"):
            self.arguments["--name-format"] = NAME_FORMAT
        
        if not self.arguments.get("--playlist-name-format"):
            self.arguments["--playlist-name-format"] = PLAYLIST_NAME_FORMAT
            
        if self.arguments.get("me"):
            # set url to profile associated with auth token
            self.arguments.get["-l"] = self.client.get_me().permalink_url
        try:
            self.arguments["-l"] = validate_url(self.client, self.arguments["-l"])
        except Exception:
            raise               
            
        # convert arguments dict to python_args (kwargs-friendly args)
        for key, value in self.arguments.items():
            key = key.strip("-").replace("-", "_")
            self.python_args[key] = value
            
        # change download path
        path = self.arguments.get("--path")
        if os.path.exists(path):
            try:
                os.chdir(path)
            except OSError:
                raise SoundCloudException('"os.chdir" failed.')
        else:
            if self.arguments.get("--path"):
                raise SoundCloudException(f"Invalid download path '{path}' specified by --path argument")
            else:
                raise SoundCloudException(f"Invalid download path '{path}'")            

    def execute(self, **kwargs):       
        """
        Detects if a URL is a track or a playlist, and parses the track(s)
        to the track downloader
        """    
        kwargs = kwargs | self.python_args
        # variables 'cfg', 'man_metadata_entries', 'path' are being used in the FilenameHandler
        try:
            kwargs['path'] = self.vargs['path']
            kwargs['cfg'] = self.cfg
            kwargs['man_metadata_entries'] = self.vargs['man_metadata_entries']
        except KeyError:
            pass
                
        url = kwargs.get("l")
        item = self.client.resolve(url)
        logger.debug(item)
        if not item:    
            raise SoundCloudException("URL is not valid.")
        elif item.kind == "track":
            kwargs['track_number'] = 0     
            console_output("Found a track.")
            download_track(self.client, item, **kwargs)
        elif item.kind == "playlist":
            console_output("Found a playlist.")
            download_playlist(self.client, item, **kwargs) 
        else:       
            raise SoundCloudException(f"Unknown item type {item.kind}")                           
    
        if self.arguments.get("--remove"):
            remove_files()       

        # go to the original directory
        if os.getcwd() != kwargs['path']:
            try:
                os.chdir(kwargs['path'])
            except OSError:
                raise SoundCloudException('"os.chdir" to the SoundCloud downloads directory failed.')

#######################
####### UTILITY #######
#######################

def get_playlist_info(playlist: BasicAlbumPlaylist, metadata: dict, **kwargs):
    
    metadata['artist'] = playlist.user.username
    metadata['album'] = playlist.title
    try:            
        for idx, track in itertools.islice(enumerate(playlist.tracks, 1), 0, None):

            ret = parse_title(track.title)  
            title = ret.get("title")  
            artist = metadata['artist'] = ret.get("artist", track.user.username)           

            metadata['trackinfo'].append(
            {            
                'artist': artist,      
                'track_num': idx,
                'title': title
            }
        )      
    finally:
        return metadata           
    
def get_track_info(track: BasicTrack, metadata: dict):
   
    ret = parse_title(track.title) 
    title = ret.get("title") 
    artist = ret.get("artist", track.user.username)

    metadata['album'] = title + ' (Single)'
    metadata['artist'] = artist    
    metadata['trackinfo'].append(
        {    
            'artist': artist,          
            'track_num': 1,
            'title': title
        }
    ) 
    return metadata    

def parse_title(title):

    if '-' in title:
        pattern_text = r'(?P<artist>\w+)(\s+-\s+)(?P<title>.*)'
        pattern = re.compile(pattern_text)
        match = pattern.match(title)
        if match:
            return {
                "artist": match.group('artist'), 
                "title": match.group('title')
            }    
    return  {"title": title}
      
def validate_url(client: SoundCloud, url: str):
    """
    If url is a valid soundcloud.com url, return it.
    Otherwise, try to fix the url so that it is valid.
    If it cannot be fixed, exit the program.
    """
    if url.startswith("https://m.soundcloud.com") or url.startswith("http://m.soundcloud.com") or url.startswith("m.soundcloud.com"):
        url = url.replace("m.", "", 1)
    if url.startswith("https://www.soundcloud.com") or url.startswith("http://www.soundcloud.com") or url.startswith("www.soundcloud.com"):
        url = url.replace("www.", "", 1)
    if url.startswith("soundcloud.com"):
        url = "https://" + url
    if url.startswith("https://soundcloud.com") or url.startswith("http://soundcloud.com"):
        url = urllib.parse.urljoin(url, urllib.parse.urlparse(url).path)
        return url
    
    # see if link redirects to soundcloud.com
    try:
        resp = requests.get(url)
        if url.startswith("https://soundcloud.com") or url.startswith("http://soundcloud.com"):
            return urllib.parse.urljoin(resp.url, urllib.parse.urlparse(resp.url).path)
    except Exception:
        # see if given a username instead of url
        if client.resolve(f"https://soundcloud.com/{url}"):
            return f"https://soundcloud.com/{url}"
    
    raise SoundCloudException(f"URL is not valid.")   


def remove_files():
    """
    Removes any pre-existing tracks that were not just downloaded
    """
    logger.info("Removing local track files that were not downloaded.")
    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    for f in files:
        if f not in fileToKeep:
            os.remove(f)


def download_playlist(client: SoundCloud, playlist: BasicAlbumPlaylist, **kwargs):
    """
    Downloads a playlist
    """

    if kwargs.get("no_playlist"):
        logger.info("Skipping playlist.")
        return
    playlist_name = playlist.title.encode("utf-8", "ignore")
    playlist_name = playlist_name.decode("utf-8")
    playlist_name = sanitize_filename(playlist_name)
    playlist_info = {
                "author": playlist.user.username,
                "id": playlist.id,
                "title": playlist.title
    }  
    
    if kwargs.get("n"):  # Order by creation date and get the n lasts tracks
        playlist.tracks.sort(
            key=lambda track: track.id, reverse=True
        )
        playlist.tracks = playlist.tracks[: int(kwargs.get("n"))]       

    tracknumber_digits = len(str(len(playlist.tracks)))      
    for idx, track in itertools.islice(enumerate(playlist.tracks, 1), 0, None):

        # save current track index to the kwargs
        kwargs['track_number'] = idx
        
        metadata = kwargs.get("metadata")
        if not metadata['trackinfo'][idx - 1].get('download_enabled'):
            continue

        logger.debug(track)
        console_output(f'Track n°"{idx}".') 
        playlist_info["tracknumber"] = str(idx).zfill(tracknumber_digits)
        if isinstance(track, MiniTrack):
            if playlist.secret_token:
                track = client.get_tracks([track.id], playlist.id, playlist.secret_token)[0]
            else:
                track = client.get_track(track.id)

        download_track(client, track, playlist_info, kwargs.get("strict_playlist"), **kwargs)   
           

def try_utime(path, filetime):
    try:
        os.utime(path, (time.time(), filetime))
    except Exception:
        logger.error("Cannot update utime of file")

def get_filename(track: BasicTrack, original_filename=None, aac=False, playlist_info=None, **kwargs):
    
    username = track.user.username
    title = track.title.encode("utf-8", "ignore").decode("utf-8")

    if kwargs.get("addtofile"):
        if username not in title and "-" not in title:
            title = "{0} - {1}".format(username, title)
            logger.debug('Adding "{0}" to filename'.format(username))

    timestamp = str(int(track.created_at.timestamp()))
    if kwargs.get("addtimestamp"):
        title = timestamp + "_" + title
    
    if not kwargs.get("addtofile") and not kwargs.get("addtimestamp"):
        if playlist_info:
            title = kwargs.get("playlist_name_format").format(**asdict(track), playlist=playlist_info, timestamp=timestamp)
        else:
            title = kwargs.get("name_format").format(**asdict(track), timestamp=timestamp)

    ext = ".m4a" if aac else ".mp3"  # contain aac in m4a to write metadata
    if original_filename is not None:
        original_filename = original_filename.encode("utf-8", "ignore").decode("utf-8")
        ext = os.path.splitext(original_filename)[1]
    filename = limit_filename_length(title, ext)
    filename = sanitize_filename(filename)

    # Custom filename format  
    try:
        artist = track.artist 
    except AttributeError:
        artist = track.user.username 
    ext = os.path.splitext(filename)[1]    
    filename = f'{artist} - {track.title}{ext}'

    return filename

def fetch_original_file(track: BasicTrack, playlist_info: dict, client: SoundCloud, **kwargs):

    logger.info("Downloading the original file.")
    # Get the requests stream
    url = client.get_track_original_download(track.id, track.secret_token)
    
    if not url:
        logger.info("Could not get original download link")
        return {'filename': None}
    
    r = requests.get(url, stream=True)
    if r.status_code == 401:
        logger.info("The original file has no download left.")
        return {'filename': None}

    if r.status_code == 404:
        logger.info("Could not get name from stream - using basic name")
        return {'filename': None}

    # Find filename
    header = r.headers.get("content-disposition")
    _, params = cgi.parse_header(header)
    if "filename*" in params:
        encoding, filename = params["filename*"].split("''")
        filename = urllib.parse.unquote(filename, encoding=encoding)
    elif "filename" in params:
        filename = urllib.parse.unquote(params["filename"], encoding="utf-8")
    else:
        raise SoundCloudException(f"Could not get filename from content-disposition header: {header}")
    
    if not kwargs.get("original_name"):
        filename, ext = os.path.splitext(filename)

        # Find file extension
        mime = r.headers.get("content-type")
        ext = ext or mimetypes.guess_extension(mime)
        filename += ext

        filename = get_filename(track, filename, playlist_info=playlist_info, **kwargs)

    logger.debug(f"filename : {filename}")
    
    return {'filename': None, 'kwargs': kwargs}


def download_original_file(track: BasicTrack, filename: str, playlist_info: dict, **kwargs):
  
    title = track.title
    # Skip if file ID or filename already exists
    if already_downloaded(track, title, filename, **kwargs):
        if kwargs.get("flac") and can_convert(filename):
            filename = filename[:-4] + ".flac"
        return (filename, True)

    # Write file
    r = kwargs.get('request')
    total_length = int(r.headers.get("content-length"))
        
    temp = tempfile.NamedTemporaryFile(delete=False)
    received = 0  
    
    if playlist_info is not None:
        idx = int(playlist_info.get('tracknumber')) - 1
    else:
        idx = 0
  
    emit_signal(kwargs, 'progress_init', [idx, total_length])  
    emit_signal(kwargs, 'resize_window')  
    with temp as f:
        for chunk in progress.bar(
            r.iter_content(chunk_size=1024),
            expected_size=(total_length / 1024) + 1,
            hide=True if kwargs.get("hide_progress") else False,
        ):
            if chunk:
                received += len(chunk)
                emit_signal(kwargs, 'progress_set', [idx, len(chunk)])  
                f.write(chunk)
                f.flush()        

    emit_signal(kwargs, 'checkbox_set', [idx, False])   

    if received != total_length:
        raise SoundCloudException("Connection closed prematurely, download incomplete.", idx=idx)             
 
    shutil.move(temp.name, os.path.join(os.getcwd(), filename))
  
    if kwargs.get("flac") and can_convert(filename):
        logger.info("Converting to .flac.")
        newfilename = limit_filename_length(filename[:-4], ".flac")

        commands = ["ffmpeg", "-i", filename, newfilename, "-loglevel", "error"]
        logger.debug(f"Commands: {commands}")
        subprocess.call(commands)
        os.remove(filename)
        filename = newfilename    

    return (filename, False)


def get_transcoding_m3u8(client: SoundCloud, transcoding: Transcoding):
    url = transcoding.url
    if url is not None:
        headers = client.get_default_headers()
        if client.auth_token:
            headers["Authorization"] = f"OAuth {client.auth_token}"
        r = requests.get(url, params={"client_id": client.client_id}, headers=headers)
        logger.debug(r.url)
        return r.json()["url"]
        

def fetch_hls(track: BasicTrack, playlist_info: dict, **kwargs):

    if not track.media.transcodings:
        raise SoundCloudException(f"Track {track.permalink_url} has no transcodings available")
    
    logger.debug(f"Trancodings: {track.media.transcodings}")
    
    aac_transcoding = None
    mp3_transcoding = None
    
    for t in track.media.transcodings:
        if t.format.protocol == "hls" and "aac" in t.preset:
            aac_transcoding = t
        elif t.format.protocol == "hls" and "mp3" in t.preset:
            mp3_transcoding = t
    
    aac = False
    transcoding = None
    if not kwargs.get("onlymp3") and aac_transcoding:
        transcoding = aac_transcoding
        aac = True
    elif mp3_transcoding:
        transcoding = mp3_transcoding
                
    if not transcoding:
        raise SoundCloudException(
            f"Could not find mp3 or aac transcoding. "
            f"Available transcodings: {[t.preset for t in track.media.transcodings if t.format.protocol == 'hls']}"
        )

    filename = get_filename(track, None, aac, playlist_info, **kwargs)
    logger.debug(f"filename : {filename}")

    # transcoding is needed in download_hls()
    kwargs['transcoding'] = transcoding

    return {'filename': filename, 'kwargs': kwargs}

def download_hls(track: BasicTrack, filename: str, playlist_info: dict, client: SoundCloud, **kwargs):
    
    title = track.title   
    # Skip if file ID or filename already exists
    if already_downloaded(track, title, filename, **kwargs):
        return (filename, True)    
    
    # Get the requests stream
    transcoding = kwargs.get('transcoding') 
    url = get_transcoding_m3u8(client, transcoding)
    filename_path = os.path.abspath(filename)  

    if playlist_info is not None:
        idx = int(playlist_info.get('tracknumber')) - 1
    else:
        idx = 0
    
    emit_signal(kwargs, 'progress_init', [idx, 100])  
    emit_signal(kwargs, 'resize_window')  
    
    process = FfmpegProcess(["ffmpeg", "-i", url, "-c", "copy", filename_path])
    # Use the run method to run the FFmpeg command.
    kwargs['idx'] = idx
    process.run(ffmpeg_output_file=filename_path, progress_handler=handle_progress_info, **kwargs)     

    emit_signal(kwargs, 'progress_set', [idx, 100])  
    emit_signal(kwargs, 'checkbox_set', [idx, False])  
    emit_signal(kwargs, 'resize_window') 
              
    return (filename_path, False)


def download_track(client: SoundCloud, track: BasicTrack, playlist_info=None, exit_on_fail=True, **kwargs):
    """
    Downloads a track
    """      
    try:
        idx = kwargs.get('track_number')
        title = track.title
        title = title.encode("utf-8", "ignore").decode("utf-8")   

        # Not streamable
        if not track.streamable:
            logger.warning("Track is not streamable.")

        # Geoblocked track
        if track.policy == "BLOCK":
            raise SoundCloudException(f"{title} is not available in your location.")

        # Downloadable track
        filename = None
        emit_signal(kwargs, 'messagebox_set', [idx, 'Downloading...'])     
        emit_signal(kwargs, 'resize_window')  
        if (
            track.downloadable
            and not kwargs.get("onlymp3")
            and not kwargs.get("no_original")
        ):
            mode = 'original_file'
            ret = fetch_original_file(track, playlist_info, client, **kwargs)   
            filename = ret.get('filename')
            kwargs = ret.get('kwargs') if ret.get('kwargs') is not None else kwargs         

        if filename is None:
            if kwargs.get("only_original"):
                raise SoundCloudException(f'Track "{track.permalink_url}" does not have original file available. Not downloading.')
            mode = 'hls'
            ret = fetch_hls(track, playlist_info, **kwargs) 
            filename = ret.get('filename')
            kwargs = ret.get('kwargs') if ret.get('kwargs') is not None else kwargs         

        # Metadata correction
        metadata = kwargs.get('metadata')
        fh = FilenameHandler(              
            dir=kwargs.get('path'), 
            cfg=kwargs.get('cfg'),         
            filename=filename,
            track_number=idx,
            album=metadata.get('album'),
            metadata_entries=metadata['trackinfo'][idx],
            man_metadata_entries=kwargs.get('man_metadata_entries')          
        )              
        ret = fh.getOutput()        
        filename, dir, metadata = ret.get('filename'), ret.get('dir'), ret.get('metadata')   
        track.title, track.user.username = ret.get('title'), ret.get('artist')
            
        try:
            os.chdir(dir)
        except OSError:
            raise SoundCloudException('"os.chdir" failed.')
        logger.debug("Downloading to " + os.getcwd() + ".")  
                
        if mode == 'original_file':
            filename, is_already_downloaded = download_original_file(track, filename, playlist_info, **kwargs)
        elif mode == 'hls':
            filename, is_already_downloaded = download_hls(track, filename, playlist_info, client, **kwargs)
        else:
            raise ValueError('Value error, expected "hls" or "original_file".')
        
        if is_already_downloaded:
            emit_signal(kwargs, 'messagebox_set', [idx, f'Track already downloaded: "{filename}".'])                        
            return               
        
        if kwargs.get("remove"):
            fileToKeep.append(filename)          

        # If file does not exist an error occurred
        if not os.path.isfile(filename):
            stem = Path(filename).stem     
            raise SoundCloudException(f'An error occurred downloading "{stem}".')     
        
        emit_signal(kwargs, 'messagebox_set', [idx, 'Setting tags...'])                   
        emit_signal(kwargs, 'resize_window')   
                       
        # Try to set the metadata
        if (
            filename.endswith(".mp3")
            or filename.endswith(".flac")
            or filename.endswith(".m4a")
            or filename.endswith(".wav")
        ):
            try:          
                set_metadata(track, filename, playlist_info, **kwargs)
            except Exception:
                try:
                    os.remove(filename)   
                except OSError:
                    raise SoundCloudException('Could not remove temp file.')            
                raise SoundCloudException("Error trying to set the tags.")
        else:
            logger.error("This type of audio doesn't support tagging.")

        # Try to change the real creation date
        filetime = int(time.mktime(track.created_at.timetuple()))
        try_utime(filename, filetime)
        
        logger.info(f"'{filename}' downloaded.")      

        emit_signal(kwargs, 'messagebox_set', [kwargs.get('track_number'), f'Downloaded "{track.title}".'])   
        emit_signal(kwargs, 'resize_window') 

    except SoundCloudException as err:
        logger.error(err)
        if exit_on_fail:
            sys.exit(1)


def can_convert(filename):
    ext = os.path.splitext(filename)[1]
    return "wav" in ext or "aif" in ext


def already_downloaded(track: BasicTrack, title: str, filename: str, **kwargs):
    """
    Returns True if the file has already been downloaded
    """
    already_downloaded = False

    if os.path.isfile(filename):
        already_downloaded = True
        if kwargs.get("overwrite"):
            os.remove(filename)
            already_downloaded = False
  
    if already_downloaded:
        if kwargs.get("c") or kwargs.get("remove") or kwargs.get("force_metadata"):
            return True
        else:
            logger.error(f'Track "{title}" already exists!')
            raise SoundCloudException(f'Track "{title}" already exists.')
            
    return False


def set_metadata(track: BasicTrack, filename: str, playlist_info=None, **kwargs):
    """
    Sets the mp3 file metadata using the Python module Mutagen
    """
    logger.info("Setting tags.")
    artwork_url = track.artwork_url
    user = track.user
    if not artwork_url:
        artwork_url = user.avatar_url
    response = None
    if kwargs.get("original_art"):
        new_artwork_url = artwork_url.replace("large", "original")
        try:
            response = requests.get(new_artwork_url, stream=True)
            if response.headers["Content-Type"] not in (
                "image/png",
                "image/jpeg",
                "image/jpg",
            ):
                response = None
        except Exception:
            pass
    if response is None:
        new_artwork_url = artwork_url.replace("large", "t500x500")
        response = requests.get(new_artwork_url, stream=True)
        if response.headers["Content-Type"] not in (
            "image/png",
            "image/jpeg",
            "image/jpg",
        ):
            response = None
    if response is None:
        logger.error(f"Could not get cover art at {new_artwork_url}")
    with tempfile.NamedTemporaryFile() as out_file:
        if response:
            shutil.copyfileobj(response.raw, out_file)
            out_file.seek(0)

        track.date = track.created_at.strftime("%Y-%m-%d %H::%M::%S")

        track.artist = user.username
        if kwargs.get("extract_artist"):
            for dash in [" - ", " − ", " – ", " — ", " ― "]:
                if dash in track.title:
                    artist_title = track.title.split(dash)
                    track.artist = artist_title[0].strip()
                    track.title = artist_title[1].strip()
                    break
        mutagen_file = mutagen.File(filename)
        mutagen_file.delete()
        if track.description:
            if mutagen_file.__class__ == mutagen.flac.FLAC:
                mutagen_file["description"] = track.description
            elif mutagen_file.__class__ == mutagen.mp3.MP3 or mutagen_file.__class__ == mutagen.wave.WAVE:
                mutagen_file["COMM"] = mutagen.id3.COMM(
                    encoding=3, lang="ENG", text=track.description
                )
            elif mutagen_file.__class__ == mutagen.mp4.MP4:
                mutagen_file["\xa9cmt"] = track.description
        if response:
            if mutagen_file.__class__ == mutagen.flac.FLAC:
                p = mutagen.flac.Picture()
                p.data = out_file.read()
                p.mime = "image/jpeg"
                p.type = mutagen.id3.PictureType.COVER_FRONT
                mutagen_file.add_picture(p)
            elif mutagen_file.__class__ == mutagen.mp3.MP3 or mutagen_file.__class__ == mutagen.wave.WAVE:
                mutagen_file["APIC"] = mutagen.id3.APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=out_file.read(),
                )
            elif mutagen_file.__class__ == mutagen.mp4.MP4:
                mutagen_file["covr"] = [mutagen.mp4.MP4Cover(out_file.read())]

        if mutagen_file.__class__ == mutagen.wave.WAVE:
            mutagen_file["TIT2"] = mutagen.id3.TIT2(encoding=3, text=track.title)
            mutagen_file["TPE1"] = mutagen.id3.TPE1(encoding=3, text=track.artist)
            if track.genre:
                mutagen_file["TCON"] = mutagen.id3.TCON(encoding=3, text=track.genre)
            if track.permalink_url:
                mutagen_file["WOAS"] = mutagen.id3.WOAS(url=track.permalink_url)
            if track.date:
                mutagen_file["TDAT"] = mutagen.id3.TDAT(encoding=3, text=track.date)
            if playlist_info:
                if not kwargs.get("no_album_tag"):
                    mutagen_file["TALB"] = mutagen.id3.TALB(encoding=3, text=playlist_info["title"])
                mutagen_file["TRCK"] = mutagen.id3.TRCK(encoding=3, text=str(playlist_info["tracknumber"]))
            mutagen_file.save()
        else:
            mutagen_file.save()
            audio = mutagen.File(filename, easy=True)
            audio["title"] = track.title
            audio["artist"] = track.artist
            if track.genre:
                audio["genre"] = track.genre
            if track.permalink_url:
                audio["website"] = track.permalink_url
            if track.date:
                audio["date"] = track.date
            if playlist_info:
                if not kwargs.get("no_album_tag"):
                    audio["album"] = playlist_info["title"]
                audio["tracknumber"] = str(playlist_info["tracknumber"])

            audio.save()

def limit_filename_length(name: str, ext: str, max_bytes=255):
    while len(name.encode("utf-8")) + len(ext.encode("utf-8")) > max_bytes:
        name = name[:-1]
    return name + ext

def is_ffmpeg_available():
    """
    Returns true if ffmpeg is available in the operating system
    """
    return shutil.which("ffmpeg") is not None

def size_in_bytes(insize):
    """
    Returns the size in bytes from strings such as '5 mb' into 5242880.

    >>> size_in_bytes('1m')
    1048576
    >>> size_in_bytes('1.5m')
    1572864
    >>> size_in_bytes('2g')
    2147483648
    >>> size_in_bytes(None)
    Traceback (most recent call last):
        raise ValueError('no string specified')
    ValueError: no string specified
    >>> size_in_bytes('')
    Traceback (most recent call last):
        raise ValueError('no string specified')
    ValueError: no string specified
    """
    if insize is None or insize.strip() == '':
        raise ValueError('no string specified')

    units = {
        'k': 1024,
        'm': 1024 ** 2,
        'g': 1024 ** 3,
        't': 1024 ** 4,
        'p': 1024 ** 5,
    }
    match = re.search('^\s*([0-9\.]+)\s*([kmgtp])?', insize, re.I)

    if match is None:
        raise ValueError('match not found')

    size, unit = match.groups()

    if size:
        size = float(size)

    if unit:
        size = size * units[unit.lower().strip()]

    return int(size)
