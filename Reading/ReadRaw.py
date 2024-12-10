#!/usr/bin/python2

from .LoadLicel import LoadLicel
from netCDF4   import Dataset, num2date, date2num
from datetime  import datetime, timedelta, time
import numpy as np
import os
from os.path import isfile, join

################# Parameters ###############################################
dt           = timedelta(minutes=1)                                        # Delta time (1 min). NO CHANGE
#FileSize = 82492                                                          # Filesize in bytes
fmt          = "%y%m%d%H.%M%S"                                             # Format file
channel_list = ["532oo","532po","1064oo"]
Debug        = True
############################################################################

def read_firstline(fname):
  with open(fname,'r') as f:
    output = f.readline()
  return output.strip()

def valid_files(prefix,tdate,bpath,FileSize):
  folder = bpath + tdate.strftime("%Y%m%d/")
  bname  = prefix + tdate.strftime("%y") + format(tdate.month,'X') + tdate.strftime("%d")
  
  verify_name = lambda x: bname in x and len(x)==15
  verify_size = lambda x: os.stat(folder + x).st_size == FileSize
  verify_head = lambda x: read_firstline(folder + x) == x
  verify_file = lambda x: verify_name(x) and verify_size(x) and verify_head(x)
  
  filelist_folder = [f for f in os.listdir(folder) if isfile(join(folder, f))]
  filelist_folder = list(filter(verify_file, filelist_folder))
  filelist_folder.sort()
  return filelist_folder

def parse_datetime(st):
  date_st = st[1:3] + "{:02d}".format(int(st[3],16)) + st[4:13]
  return datetime.strptime(date_st, fmt)

