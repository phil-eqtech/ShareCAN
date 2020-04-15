from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time
import logging
from bitstring import BitArray

from modules.Constants import *

class TableView(QTableView):
  def __init__(self, *args, **kwargs):
    super(TableView, self).__init__(*args, **kwargs)

  def contextMenuEvent(self, event):
    self.menu = QMenu(self)
    renameAction = QAction('MENU_IN_PROGRESS....', self)
    renameAction.triggered.connect(lambda: self.renameSlot(event))
    self.menu.addAction(renameAction)
    # add other required actions
    self.menu.popup(QCursor.pos())

  def renameSlot(self, event):
      print("renaming slot called")
      # get the selected row and column
      """row = self.rowAt(event.pos().y())
      col = self.columnAt(event.pos().x())
      # get the selected cell
      cell = self.item(row, col)
      # get the text inside selected cell (if any)
      cellText = cell.text()
      # get the widget inside selected cell (if any)
      widget = self.tableWidget.cellWidget(row, col)
      """

class CustomDelegate(QStyledItemDelegate):
  def anchorAt(self, html, point):
    doc = QTextDocument()
    doc.setHtml(html)
    textLayout = doc.documentLayout()
    return textLayout.anchorAt(point)

  def paint(self, painter, option, index):
    options = QStyleOptionViewItem(option)
    self.initStyleOption(options, index)

    if options.widget:
      style = options.widget.style()
    else:
      style = QtWidgets.QApplication.style()

    doc = QTextDocument()
    doc.setHtml(options.text)
    options.text = ''

    style.drawControl(QStyle.CE_ItemViewItem, options, painter)
    ctx = QAbstractTextDocumentLayout.PaintContext()

    textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)

    painter.save()
    painter.translate(textRect.topLeft())
    painter.setClipRect(textRect.translated(-textRect.topLeft()))
    painter.translate(0, 0.5*(options.rect.height() - doc.size().height()))
    doc.documentLayout().draw(painter, ctx)

    painter.restore()

  def sizeHint(self, option, index):
    options = QStyleOptionViewItem(option)
    self.initStyleOption(options, index)

    doc = QTextDocument()
    doc.setHtml(options.text)
    doc.setTextWidth(options.rect.width())
    return QSize(doc.idealWidth(), doc.size().height())


class framesTableModel(QAbstractTableModel):
    def __init__(self, columnsDef, frames=[], parent=None):
        super().__init__()
        self.parent = parent
        self._sortBy = []
        self._sortDirection = []

        self.frames = frames
        self.filters = {}
        self.filteredFrames = []
        self.signals = {}

        self.ts = 0
        self.lastRefresh = 0
        self.refreshRate = TABLE_REFRESH_RATE

        self.columnLabel = columnsDef
        self.sortCol = 0
        self.sortOrder = Qt.DescendingOrder


    def __getitem__(self, key):
      return getattr(self, key)

    def __setitem__(self, key, value):
      return setattr(self, key, value)

    def rowCount(self, parent):
      return len(self.filteredFrames)

    def columnCount(self, parent):
      return len(self.columnLabel)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return QCoreApplication.translate("FRAME",self.columnLabel[section]['label'])
            if orientation == Qt.Vertical:
                return str(section +1)

    def data(self, index, role):
        r = index.row()
        f = self.filteredFrames[r]
        c = index.column()
        if role == Qt.DisplayRole:
          if self.columnLabel[c]['field'] == 'id': # ID
            if f['extendedId']==True:
              return "{0:#0{1}x}".format(f['id'],10)
            else:
              return "{0:#0{1}x}".format(f['id'],5)
          elif self.columnLabel[c]['field'] == 'msg':
            return f['msgColored']
          elif self.columnLabel[c]['field'] == 'ts':
            return "{:.3f}".format(f['ts'] - self.ts)
          elif self.columnLabel[c]['field'] == 'ecu':
            if f['type'] in self.signals and f['preset'] in self.signals[f['type']] and f['id'] in self.signals[f['type']][f['preset']]:
              ecu = []
              for elt in self.signals[f['type']][f['preset']][f['id']]:
                if not elt['ecu'] in ecu:
                  ecu.append(elt['ecu'])
              return "<br>".join(ecu)
            else:
              return ""
          elif self.columnLabel[c]['field'] == 'signal':
            if f['type'] in self.signals and f['preset'] in self.signals[f['type']] and f['id'] in self.signals[f['type']][f['preset']]:
              signals = []
              for elt in self.signals[f['type']][f['preset']][f['id']]:
                signals.append(self.parseSignal(elt, f['msg']))

              return "<br>".join(signals)
            else:
              return ""
          else:
            return str(self.filteredFrames[index.row()][self.columnLabel[index.column()]['field']])

    def parseSignal(self, signal, msg):
      bitArray = ''.join(format(byte, '08b') for byte in msg)
      bitLen = int(signal['len'])
      bit = bitArray[int(signal['start']): int(signal['start']) + int(signal['len'])]
      #if signal['endian'] == 0:
      #  bit = bit[::-1]
      if signal['signed'] == True:
        value = BitArray(bin=bit).int
      else:
        value = BitArray(bin=bit).uint

      if signal['factor'] != None and len(signal['factor']) > 0:
        value *= float(signal['factor'])
      if signal['offset'] != None and len(signal['offset']) > 0:
        value += float(signal['offset'])
      if signal['min'] != None and len(signal['min']) > 0:
        if value < float(signal['min']):
          value = float(signal['min'])
      if signal['max'] != None and len(signal['max']) > 0:
        if value > float(signal['max']):
          value = float(signal['max'])
      value = round(value,3)
      if len(signal['values']) > 0:
        for v in signal['values']:
          if int(v['value']) == value:
            value = v['label']
            break
      str_ = "<b>" + signal['name'] + " : </b>"
      str_ += str(value)

      if signal['unit'] != None:
        str_ += " " + signal['unit']
      return str_

    def sort(self, col, order=Qt.AscendingOrder):
      # Parse SIGNAL DETAIL
      self.applyFilters()
      self.sortCol = col
      self.sortOrder = order
      self.filteredFrames = sorted(self.filteredFrames, key= lambda i: i[self.columnLabel[col]['field']], reverse = (1 - order))
      self.layoutChanged.emit()


    def updateFilters(self, filters):
      self.filters = filters
      self.sort(self.sortCol, self.sortOrder)


    def applyFilters(self):
      self.filteredFrames = []
      for idx in range(0, len(self.frames)):
        if not self.frames[idx]['id'] in self.filters[self.frames[idx]['presetLabel']]:
          self.filteredFrames.append(self.frames[idx])


    def addElt(self, elt):
      if type(elt) == 'list':
        for msg in elt:
          self.frames.append(msg)
      else:
        self.frames.append(elt)

      if self.lastRefresh + self.refreshRate < time.time():
        if self.lastRefresh == 0:
          if type(elt) == 'list':
            self.ts = elt[0]['ts']
          else:
            self.ts = elt['ts']
        self.sort(self.sortCol, self.sortOrder)
        self.lastRefresh = time.time()


    def clearElt(self):
      self.frames = []
      self.filteredFrames = []

    def updateSignals(self, signals):
      self.signals = signals
      logging.debug("Signals updated to : %s"%signals)
