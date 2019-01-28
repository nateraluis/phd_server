
# coding: utf-8

# In[1]:


import time
import osmnx as ox
import os
import networkx as nx
get_ipython().run_line_magic('matplotlib', 'inline')


# In[2]:


useful_tags = ox.settings.useful_tags_path + ['cycleway']
ox.config(data_folder='Data', logs_folder='logs',
          imgs_folder='imgs', cache_folder='cache',
          use_cache=True, log_console=True, useful_tags_path=useful_tags)


# In[3]:


def get_network(city, n_type='all', infrastructure='way["highway"]'):
    try:
        G = ox.graph_from_place(city, network_type=n_type, simplify=True, which_result=1, infrastructure=infrastructure)
    except:
        G = ox.graph_from_place(city, network_type=n_type, simplify=True, which_result=2, infrastructure=infrastructure)
    return ox.project_graph(G)


# In[4]:


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


# In[5]:


def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)


# In[6]:


def simplify_graph(G):
    G_simple = nx.Graph()

    for i,j,data in G.edges(data=True):
        w = data['weight'] if 'weight' in data else 1.0
        if G_simple.has_edge(i,j):
            G_simple[i][j]['weight'] += w
        else:
            G_simple.add_edge(i,j,weight=w)
    return G_simple


# In[7]:


def bike_walk_network(G):
    """
    Filter the network to get only the cycleways or pedestrians
    """

    #G = get_network(city)
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


# In[8]:


def area(city):
    city_shape = ox.gdf_from_place(city)
    if city_shape.geom_type.all() != 'Polygon' or city_shape.geom_type.all() != 'MultiPolygon':
        city_shape = ox.gdf_from_place(city, which_result=2)
    return city_shape




# In[9]:


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
          'Melbourne':'Melbourne, Australia',
          'LA':'Los Angeles, Los Angeles County, California, USA',
          'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}


# In[17]:


start = time.time()
for name, city in cities.items():
    start_0 = time.time()

    #Create and check the path
    path = 'data/{}/'.format(name)
    assure_path_exists(path)

    path_simple = 'data/{}/simple/'.format(name)
    assure_path_exists(path_simple)

    print('Starting with: {}'.format(name))

    #Download the shape
    city_shape = area(city)
    city_shape = ox.project_gdf(city_shape)
    ox.save_gdf_shapefile(city_shape, filename='{}_shape'.format(name), folder=path)
    print('Saved')
    ox.plot_shape(city_shape)

    #Drive
    G_drive = get_network(city, n_type='drive')
    ox.save_graphml(G_drive, filename='{}_drive.graphml'.format(name), folder=path)
    print('{} Drive downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G_drive)
    nx.write_edgelist(G_simple, path=path_simple+'{}_drive_simple.txt'.format(name))
    print('{} Drive simplified and saved. Elapsed time {} s'.format(name,round(time.time()-start_0,2)))


    #Pedestrian
    G = get_network(city, n_type='walk')
    ox.save_graphml(G, filename='{}_pedestrian.graphml'.format(name), folder=path)
    print('{} Pedestrian downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_pedestrian_simple.txt'.format(name))
    print('{} Pedestrian simplified and saved. Elapsed time {} s'.format(name,round(time.time()-start_0,2)))

    #Bike
    if name == 'Beihai':
        G = bike_walk_network(G_drive)
    else:
        G = bike_network(city)
    ox.save_graphml(G, filename='{}_bike.graphml'.format(name),folder=path)
    print('{} Bike downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_bike_simple.txt'.format(name))
    print('{} Bike simplified and saved. Elapsed time {} s'.format(name,round(time.time()-start_0,2)))

    #Rail
    try:
        G = get_network(city, n_type='none', infrastructure='way["railway"~"subway|tram|light_rail"]')
    except:
        G = get_network(city, n_type='none', infrastructure='way["railway"]')
    ox.save_graphml(G, filename='{}_rail.graphml'.format(name), folder=path)
    print('{} Rail downloaded and saved. Elapsed time {} s\nSimplifying the network...'.format(name,round(time.time()-start_0,2)))
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_rail_simple.txt'.format(name))
    print('{} Bike simplified and saved. Elapsed time {} s'.format(name,round(time.time()-start_0,2)))

    print('{} done in {} s'.format(name,round(time.time()-start_0,2)))

print('All cities done in {} min'.format((time.time()-start)/60))
