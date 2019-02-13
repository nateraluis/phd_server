import osmnx as ox
import pandas as pd
import geopandas as gpd
import networkx as nx
import peartree as pt
import time
import copy
from shapely.geometry import Point, LineString
from shapely.ops import cascaded_union

pt.utilities.config(log_console=True)


ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')
crs_osm = {'init':'epsg:4326'}           #crs that osm uses

def load_data(name):
    #Load the streets
    G_s = ox.load_graphml('{}/{}_drive.graphml'.format(name, name))

    #Load the area
    area = gpd.read_file('Data/{}/{}_shape'.format(name, name))
    area = ox.project_gdf(area, to_crs={'datum': 'WGS84', 'ellps': 'WGS84', 'proj': 'utm', 'zone': 34, 'units': 'm'})

    path = 'GTF/{}_gtfs.zip'.format(name)

    # Automatically identify the busiest day and read that in as a Partidge feed
    feed = pt.get_representative_feed(path)

    # Set a target time period to use to summarize impedance
    start = 7*60*60  # 7:00 AM
    end = 23*60*60  # 10:00 AM

    # Converts feed subset into a directed network multigraph
    G = pt.load_feed_as_graph(feed, start, end,walk_speed_kmph=3, impute_walk_transfers=False, interpolate_times=False)

    return G_s, area, G

def filter_network(G, gdf):
    '''
    Filter the GTFS network to retain only the nodes and edges that are inside the area of analysis

    Parameters
    ------
    G: networkx Graph
       Use the public transport graph generated from a GTF with peartree
    gdf: GeoPandas Dataframe
         The GDF that contains the area to use as the filter

    Returns
    ------
    G: networkx Graph
       Filtered graph without the nodes and edges thay were outside of the working permiter
    '''

    # Project the area and the network to the same coordinate system
    G = pt.reproject(G, to_epsg=4326)
    gdf = ox.project_gdf(gdf, to_crs=crs_osm)

    #get the polygon
    polygons = [row.geometry for i, row in gdf.iterrows()]
    polygon = cascaded_union(polygons)



    #get the nodes to a dataframe
    nodes_df = pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index')

    # Zip the coordinates into a point object and convert to a GeoDataFrame
    nodes_df = gpd.GeoDataFrame(nodes_df, geometry=[Point(xy) for xy in zip(nodes_df.x, nodes_df.y)])
    nodes_df = gpd.GeoDataFrame(nodes_df, geometry='geometry')

    #Get the nodes that are inside the area
    nodes_df['inside'] = nodes_df.within(polygon)

    #Remove the nodes that are outside of the polygon
    G.remove_nodes_from(list(nodes_df[~nodes_df.inside].index))
    return G

def pt_network(G, G_s):
    '''
    Create a public transportation network matching the bus stops to the clossest intersection to be used in the analysis of multilayer urban networks.

    Parameters
    ------
    G: networkx MultiDiGraph
       Public transport graph generated from a GTF with peartree

    G_s: networkx MultiDiGraph
         Streets network, generated using OSMnx

    Returns
    ------
    G_pt: networkx MultiDigraph
          Graph where the nodes are the clossest street intersections to bus stops and the edges the public transportation routes
    '''

    G_pt = copy.deepcopy(G_s)
    G = pt.reproject(G,to_epsg=4326)
    G_s = pt.reproject(G_s,to_epsg=4326)

    #1.- Get a list of nodes, x's and y's
    nodes = []
    x_s = []
    y_s = []
    for n, data in G.nodes(data=True):
        nodes.append(n)
        x_s.append(data['x'])
        y_s.append(data['y'])

    #Get the closest intersections as a numpy array of ID's
    match_nodes = ox.get_nearest_nodes(G_s, x_s, y_s, method='kdtree')

    #Pair the bus stop with its closest intersection
    pairs = {}
    for i, i_s in zip(nodes, match_nodes):
        pairs[i] = i_s

    #Remove all the edges from the public transport graph
    G_pt.remove_edges_from(list(G_pt.edges()))

    #Remove the unmatched intersections
    remove = [i for i in G_pt.nodes() if i not in match_nodes]
    G_pt.remove_nodes_from(remove)

    #Add the bus routes (edges)
    edges = [(pairs[i], pairs[j], d) for i,j,d in G.edges(data=True) if pairs[i] != pairs[j]]
    G_pt.add_edges_from(edges)
    for e, data in G_pt.edges(data=True):
        data['oneway']=False
    return G_pt

def simplify_graph(G):
    G_simple = nx.Graph()

    for i,j,data in G.edges(data=True):
        w = data['weight'] if 'weight' in data else 1.0
        if G_simple.has_edge(i,j):
            G_simple[i][j]['weight'] += w
        else:
            G_simple.add_edge(i,j,weight=w)
    return G_simple

name = 'Budapest'

start_time = time.time()
print('Starting with {}'.format(name))
        #Load the data
G_s, area, G = load_data(name)

print('Data loaded in {} min.'.format(round((time.time()-start_time)/60,2)))

#Filter the GTF network
time_temp = time.time()
G = filter_network(G, area)
print('Data filter in {} s.'.format(round(time.time()-time_temp,2)))

#Create the network
time_temp = time.time()
G_pt = pt_network(G, G_s)
print('G_pt network created in {} s'.format(round(time.time()-time_temp,2)))
ox.save_graphml(G_pt, filename='{}/{}_pt.graphml'.format(name, name))
print('G_pt saved')
print('{} done. Total time: {} min.'.format(name, round((time.time()-start_time)/60,2)))
print();
