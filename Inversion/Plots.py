#!/usr/bin/python
import matplotlib
matplotlib.use('Agg') 

import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as axisartist
from matplotlib.dates import DayLocator, HourLocator, DateFormatter
from matplotlib.colors import LinearSegmentedColormap,ListedColormap,BoundaryNorm
from matplotlib.ticker import LogFormatterMathtext
from netCDF4 import num2date, date2num
import warnings

################# Parameters ###############################################
NMAX     = 1E6
ratio    = 1E-3                                                              # Aspect ratio km/min
Debug    = True
############################################################################

### Color map creation
colors1    = plt.cm.jet(np.linspace(0, 1, 256))
startcolor = np.array([1,1,1,1])
endcolor   = colors1[0]
cmap       = LinearSegmentedColormap.from_list('own',[startcolor,endcolor])
colors2    = cmap(np.linspace(0, 1, 72))
colors     = np.vstack((colors2, colors1))
my_cmap    = LinearSegmentedColormap.from_list('colormap', colors)

def build_palette4(l1,l2,l3,l4):
  levs  = l1+l2+l3+l4
  
  cm1   = LinearSegmentedColormap.from_list("",["#000080", "#00b2ee"])
  cm2   = LinearSegmentedColormap.from_list("",["#ffff00", "#ff0000"])
  cm3   = LinearSegmentedColormap.from_list("",["#ff0000", "#bebebe"])
  cm4   = LinearSegmentedColormap.from_list("",["#bebebe", "#ffffff"])

  cl1   = cm1(np.linspace(0,1.,len(l1)+1, endpoint=True))
  cl2   = cm2(np.linspace(0,1.,len(l2),   endpoint=False))
  cl3   = cm3(np.linspace(0,1.,len(l3),   endpoint=False))
  cl4   = cm4(np.linspace(0,1.,len(l4),   endpoint=True))

  rgb   = np.vstack([cl1,cl2,cl3,cl4])

  cmap  = ListedColormap(rgb[1:-1], name="Caliop")
  norm  = BoundaryNorm(levs, ncolors=len(levs)-1, clip=False)
  cmap.set_under( rgb[0]  )
  cmap.set_over(  rgb[-1] )
  return cmap,norm

def resampling(x, data, z, maxalt, maxdays):
  NX = len(x)
  NZ = len(z)
  
  day_0 = x[0]
  units = day_0.strftime("minutes since %Y-%m-%d 00:00:00")
  xm    = date2num(x,units=units)

  DX    = xm[1]-xm[0]
  DZ    = z[1]-z[0]
  DZinv = 1.0/DZ
  if maxalt>0:
    NZ0 = int(round(maxalt * DZinv))
    if NZ0<NZ: NZ=NZ0
  if maxdays>0:
    profiles_per_day = 1440/DX
    NX0 = int(round(maxdays*profiles_per_day))
    if NX0<NX: NX=NX0
  
  N  = NX*NZ
  if Debug: print("Original data: {} points".format(N))
  wz = 1
  wx = 1
  while N>NMAX:
    if DX*DZinv*ratio>1.0: 
      wz = 2*wz
      DZinv = 0.5 * DZinv
    else: 
      wx = 2*wx
      DX = 2*DX
    N = 0.5*N

  NZ   = NZ - NZ%wz
  NX   = NX - NX%wx
  data = data[:NZ,-NX:]

  zmax = z[NZ-1]
  xmin = xm[-NX]
  
  if wz>1:
    if Debug: print("Using vertical rebin with wz={}".format(wz))
    NZ = NZ/wz
    data_wz = np.full((NZ,NX),np.nan)
    for it in range(NX):
      if not np.all(np.isnan(data[:,it])):
        data_wz[:,it] = np.nanmean(data[:,it].reshape(-1, wz), axis=1)
  else:
    data_wz = np.copy(data)

  if wx>1:
    if Debug: print("Using horizontal rebin with wx={}".format(wx))
    NX = NX/wx
    data_wzwx = np.full((NZ,NX),np.nan)
    with warnings.catch_warnings():
      # I expect to see RuntimeWarnings in this block
      warnings.simplefilter("ignore", category=RuntimeWarning)
      for iz in range(NZ):
        data_wzwx[iz,:] = np.nanmean(data_wz[iz,:].reshape(-1, wx), axis=1)
  else:
    data_wzwx = data_wz

  z_wz = np.linspace(0,zmax,NZ+1)
  x_wx = num2date([xmin + i*DX for i in range(NX+1)], units=units)

  return x_wx, data_wzwx, z_wz

