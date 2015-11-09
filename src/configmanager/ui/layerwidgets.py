__author__ = 'Nathan.Woodrow'

import os
import shutil
from PyQt4.QtCore import Qt, QUrl, QVariant
from PyQt4.QtGui import (QWidget, QPixmap, QStandardItem, QStandardItemModel, QIcon, QDesktopServices, QMenu, QToolButton,
                         QFileDialog)
from PyQt4.Qsci import QsciLexerSQL, QsciScintilla

from qgis.core import QgsDataSourceURI
from qgis.gui import QgsExpressionBuilderDialog

from configmanager.ui.nodewidgets import (ui_layersnode, ui_layernode, ui_infonode, ui_projectinfo, ui_formwidget,
                                          ui_searchsnode, ui_searchnode)
from configmanager.models import (CaptureLayersModel, LayerTypeFilter, QgsFieldModel, WidgetsModel,
                                  QgsLayerModel, CaptureLayerFilter, widgeticon, SearchFieldsModel)

import roam.editorwidgets
import configmanager.editorwidgets
from roam.api import FeatureForm, utils
from roam.utils import log

from configmanager.utils import openqgis


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

        self.iconlabel.mouseReleaseEvent = self.change_icon

        self.fieldsmodel = QgsFieldModel()
        self.widgetmodel = WidgetsModel()
        self.possiblewidgetsmodel = QStandardItemModel()
        self.formlayersmodel = QgsLayerModel(watchregistry=True)
        self.formlayers = CaptureLayerFilter()
        self.formlayers.setSourceModel(self.formlayersmodel)

        self.layerCombo.setModel(self.formlayers)
        self.useablewidgets.setModel(self.possiblewidgetsmodel)
        self.fieldList.setModel(self.fieldsmodel)

        self.userwidgets.setModel(self.widgetmodel)
        self.userwidgets.selectionModel().currentChanged.connect(self.load_widget)
        self.widgetmodel.rowsRemoved.connect(self.set_widget_config_state)
        self.widgetmodel.rowsInserted.connect(self.set_widget_config_state)
        self.widgetmodel.modelReset.connect(self.set_widget_config_state)

        self.addWidgetButton.pressed.connect(self.newwidget)
        self.addSectionButton.pressed.connect(self.add_section)
        self.removeWidgetButton.pressed.connect(self.removewidget)

        self.formfolderLabel.linkActivated.connect(self.openformfolder)
        self.expressionButton.clicked.connect(self.opendefaultexpression)
        self.expressionButton_2.clicked.connect(self.opendefaultexpression_advanced)

        self.fieldList.currentIndexChanged.connect(self.updatewidgetname)
        self.fieldwarninglabel.hide()
        self.formtab.currentChanged.connect(self.formtabchanged)

        for item, data in readonlyvalues:
            self.readonlyCombo.addItem(item, data)

        self.loadwidgettypes()

        self.formLabelText.textChanged.connect(self.form_name_changed)
        self.newStyleCheck.stateChanged.connect(self.form_style_changed)
        self.layerCombo.currentIndexChanged.connect(self.layer_updated)

        self.fieldList.currentIndexChanged.connect(self._save_current_widget)
        self.nameText.textChanged.connect(self._save_current_widget)
        self.sectionNameText.textChanged.connect(self._save_current_widget)

        self.useablewidgets.currentIndexChanged.connect(self._save_current_widget)
        self.useablewidgets.currentIndexChanged.connect(self.swapwidgetconfig)

        menu = QMenu("Field Actions")
        action = menu.addAction("Auto add all fields")
        action.triggered.connect(self.auto_add_fields)

        self.addWidgetButton.setMenu(menu)
        self.addWidgetButton.setPopupMode(QToolButton.MenuButtonPopup)

        self.defaultLayerCombo.layerChanged.connect(self.defaultFieldCombo.setLayer)

    def change_icon(self, *args):
        """
        Change the icon for the form
        """
        icon = QFileDialog.getOpenFileName(self, "Select form icon image", filter="Images (*.png *.svg)")
        if not icon:
            return
        ext = os.path.splitext(icon)[1]
        shutil.copy(icon, os.path.join(self.form.folder, "icon" + ext))
        self.set_icon(self.form.icon)
        self.treenode.emitDataChanged()

    def set_icon(self, path):
        """
        Set the forms icon preview
        :param path: The path to icon.
        """
        pixmap = QPixmap(path)
        w = self.iconlabel.width()
        h = self.iconlabel.height()
        self.iconlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def layer_updated(self, index):
        """
        Called when the forms layer has changed.
        :param index: The index of the new layer.
        """
        if not self.selected_layer:
            return

        self.updatefields(self.selected_layer)

    def form_style_changed(self, newstyle):
        """
        Called when the form style has changed from label-above style to label-beside style.
        :param newstyle: True if to use the new label-above style forms.
        """
        self.form.settings['newstyle'] = newstyle
        self.treenode.emitDataChanged()

    def form_name_changed(self, text):
        """
        Called when the forms name has changed. Also updates the tree view to reflect the new name.
        :param text: The new text of the label.
        :return:
        """
        self.form.settings['label'] = text
        self.treenode.emitDataChanged()

    def updatewidgetname(self, index):
        """
        Update the widget name if the field has changed. Doesn't change the name if it has been user set already.
        :param index: index of the new field.
        """
        # Only change the edit text on name field if it's not already set to something other then the
        # field name.
        field = self.fieldsmodel.index(index, 0).data(QgsFieldModel.FieldNameRole)
        currenttext = self.nameText.text()
        foundfield = self.fieldsmodel.findfield(currenttext)
        if foundfield:
            self.nameText.setText(field)

    def opendefaultexpression_advanced(self):
        """
        Open the default expression builder for setting advanced default values based on QGIS Expressions.
        """
        layer = self.form.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultValueExpression.text()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultValueExpression.setText(dlg.expressionText())

    def opendefaultexpression(self):
        """
        Open the default expression builder for setting default values based on QGIS Expressions.
        """
        layer = self.form.QGISLayer
        dlg = QgsExpressionBuilderDialog(layer, "Create default value expression", self)
        text = self.defaultvalueText.text().strip('[%').strip('%]').strip()
        dlg.setExpressionText(text)
        if dlg.exec_():
            self.defaultvalueText.setText('[% {} %]'.format(dlg.expressionText()))

    def formtabchanged(self, index):
        """
        Called when the tab widget changes tab.  Normally used to control when to render the form preview on demand.
        :param index: The index of the new tab.
        """
        def setformpreview(form):
            """
            Create the form preview to show to the user.
            """
            item = self.frame_2.layout().itemAt(0)
            if item and item.widget():
                item.widget().setParent(None)

            featureform = FeatureForm.from_form(form, form.settings, None, {})
            from roam import defaults
            defaultwidgets = form.widgetswithdefaults()
            layer = form.QGISLayer
            try:
                values = {}
                feature = layer.getFeatures().next()
                defaultvalues = defaults.default_values(defaultwidgets, feature, layer)
                values.update(defaultvalues)
                featureform.bindvalues(values)
            except StopIteration:
                pass

            self.frame_2.layout().addWidget(featureform)

        # Don't generate the form preview if we are not on the preview tab.
        if index == 2:
            form = self.form.copy()
            form.settings['widgets'] = list(self.widgetmodel.widgets())
            setformpreview(form)

    def usedfields(self):
        """
        Return the list of fields that have been used by the the current form's widgets
        """
        widgets = self.widgetmodel.widgets()
        for widget in widgets:
            yield widget['field']

    def openformfolder(self, url):
        """
        Open the form folder using the OS file manager.
        :param url:
        :return:
        """
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.form.folder))

    def loadwidgettypes(self):
        """
        Load all supported widgets into the combobox for the form designer.
        :return:
        """
        self.useablewidgets.blockSignals(True)
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
            self.useablewidgets.model().appendRow(item)
            self.widgetstack.addWidget(configwidget)
        self.useablewidgets.blockSignals(False)

    def set_widget_config_state(self, *args):
        """
        Enable or disable the widget config section based on widget count
        :param args: Unused.
        :return:
        """
        haswidgets = self.widgetmodel.rowCount() > 0
        self.widgetConfigTabs.setEnabled(haswidgets)

    def add_section(self):
        """
        Add a new widget section into the form. Widget sections can be used to group
        widgets on the form together.
        """
        currentindex = self.userwidgets.currentIndex()
        widget = {"widget": "Section",
                  "name": "default"}
        index = self.widgetmodel.addwidget(widget, currentindex.parent())
        self.userwidgets.setCurrentIndex(index)

    def newwidget(self, field=None):
        """
        Create a new widget. Tries to match the field type to the right kind of widget as a best guess.
        """
        mapping = {QVariant.String: "Text",
                   QVariant.Int: "Number",
                   QVariant.Double: "Number(Double)",
                   QVariant.ByteArray: "Image",
                   QVariant.Date: "Date",
                   QVariant.DateTime: "Date"}
        widget = {}
        if not field:
            field = self.fieldsmodel.index(0, 0).data(Qt.UserRole)
            if not field:
                return
            widget['field'] = field.name()
        else:
            widget['field'] = field.name()

        try:
            widget['widget'] = mapping[field.type()]
        except KeyError:
            widget['widget'] = 'Text'
        # Grab the first field.

        widget['name'] = field.name().replace("_", " ").title()

        currentindex = self.userwidgets.currentIndex()
        currentitem = self.widgetmodel.itemFromIndex(currentindex)
        if currentitem and currentitem.iscontainor():
            parent = currentindex
        else:
            parent = currentindex.parent()
        index = self.widgetmodel.addwidget(widget, parent)
        self.userwidgets.setCurrentIndex(index)

    def auto_add_fields(self):
        """
        Auto add all fields to the form config. Any missing fields will be added.
        """
        used = list(self.usedfields())
        for field in self.selected_layer.pendingFields():
            if field.name() in used:
                continue

            self.newwidget(field)

    def removewidget(self):
        """
        Remove the selected widget from the widgets list
        """
        widget, index = self.currentuserwidget
        if index.isValid():
            self.widgetmodel.removeRow(index.row(), index.parent())

    def set_project(self, project, treenode):
        """
        Set the project for this widget also sets the form from the tree node.

        :note: This method is called from the parent node when the page and widget is loaded.
        :param project: The current project.j
        :param treenode: The current tree node.  Can be used to signel a update back to the tree for it to update it
        self.
        """
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
            """
            Get the first layer from the forms layer combo box
            """
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
            """
            Find the layer with the same name in the layer combobox widget
            """
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
        newstyleform = settings.setdefault('newstyle', False)
        self.set_icon(form.icon)

        self.formLabelText.setText(label)
        folderurl = "<a href='{path}'>{name}</a>".format(path=form.folder, name=os.path.basename(form.folder))
        self.formfolderLabel.setText(folderurl)
        self.newStyleCheck.setChecked(newstyleform)
        self.layerCombo.setCurrentIndex(layerindex.row())
        self.updatefields(layer)

        if formtype == "auto":
            formtype = "Auto Generated"
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
            self.userwidgets.setCurrentIndex(index)
            self.load_widget(index, None)

    def swapwidgetconfig(self, index):
        widgetconfig, _, _ = self.current_config_widget
        defaultvalue = widgetconfig.defaultvalue
        self.defaultvalueText.setText(defaultvalue)

        self.updatewidgetconfig({})

    def load_widget(self, index, last):
        """
        Update the UI with the config for the current selected widget.
        """
        self.fieldList.blockSignals(True)
        self.nameText.blockSignals(True)
        self.useablewidgets.blockSignals(True)

        if last:
            self._save_widget(last)

        widget = index.data(Qt.UserRole)
        if not widget:
            self.fieldList.blockSignals(False)
            self.nameText.blockSignals(False)
            self.useablewidgets.blockSignals(False)
            return

        widgettype = widget['widget']
        if widgettype == "Section":
            self.propertiesStack.setCurrentIndex(1)
            self.sectionNameText.blockSignals(True)
            name = widget['name']
            self.sectionNameText.setText(name)
            self.sectionNameText.blockSignals(False)
            return
        else:
            self.propertiesStack.setCurrentIndex(0)

        field = widget['field']
        required = widget.setdefault('required', False)
        savevalue = widget.setdefault('rememberlastvalue', False)
        name = widget.setdefault('name', field)
        default = widget.setdefault('default', '')
        readonly = widget.setdefault('read-only-rules', [])
        hidden = widget.setdefault('hidden', False)

        try:
            data = readonly[0]
        except IndexError:
            data = 'never'

        index = self.readonlyCombo.findData(data)
        self.readonlyCombo.setCurrentIndex(index)

        if not isinstance(default, dict):
            self.defaultTab.setCurrentIndex(0)
            self.defaultvalueText.setText(default)
        else:
            self.defaultTab.setCurrentIndex(1)
            layer = default['layer']
            # TODO Handle the case of many layer fall though with defaults
            # Not sure how to handle this in the UI just yet
            if isinstance(layer, list):
                layer = layer[0]

            if isinstance(layer, basestring):
                defaultfield = default['field']
                expression = default['expression']
                self.defaultValueExpression.setText(expression)
                layer = roam.api.utils.layer_by_name(layer)
                self.defaultLayerCombo.setLayer(layer)
                self.defaultFieldCombo.setLayer(layer)
                self.defaultFieldCombo.setField(defaultfield)

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

        index = self.useablewidgets.findText(widgettype)
        if index > -1:
            self.useablewidgets.setCurrentIndex(index)

        config = widget.get('config', {})
        self.updatewidgetconfig(config)

        self.fieldList.blockSignals(False)
        self.nameText.blockSignals(False)
        self.useablewidgets.blockSignals(False)

    @property
    def currentuserwidget(self):
        """
        Return the selected user widget.
        """
        index = self.userwidgets.currentIndex()
        return index.data(Qt.UserRole), index

    @property
    def current_config_widget(self):
        """
        Return the selected widget in the widget combo.
        """
        index = self.useablewidgets.currentIndex()
        index = self.possiblewidgetsmodel.index(index, 0)
        return index.data(Qt.UserRole), index, index.data(Qt.UserRole + 1)

    def updatewidgetconfig(self, config):
        configwidget, _, _ = self.current_config_widget
        self.setconfigwidget(configwidget, config)

    def setconfigwidget(self, configwidget, config):
        """
        Set the active config widget.
        """

        try:
            configwidget.widgetdirty.disconnect(self._save_current_widget)
        except TypeError:
            pass

        self.widgetstack.setCurrentWidget(configwidget)
        configwidget.setconfig(config)

        configwidget.widgetdirty.connect(self._save_current_widget)

    def _save_current_widget(self, *args):
        _, index = self.currentuserwidget
        self._save_widget(index)

    def _save_widget(self, index):
        widgetdata = self._get_widget_config()
        self.widgetmodel.setData(index, widgetdata, Qt.UserRole)

    def _get_default_config(self):
        if self.defaultTab.currentIndex() == 0:
            return self.defaultvalueText.text()
        else:
            default = {}
            default['layer'] = self.defaultLayerCombo.currentLayer().name()
            default['field'] = self.defaultFieldCombo.currentField()
            default['expression'] = self.defaultValueExpression.text()
            default['type'] = 'layer-value'
            return default

    def _get_widget_config(self):
        def current_field():
            row = self.fieldList.currentIndex()
            field = self.fieldsmodel.index(row, 0).data(QgsFieldModel.FieldNameRole)
            return field

        configwidget, _, widgettype = self.current_config_widget
        if self.propertiesStack.currentIndex() == 1:
            return {'name': self.sectionNameText.text(),
                    "widget": "Section"}

        widget = {}
        widget['field'] = current_field()
        widget['default'] = self._get_default_config()
        widget['widget'] = widgettype
        widget['required'] = self.requiredCheck.isChecked()
        widget['rememberlastvalue'] = self.savevalueCheck.isChecked()
        widget['name'] = self.nameText.text()
        widget['read-only-rules'] = [self.readonlyCombo.itemData(self.readonlyCombo.currentIndex())]
        widget['hidden'] = self.hiddenCheck.isChecked()
        widget['config'] = configwidget.getconfig()
        return widget

    @property
    def selected_layer(self):
        index = self.formlayers.index(self.layerCombo.currentIndex(), 0)
        layer = index.data(Qt.UserRole)
        return layer

    def write_config(self):
        if not self.selected_layer:
            return

        self._save_current_widget()
        self.form.settings['layer'] = self.selected_layer.name()
        formtype = self.formtypeCombo.currentText()
        self.form.settings['type'] = "auto" if formtype == "Auto Generated" else formtype
        self.form.settings['label'] = self.formLabelText.text()
        self.form.settings['newstyle'] = self.newStyleCheck.isChecked()
        self.form.settings['widgets'] = list(self.widgetmodel.widgets())


