__author__ = 'Nathan.Woodrow'

import os
from PyQt4.QtCore import Qt, QUrl
from PyQt4.QtGui import QWidget, QPixmap, QStandardItem, QStandardItemModel, QIcon, QDesktopServices
from PyQt4.Qsci import QsciLexerSQL, QsciScintilla

from qgis.core import QgsDataSourceURI

from configmanager.ui.nodewidgets import ui_layersnode, ui_layernode, ui_infonode, ui_projectinfo, ui_formwidget
from configmanager.models import (CaptureLayersModel, LayerTypeFilter, QgsFieldModel, WidgetsModel,
                                  QgsLayerModel, CaptureLayerFilter, widgeticon)

import roam.editorwidgets
import configmanager.editorwidgets
from roam.api import FeatureForm


class WidgetBase(QWidget):
    def set_project(self, project, treenode):
        self.project = project
        self.treenode = treenode

    def write_config(self):
        """
        Write the config back to the project settings.
        """
        pass


readonlyvalues = [('Never', 'never'),
                  ('Always', 'always'),
                  ('When editing', 'editing'),
                  ('When inserting', 'insert')]


class FormWidget(ui_formwidget.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(FormWidget, self).__init__(parent)
        self.setupUi(self)
        self.form = None

        self.fieldsmodel = QgsFieldModel()
        self.widgetmodel = WidgetsModel()
        self.possiblewidgetsmodel = QStandardItemModel()
        self.formlayersmodel = QgsLayerModel(watchregistry=True)
        self.formlayers = CaptureLayerFilter()
        self.formlayers.setSourceModel(self.formlayersmodel)

        self.layerCombo.setModel(self.formlayers)
        self.widgetCombo.setModel(self.possiblewidgetsmodel)
        self.fieldList.setModel(self.fieldsmodel)

        self.widgetlist.setModel(self.widgetmodel)
        self.widgetlist.selectionModel().currentChanged.connect(self.updatecurrentwidget)
        self.widgetmodel.rowsRemoved.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.rowsInserted.connect(self.setwidgetconfigvisiable)
        self.widgetmodel.modelReset.connect(self.setwidgetconfigvisiable)

        self.addWidgetButton.pressed.connect(self.newwidget)
        self.removeWidgetButton.pressed.connect(self.removewidget)

        self.formfolderLabel.linkActivated.connect(self.openformfolder)
        self.expressionButton.clicked.connect(self.opendefaultexpression)

        self.fieldList.currentIndexChanged.connect(self.updatewidgetname)
        self.fieldwarninglabel.hide()
        self.formtab.currentChanged.connect(self.formtabchanged)

        for item, data in readonlyvalues:
            self.readonlyCombo.addItem(item, data)

        self.loadwidgettypes()

        self.formLabelText.textChanged.connect(self.form_name_changed)
        self.layerCombo.currentIndexChanged.connect(self.layer_updated)

    def layer_updated(self, index):
        index = self.formlayers.index(index, 0)
        layer = index.data(Qt.UserRole)
        self.updatefields(layer)

    def form_name_changed(self, text):
        self.form.settings['label'] = self.formLabelText.text()
        self.treenode.emitDataChanged()

    def updatewidgetname(self, index):
        # Only change the edit text on name field if it's not already set to something other then the
        # field name.
        field = self.fieldsmodel.index(index, 0).data(QgsFieldModel.FieldNameRole)
        currenttext = self.nameText.text()
        foundfield = self.fieldsmodel.findfield(currenttext)
        if foundfield:
            self.nameText.setText(field)

    def updatecurrentwidget(self):
        pass

    def opendefaultexpression(self):
        layer = self.form.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultvalueText.text().strip('[%').strip('%]').strip()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultvalueText.setText('[% {} %]'.format(dlg.expressionText()))

    def formtabchanged(self, index):
        def setformpreview(form):
            def removewidget():
                item = self.frame_2.layout().itemAt(0)
                if item and item.widget():
                    item.widget().setParent(None)

            removewidget()

            featureform = FeatureForm.from_form(form, form.settings, None, {})

            self.frame_2.layout().addWidget(featureform)

        if index == 1:
            self.form.settings['widgets'] = list(self.widgetmodel.widgets())
            setformpreview(self.form)

    def usedfields(self):
        """
        Return the list of fields that have been used by the the current form's widgets
        """
        for widget in self.currentform.widgets:
            yield widget['field']

    def openformfolder(self, url):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.form.folder))

    def loadwidgettypes(self):
        self.widgetCombo.blockSignals(True)
        for widgettype in roam.editorwidgets.core.supportedwidgets():
            try:
                configclass = configmanager.editorwidgets.widgetconfigs[widgettype]
            except KeyError:
                continue

            configwidget = configclass()
            item = QStandardItem(widgettype)
            item.setData(configwidget, Qt.UserRole)
            item.setData(widgettype, Qt.UserRole + 1)
            item.setIcon(QIcon(widgeticon(widgettype)))
            self.widgetCombo.model().appendRow(item)
            self.widgetstack.addWidget(configwidget)
        self.widgetCombo.blockSignals(False)

    def setwidgetconfigvisiable(self, *args):
        haswidgets = self.widgetmodel.rowCount() > 0
        self.widgetframe.setEnabled(haswidgets)

    def newwidget(self):
        """
        Create a new widget.  The default is a list.
        """
        widget = {}
        widget['widget'] = 'Text'
        # Grab the first field.
        widget['field'] = self.fieldsmodel.index(0, 0).data(QgsFieldModel.FieldNameRole)
        currentindex = self.widgetlist.currentIndex()
        currentitem = self.widgetmodel.itemFromIndex(currentindex)
        if currentitem and currentitem.iscontainor():
            parent = currentindex
        else:
            parent = currentindex.parent()
        index = self.widgetmodel.addwidget(widget, parent)
        self.widgetlist.setCurrentIndex(index)

    def removewidget(self):
        """
        Remove the selected widget from the widgets list
        """
        widget, index = self.currentuserwidget
        if index.isValid():
            self.widgetmodel.removeRow(index.row(), index.parent())

    def set_project(self, project, treenode):
        super(FormWidget, self).set_project(project, treenode)
        self.formlayers.setSelectLayers(self.project.selectlayers)
        form = self.treenode.form
        self.form = form
        self.setform(self.form)

    def updatefields(self, layer):
        """
        Update the UI with the fields for the selected layer.
        """
        self.fieldsmodel.setLayer(layer)

    def setform(self, form):
        """
        Update the UI with the currently selected form.
        """

        def getfirstlayer():
            index = self.formlayers.index(0, 0)
            layer = index.data(Qt.UserRole)
            layer = layer.name()
            return layer

        def loadwidgets(widget):
            """
            Load the widgets into widgets model
            """
            self.widgetmodel.clear()
            self.widgetmodel.loadwidgets(form.widgets)

        def findlayer(layername):
            index = self.formlayersmodel.findlayer(layername)
            index = self.formlayers.mapFromSource(index)
            layer = index.data(Qt.UserRole)
            return index, layer

        settings = form.settings
        label = form.label
        layername = settings.setdefault('layer', getfirstlayer())
        layerindex, layer = findlayer(layername)
        if not layer or not layerindex.isValid():
            return

        formtype = settings.setdefault('type', 'auto')
        widgets = settings.setdefault('widgets', [])

        self.formLabelText.setText(label)
        folderurl = "<a href='{path}'>{name}</a>".format(path=form.folder, name=os.path.basename(form.folder))
        self.formfolderLabel.setText(folderurl)
        self.layerCombo.setCurrentIndex(layerindex.row())
        self.updatefields(layer)

        index = self.formtypeCombo.findText(formtype)
        if index == -1:
            self.formtypeCombo.insertItem(0, formtype)
            self.formtypeCombo.setCurrentIndex(0)
        else:
            self.formtypeCombo.setCurrentIndex(index)

        loadwidgets(widgets)

        # Set the first widget
        index = self.widgetmodel.index(0, 0)
        if index.isValid():
            self.widgetlist.setCurrentIndex(index)
            self.updatecurrentwidget(index, None)

    def swapwidgetconfig(self, index):
        widgetconfig, _, _ = self.currentwidgetconfig
        defaultvalue = widgetconfig.defaultvalue
        self.defaultvalueText.setText(defaultvalue)

        self.updatewidgetconfig({})

    def updatecurrentwidget(self, index, _):
        """
        Update the UI with the config for the current selected widget.
        """
        if not index.isValid():
            return

        widget = index.data(Qt.UserRole)
        widgettype = widget['widget']
        field = widget['field']
        required = widget.setdefault('required', False)
        savevalue = widget.setdefault('rememberlastvalue', False)
        name = widget.setdefault('name', field)
        default = widget.setdefault('default', '')
        readonly = widget.setdefault('read-only-rules', [])
        hidden = widget.setdefault('hidden', False)

        try:
            data = readonly[0]
        except:
            data = 'never'

        index = self.readonlyCombo.findData(data)
        self.readonlyCombo.setCurrentIndex(index)

        if not isinstance(default, dict):
            self.defaultvalueText.setText(default)
            self.defaultvalueText.setEnabled(True)
            self.expressionButton.setEnabled(True)
        else:
            # TODO Handle the more advanced default values.
            self.defaultvalueText.setText("Advanced default set in config")
            self.defaultvalueText.setEnabled(False)
            self.expressionButton.setEnabled(False)

        self.nameText.setText(name)
        self.requiredCheck.setChecked(required)
        self.savevalueCheck.setChecked(savevalue)
        self.hiddenCheck.setChecked(hidden)

        if field is not None:
            index = self.fieldList.findData(field.lower(), QgsFieldModel.FieldNameRole)
            if index > -1:
                self.fieldList.setCurrentIndex(index)
            else:
                self.fieldList.setEditText(field)

        index = self.widgetCombo.findText(widgettype)
        if index > -1:
            self.widgetCombo.setCurrentIndex(index)

        self.updatewidgetconfig(config=widget.setdefault('config', {}))

    @property
    def currentuserwidget(self):
        """
        Return the selected user widget.
        """
        index = self.widgetlist.currentIndex()
        return index.data(Qt.UserRole), index

    @property
    def currentwidgetconfig(self):
        """
        Return the selected widget in the widget combo.
        """
        index = self.widgetCombo.currentIndex()
        index = self.possiblewidgetsmodel.index(index, 0)
        return index.data(Qt.UserRole), index, index.data(Qt.UserRole + 1)

    def updatewidgetconfig(self, config):
        widgetconfig, index, widgettype = self.currentwidgetconfig
        self.setconfigwidget(widgetconfig, config)

    def setconfigwidget(self, configwidget, config):
        """
        Set the active config widget.
        """

        try:
            configwidget.widgetdirty.disconnect(self._save_selectedwidget)
        except TypeError:
            pass

        self.widgetstack.setCurrentWidget(configwidget)
        configwidget.setconfig(config)

        configwidget.widgetdirty.connect(self._save_selectedwidget)

    def _save_selectedwidget(self, index):
        configwidget, index, widgettype = self.currentwidgetconfig
        widget, index = self.currentuserwidget
        if not widget:
            return

        widget['widget'] = widgettype
        widget['required'] = self.requiredCheck.isChecked()
        widget['rememberlastvalue'] = self.savevalueCheck.isChecked()
        widget['config'] = configwidget.getconfig()
        widget['name'] = self.nameText.text()
        widget['read-only-rules'] = [self.readonlyCombo.itemData(self.readonlyCombo.currentIndex())]
        widget['hidden'] = self.hiddenCheck.isChecked()

        row = self.fieldList.currentIndex()
        field = self.fieldsmodel.index(row, 0).data(QgsFieldModel.FieldNameRole)
        widget['field'] = field

        default = self.defaultvalueText.text()
        widget['default'] = default

        self.widgetmodel.setData(index, widget, Qt.UserRole)

    def _save_formtype(self, index):
        form = self.currentform

    def write_config(self):
        index = self.formlayers.index(self.layerCombo.currentIndex(), 0)
        layer = index.data(Qt.UserRole)
        self.form.settings['layer'] = layer.name()
        self.form.settings['type'] = self.formtypeCombo.currentText()
        self.form.settings['label'] = self.formLabelText.text()
        self.form.settings['widgets'] = list(self.widgetmodel.widgets())


