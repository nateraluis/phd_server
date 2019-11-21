'''
Code to filter out a street network and keep only bicycle infrastructure and streets with max speed =<30 km/h
'''
import os
import osmnx as ox
import networkx as nx 
from multiprocessing import Pool


# Confg osmnx
ox.config(data_folder='../Data/bike_streets', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')

def load_graph(name, layer):
    return ox.load_graphml('{}/{}_{}.graphml'.format(name, name, layer))

def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

def simplify_graph(G):
    G_simple = nx.Graph()
    for i, j, data in G.edges(data=True):
        w = data['weight'] if 'weight' in data else 1.0
        if G_simple.has_edge(i, j):
            G_simple[i][j]['weight'] += w
        else:
            G_simple.add_edge(i, j, weight=w)
    return G_simple

def filter_speed(G):
    remove = []
    for u, v, k, d in G.edges(keys=True, data=True):
        if not ('cycleway' in d or d['highway']=='cycleway'):
            try:
                 if float(d['maxspeed']) > 30:
                        remove.append((u, v, k))
            except:
                remove.append((u, v, k))
                pass
    return remove

def save_new(G, name):
    path = '../Data/bike_streets/filter/{}/'.format(name)
    assure_path_exists(path)
    path_simple = '../Data/bike_streets/filter/{}/simple/'.format(name)
    assure_path_exists(path_simple)

    ox.save_graphml(G, filename='{}_bike.graphml'.format(name), folder=path)
    G_simple = simplify_graph(G)
    nx.write_edgelist(G_simple, path=path_simple+'{}_bike__streets30_simple.txt'.format(name))
    print('{} Bike filtered and saved.'.format(name))

def main(name):
    print('Starting with: {}'.format(name))
    G = load_graph(name,'bike')
    remove = filter_speed(G)
    G.remove_edges_from(remove)
    G = ox.remove_isolated_nodes(G)
    save_new(G, name)

if __name__ == '__main__':
    # Execute the script
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
            'Bogota':'Bogota, Colombia',
            'LA':'Los Angeles, Los Angeles County, California, USA',
            'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}
    pool = Pool(processes=15)
    pool.map(main, cities)