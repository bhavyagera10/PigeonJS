#!/usr/bin/python

import multiprocessing
import os
import sys
import shutil
import subprocess
from threading import Timer
import sys
from subprocess import Popen,PIPE, STDOUT, call

def PrintUsage():
  print """
Usage:
  extract_features.py --filelist <file> --max_path_length <number>
OR
  extract_features.py --dir <directory> --max_path_length <number> [--infer_labels]
"""
  exit(1)

def GetJSFilesInDir(d):
  for root, _, files in os.walk(d):
    for f in files:
      fname = os.path.join(root, f)
      if fname.endswith('.js'):
        yield fname


TMP_DIR = ""
original_features = ""
MAX_PATH_LENGTH = 0
if ((len(sys.argv) > 4) and (sys.argv[3] == "--max_path_length")):
    MAX_PATH_LENGTH = int(sys.argv[4])
else:
    original_features = "--original_features"
infer_labels = ""
nodejsFile = "unuglifyjs"

def ExtractFeaturesForFile(f):
  command = ['nodejs', '--max_old_space_size=64000', 'bin/unuglifyjs', f, '--extract_features', '--max_path_length=' + str(MAX_PATH_LENGTH), '--skip_minified']
  if (original_features != ""):
	command.append(original_features)
  #os.system(command)
  kill = lambda process: process.kill()
  with open(TMP_DIR + str(os.getpid()), 'a') as outputFile:
    sleeper = subprocess.Popen(command, stdout=outputFile, stderr=subprocess.PIPE)
    timer = Timer(60, kill, [sleeper])

    try:
      timer.start()
      stdout, stderr = sleeper.communicate()
    finally:
      timer.cancel()

    if (sleeper.poll() == 0):
      print >> sys.stderr, stderr,
    else:
      print >> sys.stderr, 'file: ' + str(f) + ' was not completed in time'

def ExtractFeaturesForFileList(files):
  global TMP_DIR
  TMP_DIR = "./tmp/feature_extractor%d/" % (os.getpid())
  if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)
  os.makedirs(TMP_DIR)
  try:
    p = multiprocessing.Pool(multiprocessing.cpu_count())
    p.map(ExtractFeaturesForFile, files)
    output_files = os.listdir(TMP_DIR)
    for f in output_files:
      os.system("cat %s/%s" % (TMP_DIR, f))
  finally:
    shutil.rmtree(TMP_DIR)


if __name__ == '__main__':
  if (len(sys.argv) <= 3):
    PrintUsage()

  # Process command line arguments
  if (sys.argv[1] == "--filelist"):
    files = open(sys.argv[2], 'r').read().split('\n')
  elif (sys.argv[1] == "--dir"):
    files = [f for f in GetJSFilesInDir(sys.argv[2])]
  else:
    PrintUsage()
  
  # Remove files that say they are minified.
  files = [f for f in files if not f.endswith('.min.js')]
  ExtractFeaturesForFileList(files)
	
