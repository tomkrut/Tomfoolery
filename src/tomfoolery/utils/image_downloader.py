#! /usr/bin/env python
from PyQt6.QtCore import pyqtSignal, QObject, QUrl
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from functools import cached_property
import os

class ThumbnailHandler:

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.scraper = None
        self.res = None

    def setPixmap(self, pixmap, label):       
        label.setPixmap(
            pixmap.scaled(
            self.horizontalLayout_3.maximumSize().height(),
            self.horizontalLayout_3.maximumSize().height()
            )
        )                

    def handleFinished(self, image, label):
        pixmap = QPixmap.fromImage(image)
        self.setPixmap(pixmap, label)

    def resetThumbnail(self, label):
        assert self.res is not None
        pixmap = QPixmap(os.path.join(self.res, 'missing_image.png'))
        self.setPixmap(pixmap, label)

    def getThumbnail(self, label):  
        assert self.scraper is not None
        if hasattr(self.scraper, 'thumbnail_url'):            
            url = QUrl.fromUserInput(self.scraper.thumbnail_url)
            self.imageDownloader.start_download(url) 
        else:
            self.resetThumbnail(label)

class ImageDownloader(QObject):

    download_finished = pyqtSignal(QImage, QObject)

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label
        self.manager.finished.connect(self.handle_finished)

    @cached_property
    def manager(self):
        return QNetworkAccessManager()

    def start_download(self, url):
        self.manager.get(QNetworkRequest(url))

    def handle_finished(self, reply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            print("error: ", reply.errorString())
            return
        image = QImage()
        image.loadFromData(reply.readAll())
        self.download_finished.emit(image, self.label) 
