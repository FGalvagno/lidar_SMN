#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import scipy.integrate as integrate
from . import Physics
import pickle

"""
#PARA NIES
thVFMac = 0.0000005 # Molecule/Aerosol
thVFMar = 0.000003  # Aerosol/Unknown
thVFMra = 0.000009  # Unknown/rain-fog
thVFMcl = 0.00001   # cloud
"""

#PARA SMN
thVFMac = 0.0005 # Molecule/Aerosol
thVFMar = 0.003  # Aerosol/Unknown
thVFMra = 0.009  # Unknown/rain-fog
thVFMcl = 0.01   # cloud

# TIPOS DE AEROSOLES
UNDEFINED      = -1
NO_DATA        = 0
NOISY          = 1
MOLECULE       = 2
CLEAN          = 3
AEROSOL        = 4
UNKNOWN        = 5
RAIN_FOG_CLOUD = 6
CLOUD          = 7
SATURATED      = 8
UNKNOWN2       = 9 # REVISAR!!!!


def classify_tomoaki(absc1064, alt, NT, NZ1, stationHeight):
    print(("Altura de estacion: ", stationHeight))
    # Levantamos absc.
    #plt.plot(np.log(np.abs(absc1064[:,0])), range(NZ1), 'r')
    #plt.show()
    #print("absc1064: ", absc1064)
    # Transposicion...
    #print("absc1064: ", absc1064)
    mask = np.zeros((NT, NZ1))
    # Calculos moleculares
    alturasMetros = [0.0]
    for i in range(0, NZ1):
        alturasMetros.append(1000.0*alt[i])
    #print("Alturos Metros: ", alturasMetros)
    np_alturas_metros = np.array(alturasMetros)
    betaR, alfaR = Physics.rayleigh(np_alturas_metros, 1064.0, stationHeight)
    #print("Beta: ", betaR)
    #print("Alfa: ", alfaR)
    optM_array = integrate.cumtrapz(alfaR, alturasMetros)
    #print("OptM: ", optM_array)
    #
    for indexT in range(0, NT):
        if indexT % 50 == 0:
          print(("INdex T: ", indexT))
        # ACA SE DEBE HACER EL ALGORITMO DE NISHIZAWA.
        lower = NZ1 - 50
        upper = NZ1
        tail = absc1064[indexT, lower:upper].copy()
        for indexA in range(lower, upper):
            tail[indexA - lower] = tail[indexA - lower] / (alt[indexA]**2.0)
        #print("Tail: ", tail)
        #sys.exit(0)
        std = np.nanstd(tail)
        #print("std: ", std)
        stdNoise = np.zeros(NZ1)
        for indexA in range(0, len(stdNoise)):
            stdNoise[indexA] = std * (alt[indexA]**2.0)
        #print ("Absc \t StdNoise")
        #for i in range(NZ1):
        #    print(str(absc1064[indexT, i]) + "\t" + str(stdNoise[i]))
        #plt.plot(np.log(np.abs(absc1064[indexT,:])), range(NZ1), 'r')
        #plt.plot(np.log(stdNoise), range(NZ1), 'b')
        #plt.show()
        #print("absc1064: ", absc1064[indexT,:])
        #sys.exit(0)
        #print("Absc 1064: ", absc[indexT,:])
        #print("StdNoise: ", stdNoise)
        bn_array = np.zeros(NZ1)
        th2_array = np.zeros(NZ1)
        th3_array = np.zeros(NZ1)
        th4_array = np.zeros(NZ1)
        for indexA in range(0, NZ1):
            bn = absc1064[indexT, indexA]
            #bn = bn*1000 # Prueba, no cambio mucho.
            bnns = stdNoise[indexA]
            bscM = betaR[indexA] 
            optM = optM_array[indexA] 
            th0 = -1.0
            th1 = 3.0*bnns
            th2 = 3.0*bnns + bscM*np.exp(-2.0*optM)
            th3 = 3.0*bnns + (bscM+thVFMac)*np.exp(-2.0*optM)
            th4 = 3.0*bnns + (bscM+thVFMar)*np.exp(-2.0*optM)            
            th5 = 3.0*bnns + (bscM+thVFMra)*np.exp(-2.0*optM)            
            th6 = 3.0*bnns + (bscM+thVFMcl)*np.exp(-2.0*optM)            
            th7 = 0.9e10
            maskPos = UNDEFINED
            if (bn <= th0 or np.isnan(bn)):
                maskPos = NO_DATA
            elif (bn > th0 and bn <= th1):
                maskPos = NOISY
            elif (bn > th1 and bn <= th2):
                maskPos = MOLECULE
            elif (bn > th2 and bn <= th3):
                maskPos = CLEAN
            elif (bn > th3 and bn <= th4):
                maskPos = AEROSOL
            elif (bn > th4 and bn <= th5):
                maskPos = UNKNOWN
            elif (bn > th5 and bn <= th6):
                maskPos = RAIN_FOG_CLOUD
            elif (bn > th6 and bn <= th7):
                maskPos = CLOUD
            else:
                maskPos = SATURATED
            mask[indexT, indexA] = maskPos
            bn_array[indexA] = bn
            th2_array[indexA] = th2
            th3_array[indexA] = th3
            th4_array[indexA] = th4
        if indexT == 40:
            #plt.plot(range(NZ1), np.log10(np.abs(bn_array)), 'r')
            #plt.plot(range(NZ1), np.log10(th2_array), 'b')
            #plt.plot(range(NZ1), np.log10(th3_array), 'c')
            #plt.plot(range(NZ1), np.log10(th4_array), 'm')
            #plt.show()
            #sys.exit(0)
            pass
    nvfm = np.zeros((NT, NZ1))
    for indexT in range(0, NT):
        for indexA in range(0, NZ1):
            nvfm[indexT, indexA] = mask[indexT, indexA]
    # Dense aerosol at lower layer adjustment.
    for indexT in range(0, NT):
        for indexA in range(0,NZ1):
            if alt[indexA] <= 0.1: # La altura menor a 100 metros...
                if (nvfm[indexT, indexA] == RAIN_FOG_CLOUD or nvfm[indexT, indexA] == CLOUD):
                    nvfm[indexT, indexA] = UNKNOWN
                    mask[indexT, indexA] = UNKNOWN
    # Around Cloud adjustment.
    for indexT in range(0,NT):
        for indexA in range(0,NZ1):
            if mask[indexT, indexA] >= CLOUD:
                for itt in range(-1,2):
                    for iaa in range(-3,4):
                        ittt = indexT + itt
                        iaaa = indexA + iaa
                        if ittt < 0 or ittt >= NT:
                            continue
                        elif iaaa < 0 or iaaa >= NZ1:
                            continue
                        elif np.isnan(absc1064[ittt, iaaa]):
                            continue
                        elif (nvfm[ittt, iaaa] >=CLEAN and nvfm[ittt, iaaa] <=UNKNOWN):
                            nvfm[ittt, iaaa] = RAIN_FOG_CLOUD
    
    # Above cloud/rain/fog
    for indexT in range(0,NT):
        for indexA in range(0,NZ1):
            if nvfm[indexT, indexA] >= RAIN_FOG_CLOUD and indexA < NT - 1:
                for iaa in range(indexA + 1, NZ1):
                    if nvfm[indexT, iaa] <= UNKNOWN and nvfm[indexT, iaa]  >= NOISY:
                        nvfm[indexT, iaa] = UNKNOWN2
                        
                
    # Reescribimos la mascara.
    #for i in range(NT):
    #    for j in range(NZ1):
    #        nvfm[i,j] = 5.0
    #ncFile.variables["mask"][:,:] = nvfm[:,:]
    #ncFile.close()
    return nvfm

