__author__ = 'Nathan.Woodrow'

from PyQt4.QtGui import QWidget
from PyQt4.Qsci import QsciLexerSQL, QsciScintilla

from configmanager.ui.nodewidgets import ui_layersnode, ui_layernode, ui_infonode
from configmanager.models import CaptureLayersModel, LayerTypeFilter


class WidgetBase(QWidget):
    def set_project(self, project, treenode):
        self.project = project
        self.treenode = treenode

    def write_config(self):
        """
        Write the config back to the project settings.
        """
        pass


class InfoNode(ui_infonode.Ui_Form, WidgetBase):
    def __init__(self, parent=None):
        super(InfoNode, self).__init__(parent)
        self.setupUi(self)
        self.Editor.setLexer(QsciLexerSQL())
        self.Editor.setMarginWidth(0, 0)
        self.Editor.setWrapMode(QsciScintilla.WrapWord)
        self.layer = None

    def set_project(self, project, node):
        super(InfoNode, self).set_project(project, node)
        self.layer = node.layer
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
        pass

    def set_project(self, project, node):
        super(LayersWidget, self).set_project(project, node)
        self.selectlayermodel.config = project.settings
        self.selectlayermodel.refresh()

