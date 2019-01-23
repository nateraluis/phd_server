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
from multiprocessing import Pool

#Confg osmnx
ox.config(data_folder='/mnt/cns_storage3/luis/Data', logs_folder='/mnt/cns_storage3/luis/logs',
          imgs_folder='/mnt/cns_storage3/luis/imgs', cache_folder='/mnt/cns_storage3/luis/cache',
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
    for i in pick.nodes(data=True): #Pick a random component, iterate over its nodes
        i_coord = (i[1]['y'], i[1]['x'])
        for cc in wcc:
            if cc != pick:
                for j in cc.nodes(data=True):
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

    # 2.- Get weakly connected components and sort them
    #print('  + Getting the connected components')
    wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)]
    wcc.sort(key=len, reverse=True)

    l_temp = 0
    for e in wcc[0].edges(data=True):
        l_temp += e[2]['length']

    #Save the initial status
    length_cc.append(l_temp/1000)
    delta.append(0)
    nodes_cc.append(len(wcc[0]))

    to_iterate = len(wcc)-1
    ncc = 0
    print('  + Starting the loop:')
    for it in range(to_iterate): #loop over N-1 components
        if it == 0:
            wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)] #Get the WCC's
        closest_ij = closest_pair(wcc) #Find the closest pair of nodes
        if closest_ij['i'] != closest_ij['j']: #Sanity check, the nodes have to be different
            G_bike.add_edge(closest_ij['i'],closest_ij['j'], length=closest_ij['dist']) #Add the new link
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
    return delta, nodes_cc, length_cc



def main(name):
    #Global_start = time.time()
    path_plot = '/mnt/cns_storage3/luis/imgs/Percolation/'
    assure_path_exists(path_plot)
    #for name in cities:
    print('Starting with {}'.format(name))
    G_bike = load_graph(name, 'bike')
    data_path = '/mnt/cns_storage3/luis/Data/WCC/'
    assure_path_exists(data_path)
    delta, nodes_cc, length_cc = get_data(G_bike, name )
    df = pd.DataFrame(np.column_stack([delta, nodes_cc, length_cc]), columns=['delta', 'nodes_cc', 'length_cc'])
    df.to_csv(data_path+'{}_CC_Random_data.csv'.format(name), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
    print('{} done\n------------\n------------\n\n'.format(name))

if __name__ == '__main__':
    Global_start = time.time()
    cities = {'Amsterdam':'Amsterdam, Netherlands',
              'Barcelona':'Barcelona, Catalunya, Spain',
              'Beihai':'Beihai, China',
              'Bogota':'Bogotá, Colombia',
              'Budapest':'Budapest, Hungary',
              'Copenhagen':'Copenhagen Municipality, Denmark',
              'Detroit':'Detroit, Michigan, USA',
              'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia',
              'LA':'Los Angeles, Los Angeles County, California, USA',
              'London':'London, England',
              'Manhattan':'Manhattan, New York City, New York, USA',
              'Mexico':'DF, Mexico',
              'Phoenix':'Phoenix, Arizona, USA',
              'Portland':'Portland, Oregon, USA',
              'Singapore':'Singapore, Singapore'}
    print('Starting the script, go and grab a coffe, it is going to be a long one :)')
    pool = Pool()
    pool.map(main, cities)
    print('All cities done in {} min'.format((time.time()-Global_start)/60))