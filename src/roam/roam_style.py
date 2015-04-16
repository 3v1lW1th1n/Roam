from PyQt4.QtGui import QDesktopWidget
from string import Template

def width():
    widget = QDesktopWidget()
    rec = widget.availableGeometry(widget.primaryScreen())
    return rec.width()

def height():
    widget = QDesktopWidget()
    rec = widget.availableGeometry(widget.primaryScreen())
    return rec.height()

def font():
    if width() == 1024 and height() == 728:
        return 'font: 9pt "Segoe UI" ;'
    else:
        return 'font: 14pt "Segoe UI" ;'

def iconsize():
    iconsize = 48
    if width() == 1024 and height() == 728:
        iconsize = 24
    return iconsize

def appstyle():
    return Template("""
    * {

        $FONT
    }

    QToolButton {
        padding: 4px;
        color: #4f4f4f;
    }

    QToolButton:hover {
        padding: 4px;
        background-color: rgb(211, 228, 255);
    }

    QStatusBar {
        background: white;
        border: none;
        $FONT
    }


    QStatusBar::item {
                border: none;
    }

    QCheckBox {
        color: #4f4f4f;
    }

    QCheckBox::indicator {
        width: 40px;
        height: 40px;
    }

    QLabel {
        color: #4f4f4f;
    }

    QLabel[projectlabel="true"] {
        background-color: rgba(255, 255, 255, 0);
    }

    QLabel[headerlabel="true"] {
        font: 75 17pt "Segoe UI";
    }

    QComboBox {
        border: 1px solid #d3d3d3;
    }

    QComboBox::drop-down {
        width: 30px;
    }

    QWidget QStackedWidget {
        background-color: white;
    }

    QScollArea, QScollArea * {
        background-color: white;
    }

    QFrame {
        background-color: rgb(255,255,255);
    }


    QFrame#infoframe {
        background-color: rgb(255,255,255, 220);
    }

    QListWidget:item:hover {
        background-color: #5b93c2;
    }

    QListWidget#layerList {
        font: 12pt "Segoe UI";
        background-color: rgb(149,150,145, 220);
    }

    QListWidget#layerList::item {
        color: white;
        border-bottom: 1px solid black;
        padding: 4px;
    }

    QListWidget[large="true"]::item {
        font: 12pt "Segoe UI";
        padding: 8px;
    }

    QListWidget#layerList::item::selected {
        background-color: #5b93c2;
    }

    QPushButton {
        border: 1px solid #e1e1e1;
        padding: 6px;
        color: #4f4f4f;
    }

    QPushButton:checked  {
        border: 3px solid rgb(137, 175, 255);
        background-color: rgb(211, 228, 255);
    }

    QPushButton:hover {
        background-color: rgb(211, 228, 255);
    }

    QToolButton[action="true"] {
        border: 1px solid #e1e1e1;
        padding: 6px;
        color: #4f4f4f;
    }

    QWidget#featureformarea {
        background-color: white;
    }

    QWidget#helpframe {
        font: 20px "Segoe UI" ;
        background-color: rgb(255,255,255, 220);
    }

    QDialog {
        color: #4f4f4f;
        font: 12pt "Segoe UI" ;
        background-color: rgb(255, 255, 255);
    }

    QPushButton#deleteButton {
        background-color: rgb(255, 134, 125);
        color: white;
        font: 75 17pt "Segoe UI";
    }

    QLabel#headerlabel {
        color: rgb(255, 134, 125);
        font: 75 17pt "Segoe UI";
    }

    QTreeWidget#synctree {
        font: 20pt "Segoe UI";
    }

    QTreeWidget#synctree::item {
        padding-top: 4px;
    }

    QScrollBar:vertical {
    border: 2px solid grey;
    background: rgba(80, 80, 80, 20);
    width: 40px;
    margin: 22px 0 22px 0;
    }
    QScrollBar::handle:vertical {
    background: #678fb2;
    min-height: 20px;
    }
    QScrollBar::add-line:vertical {
    border: 2px solid grey;
    background: rgba(80, 80, 80, 20);
    height: 20px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
    }

    QScrollBar::sub-line:vertical {
    border: 2px solid grey;
    background: rgba(80, 80, 80, 20);
    height: 20px;
    subcontrol-position: top;
    subcontrol-origin: margin;
    }
    """).substitute(FONT=font())


def menubarstyle():
    return Template("""
    QToolBar#menutoolbar {
        $FONT
        background-color: rgb(85,85,85);
        padding: 0px;
    }

    QToolButton {
        color: rgb(221,221,219);
    }

    QToolButton:hover {
        color: rgb(0,0,0);
    }

    QToolButton:checked {
        color: rgb(91,147,194);
        padding-right: 0px;
        background-color: rgb(240, 240, 240);
    }
    """).substitute(FONT=font())

def featureform():
    return Template("""
    * {
        $FONT 
    }

    QLabel[projectlabel="true"] {
        background-color: rgba(255, 255, 255, 0);
    }

    QLabel[headerlabel="true"] {
        $FONT
    }

    QPushButton {
        border: 1px solid rgb(137, 175, 255);
        background-color: rgb(203, 203, 203, 50);
        padding: 6px;
        color: #4f4f4f;
    }

    QScrollBar:vertical {
    border: 2px solid grey;
    background: rgba(80, 80, 80, 20);
    width: 40px;
    margin: 22px 0 22px 0;
    }
    QScrollBar::handle:vertical {
    background: #678fb2;
    min-height: 20px;
    }
    QScrollBar::add-line:vertical {
    border: 2px solid grey;
    background: rgba(80, 80, 80, 20);
    height: 20px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
    }

    QScrollBar::sub-line:vertical {
    border: 2px solid grey;
    background: rgba(80, 80, 80, 20);
    height: 20px;
    subcontrol-position: top;
    subcontrol-origin: margin;
    }

    QPushButton:checked  {
        border: 3px solid rgb(137, 175, 255);
        background-color: rgb(211, 228, 255);
    }

    QPushButton:hover {
        background-color: rgb(211, 228, 255);
    }

    QToolButton {
        border: 1px solid #e1e1e1;
        padding: 6px;
        color: #4f4f4f;
    }

    QToolButton:checked  {
        border: 3px solid rgb(137, 175, 255);
        background-color: rgb(211, 228, 255);
    }
    """).substitute(FONT=font())

