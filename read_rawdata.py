#!/usr/bin/env python2

from Reading import ReadRaw
from datetime import datetime
from ConfigParser import SafeConfigParser
from os.path import isfile, join, dirname, abspath
import sys

################# Parameters ###############################################
cfgfile       = "parameters.cfg"                                           # CFG file
t1            = datetime(year=2019, month=4, day=1,  hour=0, minute=0)     # Start date and time
t2            = datetime(year=2019, month=4, day=30, hour=0, minute=0)     # Final date and time
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

station_block = sys.argv[1]

if station_block in station_list:
  print "Working for station {}".format(station_block)
else:
  print "{} is not a valid station".format(station_block)
  print "Posible options:"
  for item in station_list: print item
  sys.exit()

config = SafeConfigParser()
config.read(cfgpath)

#Read parameters from an external file
block      = station_block
sampling   = config.getint(block, "sampling")
FileSize   = config.getint(block, "FileSize")
prefix     = config.get(block, "prefix")
ncpath_raw = config.get("Paths", "ncpath_raw")
ncfile_raw = config.get("Paths", "ncfile_raw")
binpath    = config.get("Paths", "binpath")

ncfile_raw = join(ncpath_raw,prefix + ncfile_raw)
binpath    = join(binpath, station_block) + "/"

print "Program for reading binary data from LICEL raw data"
print "***************************************************"
print "Looking for binary raw data in {}".format(binpath)
print "Reading binary data from {} to {}".format(t1,t2)
t1_data, t2_data = ReadRaw.findtimes(t1,t2,sampling,binpath,prefix,ncfile_raw,FileSize)
print "Time range found: {}-{}".format(t1_data, t2_data)

if t2_data>t1_data:
  x, y1, y2, y3, z, height = ReadRaw.get_data(t1_data,t2_data,sampling,binpath,prefix,FileSize)
  if isfile(ncfile_raw):
    print "Updating output file: {}".format(ncfile_raw)
    ReadRaw.updatencd(x, y1, y2, y3, z, ncfile_raw)
  else:
    print "Creating output file: {}".format(ncfile_raw)
    ReadRaw.createncd(x, y1, y2, y3, z, height, ncfile_raw)
else:
  print "Nothing to do"
  print "Waiting for new data"
print "******** Done ! **********"
