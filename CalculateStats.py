import datetime
import time
import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Polygon, MultiPolygon

start = time.time()
ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')

colors_layers = ['#e9c46a','#e76f51','#f4a261','#264653']
names = ['_walk', '_bike', '_rail', '_drive']
now = datetime.datetime.now()

cities = {'Phoenix':'Phoenix, Arizona, USA',
          'Detroit':'Detroit, Michigan, USA',
          'Manhattan':'Manhattan, New York City, New York, USA',
          'Amsterdam':'Amsterdam, Netherlands',
          'Mexico':'DF, Mexico',
          'London':'London, England',
          'Singapore':'Singapore, Singapore',
          'Budapest':'Budapest, Hungary',
          'Copenhagen':'Copenhagen Municipality, Denmark',
          'Barcelona':'Barcelona, Catalunya, Spain',
          'Portland':'Portland, Oregon, USA',
          'Bogota':'Bogotá, Colombia',
          'LA':'Los Angeles, Los Angeles County, California, USA',
          'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}

cities = {'Phoenix':{'init':'epsg:2763'},
          'Detroit':{'init':'epsg:2763'},
          'Manhattan':{'init':'epsg:2763'},
          'Amsterdam':{'init':'epsg:32633'},
          'Mexico':{'init':'epsg:6372'},
          'London':{'init':'epsg:32633'},
          'Singapore':{'init':'epsg:3414'},
          'Budapest':{'init':'epsg:32633'},
          'Copenhagen':{'init':'epsg:32633'},
          'Barcelona':{'init':'epsg:32633'},
          'Portland':{'init':'epsg:26949'},
          'Bogota':{'init':'epsg:6247'},
          'LA':{'init':'epsg:2763'},
          'Jakarta':{'init':'epsg:5331'}}


#Dictionary to store the data to be sent to a dataframe
cities_dict = {}
start = time.time()
networks = ['walk', 'bike', 'rail', 'drive']

#Iterate over cities.
for name, crs in cities.items():
    start_0 = time.time()
    print('------\nStarting with {}:'.format(name))
    data_temp = {} #Temporal dict to store the layers of each city
    path = '../Data/{}'.format(name)
    gdf = gpd.read_file('../Data/{}/{}_shape/'.format(name, name))
    print('Area loaded')
    gdf = ox.project_gdf(gdf, to_crs=crs) #projection to meters to calculate the area correctly
    area_m2 = gdf.unary_union.area
    area_km2 = area_m2/1000000

    for layer in networks:

        start_layer = time.time()
        G = ox.load_graphml('{}_{}.graphml'.format(name,layer), folder=path)
        print('  Starting with {}'.format(layer))
        if len(G.nodes)>0:
            G = ox.project_graph(G, to_crs=crs) #Same as with the area, project the graph to meters
            print('  + Getting the stats')
            stats = ox.basic_stats(G, area=area_m2)
            row = {}
            row['$Area\ km^2$'] = round(area_km2,3)
            row['$N$'] = G.number_of_nodes()
            row['$L$'] = G.number_of_edges()
            row['$<k>$'] = round(stats['k_avg'],3)
            row['$Node\ density\ km^2$'] = round((G.number_of_nodes()/area_km2),3)
            row['$Edge\ density\ km^2$'] = round((G.number_of_edges()/area_km2),3)
            row['$Edge\ length\ avg$'] = round(stats['edge_length_avg'],3)
            row['$Edge\ length\ total$'] = round(stats['edge_length_total'],3)
            row['$Connected\ Components$'] = len(list(nx.weakly_connected_component_subgraphs(G)))
            data_temp[layer] = row
            row = {}

        else:
            print('  + The layer is empty')
            row = {}
            row['$Area\ km^2$'] = round(area_km2,3)
            row['$N$'] = G.number_of_nodes()
            row['$L$'] = G.number_of_edges()
            row['$<k>$'] = np.NaN
            row['$Node\ density\ km^2$'] = np.NaN
            row['$Edge\ density\ km^2$'] = np.NaN
            row['$Edge\ length\ avg$'] = np.NaN
            row['$Edge\ length\ total$'] = np.NaN
            row['$Connected\ Components$'] = np.NaN
            data_temp[layer] = row
            row = {}


        print('  + Done in {} s.'.format(round(time.time()-start_layer,3)))
    cities_dict[name]=data_temp
    print('------\n{} done in: {} min.\n------\nElapsed time: {} min\n------\n\n'.format(name,round((time.time()-start_0)/60,2),round((time.time()-start)/60,2)))

df = pd.DataFrame.from_dict({(i,j): cities_dict[i][j]
                           for i in cities_dict.keys()
                           for j in cities_dict[i].keys()})
df.sort_index(axis=1, level=0, inplace=True, sort_remaining=False)
df = df.T[['$Area\ km^2$','$N$','$L$','$<k>$','$Node\ density\ km^2$','$Edge\ density\ km^2$','$Edge\ length\ avg$', '$Edge\ length\ total$','$Connected\ Components$']]



for column in df:
    df[column] = df.apply(lambda x: "{:,}".format(x[column]), axis=1)
df.to_csv('../outputs/Cities_stats.csv', encoding='utf-8', index=True, na_rep='/')
print('CSV file saved.')
with open('../outputs/Table1.tex','w') as tf:
    tf.write(df.to_latex(na_rep='/',multirow=True, escape=False))
print('Latex file saved.')
print('\n\n------\n------\nAll done in: {} min.\n\n------\n------\n'.format(round((time.time()-start)/60,2)))
