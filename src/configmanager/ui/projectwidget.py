import os
import copy
from PyQt4.Qsci import QsciLexerYAML

from PyQt4.QtCore import Qt, QDir, QFileInfo, pyqtSignal
from PyQt4.QtGui import QWidget, QStandardItemModel, QStandardItem, QIcon

from qgis.core import QgsProject, QgsMapLayerRegistry, QgsPalLabeling
from qgis.gui import QgsMapCanvas

from configmanager.ui.ui_projectwidget import Ui_Form
from configmanager.models import widgeticon, WidgetsModel, QgsLayerModel, QgsFieldModel, LayerFilter

import roam.projectparser
import roam.yaml
import roam


class ProjectWidget(Ui_Form, QWidget):
    projectsaved = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(ProjectWidget, self).__init__(parent)
        self.setupUi(self)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        self.canvas.setWheelAction(QgsMapCanvas.WheelZoomToMouseCursor)
        self.canvas.mapRenderer().setLabelingEngine(QgsPalLabeling())

        self.fieldsmodel = QgsFieldModel()
        self.formmodel = QStandardItemModel()
        self.widgetmodel = WidgetsModel()
        self.possiblewidgetsmodel = QStandardItemModel()
        self.layermodel = QgsLayerModel(watchregistry=True)
        self.selectlayermodel = QgsLayerModel(watchregistry=True, checkselect=True)
        self.selectlayermodel.layerchecked.connect(self._save_selectionlayers)

        self.layerfilter = LayerFilter()
        self.layerfilter.setSourceModel(self.layermodel)

        self.selectlayerfilter = LayerFilter()
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)

        self.layerCombo.setModel(self.layerfilter)
        self.widgetCombo.setModel(self.possiblewidgetsmodel)

        self.widgetlist.setModel(self.widgetmodel)
        self.widgetlist.selectionModel().currentChanged.connect(self.updatecurrentwidget)

        self.formlist.setModel(self.formmodel)
        self.formlist.selectionModel().currentChanged.connect(self.updatecurrentform)

        self.selectLayers.setModel(self.selectlayerfilter)

        self.fieldList.setModel(self.fieldsmodel)

        QgsProject.instance().readProject.connect(self._readproject)

        self.menuList.setCurrentRow(0)

        # Form settings
        self.formLabelText.textChanged.connect(self._save_formname)
        self.layerCombo.currentIndexChanged.connect(self._save_layer)
        self.formtypeCombo.currentIndexChanged.connect(self._save_formtype)

        #widget settings
        self.fieldList.currentIndexChanged.connect(self._save_field)
        self.fieldList.editTextChanged.connect(self._save_fieldname)

    @property
    def currentform(self):
        """
        Return the current selected form.
        """
        index = self.formlist.selectedIndexes()[0]
        return index.data(Qt.UserRole), index

    @property
    def currentwidget(self):
        index = self.widgetlist.selectedIndexes()[0]
        return index.data(Qt.UserRole), index

    def _save_field(self, index):
        self._save_fieldname(self.fieldList.currentText())

    def _save_fieldname(self, name):
        widget, index = self.currentwidget
        widget['field'] = name


    def _save_selectionlayers(self, index, layer, value):
        config = self.project.settings
        selectlayers = config.get('selectlayers', [])
        layername = unicode(layer.name())
        if value == Qt.Checked:
            selectlayers.append(layername)
        else:
            selectlayers.remove(layername)

        self.selectlayermodel.dataChanged.emit(index, index)

    def _save_formtype(self, index):
        formtype = self.formtypeCombo.currentText()
        form, index = self.currentform
        form.settings['type'] = formtype

    def _save_formname(self, text):
        """
        Save the form label to the settings file.
        """
        try:
            form, index = self.currentform
            form.settings['label'] = text
            self.formmodel.dataChanged.emit(index, index)
        except IndexError:
            return

    def _save_layer(self, index):
        """
        Save the selected layer to the settings file.
        """
        index = self.layerfilter.index(index, 0)
        layer = index.data(Qt.UserRole)
        if not layer:
            return

        form = self.currentform
        form.settings['layer'] = layer.name()
        self.formmodel.dataChanged.emit(index, index)
        self.updatefields(layer)

    def setproject(self, project, loadqgis=True):
        """
        Set the widgets active project.
        """
        self.startsettings = copy.deepcopy(project.settings)
        self.project = project
        self.selectlayermodel.config = project.settings
        if loadqgis:
            self.loadqgisproject(project, self.project.projectfile)
        else:
            self._updateforproject(self.project)

    def loadqgisproject(self, project, projectfile):
        self._closeqgisproject()
        QDir.setCurrent(os.path.dirname(project.projectfile))
        fileinfo = QFileInfo(project.projectfile)
        QgsProject.instance().read(fileinfo)

    def _closeqgisproject(self):
        self.canvas.freeze()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        self.canvas.clear()
        self.canvas.freeze(False)

    def _readproject(self, doc):
        parser = roam.projectparser.ProjectParser(doc)
        canvasnode = parser.canvasnode
        self.canvas.mapRenderer().readXML(canvasnode)
        self.canvaslayers = parser.canvaslayers()
        self.canvas.setLayerSet(self.canvaslayers)
        self.canvas.updateScale()
        self.canvas.freeze(False)
        self.canvas.refresh()
        self.layermodel.updateLayerList(QgsMapLayerRegistry.instance().mapLayers().values())
        self.selectlayermodel.updateLayerList(QgsMapLayerRegistry.instance().mapLayers().values())
        self._updateforproject(self.project)

    def _updateforproject(self, project):
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        self._loadforms(project.forms)

    def _loadforms(self, forms):
        self.formmodel.clear()
        for form in forms:
            item = QStandardItem(form.name)
            item.setEditable(False)
            item.setIcon(QIcon(form.icon))
            item.setData(form, Qt.UserRole)
            self.formmodel.appendRow(item)

        index = self.formmodel.index(0, 0)
        if index.isValid():
            self.formlist.setCurrentIndex(index)
            self.formframe.show()
        else:
            self.formframe.hide()

    def updatecurrentform(self, index, _):
        """
        Update the UI with the currently selected form.
        """
        form = index.data(Qt.UserRole)
        settings = form.settings
        label = settings['label']
        layer = settings['layer']
        version = settings.get('version', roam.__version__)
        formtype = settings.get('type', 'auto')
        widgets = settings.get('widgets', [])

        self.formLabelText.setText(label)
        self.versionText.setText(version)
        index = self.layermodel.findlayer(layer)
        index = self.layerfilter.mapFromSource(index)
        if index.isValid():
            self.layerCombo.blockSignals(True)
            self.layerCombo.setCurrentIndex(index.row())
            self.updatefields(index.data(Qt.UserRole))
            self.layerCombo.blockSignals(False)

        index = self.formtypeCombo.findText(formtype)
        if index == -1:
            self.formtypeCombo.insertItem(0, formtype)
            self.formtypeCombo.setCurrentIndex(0)
        else:
            self.formtypeCombo.setCurrentIndex(index)

        self.widgetmodel.loadwidgets(widgets)

        index = self.widgetmodel.index(0, 0)
        if index.isValid():
            self.widgetlist.setCurrentIndex(index)

    def updatefields(self, layer):
        """
        Update the UI with the fields for the selected layer.
        """
        self.fieldsmodel.setLayer(layer)

    def updatecurrentwidget(self, index, _):
        """
        Update the UI with the config for the current selected widget.
        """
        widget = index.data(Qt.UserRole)
        widgettype = widget['widget']
        field = widget['field']
        required = widget.get('required', False)

        self.requiredCheck.blockSignals(True)
        self.requiredCheck.setChecked(required)
        self.requiredCheck.blockSignals(False)

        self.fieldList.blockSignals(True)
        index = self.fieldList.findText(field)
        if index > -1:
            self.fieldList.setCurrentIndex(index)
        else:
            self.fieldList.setEditText(field)
        self.fieldList.blockSignals(False)

        index = self.possiblewidgetsmodel.findwidget(widgettype)
        if index.isValid():
            self.widgetCombo.setCurrentIndex(index.row())

    def _saveproject(self):
        """
        Save the project config to disk.
        """
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()
        version = str(self.versionText.text())

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description
        settings['version'] = version

        self.projectsaved.emit(self.startsettings, self.project)

        self.startsettings = copy.deepcopy(settings)