def findtimes(t1,t2,sampling,bpath,prefix,ncfile,FileSize):
  print("File checking assuming size: {} B".format(FileSize))
  if isfile(ncfile):
    if Debug: print("Found file: ", ncfile)
    ncfile = Dataset(ncfile,'r',format="NETCDF3_CLASSIC") 
    t      = ncfile.variables["time"]
    t1_raw = num2date(t[-1], units = t.units)
    ncfile.close()
  else:
    if Debug: print("Not found file: ", ncfile)
    td = t1.date()
    SearchFile = True
    while td<=t2.date() and SearchFile:
      folder = td.strftime("%Y%m%d/")
      if os.path.exists(bpath + folder): 
        filelist_folder = valid_files(prefix,td,bpath,FileSize)
        if filelist_folder:
          if t1<=parse_datetime(filelist_folder[0]):
            SearchFile = False
            t1_raw     = parse_datetime(filelist_folder[0])
          elif t1<=parse_datetime(filelist_folder[-1]):
            SearchFile = False
            t1_raw     = next(parse_datetime(x) for x in filelist_folder if parse_datetime(x)>=t1) 
      td += timedelta(days=1)
    if SearchFile: t1_raw = t2
  
  td = t2.date()
  SearchFile = True
  while td>=t1_raw.date() and SearchFile:
    folder = td.strftime("%Y%m%d/")
    if os.path.exists(bpath + folder): 
      filelist_folder = valid_files(prefix,td,bpath,FileSize)
      if filelist_folder:
        if t2>parse_datetime(filelist_folder[-1]):
          SearchFile = False
          t2_raw     = parse_datetime(filelist_folder[-1])
        elif t2>parse_datetime(filelist_folder[0]):
          SearchFile = False
          t2_raw     = next(parse_datetime(x) for x in reversed(filelist_folder) if parse_datetime(x)<t2) 
    td -= timedelta(days=1)
  if SearchFile: t2_raw = t1_raw

  dt_shift1 = timedelta( minutes = int((t1_raw-t1).total_seconds()//60.0)%sampling, 
                        seconds = t1_raw.second
                       )
  dt_shift2 = timedelta( minutes = int((t2_raw-t1).total_seconds()//60.0)%sampling, 
                        seconds = t2_raw.second
                        )  
  return t1_raw-dt_shift1, t2_raw-dt_shift2
  
def get_data(t1,t2,sampling,path,prefix,FileSize):
  x_time=[]
  t=t1
  while t<=t2:
    x_time.append(t)
    t=t+sampling*dt
  NT=len(x_time)
  x_time    = np.array(x_time)
  n_data    = np.zeros(NT)
  FileFound = False
  td = t1.date()
  while td<=t2.date():
    folder = td.strftime("%Y%m%d/")
    if os.path.exists(path + folder):
      filelist_folder = valid_files(prefix,td,path,FileSize)
      if filelist_folder:
        if Debug: print("Reading folder: ", folder)
        for file_item in filelist_folder:
          file_date = parse_datetime(file_item)
          i_time    = int((file_date-t1).total_seconds()//(60.0*sampling))
          if 0<=i_time<NT:
            n_data[i_time] = n_data[i_time] + 1
            # Get Licel data
            x = LoadLicel(path + folder + file_item, channel_list)
            if not FileFound:
              FileFound = True
              height = x.GlobalP.HeightASL
              z      = x.channel["532oo"].Range * 0.001      # Height in kilometers
              NZ     = len(z)
              y1     = np.zeros((NT,NZ))
              y2     = np.zeros((NT,NZ))
              y3     = np.zeros((NT,NZ))
            y1[i_time,:] += x.channel["532oo"].Signal
            y2[i_time,:] += x.channel["532po"].Signal
            y3[i_time,:] += x.channel["1064oo"].Signal
    td += timedelta(days=1)
  for it in range(NT):
    if n_data[it]==0:
      y1[it,:] = np.nan
      y2[it,:] = np.nan
      y3[it,:] = np.nan        
    else:
      #print x_time[it], n_data[it], np.max(y1[it,:])
      y1[it,:] = y1[it,:] / n_data[it]
      y2[it,:] = y2[it,:] / n_data[it]
      y3[it,:] = y3[it,:] / n_data[it]
  return x_time, y1, y2, y3, z, height
  
def createncd(x, data1, data2, data3, z, height, ncfilename):
  NT = len(x)
  NZ = len(z)
  print("**********************")
  print("Creating file: {}".format(ncfilename))
  #Dimensions
  ncfile = Dataset(ncfilename,'w',format="NETCDF3_CLASSIC") 
  ncfile.createDimension("time", None)
  ncfile.createDimension("alt", NZ)

  #Coordinate variables
  time = ncfile.createVariable("time","f4",("time",))
  altitude = ncfile.createVariable("alt","f4",("alt",))

  #Coordinate variable attributes
  altitude.units = "km"
  altitude.description = "altitude"
  altitude[:] = z

  day_0 = datetime(x[0].year,x[0].month,x[0].day)
  time.units = day_0.strftime("minutes since %Y-%m-%d 00:00:00")
  time.description = "time after 0000UTC"
  time[:] = [item.total_seconds()/60.0 for item in x-day_0]

  #Variables
  ch1 = ncfile.createVariable("ch1","f4",("time","alt",))
  ch1.units = "mV"
  ch1.description = "532-nm channel - component: o"
  ch1[:,:] = data1

  ch2 = ncfile.createVariable("ch2","f4",("time","alt",))
  ch2.units = "mV"
  ch2.description = "532-nm channel - component: p"
  ch2[:,:] = data2

  ch3 = ncfile.createVariable("ch3","f4",("time","alt",))
  ch3.units = "mV"
  ch3.description = "1064-nm channel"
  ch3[:,:] = data3

#Global Attributes
  ncfile.TITLE  = "LIDAR data from Licel"
  ncfile.YEAR   = day_0.year
  ncfile.MONTH  = day_0.month
  ncfile.DAY    = day_0.day
  ncfile.HEIGHT = height

  ncfile.close()
  print("Done!")
  print("**********************")
  
def updatencd(x, data1, data2, data3, z, ncfilename):
  NT = len(x)
  NZ = len(z)
  print("**********************")
  print("Updating file: {}".format(ncfilename))
  ncfile = Dataset(ncfilename,'a',format="NETCDF3_CLASSIC") 
  #Dimensions
  NT_file = len(ncfile.dimensions["time"])
  NZ_file = len(ncfile.dimensions["alt"])
  #Variables
  t       = ncfile.variables["time"]
  t_end   = num2date(t[-1], units = t.units)
  ch1     = ncfile.variables["ch1"]
  ch2     = ncfile.variables["ch2"]
  ch3     = ncfile.variables["ch3"]
  
  #Check file consistence  
  if NZ==NZ_file and x[0]==t_end:
    for it in range(NT):
      t[NT_file+it-1]     = date2num(x[it], units = t.units)
      ch1[NT_file+it-1,:] = data1[it,:]
      ch2[NT_file+it-1,:] = data2[it,:]
      ch3[NT_file+it-1,:] = data3[it,:]
  else:
    print("Error: File is not consistent with input data")

  ncfile.close()
  print("Done!")
  print("**********************")

if __name__ == "__main__":
  FileSize = 66042
  sampling = 15
  prefix   = "a"
  path     = "/home/leonardo/Desktop/aeroparque/"
  ncfile   = "void"
  t1       = datetime(2019,3,20,11,0)
  t2       = datetime(2019,3,24,23,46)
  t1_out, t2_out = findtimes(t1,t2,sampling,path,prefix,ncfile,FileSize)
  print(t1_out, t2_out)
  #lista = valid_files('a',datetime(2018,3,26),path,66042)
  #print len(lista)