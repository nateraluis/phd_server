import datetime
import time
import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Polygon, MultiPolygon

start = time.time()
ox.config(data_folder='/mnt/cns_storage3/luis/Data', logs_folder='/mnt/cns_storage3/luis/logs',
          imgs_folder='/mnt/cns_storage3/luis/imgs', cache_folder='/mnt/cns_storage3/luis/cache',
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
          'Beihai':'Beihai, China',
          'LA':'Los Angeles, Los Angeles County, California, USA',
          'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}

names=[v for k,v in cities.items()]

#Directory to store the data to be send to a dataframe
cities_dict = {}

networks = ['walk', 'bike', 'rail', 'drive']

#Iterate over cities.
for name, city in cities.items():
    start_0 = time.time()
    print('------\nStarting with {}:'.format(name))
    data_temp = {} #Temporal dict to store the layers of each city
    path = '/mnt/cns_storage3/luis/Data/{}'.format(name)
    gdf = gpd.read_file('/mnt/cns_storage3/luis/Data/{}/{}_shape/'.format(name, name))
    print('Area loaded')
    gdf = ox.project_gdf(gdf, to_crs={'init':'epsg:4326'})
    area_m2 = gdf.unary_union.area
    area_km2 = area_m2 / 1e6

    for layer in networks:

        start_layer = time.time()
        G = ox.load_graphml('{}_{}.graphml'.format(name,layer), folder=path)
        print('  Starting with {}'.format(layer))
        if len(G.nodes)>0:
            G = ox.project_graph(G, to_crs={'init':'epsg:4326'})
        print('  + Getting the stats')
        if len(G.nodes)>0:
            stats = ox.basic_stats(G, area=area_m2)
            row = {}
            row['$N$'] = G.number_of_nodes()
            row['$L$'] = G.number_of_edges()
            row['$<k>$'] = stats['k_avg']
            row['area_km2'] = area_km2
            row['node_density_km'] = stats['node_density_km']
            row['edge_density_km'] = stats['edge_density_km']
            row['intersections_count'] = stats['intersection_count']
            row['edge_length_avg'] = stats['street_length_avg']
            try:
                row['intersect_density_2way'] = stats['streets_per_node_counts'][2] / area_km2
            except:
                row['intersect_density_2way'] = np.NaN
            try:
                row['intersect_density_3way'] = stats['streets_per_node_counts'][3] / area_km2
            except:
                row['intersect_density_3way'] = np.NaN
            try:
                row['intersect_density_4way'] = stats['streets_per_node_counts'][4] / area_km2
            except:
                row['intersect_density_4way'] = np.NaN
            row['circuity_avg'] = stats['circuity_avg']
            row['streets_per_node_avg'] = stats['streets_per_node_avg']
            data_temp[layer] = row
            row = {}

        else:
            row = {}
            row['$N$'] = G.number_of_nodes()
            row['$L$'] = G.number_of_edges()
            row['$<k>$'] = np.NaN
            row['area_km2'] = area_km2
            row['node_density_km'] = np.NaN
            row['edge_density_km'] = np.NaN
            row['intersections_count'] = np.NaN
            row['edge_length_avg'] = np.NaN
            row['intersect_density_2way'] = np.NaN
            row['intersect_density_3way'] = np.NaN
            row['intersect_density_4way'] = np.NaN
            row['circuity_avg'] = np.NaN
            row['streets_per_node_avg'] = np.NaN
            data_temp[layer] = row
            row = {}

        print('  + Done in {} s.'.format(round(time.time()-start_layer,3)))
    cities_dict[name]=data_temp
    print('------\n{} done in: {} min.\n'.format(name,round((time.time()-start_0)/60,2)))
print('\n\n------\n------\nAll cities done in {}------\n------\n'.format(round((time.time()-start)/60,2)))
df = pd.DataFrame.from_dict({(i,j): cities_dict[i][j]
                           for i in cities_dict.keys()
                           for j in cities_dict[i].keys()})
df.sort_index(axis=1, level=0, inplace=True, sort_remaining=False)
df = df.T
df.to_csv('/mnt/cns_storage3/luis/Cities_stats.csv', encoding='utf-8', index=False)
print('File saved. All done!')
