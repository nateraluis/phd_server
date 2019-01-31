'''
Script to connect and analyze the different connected components on the bicycle layer of the cities.
This iteration of the algorithm randomly takes on of the connected commponents, looks for the distance to all other commponents and create a link with the closest one.
'''

#Imports
import matplotlib
matplotlib.use('Agg')
import osmnx as ox
import time
import os
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import datetime
import random
import matplotlib.colors as colors
import matplotlib.cm as cm
import matplotlib.colors as mpcol
from itertools import combinations
from multiprocessing import Pool

#Confg osmnx
ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')
now = datetime.datetime.now()


#Auxiliar functions
def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

def load_graph(name, layer):
    return ox.load_graphml('{}/{}_{}.graphml'.format(name, name, layer))

def euclidean_dist_vec(y1,x1,y2,x2):
    """
    Calculate the euclidean distance between two nodes
    """
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return distance

def closest_pair(wcc):
    """
    Find the closest nodes between two connected component.

    wcc: List of weakly connected components
    """
    closest_pair = {'i':0,'j':0,'dist':np.inf}
    pick = random.choice(wcc) #Pick a random component
    for cccc in combinations(wcc, 2):
        for i in cccc[0].nodes(data=True):
            i_coord = (i[1]['y'], i[1]['x'])
            for j in cccc[1].nodes(data=True):
                j_coord = (j[1]['y'], j[1]['x'])
                dist = euclidean_dist_vec(i_coord[0],i_coord[1],j_coord[0],j_coord[1])
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
    delta = []
    i_s = []
    j_s = []

    # 2.- Get weakly connected components and sort them
    print('  + Getting the connected components')
    wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)]
    wcc.sort(key=len, reverse=True)

    #Get the bike KM inside the LCC
    l_temp = 0
    #for e in wcc[0].edges(data=True):
    #    l_temp += e[2]['length']

    #Save the current status
    length_cc.append(l_temp) #Bike km
    delta.append(0) #Delta_x 0
    #nodes_cc.append(len(wcc[0])) #Number of nodes inside the LCC
    nodes_cc.append(0) #Number of nodes inside the LCC

    to_iterate = len(wcc)-1
    ncc = 0
    for it in range(to_iterate):
        if it == 0:
            wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)] #Get the WCC's
        closest_ij = closest_pair(wcc) #Find the closest pair of nodes
        if closest_ij['i'] != closest_ij['j']: #Sanity check, the nodes have to be different
            i_s.append(closest_ij['i']) #Store the sequence of links connected
            j_s.append(closest_ij['j'])
            G_bike.add_edge(closest_ij['i'],closest_ij['j'], length=0) #Add the new link closest_ij['dist']
            p_delta = delta[-1] #Get the previous aggregated delta
            delta.append(p_delta+closest_ij['dist']) #Record the new sum of deltas
            wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)] #Get the new WCC's
            wcc.sort(key=len, reverse=True) #Sort them to get the largest one
            nodes_cc.append(len(wcc[0])) #Record the number of nodes from the largest one
            l_temp = 0 #Temporal store of the length
            for e in wcc[0].edges(data=True):
                l_temp += e[2]['length'] #Get the total length of the LCC
            length_cc.append(l_temp/1000)
        ncc += 1
        print('{} {}/{} done, elapsed time {} min, avg {} seg, to go: {} min.'.format(name, ncc, to_iterate, round((time.time()-start)/60,2),round((time.time()-start)/ncc,2),round((((time.time()-start)/ncc)*to_iterate-ncc)/60,2)))
        if delta[-1] > 200000:
            break
    return delta, nodes_cc, length_cc, i_s, j_s



def main(name):
    #Global_start = time.time()
    path_plot = '../imgs/Percolation/'
    assure_path_exists(path_plot)
    print('Path ready')
    #for name in cities:
    print('Starting with {}'.format(name))
    G_bike = load_graph(name, 'bike')
    data_path = '../Data/WCC/'
    assure_path_exists(data_path)
    print(' + Data loaded\n + Starting the calculations:')
    delta, nodes_cc, length_cc, i_s, j_s = get_data(G_bike, name )
    df = pd.DataFrame(np.column_stack([delta, nodes_cc, length_cc, i_s, j_s]), columns=['delta', 'nodes_cc', 'length_cc', 'i', 'j'])
    df.to_csv(data_path+'{}_CC_SmallestDelta_data.csv'.format(name), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
    print('{} done\n------------\n------------\n\n'.format(name))

if __name__ == '__main__':
    Global_start = time.time()
    cities = {'Phoenix':'Phoenix, Arizona, USA',
              'Detroit':'Detroit, Michigan, USA',
              'Manhattan':'Manhattan, New York City, New York, USA',
              'Amsterdam':'Amsterdam, Netherlands',
              'Mexico':'DF, Mexico',
              'London':'London, England',
              'Singapore':'Singapore, Singapore',
              'Budapest':'Budapest, Hungary',
              'Copenhagen':'Copenhagen Municipality, Denmark',
              'Barcelona':'Barcelona, Catalunya, Spain',
              'Portland':'Portland, Oregon, USA',
              'Bogota':'Bogotá, Colombia',
              'LA':'Los Angeles, Los Angeles County, California, USA',
              'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}
    print('Starting the script, go and grab a coffe, it is going to be a long one :)')
    pool = Pool(processes=10)
    pool.map(main, cities)
    print('All cities done in {} min'.format((time.time()-Global_start)/60))
