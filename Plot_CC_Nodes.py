'''
Script to plot the distribution of nodes, areas and km by each connected component in the different layers for the different cities.
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
from collections import Counter, OrderedDict
import matplotlib.cm as cm
import matplotlib.colors as mpcol

#Confg osmnx

ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=True, log_name='osmnx',
          log_file=True, log_filename='osmnx')
now = datetime.datetime.now()

#Cities and layers to analyze
cities = {'Amsterdam':'Amsterdam, Netherlands',
          'Barcelona':'Barcelona, Catalunya, Spain',
          'Melbourne':'Melbourne, Australia',
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
layers = ['walk', 'bike', 'rail', 'drive']

#Colors and shapes for plots
colors = ['#66c2a5','#fc8d62','#e78ac3','#8da0cb']
shapes = ['o', '*', '+', 'x']

#Auxiliar functions
def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

def load_graph(name, layer):
    return ox.load_graphml('{}/{}_{}.graphml'.format(name, name, layer))

def area(G):
    nodes_proj = ox.graph_to_gdfs(G, edges=False)
    graph_area_m = nodes_proj.unary_union.convex_hull.area
    return graph_area_m


def plot_nodes_by_cc(cities, layers, colors, shapes, path_plot, normalize):
    start_t = time.time()
    fig, axes = plt.subplots(5, 3, figsize=(20,17), sharex=True, sharey=True, constrained_layout=True)
    for name, ax in zip(cities, axes.flat):
        print('Starting with {}:'.format(name))
        for layer, color, shape in zip(layers, colors, shapes):
            G = load_graph(name, layer)
            total_n = len(G.nodes())
            wcc = list(nx.weakly_connected.weakly_connected_component_subgraphs(G))
            size = [len(cc.nodes())/total_n if normalize==True else len(cc.nodes()) for cc in wcc ]
            ax.loglog([i+1 for i in range(len(wcc))],(sorted(size, reverse=True)), color=color, marker=shape, label=layer, alpha=0.5)
            print('  + {} done'.format(layer))
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_title(name, fontsize=15, pad=6)
        ax.legend()
    title = fig.suptitle('Nodes by connected component', fontsize=17,y=1)
    xlabel = fig.text(0.5, -0.01, 'Connected Components', va='center', ha='center', fontsize=12)
    if normalize == True:
        ylabel = fig.text(-0.01, 0.5, 'Normalized Size', va='center', ha='center', rotation='vertical', fontsize=12)
        fig.savefig(path_plot+'{}_Cities_NodeConnectedComponent_Normalized.png'.format(now.date()),dpi=300, bbox_inches='tight',bbox_extra_artists=[title, xlabel, ylabel])
    else:
        ylabel = fig.text(-0.01, 0.5, 'Size', va='center', ha='center', rotation='vertical', fontsize=12)
        fig.savefig(path_plot+'{}_Cities_NodeConnectedComponent.png'.format(now.date()),dpi=300, bbox_inches='tight',bbox_extra_artists=[title, xlabel, ylabel])
    print('Plot nodes by wcc done in {} s'.format(time.time()-start_t))


#Run the script
if __name__ == '__main__':
    start = time.time()
    print('Starting the script, go and grab a coffe, it is going to be a long one')
    path_plot = '../imgs/ConnectedComponents/'
    assure_path_exists(path_plot)
    plot_nodes_by_cc(cities, layers, colors, shapes, path_plot, normalize=True)
    print('-----------\nFirst plot done, elapsed time: {} min.'.format((time.time()-start)/60))

    plot_nodes_by_cc(cities, layers, colors, shapes, path_plot, normalize=False)
    print('-----------\nSecond plot done, elapsed time: {} min.'.format((time.time()-start)/60))
