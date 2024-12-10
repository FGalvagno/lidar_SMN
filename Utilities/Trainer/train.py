#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 11:23:29 2018
"""

#from configparser import SafeConfigParser
#from netCDF4 import Dataset
import os
import numpy as np
import matplotlib.pyplot as plt
import sys
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
import pickle
from matplotlib import colors


def generate_qda_advanced_plot():
    file_ash = "./AEP15_04_25_ash_time.txt"
    file_cloud = "./AEP16_12_13_cloud_time.txt"
    ash_data = np.loadtxt(file_ash, skiprows=1)
    cloud_data = np.loadtxt(file_cloud, skiprows=1)
    x_ash = np.log(ash_data[:,4])
    y_ash = ash_data[:,5]
    labels_ash = np.ones(len(x_ash))*1
    x_cloud = np.log(cloud_data[:,4])
    y_cloud = cloud_data[:,5]
    labels_cloud = np.ones(len(x_cloud))*2
    x_min = np.min( (np.min(x_ash), np.min(x_cloud)))
    x_max = np.max( (np.max(x_ash), np.max(x_cloud)))
    y_min = np.min( (np.min(y_ash), np.min(y_cloud)))
    y_max = np.max( (np.max(y_ash), np.max(y_cloud)))
    labels = np.zeros(len(x_ash) + len(x_cloud))
    x = np.zeros((len(x_ash) + len(x_cloud),2))
    for i in range(len(labels_ash)):
        labels[i] = labels_ash[i]
        x[i,0] = x_ash[i]
        x[i,1] = y_ash[i]
    for i in range(len(labels_cloud)):
        labels[i + len(labels_ash)] = labels_cloud[i]
        x[i + len(labels_ash), 0] = x_cloud[i]
        x[i + len(labels_ash), 1] = y_cloud[i]
    print(("X: ", x))
    print(("Labels: ", labels))
    disc = QuadraticDiscriminantAnalysis()
    disc.fit(x, labels)
    # Grafica.
    x_grid = np.linspace(x_min, x_max, 100)
    y_grid = np.linspace(y_min, y_max, 100)
    data = np.zeros((len(x_grid), len(y_grid)))
    for i in range(len(x_grid)):
        for j in range(len(y_grid)):
            data[i,j] = disc.predict([(x_grid[i], y_grid[j])])
    #plt.imshow(data.transpose(), origin="lower")
    #plt.show()
    # Pickleado del discriminador.
    with open("disc.pickle", "wb") as f:
        pickle.dump(disc, f, pickle.HIGHEST_PROTOCOL)
    alpha = 0.5

    cmap = colors.LinearSegmentedColormap(
        'red_blue_classes',
        {'red': [(0, 1, 1), (1, 0.7, 0.7)],
         'green': [(0, 0.7, 0.7), (1, 0.7, 0.7)],
         'blue': [(0, 0.7, 0.7), (1, 1, 1)]})
    plt.cm.register_cmap(cmap=cmap)

    # class 0: dots
    plt.plot(x_ash, y_ash, 'o', alpha=alpha,
             color='red', markeredgecolor='k')

    # class 1: dots
    plt.plot(x_cloud, y_cloud, 'o', alpha=alpha,
             color='blue', markeredgecolor='k')
    nx, ny = 100, 100
    x_min, x_max = plt.xlim()
    y_min, y_max = plt.ylim()
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, nx),
                         np.linspace(y_min, y_max, ny))
    Z = disc.predict_proba(np.c_[xx.ravel(), yy.ravel()])
    Z = Z[:, 1].reshape(xx.shape)
    plt.pcolormesh(xx, yy, Z, cmap='red_blue_classes',
                   norm=colors.Normalize(0., 1.))
    plt.contour(xx, yy, Z, [0.5], linewidths=2., colors='k')
    plt.show()

generate_qda_advanced_plot()
