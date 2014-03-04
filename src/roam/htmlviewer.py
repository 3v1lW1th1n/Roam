import os
from types import NoneType
from string import Template

from PyQt4.QtCore import QUrl, QByteArray, QDate, QDateTime, QTime
from PyQt4.QtGui import (QDialog, QWidget, QGridLayout, QPixmap,
                         QImageReader, QDesktopServices)
from PyQt4.QtWebKit import QWebView, QWebPage

from roam import utils

import templates

images = {}
supportedformats = []

def image_handler(key, value, **kwargs):
    imageblock = '''
                    <a href="{}" class="thumbnail">
                      <img width="200" height="200" src="{}"\>
                    </a>'''

    imagetype = kwargs.get('imagetype', 'base64' )
    images[key] = (value, imagetype)
    if imagetype == 'base64':
        src = 'data:image/png;base64,${}'.format(value.toBase64())
    else:
        src = value
    return imageblock.format(key, src)


def default_handler(key, value):
    return value


def string_handler(key, value):
    if not supportedformats:
        global supportedformats
        supportedformats = [f.data() for f in QImageReader.supportedImageFormats()]

    base64 = QByteArray.fromBase64(value)
    image = QPixmap()
    loaded = image.loadFromData(base64)
    if loaded:
        return image_handler(key, base64, imagetype='base64')
    _, extension = os.path.splitext(value)
    if extension[1:] in supportedformats:
        return image_handler(key, value, imagetype='file')

    return value


def date_handler(key, value):
    return value.toString()


def none_handler(key, value):
    return ''


def updateTemplate(data, template):
    data = dict(data)
    for key, value in data.iteritems():
        handler = blocks.get(type(value), default_handler)
        block = handler(key, value)
        data[key] = block
    return template.safe_substitute(**data)


blocks = {QByteArray: image_handler,
          QDate: date_handler,
          QDateTime: date_handler,
          QTime: date_handler,
          str: string_handler,
          unicode: string_handler,
          NoneType: none_handler}


def showHTMLReport(title, html, data={}, parent=None):
    dialog = HtmlViewerDialog(title)
    dialog.showHTML(html, data)
    dialog.exec_()


class HtmlViewerDialog(QDialog):
    def __init__(self, title, parent=None):
        super(HtmlViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.htmlviewer = HtmlViewerWidget(self)
        self.layout().addWidget(self.htmlviewer)

    def showHTML(self, html, data):
        self.htmlviewer.showHTML(html, data)


class HtmlViewerWidget(QWidget):
    def __init__(self, parent):
        super(HtmlViewerWidget, self).__init__(parent)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.view = QWebView()
        self.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.layout().addWidget(self.view)

    def showHTML(self, html, data):
        if os.path.isfile(html):
            html = open(html).read()

        html = html.replace(r'\n', '<br>')
        templte = Template(html)
        html = updateTemplate(data, templte)
        self.view.setHtml(html, templates.baseurl)

