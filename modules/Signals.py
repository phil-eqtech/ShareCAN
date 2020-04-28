from PyQt5.QtCore import *

class CustomSignals(QObject):
  msg = pyqtSignal(dict)

  # Progress
  progress = pyqtSignal(int)

  # Display signals
  startAnalysis = pyqtSignal(bool)
  updateAnalysis = pyqtSignal(bool)

  # Signals "bus"
  # switchBus(bus id) : activate/deactivate bus
  switchBus = pyqtSignal(dict)

  frameRecv = pyqtSignal(dict)

  gatewayForward = pyqtSignal(dict)

  stopSessionRecording = pyqtSignal(bool)
  startSessionLive = pyqtSignal(bool)

  signalEditorRefresh  = pyqtSignal(dict)
  signalReload = pyqtSignal(bool)

  # Frame model / msg Table
  flagId = pyqtSignal(list)
  filterHideId = pyqtSignal(list)
  filterShowId = pyqtSignal(list)
  unFilterId = pyqtSignal(bool)
  replaySelection = pyqtSignal(list)
  replayCommand = pyqtSignal(dict)

  updateProgressBar = pyqtSignal(list)
