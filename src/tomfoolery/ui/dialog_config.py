
from PyQt6 import QtCore, QtGui, QtWidgets
import os

class Ui_ConfigDialog(object):
    def setupUi(self, Dialog, resources=None):
        Dialog.setObjectName("Dialog")
        style_dir = os.path.join(resources, 'stylesheet.qss')  
        with open(style_dir, mode='r') as f:
            Dialog.setStyleSheet(f.read())   
        Dialog.resize(298, 129)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.checkBoxArtistFolder = QtWidgets.QCheckBox(parent=Dialog)
        self.checkBoxArtistFolder.setObjectName("checkBoxArtistFolder")
        self.verticalLayout.addWidget(self.checkBoxArtistFolder)
        self.checkBoxAlbumFolder = QtWidgets.QCheckBox(parent=Dialog)
        self.checkBoxAlbumFolder.setObjectName("checkBoxArtistFolder")
        self.verticalLayout.addWidget(self.checkBoxAlbumFolder)        
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Config"))
        self.checkBoxArtistFolder.setText(_translate("Dialog", "Organize saved songs in folders by artists."))
        self.checkBoxAlbumFolder.setText(_translate("Dialog", "Organize saved songs in folders by album."))   
