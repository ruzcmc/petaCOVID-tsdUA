import pandas as pd  # provides interface for interacting with tabular data
import geopandas as gpd  # combines the capabilities of pandas and shapely for geospatial operations
from shapely.geometry import Point, Polygon, MultiPolygon  # for manipulating text data into geospatial shapes
from shapely import wkt  # stands for "well known text," allows for interchange across GIS programs
# import rtree  # supports geospatial join
import os
import descartes
import csv
import json
import requests
import zipfile
import io

from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, HoverTool, Slider, Select, NumeralTickFormatter
from bokeh.palettes import brewer
from bokeh.io.doc import curdoc
from bokeh.layouts import widgetbox, row, column

"""# Start Here"""

# get online shapefile

# urlshp = 'https://github.com/ruzcmc/petaCOVID-tsdUA/blob/master/dashSUB/input/Kel_SUB_2017.zip?raw=true'
# local_path = '/content/'

# r = requests.get(urlshp)
# z = zipfile.ZipFile(io.BytesIO(r.content))

# z.extractall(path=local_path) # extract to folder
# filenames = [y for y in sorted(z.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)]
# print(filenames)

# read shapefile dan debugnya

# root_path = os.getcwd()
# print(root_path)
shpfileurl = 'https://raw.githubusercontent.com/ruzcmc/petaCOVID-tsdUA/master/dashSUB/input/Kelurahan_Surabaya_2017.json'

puds = gpd.read_file(shpfileurl, crs={'init': 'epsg:4326'})  # [['name','geometry']]

puds.loc[puds.full_id == "r-395152", "is_in_muni"] = "Genteng"  # hardcode gantian kecamatan agar sama dgn csv

# puds.rename(columns = {'name' : 'Kelurahan'}, inplace= True)
# puds.sample()
# print(puds[['is_in_muni','name']])


# puds
# print(puds[puds['name']=='Karang Pilang'])
# puds.info()
# puds.to_csv(root_path+'\kelurahansub.csv', index = False, header = True)
# puds.plot(column='name', legend=True, figsize=(16,8))

# read csv data dan konfigurasi merge
# local file
# datafile = root_path+'/input/covid7aprsub.csv'

# bisa diconnect gdrive/github yg aktif / online file
datafile = 'https://raw.githubusercontent.com/ruzcmc/petaCOVID-tsdUA/master/dashSUB/input/covid7aprsub.csv'

# Read csv file using pandas
df = pd.read_csv(datafile, names=['Tanggal', 'Wilayah', 'Kecamatan', 'Kelurahan', 'Konfirmasi', 'Konfirmasi Sembuh',
                                  'Konfirmasi Meninggal', 'PDP', 'PDP Sembuh', 'PDP Meninggal', 'ODP', 'ODP Dipantau',
                                  'ODP Selesai Dipantau'], skiprows=1)


# print(df[df['Kelurahan']=='Karang Pilang'])
# df.info()


# Ini bisa dikasih input tanggal dropdown
# df[df['Kelurahan'].isnull()]

def merged_json(pilihan):
    tanggul = pilihan  # bisa dibuatkan inputan tanggal kalo mau jadi dashboard
    df_tanggal = df[df['Tanggal'] == tanggul]
    mergeset = pd.merge(puds, df_tanggal, how='inner', left_on='name', right_on='Kelurahan')
    merged_json = json.loads(mergeset.to_json())
    json_data = json.dumps(merged_json)
    return json_data


def update_plot(attr, old, new):
    # The input yr is the year selected from the slider
    yr = select2.value
    new_data = merged_json(yr)
    # Update the data
    geosource.geojson = new_data
    # The input cr is the criteria selected from the select box
    cr = select.value
    input_field = cr

    # Update the plot based on the changed inputs
    p = make_plot(input_field)

    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select), widgetbox(select2))
    curdoc().clear()
    curdoc().add_root(layout)




