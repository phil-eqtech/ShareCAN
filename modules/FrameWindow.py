from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time
import logging
from bitstring import BitArray
import qtawesome as qta

from modules.Constants import *
from modules.Signals import CustomSignals

class TableView(QTableView):
  def __init__(self, *args, **kwargs):
    super(TableView, self).__init__(*args, **kwargs)
    self.appSignals = None

  def linkAppSignals(self, appSignals):
    self.appSignals = appSignals

  def contextMenuEvent(self, event):
    cells = []
    if self.selectionModel().selection().indexes():
      for i in self.selectionModel().selection().indexes():
        row, column = i.row(), i.column()
        cells.append({"row":row, "col":column})

    self.menu = QMenu(self)
    filterHideAction = QAction(QCoreApplication.translate("MENU","FILTER_HIDE_ID"), self)
    filterHideAction.setIcon(qta.icon('fa5s.eye-slash'))
    filterHideAction.triggered.connect(lambda: self.appSignals.filterHideId.emit(cells))

    filterShowAction = QAction(QCoreApplication.translate("MENU","FILTER_ONLY_ID"), self)
    filterShowAction.setIcon(qta.icon('fa5s.filter'))
    filterShowAction.triggered.connect(lambda: self.appSignals.filterShowId.emit(cells))

    unFilterAction = QAction(QCoreApplication.translate("MENU","UNFILTER_ID"), self)
    unFilterAction.setIcon(qta.icon('mdi.eye-plus'))
    unFilterAction.triggered.connect(lambda: self.appSignals.unFilterId.emit(True))

    replayAction = QAction(QCoreApplication.translate("MENU","REPLAY"), self)
    replayAction.setIcon(qta.icon('mdi.replay'))
    replayAction.triggered.connect(lambda: self.appSignals.replaySelection.emit(cells))

    commandAction = QAction(QCoreApplication.translate("MENU","SET_COMMAND"), self)
    commandAction.setIcon(qta.icon('fa5s.terminal'))
    commandAction.triggered.connect(lambda: self.appSignals.commandSelection.emit(cells))

    flagAction = QAction(QCoreApplication.translate("MENU","SET_FLAG"), self)
    flagAction.setIcon(qta.icon('mdi.flag'))
    flagAction.triggered.connect(lambda: self.appSignals.flagId.emit(cells))

    unFlagAction = QAction(QCoreApplication.translate("MENU","RESET_FLAGS"), self)
    unFlagAction.setIcon(qta.icon('mdi.flag-remove-outline'))
    unFlagAction.triggered.connect(lambda: self.appSignals.flagId.emit([]))

    copyCellsAction = QAction(QCoreApplication.translate("MENU","COPY"), self)
    copyCellsAction.setIcon(qta.icon('fa5.copy'))
    copyCellsAction.triggered.connect(lambda: self.appSignals.copyCells.emit(True))

    self.menu.addAction(filterHideAction)
    self.menu.addAction(filterShowAction)
    self.menu.addAction(unFilterAction)
    self.menu.addSeparator()
    self.menu.addAction(replayAction)
    self.menu.addAction(commandAction)
    self.menu.addSeparator()
    self.menu.addAction(flagAction)
    self.menu.addAction(unFlagAction)
    self.menu.addSeparator()
    self.menu.addAction(copyCellsAction)
    # add other required actions
    self.menu.popup(QCursor.pos())


  def testAction(self, event):
    logging.debug("TEST ACTION")

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
    def __init__(self, columnsDef, frames=[], parent=None, appSignals = None):
        super().__init__()
        self.parent = parent
        self._sortBy = []
        self._sortDirection = []

        self.appSignals = appSignals

        self.frames = frames
        self.filters = {}
        self.filteredFrames = []
        self.signals = {}

        self.flaggedId = []

        self.ts = 0
        self.lastRefresh = 0
        self.refreshRate = TABLE_REFRESH_RATE

        self.columnLabel = columnsDef
        self.sortCol = 0
        self.sortOrder = Qt.DescendingOrder

        if self.appSignals != None:
          self.appSignals.flagId.connect(lambda cells: self.flagId(cells))

    def __getitem__(self, key):
      return getattr(self, key)

    def __setitem__(self, key, value):
      return setattr(self, key, value)

    def rowCount(self, parent):
      return len(self.filteredFrames)

    def columnCount(self, parent):
      return len(self.columnLabel)

    def flagId(self, cells):
      if len(cells) == 0:
        self.flaggedId = []
      else:
        r = []
        for cell in cells:
          if not cell['row'] in r:
            lbl = "%s_%s"%(self.filteredFrames[cell['row']]['id'], self.filteredFrames[cell['row']]['preset'])
            self.flaggedId.append(lbl)
            r.append(cell['row'])

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return QCoreApplication.translate("MainWindow",self.columnLabel[section]['label'])
            if orientation == Qt.Vertical:
                return str(section +1)

    def data(self, index, role):
        r = index.row()
        f = self.filteredFrames[r]
        c = index.column()
        if role == Qt.DecorationRole :
          if c == 0 and len(self.flaggedId) > 0:
            lbl = "%s_%s"%(self.filteredFrames[index.row()]['id'], self.filteredFrames[index.row()]['preset'])
            if lbl in self.flaggedId:
              return QIcon(qta.icon('mdi.flag', options=[{'color':'green'}]))
        elif role == Qt.DisplayRole:
          if self.columnLabel[c]['field'] == 'id': # ID
            if f['extendedId']==True:
              return "{0:0{1}x}".format(f['id'],8)
            else:
              return "{0:0{1}x}".format(f['id'],3)
          elif self.columnLabel[c]['field'] == 'msg':
            return f['msgColored']
          elif self.columnLabel[c]['field'] == 'ts':
            return "{:.3f}".format(f['ts'] - self.ts)
          elif self.columnLabel[c]['field'] == 'period':
            return "%s ms"%f['period']
          else:
            return str(self.filteredFrames[index.row()][self.columnLabel[index.column()]['field']])

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
        if self.frames[idx]['busName'] + " - " in self.frames[idx]['presetLabel']:
          busRef = self.frames[idx]['presetLabel']
        else:
          busRef = "%s : %s"%(self.frames[idx]['busName'],self.frames[idx]['presetLabel'])
        if not self.frames[idx]['id'] in self.filters[busRef]:
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
