#!/usr/bin/python2

from os.path import isfile, join, dirname, abspath
import sys
from Reading import ReadRaw
from Inversion import Invert532
from datetime  import datetime, timedelta, time
from configparser import ConfigParser
from Web import WEBoutput
from Utilities import CheckFolder

################# Parameters ############################################### 
cfgfile       = "parameters_SMN.cfg"                                           # CFG file
t2            = datetime.utcnow().replace(second=0, microsecond=0)         # Final date and time
t1            = (t2-timedelta(days=180)).replace(hour=0, minute=0)          # Start date and time 
Debug         = True
############################################################################

cfgpath       = dirname(abspath(__file__))
cfgpath       = join(cfgpath, cfgfile)

station_list  = ['aeroparque',
                 'bariloche',
                 'comodoro',
                 'cordoba',
                 'gallegos',
                 'neuquen',
                 'parenas',
                 'tucuman',
                 'vmartelli']

if Debug:
  station_block = 'cordoba'
else:
  station_block = sys.argv[1]

if station_block in station_list:
  print("Working for station {}".format(station_block))
else:
  print("{} is not a valid station".format(station_block))
  print("Posible options:")
  for item in station_list: print(item)
  exit()

config = ConfigParser(inline_comment_prefixes=";")
config.read(cfgpath)

#Read parameters from an external file
block      = station_block
sampling   = config.getint(block, "sampling")
FileSize   = config.getint(block, "FileSize")
prefix     = config.get(block, "prefix")
ncpath_out = config.get("Paths", "ncpath_out")
ncfile_out = config.get("Paths", "ncfile_out")
ncpath_raw = config.get("Paths", "ncpath_raw")
ncfile_raw = config.get("Paths", "ncfile_raw")
binpath    = config.get("Paths", "binpath")
binpath    = binpath + station_block + "/"

print("Reading binary data from LICEL from {} to {}".format(t1,t2))
print("Looking for binary raw data in {}".format(binpath))
print("Output file (NetCDF format): {}".format(prefix+ncfile_raw))
t1_data, t2_data = ReadRaw.findtimes(t1,t2,sampling,binpath,prefix,ncpath_raw+prefix+ncfile_raw,FileSize)
print("Time range found: {}-{}".format(t1_data, t2_data))
if t2_data>t1_data:
  x, y1, y2, y3, z, height = ReadRaw.get_data(t1_data,t2_data,sampling,binpath,prefix,FileSize)  
  if isfile(ncpath_raw+prefix+ncfile_raw):
    print("Updating file: ", prefix+ncfile_raw)
    ReadRaw.updatencd(x, y1, y2, y3, z, ncpath_raw+prefix+ncfile_raw)
  else:
    print("Creating a new file: ", prefix+ncfile_raw)
    ReadRaw.createncd(x, y1, y2, y3, z, height, ncpath_raw+prefix+ncfile_raw)
  CheckFolder.ensure_folder_exists("./Output/" + station_block)
  Invert532.invert(block,cfgpath)
  WEBoutput.CreateJS(block, join(ncpath_out,block), ncfile_out)
else:
  print("Nothing to do")
  print("Waiting for new data")
print("******** Done ! **********")