def get_figure(automatic):
  fig = plt.figure(figsize=(16,6))
  ax  = fig.add_subplot(axisartist.Subplot(fig, "111"))
  
  if not automatic:
    ax.xaxis.set_major_locator( DayLocator() )
#    ax.xaxis.set_minor_locator( DayLocator(range(2,32,2)) )
  ax.xaxis.set_major_formatter( DateFormatter('%d\n%b') )
  ax.xaxis.set_minor_formatter( DateFormatter('%d') )
  ax.autoscale_view()
  ax.axis["bottom"].major_ticklabels.set_va('top')
  ax.axis["bottom"].toggle(ticklabels=True)
  ax.axis["top"].toggle(all=False) 
 
  ax.axis[:].major_ticks.set_tick_out(True)
  
  ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M')
  fig.autofmt_xdate()
  return fig, ax
  
def show_raw(x,data,z,filename,maxalt=0.0,maxdays=0.0):
  x_low, data_low, z_low = resampling(x,data,z,maxalt,maxdays)
  fig, ax = get_figure(True)

  CS    = ax.pcolormesh(x_low,z_low,data_low, cmap=my_cmap, vmin=0, vmax=20)
  cbar  = plt.colorbar(CS)
  cbar.set_label(r"Signal strength [$mv \times km^2$]", labelpad=-63)

  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(filename, bbox_inches='tight', dpi=150)
  
def show_beta(x,data,z,fname="attbsc.png",label="Attenuated Backscatter coefficient",maxalt=0.0,maxdays=0.0):
  x_low, data_low, z_low = resampling(x,data,z,maxalt,maxdays)
  data_low = np.ma.masked_invalid(data_low)

  levs1 = [i*1E-4 for i in [1,2,4,6,8,10] ]
  levs2 = [i*1E-3 for i in [1.25,1.5,1.75,2,2.25,2.5,2.75,3] ]
  levs3 = [i*1E-3 for i in [4,5,6] ]
  levs4 = [i*1E-3 for i in [7,8,9,10,20,40,60,80,100] ]
  my_cmap,my_norm = build_palette4(levs1,levs2,levs3,levs4)

  auto_tick = maxdays>12
  fig, ax   = get_figure(auto_tick)
  CS        = ax.pcolormesh(x_low, z_low, data_low,
                            cmap = my_cmap,
                            norm = my_norm,
                            )
  my_ticks  = np.array([1E-4,1E-3,1E-2,1E-1])
  cbar      = plt.colorbar(CS,
                           ticks=my_ticks, 
                           extend='both',
                           format=LogFormatterMathtext(),
                           orientation='horizontal',
                           aspect=30,
                           shrink=0.6, 
                           )
  ax.set_title(label + r" $[/sr \, /km]$")
  ax.patch.set(hatch='/', edgecolor='black')

  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(fname, bbox_inches='tight', dpi=150)
  
def show_alpha(x,data,z,zb,zt,zc,filename,maxalt=0.0,maxdays=0.0):
  x_low, data_low, z_low = resampling(x,data,z,maxalt,maxdays)
  fig, ax = get_figure(True)

  masked = np.ma.array (data_low, mask=np.isnan(data_low))
    
  tick  = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
  CS    = ax.pcolormesh(x_low,z_low,masked, cmap=my_cmap, vmin=0, vmax=0.5)
  cbar  = plt.colorbar(CS, ticks=tick)
  cbar.set_label(r"Extinction coefficient $[/km]$", labelpad=-63)
  
  with np.errstate(invalid='ignore'):
    NX = len(x)
    zz = [min(zt[i],maxalt) for i in range(NX)]
    ax.fill_between(x, zb, zz,     where=zb<maxalt, color='black', alpha=0.8)
    ax.fill_between(x, zc, maxalt, where=zc<maxalt, color='green', alpha=0.1)