def make_plot(field_name):
    # Set the format of the colorbar
    min_range = df[field_name].min()
    max_range = df[field_name].max()
    # field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]

    # ganti palet, acuan ke brewerDOC
    palette = brewer['YlOrRd'][5]
    # Reverse color order -> Semakin parah semakin gelap
    palette = palette[::-1]

    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(palette=palette, low=min_range, high=max_range)

    # Create color bar.
    format_tick = NumeralTickFormatter(format='0,0')
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18, formatter=format_tick,
                         border_line_color=None, location=(0, 0))

    # Create figure object.
    # verbage = format_df.loc[format_df['field'] == field_name, 'verbage'].iloc[0]

    p = figure(title='Peta COVID-19 Per Kelurahan di Surabaya', plot_height=600, plot_width=950,
               toolbar_location='below')
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False

    # Add patch renderer to figure.
    p.patches('xs', 'ys', source=geosource, fill_color={'field': field_name, 'transform': color_mapper},
              line_color='black', line_width=0.25, fill_alpha=1)

    # Specify color bar layout.
    p.add_layout(color_bar, 'right')

    # Add the hover tool to the graph

    p.add_tools(hover)
    return p


# Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
'''
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 5)
#Define custom tick labels for color bar.
tick_labels = {'0': '0', '1': '1', '2':'2', '3':'3', '4':'4', '5':'5'}
#Create color bar.
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
border_line_color=None,location = (0,0), orientation = 'horizontal', major_label_overrides = tick_labels)
#Create hovertool
hover = HoverTool(tooltips = [('Nama Kecamatan','@Kecamatan'),('Nama Kelurahan','@Kelurahan'),('Jumlah Konfirmasi Positif COVID-19','@Konfirmasi'),()])

#Create figure object.
p = figure(title = 'Peta COVID-19 Per Kelurahan di Surabaya', plot_height = 600 , plot_width = 950, toolbar_location = 'below')
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
#Add patch renderer to figure. #field bisa disesuaikan input mau odp pdp atau konfirm
p.patches('xs','ys', source = geosource,fill_color = {'field' :'Konfirmasi', 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)
#Specify figure layout.
p.add_layout(color_bar, 'below')
p.add_tools(hover)



output_notebook()
show(p)
'''

# print(df_tanggal)
# print(df['Konfirmasi'].max()) #untuk cari range warna

# mergeset = pd.merge(puds, df_tanggal('07-04-20'), how='inner', left_on= 'name', right_on='Kelurahan')

# print(mergeset[['Kecamatan','Kelurahan', 'Konfirmasi' ,'geometry']])
# mergeset.head()
# mergeset.info()
# print(mergeset[mergeset['is_in_muni']=='Karangpilang'])

# tampilkan peta chloropleth

# ubah GEOjson.
# merged_json = json.loads(mergeset.to_json())
# json_data = json.dumps(merged_json)


# Oper data GEOJson ke parser
geosource = GeoJSONDataSource(geojson=merged_json('07-04-20'))
input_field = 'Konfirmasi'
hover = HoverTool(tooltips=[('Nama Kecamatan', '@Kecamatan'), ('Nama Kelurahan', '@Kelurahan'),
                            ('Jumlah Konfirmasi Positif COVID-19', '@Konfirmasi'),('Jumlah ODP','@ODP'),('Jumlah PDP','@PDP')])

p = make_plot(input_field)

# Make a slider object: slider
select2 = Select(title='Tanggal', value='07-04-20',
                 options=['01-04-20', '02-04-20', '03-04-20', '04-04-20', '05-04-20', '06-04-20', '07-04-20'])
select2.on_change('value', update_plot)

# Make a selection object: select
select = Select(title='Pilih Kriteria:', value='Konfirmasi', options=['ODP', 'PDP', 'Konfirmasi'])
select.on_change('value', update_plot)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
# Display the current document
layout = column(p, widgetbox(select), widgetbox(select2))
curdoc().add_root(layout)
