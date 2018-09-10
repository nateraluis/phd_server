import time
import osmnx as ox
import os
import networkx as nx

# Configure OSMnx
useful_tags = ox.settings.useful_tags_path + ['cycleway']
ox.config(data_folder='Data', logs_folder='logs',
          imgs_folder='imgs', cache_folder='cache',
          use_cache=True, log_console=True, useful_tags_path=useful_tags)

# Get networks
def get_network(city, n_type='all', infrastructure='way["highway"]'):
    try:
        G = ox.graph_from_place(city, network_type=n_type, simplify=True, which_result=1, infrastructure=infrastructure)
    except:
        G = ox.graph_from_place(city, network_type=n_type, simplify=True, which_result=2, infrastructure=infrastructure)
    return ox.project_graph(G)


def bike_network(city):
    try:
        G = ox.graph_from_place(city, network_type='all', simplify=False, which_result=1)
    except:
        G = ox.graph_from_place(city, network_type='all', simplify=False, which_result=2)
    non_cycleways = [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True) if not ('cycleway' in d or d['highway']=='cycleway')]
    G.remove_edges_from(non_cycleways)
    G = ox.remove_isolated_nodes(G)
    G = ox.simplify_graph(G)
    return ox.project_graph(G)

def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

def simplify_graph(G):
    G_simple = nx.Graph()

    for i,j,data in G.edges(data=True):
        w = data['weight'] if 'weight' in data else 1.0
        if G_simple.has_edge(i,j):
            G_simple[i][j]['weight'] += w
        else:
            G_simple.add_edge(i,j,weight=w)
    return G_simple


def bike_walk_network(G):
    """
    Filter the network to get only the cycleways or pedestrians
    """
    cycle = []
    remove = []
    edges = dict(G.edges)
    for k, v in edges.items():
        if (v['highway']) !='cycleway' or v != 'cycleway':
                cycle.append(k)
        elif isinstance(v['highway'], list):
            for s in v['highway']:
                if s != cycleway:
                    cycle.append(k)

    for c in cycle:
        u,v,w = c
        G.remove_edge(u,v)
    degree = list(G.degree())

    for k in degree:
        n,v = k
        if v == 0:
            remove.append(n)
    G.remove_nodes_from(remove)
    return G


def area(city):
    city_shape = ox.gdf_from_place(city)
    if city_shape.geom_type.all() == 'Point':
        city_shape = ox.gdf_from_place(city, which_result=2)
    return city_shape


cities = {'Amsterdam':'Amsterdam, Netherlands',
          'Phoenix':'Phoenix, Arizona, USA',
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

#Execute script
start = time.time()
for name, city in cities.items():
    start_0 = time.time()

    #Create and check the path
    path = 'data/{}/'.format(name)
    assure_path_exists(path)
    print('Starting with: {}'.format(name))

    #Download the shape
    city_shape = area(city)
    city_shape = ox.project_gdf(city_shape)
    ox.save_gdf_shapefile(city_shape, filename='{}/{}'.format(name,name))

    #Download the graphs
    G_drive = get_network(city, n_type='drive')
    G_pedestrian = get_network(city, n_type='walk')
    if name == 'Beihai':
        G_bike = bike_walk_network(G_drive)
    else:
        G_bike = bike_network(city)
    try:
        G_rail = get_network(city, n_type='none', infrastructure='way["railway"~"subway|tram|light_rail"]')
    except:
        G_rail = get_network(city, n_type='none', infrastructure='way["railway"]')

    #Save the original graphs
    ox.save_graphml(G_drive, filename='{}/{}_drive.graphml'.format(name,name))
    ox.save_graphml(G_pedestrian, filename='{}/{}_pedestrian.graphml'.format(name,name))
    ox.save_graphml(G_bike, filename='{}/{}_bike.graphml'.format(name,name))
    ox.save_graphml(G_rail, filename='{}/{}_rail.graphml'.format(name,name))

    #Simplify Graph
    G_drive_simple = simplify_graph(G_drive)
    G_rail_simple = simplify_graph(G_rail)
    G_bike_simple = simplify_graph(G_bike)
    G_pedestrian_simple = simplify_graph(G_pedestrian)

    path = 'Data/{}/simple/'.format(name)
    assure_path_exists(path)

    nx.write_edgelist(G_drive_simple, path='Data/{}/simple/{}_drive_simple.txt'.format(name, name))
    nx.write_edgelist(G_rail_simple, path='Data/{}/simple/{}_rail_simple.txt'.format(name, name))
    nx.write_edgelist(G_bike_simple, path='Data/{}/simple/{}_bike_simple.txt'.format(name, name))
    nx.write_edgelist(G_pedestrian_simple, path='Data/{}/simple/{}_pedestrian_simple.txt'.format(name, name))

    print('{} done in {0:2f} s'.format(name,time.time()-start_0))

print('All cities done in {0:2f} min'.format((time.time()-start)/60))