class ProjectInfoWidget(ui_projectinfo.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(ProjectInfoWidget, self).__init__(parent)
        self.setupUi(self)
        self.titleText.textChanged.connect(self.updatetitle)
        self.splashlabel.mouseReleaseEvent = self.change_splash
        self.btnAddLayers.pressed.connect(self.open_qgis)

    def open_qgis(self):
        try:
            openqgis(self.project.projectfile)
        except OSError:
            self.bar.pushMessage("Looks like I couldn't find QGIS",
                                 "Check qgislocation in roam.config", QgsMessageBar.WARNING)


    def change_splash(self, event):
        splash = QFileDialog.getOpenFileName(self, "Select splash image", filter="Images (*.png *.svg)")
        if not splash:
            return
        ext = os.path.splitext(splash)[1]
        shutil.copy(splash, os.path.join(self.project.folder, "splash" + ext))
        self.setsplash(self.project.splash)

    def updatetitle(self, text):
        self.project.settings['title'] = text
        self.titleText.setText(text)

    def setsplash(self, splash):
        pixmap = QPixmap(splash)
        w = self.splashlabel.width()
        h = self.splashlabel.height()
        self.splashlabel.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))

    def update_items(self):
        self.titleText.setText(self.project.name)
        self.descriptionText.setPlainText(self.project.description)
        self.setsplash(self.project.splash)
        self.versionText.setText(str(self.project.version))

    def set_project(self, project, treenode):
        super(ProjectInfoWidget, self).set_project(project, treenode)
        self.project.projectUpdated.connect(self.update_items)
        self.update_items()

    def write_config(self):
        title = self.titleText.text()
        description = self.descriptionText.toPlainText()

        settings = self.project.settings
        settings['title'] = title
        settings['description'] = description


