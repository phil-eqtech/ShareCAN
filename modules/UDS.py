# GLOBAL
from modules.Constants import *

class UDS:
  def __init__(self):
    self.wish = None
    self.response = {"status":threading.Event(), "id":None, "msg":None, "error":None, "errorCode":None, "isoTp":False}
