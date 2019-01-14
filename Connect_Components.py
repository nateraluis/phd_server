'''
Script to connect and analyze the different connected components on the bicycle layer of the cities.
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
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return distance

def closest_pair(wcc):
    closest_pair = {'i':0,'j':0,'dist':np.inf}
    for i in wcc[0].nodes(data=True):
        i_coord = (i[1]['y'], i[1]['x'])
        for j in wcc[1].nodes(data=True):
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
    print('  + Getting the connected components')
    wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)]
    wcc.sort(key=len, reverse=True)

    l_temp = 0
    for e in wcc[0].edges(data=True):
        l_temp += e[2]['length']

    #Save the current status
    length_cc.append(l_temp/1000)
    delta.append(0)
    nodes_cc.append(len(wcc[0]))

    to_iterate = len(wcc)-1
    ncc = 0
    print('  + Starting the loop:')
    for cc in range(to_iterate):
        wcc = [cc for cc in nx.weakly_connected_component_subgraphs(G_bike)]
        wcc.sort(key=len, reverse=True)
        #print('   + Looking for closest pair of nodes...')
        closest_ij = closest_pair(wcc)
        #print('   + Clossest pair of nodes found: {}'.format(closest_ij))
        p_delta = delta[-1]
        delta.append(p_delta+closest_ij['dist'])
        nodes_cc.append(len(wcc[0])+len(wcc[1]))
        l_temp = 0
        for e in wcc[0].edges(data=True):
            l_temp += e[2]['length']
        for e in wcc[1].edges(data=True):
            l_temp += e[2]['length']
        length_cc.append(l_temp/1000)
        if closest_ij['i'] != closest_ij['j']:
            G_bike.add_edge(closest_ij['i'],closest_ij['j'], length=closest_ij['dist'])
        ncc += 1
        print('{} {}/{} done, elapsed time {} min, avg {} seg'.format(name, ncc, to_iterate, (time.time()-start)/60,(time.time()-start)/ncc))
    return delta, nodes_cc, length_cc

def make_plots(name, delta, nodes_cc, length_cc, path_plot):
    shapes = ['.', '*', '+', 'x']
    colors = ['#fc8d62','#8da0cb','#e78ac3','#66c2a5']
    ylabels = ['N','Km','N','Km']
    labels = ['Connected Nodes', 'Connected Km', 'Connected Nodes (norm)', 'Connected Km (norm)']
    nodes_cc_norm = [n/nodes_cc[-1] for n in nodes_cc]
    length_cc_norm = [cc/length_cc[-1] for cc in length_cc]
    data = [nodes_cc, length_cc, nodes_cc_norm, length_cc_norm]
    fig, axes = plt.subplots(2, 2, figsize=(20,17), sharex=True, sharey=False, constrained_layout=True)
    print('  Starting the ploting')
    for d, ax, shape, label, ylab, color in zip(data, axes.flat, shapes, labels, ylabels, colors):
        ax.plot(delta, d, marker=shape, label=label, color=color, linewidth=0.5)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_title(label, fontsize=15, pad=6)
        ax.set_ylabel(ylab, fontsize=10)
        ax.set_xlabel(r'$\Delta_x$', fontsize=10)
    title = fig.suptitle(name, fontsize=17,y=1)
    fig.savefig(path_plot+'{}_{}_Delta.png'.format(now.date(),name),dpi=300, bbox_inches='tight',bbox_extra_artists=[title])

    fig, ax = plt.subplots(figsize=(16,9))
    ax.plot(delta, nodes_cc_norm, marker=shapes[2], color=colors[2], label='Nodes')
    ax.plot(delta, length_cc_norm,marker=shapes[3], color=colors[3], label='Km')
    ax.legend(frameon=False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_title(r'{} Nodes and Km Increase by $\Delta_x$'.format(name), fontsize=18, pad=6)
    ax.set_xlabel(r'$\Delta_x\ (m)$', fontsize=14)
    fig.savefig(path_plot+'{}_{}_N_KM_norm.png'.format(now.date(),name),dpi=300, bbox_inches='tight')

def main(name):
    #Global_start = time.time()
    path_plot = '/mnt/cns_storage3/luis/imgs/Percolation/'
    assure_path_exists(path_plot)
    print('Path ready')
    #for name in cities:
    print('Starting with {}'.format(name))
    G_bike = load_graph(name, 'bike')
    data_path = '/mnt/cns_storage3/luis/Data/WCC/'
    assure_path_exists(data_path)
    print(' + Data loaded\n + Starting the calculations:')
    delta, nodes_cc, length_cc = get_data(G_bike, name )
    df = pd.DataFrame(np.column_stack([delta, nodes_cc, length_cc]), columns=['delta', 'nodes_cc', 'length_cc'])
    df.to_csv(data_path+'{}_CC_data.csv'.format(name), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
    make_plots(name, delta, nodes_cc, length_cc, path_plot)
    print('{} done\n------------\n------------\n\n'.format(name))
        #End of loop
    #print('All cities done in {} min'.format((time.time()-Global_start)/60))

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
