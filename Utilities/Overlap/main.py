#!/usr/bin/env python2

import matplotlib
matplotlib.use('GTKAgg') 
import matplotlib.pyplot as plt
import numpy as np
from Plots import show_raw
from Overlap import SelectPoint
from netCDF4 import Dataset, num2date
from configparser import SafeConfigParser
from datetime import datetime
from os.path import isfile, join, dirname, abspath
import sys

################# Parameters ###############################################
cfgfile    = "parameters.cfg"
block      = "aeroparque"
varname    = "ch3"                                                         # Channel
yrfile     = 'overlap.cfg'                                                 # Overlap file
t1         = datetime(year=2018, month=10, day=4, hour=17, minute=0)       # Start date and time
t2         = datetime(year=2018, month=10, day=4, hour=18, minute=30)       # Final date and time
Plot       = False
Smooth     = False
Debug      = True
############################################################################

cfgpath    = dirname(__file__)
cfgpath    = join(cfgpath,"../..")
cfgpath    = abspath(cfgpath)
cfgfile    = join(cfgpath, cfgfile)

config     = SafeConfigParser()
config.read(cfgfile)

#Read parameters from an external file (string case)
station    = config.get(block, "prefix")
wsmooth    = config.getint(block, "wsmooth")
ncpath_raw = config.get("Paths", "ncpath_raw")
ncfile_raw = config.get("Paths", "ncfile_raw")
ncfile_raw = join(ncpath_raw,station+ncfile_raw)

if varname=='ch3':
  #Output file for IR channel
  yrfile = config.get("Paths", "yrfile_ir")
else:
  #Output file for Vis channel
  yrfile = config.get("Paths", "yrfile_vis")

if isfile(ncfile_raw):
	if Debug: print("Opening file: ", ncfile_raw)
	### Read Time, Data (mV), Heigth (km)
	ds       = Dataset(ncfile_raw)
	data     = ds.variables[varname][:]
	times    = ds.variables["time"]
	z        = ds.variables["alt"][:]
	x        = num2date(times[:],units=times.units)
	ds.close()
else:
	print("Unable to open file: ", ncfile_raw)
	sys.exit()

data = data.T 

### Number of profiles and vertical levels
NX = len(x)
NZ = len(z)

print("Time range in data: {} to {}".format(x[0],x[-1]))
print("Time range required: {} to {}".format(t1,t2))
if t1>t2:
	print("Swaping datetime range")
	t1, t2 = t2, t1
n1,n2 = np.searchsorted(x,[t1,t2])
if n1==NX:
	print("Please, redefine lower boundary in time range")
	sys.exit()
elif n2==0:
	print("Please, redefine higher boundary in time range")
	sys.exit()
else:
	n2 -= 1
print("Time range used: {} to {}".format(x[n1],x[n2]))

fig, axarr = plt.subplots(2)
#
axarr[0].set_xlabel(r'Lidar signal $[mV]$') 
axarr[0].set_ylabel(r'Altitude $[km]$')
#
axarr[1].set_xlabel(r'Range-corrected Lidar signal $[mV \, \, km^2]$')
axarr[1].set_ylabel(r'Altitude $[km]$')

#Plot Raw data
axarr[0].semilogy(data[:,n1:n2],z,'-')

#Obtain Range-corrected Lidar signal (RCLS)
if varname=='ch3':
  for it in range(NX):
    coeff = np.polyfit(z[-2000:], data[-2000:,it], 1)
    pol   = np.poly1d(coeff)
    data[:,it] = (data[:,it] - pol(z)) *z**2
elif varname=='ch2':
  for it in range(NX):
    coeff = np.polyfit(z[-1000:], data[-1000:,it], 1)
    pol   = np.poly1d(coeff)
    data[:,it] = (data[:,it] - pol(z)) *z**2
else:
  for it in range(NX):
    coeff = np.polyfit(z[-1000:], data[-1000:,it], 1)
    pol   = np.poly1d(coeff)
    data[:,it] = (data[:,it] - pol(z)) *z**2

### Smoothing
if Smooth:
  print("Performing smoothing with parameter wsmooth:{}".format(wsmooth))
  for it in range(NX):
    data[:,it] = np.convolve(data[:,it],np.ones(wsmooth)/wsmooth,mode='same')
    
if Plot:
  show_raw(x,data,z,maxalt=18.)

#Plot RCLS data
axarr[1].plot(data[:,n1:n2],z,'-')

if Debug: print("Output file: ", yrfile)

dr = SelectPoint(data[:,n1:n2],z,yrfile)

plt.show()