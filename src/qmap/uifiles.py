import os

from PyQt4 import uic

def create_ui(filename):
    basepath = os.path.dirname(__file__)
    uipath = os.path.join(basepath, filename)
    return uic.loadUiType(uipath)

project_widget, project_base = create_ui('ui_projectwidget.ui')
modules_widget, modules_base = create_ui('ui_listmodules.ui')
features_widget, features_base = create_ui('ui_listfeatures.ui')
helpviewer_widget, helpviewer_base = create_ui('ui_helpviewer.ui')
helppage_widget, helppage_base = create_ui('ui_helppage.ui')
datepicker_widget, datepicker_base = create_ui('ui_datatimerpicker.ui')