class InfoNode(ui_infonode.Ui_Form, WidgetBase):
    """
    Info query node for a layer. Allows setting the SQL query if a layer is SQL Server or SQLite.
    """
    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)
        self.Editor.setWrapMode(QsciScintilla.WrapWord)
        self.layer = None
        self.connectionCombo.currentIndexChanged.connect(self.update_panel_status)
        self.fromlayer_radio.toggled.connect(self.update_panel_status)
        self.thislayer_radio.toggled.connect(self.update_panel_status)
        self.connectionCombo.blockSignals(True)

    def update_panel_status(self, *args):
        """
        Update if the SQL panel is enabled or disable if the source is SQL Server or SQLite.
        """
        layer = None
        if self.fromlayer_radio.isChecked():
            layer = self.connectionCombo.currentLayer()

        if self.thislayer_radio.isChecked():
            layer = self.treenode.layer

        if not layer:
            self.queryframe.setEnabled(False)
            return False

        source = layer.source()
        name = layer.dataProvider().name()
        if ".sqlite" in source or name == "mssql":
            self.queryframe.setEnabled(True)
            return True
        else:
            self.queryframe.setEnabled(False)
            return False

    def set_project(self, project, node):
        """
        Set the project for the widget. Updates the selection query for the current widget..
        """
        self.connectionCombo.blockSignals(False)
        super(InfoNode, self).set_project(project, node)
        self.layer = self.treenode.layer
        # uri = QgsDataSourceURI(self.layer.dataProvider().dataSourceUri())
        if not self.update_panel_status():
            pass

        infoblock = self.project.info_query(node.key, node.layer.name())
        caption = infoblock.get("caption", node.text())
        query = infoblock.get("query", "")
        connection = infoblock.get("connection", "from_layer")

        if connection == "from_layer":
            self.thislayer_radio.setChecked(True)
        else:
            layername = connection['layer']
            layer = utils.layer_by_name(layername)
            self.fromlayer_radio.setChecked(True)
            self.connectionCombo.setLayer(layer)

        self.caption_edit.setText(caption)
        self.Editor.setText(query)

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        if self.fromlayer_radio.isChecked():
            layer = self.connectionCombo.currentLayer()
            connection = {"layer": layer.name()}
        else:
            connection = "from_layer"


        if self.Editor.text():
            infoconfig[self.treenode.key] = {
                "caption": self.caption_edit.text(),
                "query": self.Editor.text(),
                "connection": connection,
                "type": "sql"
            }
        else:
            try:
                del infoconfig[self.treenode.key]
            except KeyError:
                pass

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayerWidget(ui_layernode.Ui_Form, WidgetBase):
    """
    Select layer widget.
    """
    def __init__(self, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        """
        Set the project for this widget. Updates the select layer config based on the project info
        for the layer.
        """
        super(LayerWidget, self).set_project(project, node)
        self.layer = node.layer
        forms = self.project.forms
        self.inspection_form_combo.clear()
        self.inspection_form_combo.clear()
        for form in forms:
            self.inspection_form_combo.addItem(form.name)
        tools = self.project.layer_tools(self.layer)
        delete = 'delete' in tools
        capture = 'capture' in tools
        edit_attr = 'edit_attributes' in tools
        edit_geom = 'edit_geom' in tools
        inspection = 'inspection' in tools
        self.capture_check.setChecked(capture)
        self.delete_check.setChecked(delete)
        self.editattr_check.setChecked(edit_attr)
        self.editgeom_check.setChecked(edit_geom)
        self.inspection_check.setChecked(inspection)
        self.datasouce_label.setText(self.layer.publicSource())

        if inspection:
            config = tools['inspection']
            formindex = self.inspection_form_combo.findText(config['form'])
            self.inspection_form_combo.setCurrentIndex(formindex)
            for key, value in config['field_mapping'].iteritems():
                self.inspection_fieldmappings.appendPlainText("{}, {}".format(key, value))
        else:
            self.inspection_form_combo.setCurrentIndex(0)
            self.inspection_fieldmappings.setPlainText("")


    def inspection_mappings(self):
        """
        Return the inspection config mapping.
        """
        if not self.inspection_fieldmappings.toPlainText():
            return {}
        text = self.inspection_fieldmappings.toPlainText().split('\n')
        mappings = {}
        for line in text:
            field1, field2 = line.split(',')
            mappings[field1] = field2.strip()
        return mappings

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        config = self.project.settings.setdefault('selectlayerconfig', {})
        infoconfig = config.setdefault(self.layer.name(), {})

        capture = self.capture_check.isChecked()
        delete = self.delete_check.isChecked()
        editattr = self.editattr_check.isChecked()
        editgoem = self.editgeom_check.isChecked()
        inspection = self.inspection_check.isChecked()
        tools = []

        if capture:
            tools.append("capture")
        if delete:
            tools.append("delete")
        if editattr and not inspection:
            # Inspection tool will override the edit button so you can't have both
            tools.append("edit_attributes")
        if editgoem:
            tools.append("edit_geom")
        if inspection:
            inspectionitem = dict(inspection=dict(
                mode="Copy",
                form=self.inspection_form_combo.currentText(),
                field_mapping= self.inspection_mappings()
            ))
            tools.append(inspectionitem)

        infoconfig['tools'] = tools

        config[self.layer.name()] = infoconfig
        self.project.settings['selectlayerconfig'] = config


class LayersWidget(ui_layersnode.Ui_Form, WidgetBase):
    """
    Root widget for select layers config.
    """
    def __init__(self, parent=None):
        super(LayersWidget, self).__init__(parent)
        self.setupUi(self)

        self.selectlayermodel = CaptureLayersModel(watchregistry=True)
        self.selectlayerfilter = LayerTypeFilter(geomtypes=[])
        self.selectlayerfilter.setSourceModel(self.selectlayermodel)
        self.selectlayermodel.dataChanged.connect(self.selectlayerschanged)

        self.selectLayers.setModel(self.selectlayerfilter)

    def selectlayerschanged(self):
        """
        Update the tree node if selection layers are added or removed.
        """
        self.treenode.refresh()

    def set_project(self, project, node):
        """
        Set the project for this widget. Updates the select layers config.
        """
        super(LayersWidget, self).set_project(project, node)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()


class LayerSearchWidget(ui_searchsnode.Ui_Form, WidgetBase):
    """
    Root widget for the search config UI. Nothing here at the moment.
    """
    def __init__(self, parent=None):
        super(LayerSearchWidget, self).__init__(parent)
        self.setupUi(self)

    def set_project(self, project, node):
        """
        Set the project for this widget.
        """
        super(LayerSearchWidget, self).set_project(project, node)


class LayerSearchConfigWidget(ui_searchnode.Ui_Form, WidgetBase):
    """
    Widget to handle setting which fields are enabled for searching on the selected layer.

    Auto adds the search plugin if not loaded as well as the columns for the current layer.
    """
    def __init__(self, parent=None):
        super(LayerSearchConfigWidget, self).__init__(parent)
        self.setupUi(self)

        self.fieldsmodel = SearchFieldsModel()
        self.fieldsview.setModel(self.fieldsmodel)

    def set_project(self, project, node):
        """
        Set the project for this widget.  Updates the config on the fields model.
        """
        super(LayerSearchConfigWidget, self).set_project(project, node)
        self.fieldsmodel.setLayer(node.layer)
        self.fieldsmodel.set_settings(project.settings)

    def write_config(self):
        """
        Wrtie the config for the widget back to the project config
        """
        layers = self.fieldsmodel.layerconfig
        if layers:
            plugins = self.project.settings.setdefault('plugins', [])
            if "search_plugin" not in plugins:
                plugins.append("search_plugin")
                self.project.settings['plugins'] = plugins
            config = self.project.settings.setdefault('search', {})
            config[self.treenode.layer.name()] = dict(columns=layers)
