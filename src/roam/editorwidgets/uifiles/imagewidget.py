import os

from PyQt4.QtGui import (QLabel, QDialog, QFileDialog,
                        QPixmap, QGridLayout, QLayout,
                        QWidget)
from PyQt4.QtCore import (QByteArray, QBuffer,
                        QIODevice, QEvent, QObject, pyqtSignal)

from roam.editorwidgets.uifiles import images_rc, ui_imagewidget
import roam.utils


class QMapImageWidget(ui_imagewidget.Ui_imagewidget, QWidget):
    openRequest = pyqtSignal(QPixmap)
    imageloaded = pyqtSignal()
    imageremoved = pyqtSignal()

    def __init__(self, parent=None):
        super(QMapImageWidget, self).__init__(parent)
        self.setupUi(self)

        self.setStyleSheet(":hover {background-color: #dddddd;}")
        self.selectbutton.clicked.connect(self.selectImage)
        self.deletebutton.clicked.connect(self.removeImage)
        self.image.mouseReleaseEvent = self.imageClick
        self.installEventFilter(self)
        self.removeImage()
        self.defaultlocation = ''

    def eventFilter(self, object, event):
        """ Handle mouse click events for disabled widget state """
        if event.type() == QEvent.MouseButtonRelease and not self.isDefault:
            self.openRequest.emit(self.image.pixmap())

        return super(QMapImageWidget, self).eventFilter(object, event)

    def selectImage(self):
        # Show the file picker
        defaultlocation = os.path.expandvars(self.defaultlocation)
        print defaultlocation
        image = QFileDialog.getOpenFileName(self, "Select Image", defaultlocation)
        roam.utils.debug(image)
        if image is None or not image:
            return

        pix = QPixmap(image)
        self.loadFromPixMap(pix)

    def removeImage(self):
        pix = QPixmap(":/images/images/add.png")
        self.loadFromPixMap(pix)
        self.image.setScaledContents(False)
        self.imageremoved.emit()
        self.isDefault = True

    def imageClick(self, event):
        if self.isDefault:
            self.selectImage()
        else:
            self.openRequest.emit(self.image.pixmap())

    def loadFromPixMap(self, pixmap):
        if pixmap.isNull():
            roam.utils.debug("Image is null")
            self.removeImage()
            return

        self.image.setScaledContents(True)
        self.image.setPixmap(pixmap)
        self.isDefault = False

    def loadImage(self, data):
        """
            Load the image into the widget using a bytearray

            An empty picture will result in the default placeholder
            image.
        """
        if data is None or not data:
            self.removeImage()
            return

        pix = QPixmap()
        r = pix.loadFromData(data, 'JPG')
        self.image.setScaledContents(True)
        self.image.setPixmap(pix)
        self.isDefault = False

    @property
    def isDefault(self):
        return self._isdefault

    @isDefault.setter
    def isDefault(self, value):
        self._isdefault = value
        self.selectbutton.setVisible(not value)
        self.deletebutton.setVisible(not value)
        if value:
            self.imageloaded.emit()
        else:
            self.imageremoved.emit()

    def getImage(self):
        """ Return the loaded image """
        if self.isDefault:
            return None

        pix = self.image.pixmap()
        by = QByteArray()
        buf = QBuffer(by)
        buf.open(QIODevice.WriteOnly)
        pix.save(buf, "JPG")
        return by
