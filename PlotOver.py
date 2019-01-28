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
ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')

colors_layers = ['#f6037f','#e78708','#0aa8d5','#c1c5cc']
names = ['_rail', '_bike', '_walk', '_drive']
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
          'Sydney':'Sydney, Australia',
          'LA':'Los Angeles, Los Angeles County, California, USA',
          'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}

def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

def plot_layer(G,color_edge,gdf,name,layer):
    fig, ax = ox.plot_graph(G, fig_height=30, show=False, close=False, edge_color=color_edge, node_color='white', node_alpha=0, node_size=3, edge_linewidth=edge_w, edge_alpha=0.85)
    plt.close()
    for geometry in gdf['geometry'].tolist():
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if isinstance(geometry, Polygon):
                geometry = MultiPolygon([geometry])
            for polygon in geometry:
                patch = PolygonPatch(polygon, fc='none', ec='#c1c0ce', linewidth=2, alpha=1, zorder=-1)
                ax.add_patch(patch)
    margin = 0.02
    west, south, east, north = gdf.unary_union.bounds
    margin_ns = (north - south) * margin
    margin_ew = (east - west) * margin
    ax.set_ylim((south - margin_ns, north + margin_ns))
    ax.set_xlim((west - margin_ew, east + margin_ew))
    fig.savefig(path_plot+'{}_{}{}.png'.format(now.date(),name,layer),dpi=450, bbox_inches='tight', transparent=True)

for name, city in cities.items():
    start_0 = time.time()
    print('---------------\nStarting with {}'.format(name))

    #1.- Generate the path where the data is stored and where it is going to be saved
    path = '../Data/{}/'.format(name)
    path_plot = '../imgs/structure/{}/'.format(name)
    assure_path_exists(path_plot)

    #2.- Load the area
    gdf = gpd.read_file('../Data/{}/{}_shape/'.format(name, name))
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
    if len(G_rail.nodes)>0:741963258

        G_rail = ox.project_graph(G_rail, to_crs={'init':'epsg:4326'})
    print('  + Rail loaded')
    G_drive = ox.load_graphml('{}_drive.graphml'.format(name), folder=path)
    if len(G_drive.nodes)>0:
        G_drive = ox.project_graph(G_drive, to_crs={'init':'epsg:4326'})
    print('  + Rail loaded')
    graphs = [G_rail, G_bike, G_walk, G_drive]

    #4.- Get the edges for each transportation mode
    print('  + Getting the list of edges')
    rail = list(G_rail.edges())
    walk = list(G_walk.edges())
    bike = list(G_bike.edges())

    #5.- Generate the aggregated network
    A = nx.compose_all(graphs)
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
            edge_w.append(0.25)
        else:
            color_edge.append('#c1c5cc')
            edge_w.append(0.15)

    #4.- Plot
    print('\nStarting the ploting:')
    for G, color, layer in zip(graphs, colors_layers, names):
        if len(G.nodes)>0:
            plot_layer(G, color, gdf, name, layer)
            print('  + {}{} done in {} min.'.format(name,layer,round((time.time()-start_0)/60,2)))
        else:
            print('  + {}{} does not have active nodes and links.'.format(name,layer))
    plot_layer(A, color_edge, gdf, name, '_Area_Structure')
    print('---------------\n{} plotted in {} min.\n---------------\n---------------\n'.format(name,round((time.time()-start_0)/60,2)))
print('\n\n---------------\nAll cities done in {} min.\n---------------'.format(round((time.time()-start)/60,2)))
