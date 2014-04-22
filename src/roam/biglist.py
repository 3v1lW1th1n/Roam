from PyQt4.QtCore import QModelIndex, pyqtSignal, QSize
from PyQt4.QtGui import QWidget, QDialog

from roam.flickwidget import FlickCharm
from roam.ui.ui_list import Ui_BigList


class BigList(Ui_BigList, QWidget):
    itemselected = pyqtSignal(QModelIndex)
    closewidget = pyqtSignal()

    def __init__(self, parent=None):
        super(BigList, self).__init__(parent)
        self.setupUi(self)
        self.listView.clicked.connect(self.selected)
        self.closebutton.pressed.connect(self.closewidget.emit)
        self._index = None

        self.charm = FlickCharm()
        self.charm.activateOn(self.listView)

    def selected(self, index):
        self._index = index
        self.itemselected.emit(index)

    def setmodel(self, model):
        self.listView.setModel(model)

    def setlabel(self, fieldname):
        self.fieldnameLabel.setText(fieldname)

    def currentindex(self):
        return self._index

    def setcurrentindex(self, index):
        if index is None:
            index = QModelIndex()
        if isinstance(index, int):
            index = self.listView.model().index(index, 0)
        self.listView.setCurrentIndex(index)


