import numpy as np
from bokeh.plotting import figure, show
from bokeh.models import (ColorBar, 
                          ColumnDataSource, 
                          CustomJS,
                          DatetimeTickFormatter, 
                          FixedTicker, 
                          HoverTool, 
                          Legend, 
                          LinearColorMapper, 
                          RadioButtonGroup, 
                          Toggle
                          )
from bokeh.models.formatters import CustomJSTickFormatter
from bokeh.resources import CDN
from bokeh.embed import autoload_static
from bokeh.layouts import column, row, Spacer

from netCDF4 import Dataset, num2date
from os.path import isfile, join
from matplotlib.colors import LinearSegmentedColormap,ListedColormap,BoundaryNorm,rgb2hex
from ftplib import FTP

################# Parameters ###############################################
max_days = 5
levs1    = [i*1E-4 for i in [1,2,4,6,8,10] ]
levs2    = [i*1E-3 for i in [1.25,1.5,1.75,2,2.25,2.5,2.75,3] ]
levs3    = [i*1E-3 for i in [4,5,6] ]
levs4    = [i*1E-3 for i in [7,8,9,10,20,40,60,80,100] ]
levs     = levs1 + levs2 + levs3 + levs4
Debug    = True
############################################################################

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
  norm  = BoundaryNorm(levs, ncolors=cmap.N, clip=False)
  cmap.set_under( rgb[0]  )
  cmap.set_over(  rgb[-1] )
  return cmap,norm,rgb[1:-1]  

def create_js(plot,path,jsfile):
  js, tag = autoload_static(plot, CDN, jsfile)
  with open(join(path,jsfile), 'w') as f:
    f.write(js)
  return tag

