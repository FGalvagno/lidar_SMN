#!/usr/bin/env python2

import numpy as np
import matplotlib.pyplot as plt

class SelectPoint:
    def __init__(self,data,z,yrfile):
        self.yrfile = yrfile
        self.fig, self.axarr = plt.subplots(2, sharex=True)
        self.axarr[0].semilogx(data,z,'-')

        self.axarr[0].set_ylabel(r'Altitude $[km]$')
        self.axarr[1].set_ylabel(r'Altitude $[km]$')  
        self.axarr[1].set_xlabel(r'Range-corrected Lidar signal $[mV \, \, km^2]$')

        self.axarr[0].set_ylim([0,1])
        self.axarr[1].set_ylim([0,1])

        self.connect()
        self.points = 0
        self.zlim = []
        self.NZ = data.shape[0]
        self.NX = data.shape[1]
        self.data = data
        self.z    = z
        self.yr   = np.ones_like(z)

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.fig.canvas.mpl_connect(
            'button_press_event', self.on_press)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        self.zlim.append(event.ydata)
        self.points = self.points + 1
        print "Selected point #{}: x={} and y={}".format(self.points, event.xdata, event.ydata)
        if self.points == 2: 
          self.disconnect()
          self.zlim.sort()
          self.axarr[0].fill_between(self.axarr[0].get_xlim(),self.zlim[0],self.zlim[1])
          self.overlap_mean()
          for it in range(self.NX): self.data[:,it] = self.data[:,it] * self.yr
          self.axarr[1].semilogx(self.data,self.z,'-')
          self.fig.canvas.draw()
          print "Done!"

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.fig.canvas.mpl_disconnect(self.cidpress)

    def overlap(self):
        nmin = np.argmin(np.abs(self.z-self.zlim[0]))
        nmax = np.argmin(np.abs(self.z-self.zlim[1]))+1
        self.yr[:nmin] = 0.0
        nt = 0
        for it in range(self.NX):
          if not np.isnan(self.data[nmin:nmax,it]).any():
            nt = nt + 1
            #coeff = np.polyfit(self.z[nmin:nmax], np.log(self.data[nmin:nmax,it]), 1)
            coeff = np.polyfit(self.z[nmin:nmax], self.data[nmin:nmax,it], 1)
            pol   = np.poly1d(coeff)
            #self.yr[:nmin] = self.yr[:nmin] + np.exp(pol(self.z[:nmin])) / self.data[:nmin,it]
            self.yr[:nmin] = self.yr[:nmin] + pol(self.z[:nmin]) / self.data[:nmin,it]
        self.yr[:nmin] = self.yr[:nmin] / nt
        np.savetxt(self.yrfile, zip(self.z, self.yr), fmt='%0.8f', header='altitude (km) | overlap factor')    

    def overlap_mean(self):
        nmin  = np.argmin(np.abs(self.z-self.zlim[0]))
        nmax  = np.argmin(np.abs(self.z-self.zlim[1]))+1
        hmin  = 0.085
        arr   = np.mean(self.data[nmin:nmax,:],axis=1)
        arr2  = np.mean(self.data[:nmin,:],axis=1)
        #coeff = np.polyfit(self.z[nmin:nmax], np.log(arr), 1)
        coeff = np.polyfit(self.z[nmin:nmax], arr, 1)
        pol   = np.poly1d(coeff)
        #self.yr[:nmin] = np.exp(pol(self.z[:nmin])) / arr2
        self.yr[:nmin] = pol(self.z[:nmin]) / arr2
        for iz in range(nmin,0,-1):
          height = self.z[iz-1]
          yr_diff = self.yr[iz-1]-self.yr[iz]
          if arr2[iz-1]<0.0 and height>hmin: hmin = height
          if height<=hmin:
            self.yr[iz-1] = 1.0
#          elif yr_diff<0:
#            self.yr[iz-1]=self.yr[iz]
        print "We set yr=1 below of {} m".format(1000*hmin)
        print "Saving data..."
        np.savetxt(self.yrfile, zip(self.z, self.yr), fmt='%0.8f', header='altitude (km) | overlap factor')

#        ff, aa = plt.subplots()
#        aa.plot(self.yr[:nmin], self.z[:nmin],'o-')
#        aa.set_title('Overlap Factor')
#        ff.savefig('overlap.png', bbox_inches='tight', dpi=150)
#        plt.close(ff)