def get_ash_concentration(NT, NZ1, absc1064, absc532, mask, fname):
    color_ratio = np.zeros((NT, NZ1))
    for i in range(NT):
        for j in range(NZ1):
            color_ratio[i,j] = absc532[i,j] / absc1064[i,j]
    logAbsc1064 = np.log(absc1064)
    # Cargamos el discriminador.
    ash_mask = np.zeros((NT, NZ1))
    ash_conc = np.zeros((NT, NZ1))
    with open(fname, 'rb') as f:
        # The protocol version used is detected automatically, so we do not
        # have to specify it.
        disc = pickle.load(f)
        for i in range(NT):
            for j in range(NZ1):
                log_bsc = logAbsc1064[i,j]
                colorR = color_ratio[i,j]
                if mask[i,j] >= AEROSOL and mask[i,j] <= CLOUD:
                    label = disc.predict([(log_bsc, colorR)])[0]
                    if label == 1:
                        ash_mask[i,j] = 1
                        ash_conc[i,j] = 1.5*50.0*absc1064[i,j]
                    else:
                        ash_mask[i,j] = 0
                        ash_conc[i,j] = 0.0
                else:
                    ash_mask[i,j] = 0
                    ash_conc[i,j] = 0.0
                    
    return ash_mask, ash_conc