def lidar2js(path, ncfile, jsfile):
  fname_nc  = join(path,ncfile)
  if isfile(fname_nc):
    if Debug: 
      print("Found file: ", ncfile)
    ds      = Dataset(fname_nc,'r',format="NETCDF3_CLASSIC") 
    t_raw   = ds.variables["time"]
    z       = ds.variables["alt1"][:]
    bsc532  = ds.variables["bsc532"][:]
    bsc1064 = ds.variables["bsc1064"][:]
    zb      = ds.variables["zb"][:]
    zpbl    = ds.variables["zpbl"][:]
    t       = num2date(t_raw[:], units = t_raw.units, only_use_cftime_datetimes=False, only_use_python_datetimes=True)
    tm      = t_raw[:]
    ds.close()
  else:
    if Debug: 
      print("Not found file: ", ncfile)
    return "No Data"

  DX       = t[1]-t[0]
  Dx_sec   = DX.total_seconds()
  Nx       = len(t)
  Nx0      = int(max_days*86400.0/Dx_sec)
  if Nx0<Nx: Nx=Nx0
  tmin     = t[-Nx]
  tmax     = t[-1]+DX
  twidth   = 1000.0*(tmax-tmin).total_seconds()

  zmin = 0
  zmax = z[-1]

  my_cmap,my_norm,my_rgb = build_palette4(levs1,levs2,levs3,levs4)
  img532_raw             = my_norm(bsc532[-Nx:,:])
  img1064_raw            = my_norm(bsc1064[-Nx:,:])

  data1   = {'zbase':      zb[-Nx:], 
             'zpbl':       zpbl[-Nx:], 
             'tcenter':    t[-Nx:] + DX/2,
            }
  data2   = { 'image532':  [np.array(img532_raw.filled().T,  dtype=np.int8)], 
              'image1064': [np.array(img1064_raw.filled().T, dtype=np.int8)], 
            }
  data3   = { 'profile532': bsc532[-1,:],
              'range':      z
            }
  src     = ColumnDataSource(data=data1)
  src_img = ColumnDataSource(data=data2)
  src_z   = ColumnDataSource(data=data3)

  color_mapper = LinearColorMapper(palette=[rgb2hex(item) for item in my_rgb], 
                                   low=0, 
                                   high=my_cmap.N
                                   )

  plot = figure(x_range=(tmin,tmax), y_range=(zmin,zmax), 
              title="Attenuated Backscatter coefficient [/sr /km]",
              toolbar_location="above",
              tools = "pan,wheel_zoom,box_zoom,reset,save",
              active_scroll=None, 
              active_drag=None,
              active_inspect=None,
            #  toolbar_sticky=False,
              y_axis_label = 'Height [km]',
              width=900, 
              height=350, 
              )
  plot.toolbar.logo=None

  plot2 = figure(title="Last Profile at 532 nm - {}".format(t[-1]),
  	             tools = "pan,wheel_zoom,box_zoom,reset,save",
  	             y_axis_label = 'Height [km]',
  	             x_axis_label = 'Attenuated Backscatter coefficient [/sr /km]',
                 # y_axis_type="log",
                 active_inspect=None,
                 width=900, 
                 height=350
  	             )
  plot2.toolbar.logo=None
  
  plot2.line(x='profile532', y='range',
             source=src_z, 
             line_color="black", 
             )

  im = plot.image(image="image532", 
                  source=src_img,
                  color_mapper=color_mapper,
                  dh=zmax, dw=twidth, 
                  x=tmin, y=zmin
                  ) 
  im.visible = True

  line1 = plot.line(   x='tcenter', y='zbase', source=src, line_width=2, alpha=0.8, color="black")
  line2 = plot.line(   x='tcenter', y='zpbl' , source=src, line_width=2, alpha=0.8, color="red")

  r1 = plot.scatter( x='tcenter', y='zbase', 
                    source=src, 
                    fill_color="black", 
                    line_color="black", 
                    fill_alpha=0.3,
                    size=4,
                    name="r1"
                    )
  r2 = plot.scatter( x='tcenter', y='zpbl', 
                    source=src, 
                    fill_color="red", 
                    line_color="red", 
                    fill_alpha=0.3,
                    size=4,
                    name="r2",
                    marker = "square"
                    )
  for item in [r1,r2]: item.visible = True

  color_bar = ColorBar(color_mapper=color_mapper, 
                       ticker=FixedTicker(ticks=[0,5,20,25]),
                       label_standoff=12, 
                       border_line_color=None, 
                       location=(0,0)
                       )
  color_bar.bar_line_color = "black"
  color_bar.major_tick_line_color = "black"
  color_bar.formatter = CustomJSTickFormatter(code="return {}[tick].toExponential(2)".format(levs))

  legend = Legend(items=[("Cloud Base",[r1]), ("PBL Height",[r2])], 
                  location="top_left"
                  )
  legend.click_policy = "hide"
  legend.visible = True

  hover = HoverTool(tooltips=[
                  ("Cloud base", "@zbase km"), 
                  ("PBL height", "@zpbl km"), 
                  ("Time", "@tcenter{%d-%m-%y %H:%M}")])
  
  hover.formatters = { "@tcenter": "datetime"}
  hover.point_policy = "snap_to_data"

  hover2 = HoverTool(tooltips=[
                     ("Signal", "@profile532"), 
                     ("Range", "@range"), 
                     ])

  plot.add_layout(color_bar, 'right')
  plot.add_layout(legend)
  plot.add_tools(hover)

  plot2.add_tools(hover2)
  
  plot.xaxis.formatter = DatetimeTickFormatter(months = '%Y-%b',
                                               years  = '%Y',
                                               days   = '%d-%b-%Y'
                                               )

  callback = CustomJS(args=dict(im=im), code="""
      var f = cb_obj.active
      if (f==0){
        im.glyph.image.field = "image532"
      } else {
        im.glyph.image.field = "image1064"
      }
      im.glyph.change.emit();
  """)
  radio_button_group = RadioButtonGroup(labels=["532 nm", "1064 nm"], active=0)
  radio_button_group.js_on_change('active',callback)

  callback2 = CustomJS(args=dict(leg=legend), code="""
    leg.visible = !leg.visible
    console.log("ol")
  """)
  toggle = Toggle(label="Legend", button_type="default")
  toggle.js_on_click(callback2)

  layout = column(
  				children=[ 
  					row(column(radio_button_group, width=200), column(toggle, width=80) ), 
  					plot,
  					Spacer(height=50),
  					# row(Spacer(width=50),plot2),
  					plot2, 
					], 
  				)

  			
  #show(plot)
  return create_js(layout,path,jsfile)

def connect_ftp(USER,PASS,SERVER,PORT):
  #Connect to the server
  ftp = FTP()
  ftp.connect(SERVER, PORT)
  ftp.login(USER, PASS)
  return ftp

def upload_file(ftp_connetion, fname, binary_store=True):
  #Open the file
  try:
    upload_file = open(fname, 'r')
    #transfer the file
    print(('Uploading ' + fname + '...'))
    if binary_store:
      ftp_connetion.storbinary('STOR '+ fname, upload_file)
    else:
      ftp_connetion.storlines('STOR '+ fname, upload_file)
    print('Upload finished.')
  except IOError:
    print ("No such file or directory...")
