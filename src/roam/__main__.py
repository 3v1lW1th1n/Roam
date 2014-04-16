"""
Main entry file.  This file creates and setups the main window and then hands control over to that.

The MainWindow object handles everything from there on in.
"""

import os
import sys

import logging
import time
import roam.environ

from functools import partial

roamapp = roam.environ.setup(sys.argv)

from qgis.core import QgsApplication, QgsProviderRegistry

from PyQt4 import uic
from PyQt4.QtGui import QApplication, QFont, QImageReader, QImageWriter
from PyQt4.QtCore import QDir, QCoreApplication, QLibrary
import PyQt4.QtSql

uic.uiparser.logger.setLevel(logging.INFO)
uic.properties.logger.setLevel(logging.INFO)

# We have to start this here or else the image drivers don't load for some reason
app = QgsApplication(sys.argv, True)
locale = PyQt4.QtCore.QLocale.system().name()

translationFile = os.path.join(roamapp.i18npath, '{0}.qm'.format(locale))

translator = PyQt4.QtCore.QTranslator()
translator.load(translationFile, "i18n")
app.installTranslator(translator)

import roam
import roam.yaml as yaml
import roam.utils
from roam.mainwindow import MainWindow

def excepthook(errorhandler, exctype, value, traceback):
    errorhandler(exctype, value, traceback)
    roam.utils.error("Uncaught exception", exc_info=(exctype, value, traceback))

start = time.time()
roam.utils.info("Loading Roam")


roam.utils.info("Attempted to load translation file: " + translationFile)


QgsApplication.setPrefixPath(roamapp.prefixpath, True)
QgsApplication.initQgis()

# Fake this module to maintain API.
import roam.api.featureform
sys.modules['roam.featureform'] = roam.api.featureform


roam.utils.info(QgsApplication.showSettings())
roam.utils.info(QgsProviderRegistry.instance().pluginList())
roam.utils.info(QImageReader.supportedImageFormats())
roam.utils.info(QImageWriter.supportedImageFormats())
roam.utils.info(QgsApplication.libraryPaths())

QApplication.setStyle("Plastique")
QApplication.setFont(QFont('Segoe UI'))

import roam.config
roam.config.load(roamapp.settingspath)

window = MainWindow()
app.setActiveWindow(window)
sys.excepthook = partial(excepthook, window.raiseerror)

projectpaths = roam.environ.projectpaths(sys.argv, roam.config.settings)
roam.utils.log("Loading projects from")
roam.utils.log(projectpaths)
projects = roam.project.getProjects(projectpaths)
window.loadprojects(projects)

window.actionProject.toggle()
window.viewprojects()
window.show()

roam.utils.info("Roam Loaded in {}".format(str(time.time() - start)))

app.exec_()
QgsApplication.exitQgis()
sys.exit()