#    ax.fill_between(x,  0, zmax, where=np.all(np.isnan(data), axis=0),color='green', alpha=0.1)

  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(filename, bbox_inches='tight', dpi=150)
  
def show_dep(x,data,z,filename,maxalt=0.0,maxdays=0.0):
  x_low, data_low, z_low = resampling(x,data,z,maxalt,maxdays)
  fig, ax = get_figure(True)

  masked = np.ma.array (data_low, mask=np.isnan(data_low))
  
  tick  = np.array([0.0, 0.1, 0.2, 0.3])
  CS    = ax.pcolormesh(x_low, z_low, masked, cmap=my_cmap, vmin=0, vmax=0.3)
  cbar  = plt.colorbar(CS, ticks=tick)
  cbar.set_label(r"Volume Depolarization Ratio", labelpad=-63)

  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(filename, bbox_inches='tight', dpi=150)
  
def show_cal(x,data,z,zb,zt,filename,maxalt=0.0,maxdays=0.0):
  x_low, data_low, z_low = resampling(x,data,z,maxalt,maxdays)
  fig, ax = get_figure(True)

  CS    = ax.pcolormesh(x_low,z_low,data_low, cmap=my_cmap, vmin=0, vmax=2E5)
  cbar  = plt.colorbar(CS)
  cbar.set_label(r"Signal strength [$u.a.$]", labelpad=-80)

  ax.plot(x,zb,'ro',ms=4,label="Cloud base")
  ax.plot(x,zt,'go',ms=4,label="Cloud top")
  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(filename, bbox_inches='tight', dpi=150)

def show_ash(x,data,z,filename):
  fig, ax = get_figure(True)

  CS    = ax.pcolormesh(x, z, data.T, cmap=my_cmap)
  cbar  = plt.colorbar(CS)
  cbar.set_label(r"Ash concentration ($mg\,m^{3}$)")

  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(filename, bbox_inches='tight', dpi=150)

def show_mask(x,data,z,filename):
  fig, ax = get_figure(True)

  cmap_disc = plt.get_cmap('gist_ncar', 11)

  CS    = ax.pcolormesh(x, z, data.T, cmap=cmap_disc, vmin=-1.5, vmax=9.5)
  cbar  = plt.colorbar(CS, ticks=np.arange(-1,10))
  cbar.set_label(r"Classes")
  cbar.ax.set_yticklabels(['Undefined', 
                           'No Data', 
                           'Noisy', 
                           'Molecule', 
                           'Clean', 
                           'Aerosol', 
                           'Unknown', 
                           'Rain-Fog', 
                           'Cloud', 
                           'Saturated',
                           'Unknown2'])


  plt.xlabel('')
  plt.ylabel('Height AGL [km]')
  fig.savefig(filename, bbox_inches='tight', dpi=150)
  
def histo(hist, bin_edges):
  fig = plt.figure()
  ax = fig.add_subplot(111)
  ax.bar(bin_edges[:-1], hist, width=0.05)
  fig.savefig("histogram.png", bbox_inches='tight', dpi=150)
  
def xy(x, y, params, filename):
  fig = plt.figure()
  ax = fig.add_subplot(111)
  ax.plot(x,y,'ro')
  ax.plot(x,x*params[0]+params[1],'k-')
  if filename=='calibration.png':
    plt.xlabel(r"Visible signal (calibrated) $[u.a.]$")
    plt.ylabel(r"IR signal $[mV \, km^{2}]$")
  else:
    plt.xlabel(r"Parallel signal $[mV \, km^{2}]$")
    plt.ylabel(r"Perpendicular signal $[mV \, km^{2}]$")
  fig.savefig(filename, bbox_inches='tight', dpi=150)
