import os
from qgis.core import QgsGPSDetector

import utils

from uifiles import settings_widget, settings_base
from utils import settings, curdir

class SettingsWidget(settings_widget, settings_base):            
    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.fullScreenCheck.stateChanged.connect(self.fullScreenCheck_stateChanged)
        self.gpsPortCombo.currentIndexChanged.connect(self.gpsPortCombo_currentIndexChanged)
        
    def fullScreenCheck_stateChanged(self, state):
        utils.log("fullscreen changed")
        state = bool(state)
        settings["fullscreen"] = state
        utils.saveSettings()
        
    def gpsPortCombo_currentIndexChanged(self, index):
        port = self.gpsPortCombo.itemData(index)
        settings["gpsport"] = port
        utils.saveSettings()
         
    def readSettings(self):
        fullscreen = settings.get("fullscreen", False)
        gpsport = settings.get("gpsport", 'scan')
        self.fullScreenCheck.setChecked(fullscreen)
        gpsindex = self.gpsPortCombo.findData(gpsport)
        
        self.blockSignals(True)
        if gpsindex == -1:
            self.gpsPortCombo.addItem(gpsport)
        else:
            self.gpsPortCombo.setCurrentIndex(gpsindex)
        self.blockSignals(False)
        
    def populateControls(self):
        # First item is the local gpsd so skip that. 
        ports = QgsGPSDetector.availablePorts()[1:]
        self.blockSignals(True)
        self.gpsPortCombo.addItem('scan', 'scan')
        for port, name in ports:
            self.gpsPortCombo.addItem(name, port)
        self.blockSignals(False)   
        # Read version
        try:
            with open(os.path.join(curdir, 'version.txt')) as f:
                version = f.read().strip()
        except IOError:
            version = 'unknown'
            
        self.versionLabel.setText(version)