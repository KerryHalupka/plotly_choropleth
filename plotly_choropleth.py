import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import plotly.graph_objects as go

# Load geospatial data
lga_gdf = gpd.read_file('./data/1270055003_lga_2020_aust_shp/LGA_2020_AUST.shp') #load the data using Geopandas
lga_gdf = lga_gdf[lga_gdf['STE_NAME16']=='Victoria'] #Select the data for the state of Victoria
lga_gdf['LGA_CODE20'] = lga_gdf['LGA_CODE20'].astype('str') # we will join on this axis, so both dataframes need this to be the same type

# Load unemployment data
emp_df = pd.read_csv('./data/ABS_C16_G43_LGA_26072020234812892.csv')
emp_df = emp_df[['LGA_2016', 'Labour force status', 'Region', 'Value']]
emp_df['LGA_2016'] = emp_df['LGA_2016'].astype('str') # we will join on this axis, so both dataframes need this to be the same type
emp_df = emp_df.pivot(index='LGA_2016', columns='Labour force status', values='Value').reset_index().rename_axis(None, axis=1)
emp_df['percent_unemployed'] = emp_df['Total Unemployed']/(emp_df['Total Unemployed']+emp_df['Total Employed'])

# Merge dataframes
df_merged = pd.merge(lga_gdf[['LGA_CODE20', 'geometry', 'LGA_NAME20']], emp_df[['LGA_2016', 'percent_unemployed']], left_on='LGA_CODE20', right_on='LGA_2016', how='outer')
df_merged = df_merged.dropna(subset=['percent_unemployed', 'LGA_CODE20', 'geometry'])
df_merged.index = df_merged.LGA_CODE20

# Plot using geopandas
fig, ax = plt.subplots(1,1, figsize=(20,20))
divider = make_axes_locatable(ax)
tmp = df_merged.copy()
tmp['percent_unemployed'] = tmp['percent_unemployed']*100
cax = divider.append_axes("right", size="3%", pad=-1)
tmp.plot(column='percent_unemployed', ax=ax,cax=cax,  legend=True, 
         legend_kwds={'label': "Unemployment rate"})
tmp.geometry.boundary.plot(color='#BABABA', ax=ax, linewidth=0.3)
ax.axis('off')
fig.savefig(f"./choropleth3.png", dpi=300) 

# Convert geometry
df_merged = df_merged.to_crs(epsg=4326)
lga_json = df_merged.__geo_interface__

# Plot using plotly
MAPBOX_ACCESSTOKEN = 'your mapbox token here'

zmin = df_merged['percent_unemployed'].min()
zmax = df_merged['percent_unemployed'].max()
trace1 = go.Choroplethmapbox(
        geojson = lga_json,
        locations = df_merged.index, 
        z = df_merged.percent_unemployed, #sets the color value
        text = df_merged.LGA_NAME20,
        colorbar=dict(thickness=20, ticklen=3, tickformat='%',outlinewidth=0, title=dict(text='Unemployment rate (%)')),
        marker_line_width=1, marker_opacity=0.7, colorscale="Viridis",
        zmin=zmin, zmax=zmax, 
        hovertemplate = "<b>%{text}</b><br>" +
                    "%{z:.0%}<br>" +
                    "<extra></extra>")
latitude = -36.5
longitude = 145.5
layout = go.Layout(
    title = {'text': f"Population of Victoria, Australia",
            'font': {'size':24}},
    mapbox1 = dict(
        domain = {'x': [0, 1],'y': [0, 1]},
        center = dict(lat=latitude, lon=longitude),
        accesstoken = MAPBOX_ACCESSTOKEN, 
        zoom = 6),
    autosize=True,
    height=650,
    margin=dict(l=0, r=0, t=40, b=0))
fig=go.Figure(data=trace1, layout=layout)
fig.write_html("./victoria_unemployment.html")