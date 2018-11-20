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

#Dictionary to store the data to be sent to a dataframe
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
            stats = ox.basic_stats(G, area=area_m2)
            row = {}
            row['$N$'] = G.number_of_nodes()
            row['$L$'] = G.number_of_edges()
            row['$<k>$'] = stats['k_avg']
            row['$area_km^2$'] = area_km2
            row['$node density km^2$'] = stats['node_density_km']
            row['$edge density km^2$'] = stats['edge_density_km']
            row['edge length avg'] = stats['street_length_avg']
            row['street segments count'] = stats['street_segments_count']
            row['intersections count'] = stats['intersection_count']
            row['$intersection density km$^2'] = stats['intersection_density_km']
            row['$edge density km^2$'] = stats['edge_density_km']
            row['$street density km^2$'] = stats['street_density_km']
            row['$circuity avg'] = stats['circuity_avg']
            row['streets_per node avg'] = stats['streets_per_node_avg']
            row['self loop proportion'] = stats['self_loop_proportion']
            try:
                row['intersect density 2way'] = stats['streets_per_node_counts'][2] / area_km2
            except:
                row['intersect density 2way'] = np.NaN
            try:
                row['intersect density 3way'] = stats['streets_per_node_counts'][3] / area_km2
            except:
                row['intersect density 3way'] = np.NaN
            try:
                row['intersect density 4way'] = stats['streets_per_node_counts'][4] / area_km2
            except:
                row['intersect density 4way'] = np.NaN


            data_temp[layer] = row
            row = {}

        else:
            print('  + The layer is empty')
            row = {}
            row['$N$'] = G.number_of_nodes()
            row['$L$'] = G.number_of_edges()
            row['$<k>$'] = np.NaN
            row['$area_km^2$'] = area_km2
            row['$node density km^2$'] = np.NaN
            row['$edge density km^2$'] = np.NaN
            row['edge length avg'] = np.NaN
            row['street segments count'] = np.NaN
            row['intersections count'] = np.NaN
            row['$intersection density km$^2'] = np.NaN
            row['$edge density km^2$'] = np.NaN
            row['$street density km^2$'] = np.NaN
            row['$circuity avg'] = np.NaN
            row['streets_per node avg'] = np.NaN
            row['self loop proportion'] = np.NaN
            row['intersect density 2way'] = np.NaN
            row['intersect density 3way'] = np.NaN
            row['intersect density 4way'] = np.NaN

            data_temp[layer] = row
            row = {}


        print('  + Done in {} s.'.format(round(time.time()-start_layer,3)))
    cities_dict[name]=data_temp
    print('------\n{} done in: {} min.\n------\nElapsed time: {} min\n------\n\n'.format(name,round((time.time()-start_0)/60,2),round((time.time()-start)/60,2))
print('\n\n------\n------\nAll cities done in {} min.\n------\n------\n'.format(round((time.time()-start)/60,2)))
df = pd.DataFrame.from_dict({(i,j): cities_dict[i][j]
                           for i in cities_dict.keys()
                           for j in cities_dict[i].keys()})
df.sort_index(axis=1, level=0, inplace=True, sort_remaining=False)
df = df.T[['$N$','$L$','$<k>$','$area_km^2$','$node density km^2$','$edge density km^2$','edge length avg','street segments count','intersections count','$intersection density km$^2','$edge density km^2$','$street density km^2$','$circuity avg','streets_per node avg','self loop proportion','intersect density 2way','intersect density 3way','intersect density 4way']]


#for column in df:
#    df[column] = df.apply(lambda x: "{:,}".format(x[column]), axis=1)
df.to_csv('/mnt/cns_storage3/luis/outputs/Cities_stats.csv', encoding='utf-8', index=True, na_rep='/')
print('CSV file saved.')
with open('/mnt/cns_storage3/luis/outputs/Table1.tex','w') as tf:
    tf.write(df.to_latex(na_rep='/',multirow=True, escape=False))
print('Latex file saved.')
print('\n\n------\n------\nAll done in: {} min.\n\n------\n------\n'.format(round((time.time()-start)/60,2)))
