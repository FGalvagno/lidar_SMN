#!/bin/bash

version=2.1
RUNPATH=/home/lmingari/lidar_v$version
OUTPATH=/home/lmingari/salida

$RUNPATH/main.py $1 > $OUTPATH/$1/last.log 2>&1

#$RUNPATH/main.py aeroparque > $OUTPATH/aeroparque/last.log 2>&1
#$RUNPATH/main.py bariloche > $OUTPATH/bariloche/last.log 2>&1
#$RUNPATH/main.py comodoro > $OUTPATH/comodoro/last.log 2>&1
#$RUNPATH/main.py cordoba > $OUTPATH/cordoba/last.log 2>&1
#$RUNPATH/main.py neuquen > $OUTPATH/neuquen/last.log 2>&1
#$RUNPATH/main.py gallegos > $OUTPATH/gallegos/last.log 2>&1
#$RUNPATH/main.py tucuman > $OUTPATH/tucuman/last.log 2>&1
#$RUNPATH/main.py parenas > $OUTPATH/parenas/last.log 2>&1
#$RUNPATH/main.py vmartelli > $OUTPATH/vmartelli/last.log 2>&1

