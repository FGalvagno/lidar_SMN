#!/usr/bin/python

from os.path import isfile, join
import sys
from Reading import ReadRaw
from Inversion import Invert532
from datetime  import datetime, timedelta, time
from configparser import SafeConfigParser
from Web import WEBoutput

################# Parameters ###############################################
cfgpath       = "./"                                                       # Absolute Path with cfg file
cfgfile       = "parameters.cfg"                                           # CFG file
Debug         = True
############################################################################

station_list  = ['aeroparque',
                 'bariloche',
                 'comodoro',
                 'cordoba',
                 'gallegos',
                 'neuquen',
                 'parenas',
                 'tucuman',
		 'vmartelli']

station_block = sys.argv[1]

if station_block in station_list:
  print("Working for station {}".format(station_block))
else:
  print("{} is not a valid station".format(station_block))
  print("Posible options:")
  for item in station_list: print(item)
  exit()

config = SafeConfigParser()
config.read(cfgpath+cfgfile)

#Read parameters from an external file
block      = station_block
prefix     = config.get(block, "prefix")
ncpath_raw = config.get("Paths", "ncpath_raw")
ncfile_raw = config.get("Paths", "ncfile_raw")
ncpath_out = config.get("Paths", "ncpath_out")
ncfile_out = config.get("Paths", "ncfile_out")

if isfile(ncpath_raw+prefix+ncfile_raw):
  print("Working with file: ", ncpath_raw+prefix+ncfile_raw)
  Invert532.invert(block,cfgpath+cfgfile)
  WEBoutput.CreateJS(block, join(ncpath_out,block), ncfile_out)
else:
  print("Unable to open file: ", ncpath_raw+prefix+ncfile_raw)
  print("Nothing to do")
print("******** Done ! **********")

