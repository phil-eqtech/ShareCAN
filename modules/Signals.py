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

  setNewSession = pyqtSignal(bool)
  pauseSession = pyqtSignal(bool)
  startSessionLive = pyqtSignal(bool)
  startSessionRecording = pyqtSignal(bool)
  startSessionForensic = pyqtSignal(bool)

  signalEditorRefresh  = pyqtSignal(dict)
  signalReload = pyqtSignal(bool)

  scanEnded = pyqtSignal(bool)

  # Frame model / msg Table
  flagId = pyqtSignal(list)
  filterHideId = pyqtSignal(list)
  filterShowId = pyqtSignal(list)
  unFilterId = pyqtSignal(bool)
  replaySelection = pyqtSignal(list)
  commandSelection = pyqtSignal(list)
  replayCommand = pyqtSignal(dict)
  copyCells = pyqtSignal(bool)
  updateProgressBar = pyqtSignal(list)