class ProjectInfoWidget(ui_projectinfo.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(ProjectInfoWidget, self).__init__(parent)
        self.setupUi(self)
        self.titleText.textChanged.connect(self.updatetitle)

    def updatetitle(self, text):
        self.project.settings['title'] = text
        self.titleText.setText(text)

    def setsplash(self, splash):
        pixmap = QPixmap(splash)
        w = self.splashlabel.width()
        h = self.splashlabel.height()
        self.splashlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def set_project(self, project, treenode):
        super(ProjectInfoWidget, self).set_project(project, treenode)
        self.titleText.setText(project.name)
        self.descriptionText.setPlainText(project.description)
        self.setsplash(project.splash)
        self.versionText.setText(self.project.version)

    def write_config(self):
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()
        version = str(self.versionText.text())

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description
        settings['version'] = version


class InfoNode(ui_infonode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)
        self.Editor.setWrapMode(QsciScintilla.WrapWord)
        self.layer = None
        self.message_label.setVisible(False)

    def set_project(self, project, node):
        super(InfoNode, self).set_project(project, node)
        self.layer = node.layer
        # uri = QgsDataSourceURI(self.layer.dataProvider().dataSourceUri())
        source = self.layer.source()
        name = self.layer.dataProvider().name()
        if ".sqlite" in source or name == "mssql":
            self.setEnabled(True)
            self.message_label.setVisible(False)
        else:
            self.setEnabled(False)
            self.message_label.setVisible(True)
            return

        infoblock = self.project.info_query(node.key, node.layer.name())
        caption = infoblock.get("caption", node.text())
        query = infoblock.get("query", "")
        self.caption_edit.setText(caption)
        self.Editor.setText(query)

    def write_config(self):
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        if self.Editor.text():
            infoconfig[self.treenode.key] = {
                "caption": self.caption_edit.text(),
                "query": self.Editor.text(),
                "connection": "from_layer"
            }
        else:
            try:
                del infoconfig[self.treenode.key]
            except KeyError:
                pass

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayerWidget(ui_layernode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        super(LayerWidget, self).set_project(project, node)
        self.layer = node.layer
        tools = self.project.layer_tools(self.layer)
        delete = 'delete' in tools
        capture = 'capture' in tools
        edit_attr = 'edit_attributes' in tools
        edit_geom = 'edit_geom' in tools
        self.capture_check.setChecked(capture)
        self.delete_check.setChecked(delete)
        self.editattr_check.setChecked(edit_attr)
        self.editgeom_check.setChecked(edit_geom)
        self.datasouce_label.setText(self.layer.publicSource())

    def write_config(self):
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        capture = self.capture_check.isChecked()
        delete = self.delete_check.isChecked()
        editattr = self.editattr_check.isChecked()
        editgoem = self.editgeom_check.isChecked()
        tools = []
        if capture:
            tools.append("capture")
        if delete:
            tools.append("delete")
        if editattr:
            tools.append("edit_attributes")
        if editgoem:
            tools.append("edit_geom")

        infoconfig['tools'] = tools

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayersWidget(ui_layersnode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(LayersWidget, self).__init__(parent)
        self.setupUi(self)

        self.selectlayermodel = CaptureLayersModel(watchregistry=True)
        self.selectlayerfilter = LayerTypeFilter(geomtypes=[])
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)
        self.selectlayermodel.dataChanged.connect(self.selectlayerschanged)

        self.selectLayers.setModel(self.selectlayerfilter)

    def selectlayerschanged(self):
        self.treenode.refresh()

    def set_project(self, project, node):
        super(LayersWidget, self).set_project(project, node)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()

