# Tomfoolery

This is a *SoundCloud* / *Bandcamp* / *YouTube* downloader.

<img alt="demo.gif" src="https://raw.githubusercontent.com/tomkrut/tomfoolery/master/media/demo_small.gif">

## Installation

1. Get [ffmpeg](https://ffmpeg.org) binary and add it to your path manually, or  

   ```python
   conda install -c anaconda ffmpeg
   ```

2. Install tomfoolery.

   ```python
   pip install py-tomfoolery
   ```

### Usage

Enter following in the terminal.

```python
tomfoolery
```

### Configuration

- Menu *File*.
  - *Directories*.
    - *SoundCloud* downloads directory.
    - *Bandcamp* downloads directory.
    - *YouTube* downloads directory.
  - *Config*.
    - Organize saved songs in folders by the *artist*.
    - Organize saved songs in folders by the *album*.

### Metadata editing

*Artist* / *Title* can be edited by double-clicking a corresponding entry.  
The change will reflect both in the filename and in the file metadata.

## Acknowledgements

Tomfoolery is using bits and pieces from other repos, off the top of my head:

- [pytube/pytube](https://github.com/pytube/pytube),
- [Miserlou/SoundScrape](https://github.com/Miserlou/SoundScrape),
- [flyingrub/scdl](https://github.com/flyingrub/scdl),
- [better-ffmpeg-progress](https://github.com/CrypticSignal/better-ffmpeg-progress).
