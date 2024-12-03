#!/usr/bin/python2
import os

def ensure_folder_exists(folder_path):
  if not os.path.exists(folder_path):
    os.makedirs(folder_path)  # Create the folder
    print("Folder created:", folder_path)
  else:
    print("Folder already exists:", folder_path)
