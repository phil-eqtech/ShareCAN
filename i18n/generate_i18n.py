#!/usr/bin/python3

#
# Convert .ts files to .qm translation
#

import os.path
import subprocess

# Update this variable to register an .ui file and the desired template

files = [{"src":"fr_FR"},
          {"src":"en_EN"},]

# MainWindow
for file in files:
  srcFile = file['src'] + ".ts"
  if os.path.isfile(srcFile):
    print("Converting %s"%(srcFile))
    args = ["lrelease",srcFile]
    subprocess.Popen(args)
