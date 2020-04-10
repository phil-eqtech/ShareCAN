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
