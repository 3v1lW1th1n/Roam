from PyQt4.QtGui import QComboBox

from qgis.core import QgsMessageLog, QgsMapLayerRegistry, QgsExpression, QgsFeatureRequest

from qmap.editorwidgets.core import WidgetFactory, WidgetsRegistry, EditorWidget


class ListWidget(EditorWidget):
    def __init__(self, *args):
        super(ListWidget, self).__init__(*args)

    def createWidget(self, parent):
        return QComboBox(parent)

    def _buildfromlist(self, widget, listconfig):
        items = listconfig['items']
        for item in items:
            parts = item.split(';')
            data = parts[0]
            try:
                desc = parts[1]
            except IndexError:
                desc = data

            widget.addItem(desc, data)

    def _buildfromlayer(self, widget, layerconfig):
        layername = layerconfig['layer']
        keyfield = layerconfig['key']
        valuefield = layerconfig['value']
        filterexp = layerconfig['filter']
        try:
            layer = QgsMapLayerRegistry.instance().mapLayersByName(layername)[0]
        except IndexError:
            print "Can't find layer {} in project".format(layername)
            return

        keyfieldindex = layer.fieldNameIndex(keyfield)
        valuefieldindex = layer.fieldNameIndex(valuefield)
        if keyfieldindex == -1 or valuefieldindex == -1:
            print "Can't find key or value column"
            return

        if not filterexp and valuefieldindex == keyfieldindex:
            values = layer.uniqueValues(keyfieldindex)
            for value in values:
                widget.addItem(value, value)
            return

        attributes = {keyfieldindex, valuefieldindex}
        flags = QgsFeatureRequest.NoGeometry

        expression = None
        if filterexp:
            expression = QgsExpression(filterexp)
            expression.prepare(layer.pendingFields())
            if expression.hasParserError():
                print "Expression has parser error: {}".format(expression.parserErrorString())
                return

            if expression.needsGeometry():
                flags = QgsFeatureRequest.NoFlags

            for field in expression.referencedColumns():
                index = layer.fieldNameIndex(field)
                attributes.add(index)

        values = set()
        request = QgsFeatureRequest().setFlags(flags).setSubsetOfAttributes(list(attributes))
        for feature in layer.getFeatures(request):
            if expression and not expression.evaluate(feature):
                continue

            pair = (feature[keyfieldindex], feature[valuefieldindex])
            values.add(pair)

        if self.config['allownull']:
            widget.addItem('(no selection)', None)

        for pair in values:
            widget.addItem(pair[1], pair[0])

    def initWidget(self, widget):
        if 'list' in self.config:
            listconfig = self.config['list']
            self._buildfromlist(widget, listconfig)
        elif 'layer' in self.config:
            layerconfig = self.config['layer']
            self._buildfromlayer(widget, layerconfig)

        if widget.isEditable():
            widget.editTextChanged.connect(self.validate)

        widget.currentIndexChanged.connect(self.validate)

    def validate(self, *args):
        if (not self.config['allownull'] and (not self.widget.currentText() or
            self.widget.currentText() == "(no selection)")):
            self.raisevalidationupdate(False)
        else:
            self.raisevalidationupdate(True)

    def setvalue(self, value):
        index = self.widget.findData(value)
        self.widget.setCurrentIndex(index)
        if index == -1 and self.widget.isEditable():
            if value is None and not self.config['allownull']:
                return

            self.widget.addItem(str(value))
            index = self.widget.count() - 1
            self.widget.setCurrentIndex(index)

    def value(self):
        index = self.widget.currentIndex()
        value = self.widget.itemData(index)
        text = self.widget.currentText()
        if value is None and self.widget.isEditable() and not text == '(no selection)':
            return self.widget.currentText()

        return value

factory = WidgetFactory("List", ListWidget, None)
