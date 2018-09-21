import matplotlib
matplotlib.use('Agg')
import datetime
import time
import os
import osmnx as ox
import geopandas as gpd
import networkx as nx
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

cities = {'Amsterdam':'Amsterdam, Netherlands',
          'Budapest':'Budapest, Hungary',
          'Phoenix':'Phoenix, Arizona, USA',
          'Detroit':'Detroit, Michigan, USA',
          'Manhattan':'Manhattan, New York City, New York, USA',
          'Mexico':'DF, Mexico',
          'London':'London, England',
          'Singapore':'Singapore, Singapore',
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
    print('---------------\nStarting with {}'.format(name))

    #1.- Generate the path where the data is stored and where it is going to be saved
    path = '/mnt/cns_storage3/luis/Data/{}/'.format(name)
    path_plot = '/mnt/cns_storage3/luis/imgs/{}/structure/'.format(name)
    assure_path_exists(path_plot)

    #2.- Load the area
    gdf = gpd.read_file('/mnt/cns_storage3/luis/Data/{}/{}_shape/'.format(name, name))
    gdf = ox.project_gdf(gdf, to_crs={'init':'epsg:4326'})
    print('  + Geometry loaded')

    #3.- Load the graphs
    G_bike = ox.load_graphml('{}_bike.graphml'.format(name), folder=path)
    if len(G_bike.nodes)>0:
        G_bike = ox.project_graph(G_bike, to_crs={'init':'epsg:4326'})
    print('  + Bike loaded.')
    G_walk = ox.load_graphml('{}_walk.graphml'.format(name), folder=path)
    if len(G_walk.nodes)>0:
        G_walk = ox.project_graph(G_walk, to_crs={'init':'epsg:4326'})
    print('  + Walk loaded')
    G_rail = ox.load_graphml('{}_rail.graphml'.format(name), folder=path)
    if len(G_rail.nodes)>0:
        G_rail = ox.project_graph(G_rail, to_crs={'init':'epsg:4326'})
    print('  + Rail loaded')
    G_drive = ox.load_graphml('{}_drive.graphml'.format(name), folder=path)
    if len(G_drive.nodes)>0:
        G_drive = ox.project_graph(G_drive, to_crs={'init':'epsg:4326'})
    print('  + Rail loaded')
    layers = [G_rail, G_bike, G_walk, G_drive]

    #4.- Get the edges for each transportation mode
    print('  + Getting the list of edges')
    rail = list(G_rail.edges())
    walk = list(G_walk.edges())
    bike = list(G_bike.edges())

    #5.- Generate the aggregated network
    A = nx.compose_all(layers)
    print('  + Aggregated network done')

    #6.- Get the different colors
    print('  + Getting the colors for each mode')
    edge_w = []
    color_edge = []
    for edge in A.edges():
        if edge in rail:
            color_edge.append('#f6037f')
            edge_w.append(2.5)
        elif edge in bike:
            color_edge.append('#e78708')
            edge_w.append(1.5)
        elif edge in walk:
            color_edge.append('#0aa8d5')
            edge_w.append(0.85)
        else:
            color_edge.append('#dbdde1')
            edge_w.append(0.35)


    #4.- Plot
    print('\nStarting the ploting...')

    fig, ax = ox.plot_graph(A, fig_height=30, show=False, close=False, edge_color=color_edge, node_color='white', node_alpha=0, node_size=3, edge_linewidth=edge_w, edge_alpha=0.85)
    fig.savefig(path_plot+'{}_{}_Structure.png'.format(now.date(),name),dpi=350, bbox_inches='tight', transparent=True)


    plt.close()

    for geometry in gdf['geometry'].tolist():
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if isinstance(geometry, Polygon):
                geometry = MultiPolygon([geometry])
            for polygon in geometry:
                patch = PolygonPatch(polygon, fc='#777c87', ec='#c1c0ce', linewidth=2, alpha=1, zorder=-1)
                ax.add_patch(patch)
    margin = 0.02
    west, south, east, north = gdf.unary_union.bounds
    margin_ns = (north - south) * margin
    margin_ew = (east - west) * margin
    ax.set_ylim((south - margin_ns, north + margin_ns))
    ax.set_xlim((west - margin_ew, east + margin_ew))
    ax.set_facecolor('#2b313d')
    fig.savefig(path_plot+'{}_{}_Area_Structure.png'.format(now.date(),name),dpi=450, bbox_inches='tight', facecolor='#2b313d')
#1f2024
    print('---------------\n{} plotterd in {} min.\n---------------\n---------------\n'.format(name,round((time.time()-start_0)/60,2)))
print('\n\n---------------\nAll cities done in {} min.\n---------------'.format(round((time.time()-start)/60,2)))
