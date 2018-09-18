import os, osmnx as ox, geopandas as gpd, pandas as pd, networkx as nx, time


useful_tags = ox.settings.useful_tags_path + ['cycleway']
ox.config(data_folder='/mnt/cns_storage3/luis/Data', logs_folder='/mnt/cns_storage3/luis/logs',
          imgs_folder='/mnt/cns_storage3/luis/imgs', cache_folder='/mnt/cns_storage3/luis/cache',
          use_cache=True, log_console=False, useful_tags_path=useful_tags, log_name='osmnx',
          log_file=True, log_filename='osmnx')

crs_osm = {'init':'epsg:4326'}           #crs that osm uses


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


def bike_network(geometry):
    G = ox.graph_from_polygon(polygon=geometry, network_type='all',
                              name=name, retain_all=True, simplify=False)
    non_cycleways = [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True) if not ('cycleway' in d or d['highway']=='cycleway')]
    G.remove_edges_from(non_cycleways)
    G = ox.simplify_graph(G)
    return G


#Execute the script
start = time.time()
for name, city in cities.items():
    start_0 = time.time()

    path = '/mnt/cns_storage3/luis/Data/{}/'.format(name)
    assure_path_exists(path)

    path_simple = '/mnt/cns_storage3/luis/Data/{}/simple/'.format(name)
    assure_path_exists(path_simple)

    print('Starting with: {}'.format(name))

    #Load the gemoetry
    gdf = gpd.read_file('/mnt/cns_storage3/luis/Data/{}/{}_shape/'.format(name, name))
    gdf = gdf.to_crs(crs_osm)
    geometry = gdf.unary_union
    print('{} geometry loaded, starting the download...'.format(name))
    
    #Drive
    G_drive = ox.graph_from_polygon(polygon=geometry, network_type='drive_service',
                              name=name, retain_all=False, infrastructure='way["highway"]')
    G_drive = ox.project_graph(G_drive)
    ox.save_graphml(G_drive, filename='{}_drive.graphml'.format(name), folder=path)
    print('{} Drive downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G_drive)
    nx.write_edgelist(G_simple, path=path_simple+'{}_drive_simple.txt'.format(name))
    print('{} Drive simplified and saved. Elapsed time {} s.\nStarting with pedestrian network...\n'.format(name,round(time.time()-start_0,2)))

    #Pedestrian
    G = ox.graph_from_polygon(polygon=geometry, network_type='walk',
                              name=name, retain_all=False, infrastructure='way["highway"]')
    G = ox.project_graph(G)
    ox.save_graphml(G, filename='{}_walk.graphml'.format(name), folder=path)
    print('{} Pedestrian downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_walk_simple.txt'.format(name))
    print('{} Pedestrian simplified and saved. Elapsed time {} s\nStarting with bike network...\n'.format(name,round(time.time()-start_0,2)))

    #Bike
    if name == 'Beihai':
        G = bike_walk_network(G_drive)
    else:
        G = bike_network(geometry)
        G = ox.project_graph(G)
    ox.save_graphml(G, filename='{}_bike.graphml'.format(name),folder=path)
    print('{} Bike downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_bike_simple.txt'.format(name))
    print('{} Bike simplified and saved. Elapsed time {} s\nStarting with rail network...\n'.format(name,round(time.time()-start_0,2)))

    #Rail
    try:
        G = ox.graph_from_polygon(polygon=geometry, network_type='none',
                              name=name, retain_all=True, infrastructure='way["railway"~"subway|tram|light_rail"]')
    except:
        G = ox.graph_from_polygon(polygon=geometry, network_type='none',
                              name=name, retain_all=True, infrastructure='way["railway"]')
    G = ox.project_graph(G)
    ox.save_graphml(G, filename='{}_rail.graphml'.format(name), folder=path)
    print('{} Rail downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_rail_simple.txt'.format(name))
    print('{} Bike simplified and saved. Elapsed time {} s\n\n'.format(name,round(time.time()-start_0,2)))

    print('--------------------\n{} done in {} s\n--------------------\n\n\n'.format(name,round(time.time()-start_0,2)))

print('All cities done in {} min'.format((time.time()-start)/60))
