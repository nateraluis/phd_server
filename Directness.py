import datetime
import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import os
import time
import osmnx as ox
from multiprocessing import Pool
'''
Script to calculate the directness as the average percent difference in shortest path distances of bikes using bike lanes versus using streets.
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
    """Short summary.

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
    for u in range(pairs):
        i = random.choice(list(G_bike.nodes(data=True)))
        j = random.choice(list(G_bike.nodes(data=True)))
        if i[0] != j[0]:
            seeds_bike.append((i[0], j[0]))
            u = ox.get_nearest_node(G_drive, (i[1]['y'], i[1]['x']))
            v = ox.get_nearest_node(G_drive, (j[1]['y'], j[1]['x']))
            seeds_car.append((u, v))
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
    wcc = list(nx.connected_component_subgraphs(G_bike)).sort(key=len, reverse=True)
    return wcc[0]


def calculate_directness(df, G_bike, G_drive):
    df['d_ij_b'] = 0
    df['d_ij_s'] = 0
    for ind, row in df.iterrows():
        avg_bike = []
        avg_street = []
        if ind > 0:
            G_bike.add_edge(row['i'], row['j'], length=euclidean_dist_vec(G_bike.nodes[row['i']]['y'],
                                                                          G_bike.nodes[row['i']]['x'], G_bike.nodes[row['j']]['y'], G_bike.nodes[row['j']]['x']))
        cc = get_lcc(G_bike)
        seeds_bike, seeds_car = get_seeds(cc, G_drive, 1000)
        for i_j, u_v in zip(seeds_bike, seeds_car):
            avg_bike.append(nx.shortest_path_length(cc, i_j[0], i_j[1], weight='length'))
            avg_street.append(nx.shortest_path_length(G_drive, u_v[0], u_v[1], weight='length'))
        row['d_ij_b'] = np.average(avg_bike)
        row['d_ij_s'] = np.average(avg_street)
    return df


def main(name):
    algorithms = ['min_delta', 'greedy_LCC', 'random', 'greedy_min']
    for algorithm in algorithms:
        start = time.time()
        print('Starting with {}'.format(name))
        # Load the dataframe
        try:
            df = load_df(name, algorithm)
            # Load the graph
            G_bike, G_drive = load_graphs(name)
            data_path = '../Data/WCC/new/'
            assure_path_exists(data_path)
            print('{} {} data loaded in {}\n + Starting the calculations:'.format(name,
                                                                                  algorithm, round(time.time()-start, 3)))
            new_df = calculate_directness(df, G_bike, G_drive)
            new_df.to_csv(data_path+'{}_{}.csv'.format(name, algorithm), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None,
                          compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
            print('{} {} done in {} min.\n------------\n------------\n\n'.format(name,
                                                                                 algorithm, round((time.time()-start)/60, 3)))
        except:
            print('Problems with {} {}'.format(name, algorithm))
            pass


if __name__ == '__main__':
    Global_start = time.time()
    # 'London':'London, England',
    cities = {'Phoenix': 'Phoenix, Arizona, USA',
              'Detroit': 'Detroit, Michigan, USA',
              'Manhattan': 'Manhattan, New York City, New York, USA',
              'Amsterdam': 'Amsterdam, Netherlands',
              'Mexico': 'DF, Mexico',
              'Singapore': 'Singapore, Singapore',
              'Budapest': 'Budapest, Hungary',
              'Copenhagen': 'Copenhagen Municipality, Denmark',
              'Barcelona': 'Barcelona, Catalunya, Spain',
              'Portland': 'Portland, Oregon, USA',
              'Bogota': 'Bogotá, Colombia',
              'LA': 'Los Angeles, Los Angeles County, California, USA',
              'Jakarta': 'Daerah Khusus Ibukota Jakarta, Indonesia',
              'London': 'London, England'}
    print('Starting the script, go and grab a coffe, it is going to be a long one :)')
    pool = Pool(processes=10)
    pool.map(main, cities)
    print('All cities done in {} min'.format((time.time()-Global_start)/60))
