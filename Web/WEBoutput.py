#!/usr/bin/python2
# -*- coding: utf-8 -*-    

from .IOweb import lidar2js, connect_ftp, upload_file
from os.path import isfile, join
import jinja2

fname_template_intramet = "./Web/template_intramet.html"
fname_template_mireta   = "./Web/template_mireta.html"

st_name  = {'comodoro':   "Comodoro Rivdavia station",
            'bariloche':  "Bariloche station",
            'aeroparque': "Aeroparque station",
            'parenas':    "Punta Arenas station", 
            'neuquen':    "Neuquen station",
            'vmartelli':  "Villa Martelli station",
	    'cordoba':    "Cordoba station",
            }

def CreateJS(block, ncpath, ncfile):
  fname_js      = "{}.js".format(block)
  fname_html    = "{}.html".format(block)
  tag           = {'title':  "Lidar - Interactive visualization"}
  tag['header'] = st_name[block]
  tag["block"]  = lidar2js( ncpath,ncfile,fname_js )

  with open(fname_template_intramet, 'r') as f:
    html_data = f.read()

  template_html=jinja2.Template(html_data)
  with open(join(ncpath, fname_html), 'w') as f:
    html_out = template_html.render(tag)
    id_number = html_out.split("id=")[1].split('"')[1]
    f.write(html_out.replace(fname_js,"{}?ver={}".format(fname_js,id_number)))

  with open(fname_template_mireta, 'r') as f:
    html_data = f.read()
  
  fname_html = "{}_b.html".format(block)
  template_html=jinja2.Template(html_data)
  with open(join(ncpath, fname_html), 'w') as f:
    f.write(template_html.render(tag))

