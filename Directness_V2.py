import datetime
import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import os
import time
import osmnx as ox
import random
from multiprocessing import Pool
'''
Original Script Script to calculate the directness as the average percent difference in shortest path distances of bikes using bike lanes versus using streets.
'''

# Confg osmnx
ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')
now = datetime.datetime.now()

# Working functions


def assure_path_exists(path):
    '''
    Check if the path to one folder exists and if not create it.
    ---
    path: str containing the path to check
    '''
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)


def load_graphs(name):
    '''
    Load the graphs (bike and drive) and the CSV with the results of the algorithm into the script.
    ---
    name: str name of the city to be loaded
    layer: str layer to be loaded, it can be: drive, bike, walk, rail.

    returns: Networkx MultiDiGraph
    '''

    crs = {'Phoenix': {'init': 'epsg:2763'},
           'Detroit': {'init': 'epsg:2763'},
           'Manhattan': {'init': 'epsg:2763'},
           'Amsterdam': {'init': 'epsg:32633'},
           'Mexico': {'init': 'epsg:6372'},
           'London': {'init': 'epsg:32633'},
           'Singapore': {'init': 'epsg:3414'},
           'Budapest': {'init': 'epsg:32633'},
           'Copenhagen': {'init': 'epsg:32633'},
           'Barcelona': {'init': 'epsg:32633'},
           'Portland': {'init': 'epsg:26949'},
           'Bogota': {'init': 'epsg:3116'},
           'LA': {'init': 'epsg:2763'},
           'Jakarta': {'init': 'epsg:5331'}}

    G_bike = ox.load_graphml('{}/{}_bike.graphml'.format(name, name))
    G_drive = ox.load_graphml('{}/{}_drive.graphml'.format(name, name))
    G_bike = ox.get_undirected(G_bike)
    G_drive = ox.get_undirected(G_drive)
    return G_bike, G_drive


def load_df(name, algorithm):
    '''
    Load the dataframe with the results and sequence from the connect_component algorithms.
    name: str name of the city to be loaded
    algorithm: str name of the algorithm

    returns: Dataframe
    '''

    if algorithm == 'greedy_LCC':
        df = pd.read_csv('../Data/WCC/{}_CC_data.csv'.format(name), lineterminator='n', index_col=0)
    elif algorithm == 'random':
        df = pd.read_csv('../Data/WCC/{}_CC_Random_data.csv'.format(name),
                         lineterminator='n', index_col=0)
    elif algorithm == 'min_delta':
        df = pd.read_csv('../Data/WCC/{}_CC_SmallestDelta_data.csv'.format(name),
                         lineterminator='n', index_col=0)
    elif algorithm == 'greedy_min':
        df = pd.read_csv('../Data/WCC/{}_CC_data_Greedy_Closest.csv'.format(name),
                         lineterminator='n', index_col=0)
    df['i'] = df.i.round(0).astype(int)
    df['j'] = df.j.round(0).astype(int)
    return df


def get_seeds(G_bike, G_drive, pairs):
    """Get x pairs of random pairs of nodes in the bike and street layer.

    Parameters
    ----------
    G_bike : type
        Description of parameter `G_bike`.
    G_drive : type
        Description of parameter `G_drive`.
    pairs : type
        Description of parameter `pairs`.

    Returns
    -------
    type
        Description of returned object.

    """
    seeds_bike = []
    seeds_car = []
    u = 0
    for u in range(pairs):
        i = random.choice(list(G_bike.nodes(data=True)))
        j = random.choice(list(G_bike.nodes(data=True)))
        u = ox.get_nearest_node(G_drive, (i[1]['y'], i[1]['x']))
        v = ox.get_nearest_node(G_drive, (j[1]['y'], j[1]['x']))
        if u != v or i[0] != j[0]:
            seeds_car.append((u, v))
            seeds_bike.append((i[0], j[0]))
        else:
            i = random.choice(list(G_bike.nodes(data=True)))
            j = random.choice(list(G_bike.nodes(data=True)))
            u = ox.get_nearest_node(G_drive, (i[1]['y'], i[1]['x']))
            v = ox.get_nearest_node(G_drive, (j[1]['y'], j[1]['x']))
    return seeds_bike, seeds_car


def euclidean_dist_vec(y1, x1, y2, x2):
    '''
    Calculate the euclidean distance between two points.
    '''
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return distance


def get_lcc(G):
    """Take a graph and return the largest connected component.

    Parameters
    ----------
    G : networks.Graph
        Graph with more than one connected component.

    Returns
    -------
    networkx.Graph
        Subgraph of G with the largest connected component.

    """
    wcc = list(nx.connected_component_subgraphs(G))
    wcc.sort(key=len, reverse=True)
    return wcc[0]


def get_travel_distance(G, u_v):
    """Find the shortest path between two nodes and calculate the travel distance.

    Parameters
    ----------
    G : nx.Graph
        Networkx graph.
    u_v : touple
        Touple containing the origin and destination for the path.

    Returns
    -------
    int
        Distance for the path between 'u' to 'v'.

    """
    path = nx.shortest_path(G, u_v[0], u_v[1], weight='length')
    distance = 0
    for i, j in zip(path[:-1], path[1:]):
        #distance += float(G[i][j][0]['length'])
        try:
            distance += float(G[i][j][0]['length'])
        except:
            print('Error: {} {}'.format(G, u_v))
        #    pass
            distance += euclidean_dist_vec(G.nodes[i]['y'],
                                           G.nodes[i]['x'], G.nodes[j]['y'], G.nodes[j]['x'])
    return distance


