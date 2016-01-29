from roam.api import RoamEvents
from PyQt4.QtGui import QLineEdit, QPlainTextEdit
from PyQt4.QtCore import QEvent

from qgis.core import QgsDataSourceURI
from roam.dataaccess.database import Database
from roam.editorwidgets.core import EditorWidget, registerwidgets


def _get_sqlite_col_length(layer, fieldname):
    """
    Get the length of a sqlite based column using the metadata

    NOTE: SQLITE doesn't support this. And this is a bit of a hack.

    NOTE NOTE: Looks for VARCHAR(...) as the datatype which isn't really a
    sqlite data type.

    :returns: True, length if column is found in table metadata
    """
    source = layer.source()
    if ".sqlite" not in source:
        return False, 0

    database = Database.fromLayer(layer)
    index = source.index("|") + 1
    args = source[index:].split("=")
    args = dict(zip(args[0::2], args[1::2]))
    try:
        layer = args['layername']
    except KeyError:
        return False, 0

    tabledata = list(database.query("pragma table_info({})".format(layer)))
    for row in tabledata:
        if not row['name'] == fieldname:
            continue

        import re
        # Look for varchar(...) so we can grab the length.
        match = re.search("VARCHAR\((\d.*)\)", row['type'], re.IGNORECASE)
        if match:
            length = match.group(1)
            return True, int(length)
    return False, 0


class TextWidget(EditorWidget):
    widgettype = 'Text'

    def __init__(self, *args, **kwargs):
        super(TextWidget, self).__init__(*args)
        self.text_length = 0

    def createWidget(self, parent):
        return QLineEdit(parent)

    def initWidget(self, widget):
        widget.textChanged.connect(self.emitvaluechanged)
        widget.installEventFilter(self)
        self.text_length = self.field.length()
        passed, length = _get_sqlite_col_length(self.layer, self.field.name())
        if passed:
            self.text_length = length

        if self.text_length > 0:
            if hasattr(widget, "setMaxLength"):
                widget.setMaxLength(self.text_length)

    def eventFilter(self, object, event):
        # Hack I really don't like this but there doesn't seem to be a better way at the
        # moment
        if event.type() in [QEvent.FocusIn, QEvent.MouseButtonPress]:
            RoamEvents.openkeyboard.emit()
        return False

    def validate(self, *args):
        if not self.value():
            return False
        else:
            return True

    def setvalue(self, value):
        # Not the best way but should cover most use cases
        # for now
        value = value or ''
        value = unicode(value)
        try:
            self.widget.setPlainText(value)
        except AttributeError:
            self.widget.setText(value)

    def value(self):
        try:
            return self.widget.toPlainText()
        except AttributeError:
            return self.widget.text()


class TextBlockWidget(TextWidget):
    widgettype = 'TextBlock'

    def __init__(self, *args, **kwargs):
        super(TextBlockWidget, self).__init__(*args)
        self.text_length = 0

    def createWidget(self, parent):
        return QPlainTextEdit(parent)

    def limit_text(self):
        text = self.widget.toPlainText()
        if 0 < self.text_length < text:
            text = text[:self.text_length]
            self.widget.blockSignals(True)
            self.setvalue(text)

            cursor = self.widget.textCursor()
            cursor.setPosition(self.widget.document().characterCount() - 1)
            self.widget.setTextCursor(cursor)

        self.widget.blockSignals(False)
        self.emitvaluechanged(self.widget.toPlainText())

    def initWidget(self, widget):
        self.text_length = self.field.length()
        found, length = _get_sqlite_col_length(self.layer, self.field.name())
        if found:
            self.text_length = length
        widget.textChanged.connect(self.limit_text)
        widget.installEventFilter(self)
