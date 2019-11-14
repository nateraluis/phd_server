from multiprocessing import Pool
import matplotlib.colors as mpcol
import matplotlib.colors as colors
import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import os
import time
import osmnx as ox
import matplotlib
matplotlib.use('Agg')
'''
Script to connect and analyze the different connected components on the bicycle layer of the cities.
This is a greedy algorithm that connects the two LCC's in each iteration.
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


def load_graph(name, layer):
    '''
    Load the graph into the script.
    ---
    name: str name of the city to be loaded
    layer: str layer to be loaded, it can be: drive, bike, walk, rail.

    returns: Networkx MultiDiGraph
    '''
    return ox.load_graphml('{}/{}_{}.graphml'.format(name, name, layer), folder='../Data/bike_streets/')


def euclidean_dist_vec(y1, x1, y2, x2):
    '''
    Calculate the euclidean distance between two points.
    '''
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return distance


def closest_pair(wcc):
    '''
    Find the closest pair of nodes between two different connected components.
    ---
    wcc: list connected components

    returns: dict nodes i and j and distance
    '''
    closest_pair = {'i': 0, 'j': 0, 'dist': np.inf}
    for i in wcc[0].nodes(data=True):
        i_coord = (i[1]['y'], i[1]['x'])
        for j in wcc[1].nodes(data=True):
            j_coord = (j[1]['y'], j[1]['x'])
            dist = euclidean_dist_vec(i_coord[0], i_coord[1], j_coord[0], j_coord[1])
            if dist < closest_pair['dist']:
                closest_pair['i'] = i[0]
                closest_pair['j'] = j[0]
                closest_pair['dist'] = dist
    return closest_pair


def get_data(G_bike, name):
    start = time.time()
    # 0.- Create lists to store data
    nodes_cc = []
    length_cc = []
    directness = []
    delta = []
    i_s = []
    j_s = []

    # 2.- Get weakly connected components and sort them
    print('  + Getting the connected components')
    wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)]
    wcc.sort(key=len, reverse=True)

    # Get the bike KM inside the LCC
    l_temp = 0
    # for e in wcc[0].edges(data=True):
    #    l_temp += e[2]['length']

    # Save the current status
    length_cc.append(l_temp)  # Bike km
    delta.append(0)  # Delta_x 0
    # nodes_cc.append(len(wcc[0])) #Number of nodes inside the LCC
    nodes_cc.append(0)  # Number of nodes inside the LCC
    i_s.append(0)
    j_s.append(0)
    to_iterate = len(wcc)-1  # We'll iterate over n-1 connected components
    ncc = 0
    print('  + Starting the loop:')
    for cc in range(to_iterate):
        wcc = [cc for cc in nx.weakly_connected_component_subgraphs(
            G_bike)]  # Get a list of the WCC
        wcc.sort(key=len, reverse=True)  # Sort the list from the largest to smallest
        closest_ij = closest_pair(wcc)  # Get the clossest pair of nodes between the two LCC's
        i_s.append(closest_ij['i'])  # Store the sequence of links connected
        j_s.append(closest_ij['j'])
        p_delta = delta[-1]  # Get the latest delta
        delta.append(p_delta+closest_ij['dist'])  # Add the new delta measure to the list of deltas
        # Record the new number of nodes inside the LCC after merging the two LCC's
        nodes_cc.append(len(wcc[0])+len(wcc[1]))
        l_temp = 0
        for e in wcc[0].edges(data=True):
            try:
                l_temp += e[2]['length']
            except:
                pass
        for e in wcc[1].edges(data=True):
            try:
                l_temp += e[2]['length']
            except:
                pass
        length_cc.append(l_temp/1000)
        if closest_ij['i'] != closest_ij['j']:
            G_bike.add_edge(closest_ij['i'], closest_ij['j'], length=0)  # closest_ij['dist'
        ncc += 1
        print('{} {}/{} done, elapsed time {} min, avg {} seg, to go: {} min.'.format(name, ncc, to_iterate, round((time.time() -
                                                                                                                    start)/60, 2), round((time.time()-start)/ncc, 2), round((((time.time()-start)/ncc)*(to_iterate-ncc))/60, 2)))
        if delta[-1] > 200000:
            break
    return delta, nodes_cc, length_cc, i_s, j_s


def main(name):
    # for name in cities:
    print('Starting with {}'.format(name))
    G_bike = load_graph(name, 'bike')
    data_path = '../Data/bike_streets/'
    assure_path_exists(data_path)
    print(' + Data loaded\n + Starting the calculations:')
    delta, nodes_cc, length_cc, i_s, j_s = get_data(G_bike, name)
    df = pd.DataFrame(np.column_stack([delta, nodes_cc, length_cc, i_s, j_s]), columns=[
                      'delta', 'nodes_cc', 'length_cc', 'i', 'j'])
    df.to_csv(data_path+'{}_CC_data_L2S.csv'.format(name), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None,
              compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
    print('{} done\n------------\n------------\n\n'.format(name))
    # End of loop
    #print('All cities done in {} min'.format((time.time()-Global_start)/60))


if __name__ == '__main__':
    Global_start = time.time()
    cities = {'Phoenix': 'Phoenix, Arizona, USA',
              'Detroit': 'Detroit, Michigan, USA',
              'Manhattan': 'Manhattan, New York City, New York, USA',
              'Amsterdam': 'Amsterdam, Netherlands',
              'Mexico': 'DF, Mexico',
              'London': 'London, England',
              'Singapore': 'Singapore, Singapore',
              'Budapest': 'Budapest, Hungary',
              'Copenhagen': 'Copenhagen Municipality, Denmark',
              'Barcelona': 'Barcelona, Catalunya, Spain',
              'Portland': 'Portland, Oregon, USA',
              'Bogota': 'Bogotá, Colombia',
              'LA': 'Los Angeles, Los Angeles County, California, USA',
              'Jakarta': 'Daerah Khusus Ibukota Jakarta, Indonesia'}
    print('Starting the script, go and grab a coffe, it is going to be a long one :)')
    pool = Pool(processes=10)
    pool.map(main, cities)
    print('All cities done in {} min'.format((time.time()-Global_start)/60))