def calculate_directness(df, G_bike, G_drive, name, algorithm, seeds_bike, car_value):

    d_ij_b = []
    d_ij_s = []
    print('Calculating {}'.format(name))
    start = time.time()
    distances_ij = {}
    for i_j in seeds_bike:
        distances_ij[i_j] = 0
    for ind, row in df.iterrows():
        temp_start = time.time()
        print('{} {}: {}/{}'.format(name, algorithm, ind, len(df)))
        avg_bike = []
        if ind > 0:
            G_bike.add_edge(row['i'], row['j'], length=euclidean_dist_vec(G_bike.nodes[row['i']]['y'],
                                                                          G_bike.nodes[row['i']]['x'], G_bike.nodes[row['j']]['y'], G_bike.nodes[row['j']]['x']))
        for i_j in seeds_bike:
            euclidean_distance = euclidean_dist_vec(
                G_bike.nodes[i_j[0]]['y'], G_bike.nodes[i_j[0]]['x'], G_bike.nodes[i_j[1]]['y'], G_bike.nodes[i_j[0]]['x'])
            if distances_ij[i_j] != 0:
                avg_bike.append(euclidean_distance/distances_ij[i_j])
            if nx.has_path(G_bike, i_j[0], i_j[1]):
                bike_distance = get_travel_distance(G_bike, i_j)
                avg_bike.append(euclidean_distance/bike_distance)
                distances_ij[i_j] = bike_distance
            else:
                avg_bike.append(0)
        bike_value = np.average(avg_bike)
        d_ij_b.append(bike_value)
        d_ij_s.append(car_value)
        print('{} {} calculation {}/{} Efficiency: {}/{} done in {} s To go: {} min.'.format(name, algorithm, ind,
                                                                                             len(df), round(bike_value, 3), round(car_value, 3), time.time()-temp_start, round(((len(df)-ind)*(time.time()-temp_start))/60, 3)))
    df['d_ij_b'] = d_ij_b
    df['d_ij_s'] = d_ij_s
    print('{} done in {} min'.format(name, round((time.time()-start)/60, 3)))
    return df


def run_calculations(algorithm, G_bike_o, G_drive_o, name, seeds_bike, seeds_car, car_value):
    start = time.time()
    G_bike = G_bike_o.copy()
    G_drive = G_drive_o.copy()

    # Load the dataframe

    df = load_df(name, algorithm)
    # Load the graph

    data_path = '../Data/WCC/new/'
    assure_path_exists(data_path)
    print('{} {} data loaded in {}\n + Starting the calculations:'.format(name,
                                                                          algorithm, round(time.time()-start, 3)))
    new_df = calculate_directness(df, G_bike, G_drive, name, algorithm, seeds_bike, car_value)
    new_df.to_csv(data_path+'{}_{}.csv'.format(name, algorithm), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None,
                  compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
    print('{} {} done in {} min.\n------------\n------------\n\n'.format(name,
                                                                         algorithm, round((time.time()-start)/60, 3)))


def main(name):
    print('Starting with {}'.format(name))
    algorithms = ['greedy_min', 'greedy_LCC', 'min_delta', 'random']  #
    G_bike_o, G_drive_o = load_graphs(name)
    print('{} data loaded'.format(name))
    seeds_bike, seeds_car = get_seeds(G_bike_o, G_drive_o, 1000)
    print('{} bike seeds, {} car seeds'.format(len(seeds_bike), len(seeds_car)))
    avg_street = []
    for u_v in seeds_car:
        euclidean_distance = euclidean_dist_vec(G_drive_o.nodes[u_v[0]]['y'],
                                                G_drive_o.nodes[u_v[0]]['x'], G_drive_o.nodes[u_v[1]]['y'], G_drive_o.nodes[u_v[0]]['x'])
        travel_distance = get_travel_distance(G_drive_o, u_v)
        avg_street.append(euclidean_distance/travel_distance)
    car_value = np.average(avg_street)  # Average efficiency in the car layer
    print('Calculations done fore cars, d_ij^s = {}'.format(car_value))
    for algorithm in algorithms:
        run_calculations(algorithm, G_bike_o, G_drive_o, name, seeds_bike, seeds_car, car_value)


if __name__ == '__main__':
    Global_start = time.time()

    cities = {'Amsterdam': 'Amsterdam, Netherlands',
              'London': 'London, England',
              'Budapest': 'Budapest, Hungary',
              'Mexico': 'DF, Mexico',
              'Singapore': 'Singapore, Singapore',
              'Copenhagen': 'Copenhagen Municipality, Denmark',
              'Barcelona': 'Barcelona, Catalunya, Spain',
              'Portland': 'Portland, Oregon, USA',
              'Bogota': 'Bogotá, Colombia',
              'LA': 'Los Angeles, Los Angeles County, California, USA',
              'Jakarta': 'Daerah Khusus Ibukota Jakarta, Indonesia',
              'Phoenix': 'Phoenix, Arizona, USA',
              'Detroit': 'Detroit, Michigan, USA',
              'Manhattan': 'Manhattan, New York City, New York, USA',
              }

    print('Starting the script, go and grab a coffe, it is going to be a long one :)')
    pool = Pool(processes=15)
    pool.map(main, cities)

    print('All cities done in {} min'.format((time.time()-Global_start)/60))
