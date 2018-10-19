#!/usr/bin/python

import numpy as np
from parse import parse
import struct

################# Parameters ####################
Debug = True
#################################################

class GlobalParameters(object):
  def __init__(self,line1,line2,line3):
    self.Name            = line1.strip()

    s=parse("{} {:tg} {:tg} {:g} {:f} {:f} {:g}",line2.strip())
    self.Station         = s[0]
    self.Start           = s[1]
    self.End             = s[2]
    self.HeightASL       = s[3]
    self.Longitude       = s[4]
    self.Latitude        = s[5]
    self.ZenithAngle     = s[6]

    s=parse("{:d} {:d} {:d} {:d} {:d}",line3.strip())
    self.Laser1Shots     = s[0]
    self.Laser1Frequency = s[1]
    self.Laser2Shots     = s[2]
    self.Laser2Frequency = s[3]
    self.NumChannels     = s[4]

class Channel(object):
  def __init__(self,line):
    s=parse("{:d} {:d} {:d} {:d} {:d} {:g} {:f} {:d}.{:w} 0 0 00 000 {:d} {:d} {:g} {:w}{:d}",line.strip())
    self.isActive         = s[0]==1
    if s[1]==1:
      self.isPhotonCounting = 'p'
    else:
      self.isPhotonCounting = 'o'
    self.LaserNumber      = s[2]
    self.Bins             = s[3]
    self.isHV             = s[4]
    self.Votage           = s[5]
    self.BinSize          = s[6]
    self.Wavelength       = s[7]
    self.isPolarized      = s[8]
    self.ADC              = s[9]
    self.Shots            = s[10]
    if self.Shots==0:
      self.Shots=301
      if Debug: print "Assuming {} shots".format(self.Shots)
    if self.isPhotonCounting=='p': 
      self.Scale          = s[11]
    else: 
      self.Scale          = s[11] * 1000.0 
    self.Transien         = s[13]

    self.Key              = "{}{}{}".format(self.Wavelength,
	        	                            self.isPolarized,
	        	                            self.isPhotonCounting)

  def set_data(self, data):
    if self.isPhotonCounting=='p':
      ScaleFactor = 150.0/self.BinSize             # Signal [MCPS] (Mega Counts Per Second)
    else:
      ScaleFactor = self.Scale / (2**self.ADC - 1) # Signal [mV].
    self.Signal = data * ScaleFactor / self.Shots  # Signal [MCPS] or [mV]
    self.Range  = ( np.arange(self.Bins)+1 ) * self.BinSize  # Range [m]

class LoadLicel(object):
  """
  Description:
  Function that Loads Licel data recorded by Licel VI's
 
  Input Parameters:
  FileName: The LICEL File Name
 
  Output Structure:
 
  data
      |
      |
      |_ GlobalParameters
      |                 |_ HeightASL       : Station Height             [m]
      |                 |_ Latitude        : Station Latitude         [deg]
      |                 |_ Longitude       : Station Longitude        [deg]
      |                 |_ ZenithAngle     : Laser Zenith Angle       [deg]
      |                 |_ Laser1Shots     : Number of Acquired Shots   [-]
      |                 |_ Laser1Frequency : Laser Repetition Rate     [Hz]
      |                 |_ Laser2Shots     : Number of Acquired Shots   [-]
      |                 |_ Laser2Frequency : Laser Repetition Rate     [Hz]
      |                 |_ Channels        : Active Channels            [-]
      |
      |_ Channel
                |_ isActive         : Is it active? (T/F)               [-] 
                |_ isPhotonCounting : Is PhCount (T) or Analog (F)?     [-]
                |_ LaserNumber      : To which Laser is it associated?  [-]
                |_ Bins             : Number of acquired bins           [-]
                |_ isHV             : (T) for HV on                     [-]
                |_ Votage           : Voltage of the PMT / APD          [V]
                |_ BinSize          : Size of the bin                   [m]
                |_ Wavelength       : Detection wavelength             [nm]
                |_ ADC              : Number of eq. bits of the ADC     [-]
                |_ Shots            : Number of acquired shots          [-]
                |_ Scale            : Voltage scale or Threshold level [mV]
                |_ Transient        : Associated transient recorder     [-]
                |_ Signal           : Signal                 [mV] or [MCPS]
                |_ Range            : Altitude Scale                [m AGL]
                |_ Time             : Time Scale from first record  [hours]
 
  or data = -1 if there is an error
  """
  def __init__(self, fname, channel_list):
    self.channel = {}
    try:
      with open(fname, mode='rb') as file:
      	l1 = file.readline()
      	l2 = file.readline()
      	l3 = file.readline()
        self.GlobalP = GlobalParameters(l1,l2,l3)
        channels = []
        for i in range(self.GlobalP.NumChannels):
	        new_channel = Channel(file.readline())
	        channels.append(new_channel)
        #Reading binary data...
        offset = 0
        for item in channels:
          if item.Key in channel_list: 
            #print "Found: {}".format(item.Key)
            file.seek(offset+2,1)
            item.set_data(np.fromfile(file,dtype="<u4",count=item.Bins))
            self.channel[item.Key] = item
            offset = 0
          else:
            offset += 4*item.Bins + 2
    except IOError as e:
      print "I/O error({0}): {1}".format(e.errno, e.strerror)

def load355(fname):
  try:
    with open(fname, mode='rb') as file:
      file.seek(20)
      return np.fromfile(file,dtype="<u4")
  except IOError as e:
    print "I/O error({0}): {1}".format(e.errno, e.strerror)
    return False

if __name__ == "__main__":
  import matplotlib.pyplot as plt

  path="./"
  fname="a1841517.453007"
  a=LoadLicel(path+fname, ["355oo","532oo","532po","1064oo"])

  fig, ax = plt.subplots()

  z  = a.channel["1064oo"].Range
  y =[]
  for item in a.channel.keys(): 
    print item
    ax.semilogx(z,a.channel[item].Signal,label=item)
  print a.GlobalP.HeightASL
  print a(0)

  #ax.set_ylim([3.65E6,3.69E6])
  #ax.legend()
  plt.show()
  	#print file.readline()
  	#for item in range(20): f.read(4)
  	#f.seek(25, 1)
  	
