import os

from PyQt4.QtGui import QWidget, QDialog, QMainWindow

from qmap import resources_rc

from qmap import (ui_projectwidget, ui_listmodules, ui_listfeatures, ui_helpviewer,
                 ui_helppage, ui_datatimerpicker, ui_settings, ui_infodock, ui_mainwindow, ui_sync)

project_widget, project_base = ui_projectwidget.Ui_Form, QWidget
modules_widget, modules_base = ui_listmodules.Ui_ListModules, QWidget
features_widget, features_base = ui_listfeatures.Ui_ListFeatueForm, QDialog
helpviewer_widget, helpviewer_base = ui_helpviewer.Ui_HelpViewer, QDialog
helppage_widget, helppage_base = ui_helppage.Ui_apphelpwidget, QWidget
datepicker_widget, datepicker_base = ui_datatimerpicker.Ui_datatimerpicker, QWidget
settings_widget, settings_base = ui_settings.Ui_settingsWidget, QWidget
infodock_widget, infodock_base = ui_infodock.Ui_Form, QWidget
# drawing_widget, drawing_base = create_ui('ui_drawingpad.ui'
mainwindow_widget, mainwindow_base = ui_mainwindow.Ui_MainWindow, QMainWindow
sync_widget, sync_base = ui_sync.Ui_Form, QWidget

print mainwindow_base
