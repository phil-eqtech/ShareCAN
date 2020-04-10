#!/usr/bin/python3

#
# Convert .ui files to .py templates
#

import os.path
import subprocess

# Update this variable to register an .ui file and the desired template

files = [{"ui":"main-window", "template":"MainWindow"},
          {"ui":"form-bus", "template":"BusForm"},
          {"ui":"form-devices", "template":"DevicesForm"},
          {"ui":"form-sessions", "template":"SessionsForm"},
          {"ui":"form-signals", "template":"SignalsForm"},
          {"ui":"form-replay", "template":"ReplayForm"},
          {"ui":"form-analysis_params", "template":"AnalysisParamsForm"},]

# MainWindow
for file in files:
  uiFile = file['ui'] + ".ui"
  dstFile = file['template'] + ".py"
  if os.path.isfile(uiFile):
    print("Converting %s to %s"%(uiFile, dstFile))
    args = ["pyuic5",uiFile,"-o",dstFile]
    subprocess.Popen(args)
