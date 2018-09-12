import matplotlib
matplotlib.use('Agg')
import datetime
import time
import os
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Polygon, MultiPolygon

start = time.time()
ox.config(data_folder='/mnt/cns_storage3/luis/Data', logs_folder='/mnt/cns_storage3/luis/logs',
          imgs_folder='/mnt/cns_storage3/luis/imgs', cache_folder='/mnt/cns_storage3/luis/cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')

crs_osm = {'init':'epsg:4326'}           #crs that osm uses
colors_layers = ['#e9c46a','#e76f51','#f4a261','#264653']
names = ['_walk', '_bike', '_rail', '_drive']
now = datetime.datetime.now()

cities = {'Phoenix':'Phoenix, Arizona, USA',
          'Amsterdam':'Amsterdam, Netherlands',
          'Detroit':'Detroit, Michigan, USA',
          'Manhattan':'Manhattan, New York City, New York, USA',
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

def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

for name, city in cities.items():
    start_0 = time.time()
    print('---------------\nStarting with {}\n'.format(name))
    #1.- Generate the path where the data is stored
    path = '/mnt/cns_storage3/luis/Data/{}/'.format(name)
    path_plot = '/mnt/cns_storage3/luis/imgs/{}/'.format(name)
    assure_path_exists(path_plot)

    #2.- Load the graphs
    print('Loading the layers and geometry:')
    G_drive = ox.load_graphml('{}_drive.graphml'.format(name), folder=path)
    print('  + Drive loaded.')
    G_bike = ox.load_graphml('{}_bike.graphml'.format(name), folder=path)
    print('  + Bike loaded.')
    G_walk = ox.load_graphml('{}_walk.graphml'.format(name), folder=path)
    print('  + Walk loaded')
    G_rail = ox.load_graphml('{}_rail.graphml'.format(name), folder=path)
    print('  + Rail loaded')

    #3.- Load the area
    #gdf = gpd.read_file('/mnt/cns_storage3/luis/Data/{}/{}_shape/'.format(name, name))
    #print('  + Geometry loaded')
    #gdf = gdf.to_crs(crs_osm)

    layers = [G_walk, G_bike, G_rail, G_drive]

    #4.- Plot
    print('\nStarting the ploting...')
    for layer, color, name_layer in zip(layers, colors_layers, names):
        if len(layer.nodes)>0:
            fig, ax = ox.plot_graph(layer, fig_height=30, show=False, close=False, edge_color=color, node_color=color, node_alpha=0)
            fig.savefig(path_plot+'{}_{}{}_Layer.png'.format(now.date(),name,name_layer),dpi=600, bbox_inches='tight')

            '''
            plt.close()

            for geometry in gdf['geometry'].tolist():
                if isinstance(geometry, (Polygon, MultiPolygon)):
                    if isinstance(geometry, Polygon):
                        geometry = MultiPolygon([geometry])
                    for polygon in geometry:
                        patch = PolygonPatch(polygon, fc='#cccccc', ec='k', linewidth=3, alpha=0.1, zorder=-1)
                        ax.add_patch(patch)
            margin = 0.02
            west, south, east, north = gdf.unary_union.bounds
            margin_ns = (north - south) * margin
            margin_ew = (east - west) * margin
            ax.set_ylim((south - margin_ns, north + margin_ns))
            ax.set_xlim((west - margin_ew, east + margin_ew))
            fig.savefig(path_plot+'{}_{}{}.png'.format(now.date(),name,name_layer),dpi=300, bbox_inches='tight')
            print('{}{} plotted.'.format(name, name_layer))
            '''
    print('\nSingle plots for {} done in {} min.\n---------------\n---------------\n\n\n'.format(name,round((time.time()-start_0)/60,2)))
print('All cities done in {} min.'.format(round((time.time()-start)/60,2)))
