import sys
from PyQt4.QtGui import QDoubleSpinBox, QSpinBox

from roam.editorwidgets.core import EditorWidget, registerwidgets


class NumberWidget(EditorWidget):
    widgettype = 'Number'
    def __init__(self, *args, **kwargs):
        super(NumberWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return QSpinBox(parent)

    def initWidget(self, widget):
        widget.valueChanged.connect(self.validate)

    def validate(self, *args):
        self.raisevalidationupdate(passed=True)

    def updatefromconfig(self):
        config = self.config
        prefix = config.get('prefix', '')
        suffix = config.get('suffix', '')
        max, min = self._getmaxmin(config)
        self._setwidgetvalues(min, max, prefix, suffix)

    def _getmaxmin(self, config):
        max = config.get('max', '')
        min = config.get('min', '')
        try:
            max = int(max)
        except ValueError:
            max = sys.maxint

        try:
            min = int(min)
        except ValueError:
            min = -sys.maxint - 1
        return max, min

    def _setwidgetvalues(self, min, max, prefix, suffix):
        self.widget.setRange(min, max)
        self.widget.setPrefix(prefix)
        self.widget.setSuffix(suffix)

    def setvalue(self, value):
        if not value:
            value = 0

        value = int(value)
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()


class DoubleNumberWidget(NumberWidget):
    widgettype = 'Number(Double)'
    def __init__(self, *args, **kwargs):
        super(DoubleNumberWidget, self).__init__(*args, **kwargs)

    def createWidget(self, parent):
        return QDoubleSpinBox(parent)

    def initWidget(self, widget):
        super(DoubleNumberWidget, self).initWidget(widget)

    def _getmaxmin(self, config):
        max = config.get('max', '')
        min = config.get('min', '')
        try:
            max = float(max)
        except ValueError:
            max = sys.float_info.max

        try:
            min = float(min)
        except ValueError:
            min = sys.float_info.min
        print max, min
        return max, min

    def setvalue(self, value):
        if not value:
            value = 0.00

        value = float(value)
        self.widget.setValue(value)

