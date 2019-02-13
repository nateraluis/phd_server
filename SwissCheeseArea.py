'''
Script to analyze the coverage of the bicycle layer in each itteration of the algorithms.
'''

#Imports
import osmnx as ox
import time
import os
import pandas as pd
import networkx as nx
import geopandas as gpd
import datetime
from multiprocessing import Pool

#Confg osmnx
ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')
now = datetime.datetime.now()


#Working functions
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
    G_bike = ox.load_graphml('{}/{}_bike.graphml'.format(name,name))
    G_bike = ox.project_graph(G_bike,to_crs=crs_osm)
    G_drive = ox.load_graphml('{}/{}_drive.graphml'.format(name,name))
    G_drive = ox.project_graph(G_drive,to_crs=crs_osm)
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
        df = pd.read_csv('../Data/WCC/{}_CC_Random_data.csv'.format(name), lineterminator='n', index_col=0)
    elif algorithm == 'min_delta':
        df = pd.read_csv('../Data/WCC/{}_CC_SmallestDelta_data.csv'.format(name), lineterminator='n', index_col=0)
    elif algorithm == 'greedy_min':
        df = pd.read_csv('../Data/WCC/{}_CC_data_Greedy_Closest.csv'.format(name), lineterminator='n', index_col=0)
    df['i'] = df.i.round(0).astype(int)
    df['j'] = df.j.round(0).astype(int)
    return df

def area(G):
    '''
    Calculate the area for one spatial embed graph

    G: nx.MultiDigraph

    returns:
    area: float area in square km
    '''
    nodes_proj = ox.graph_to_gdfs(G, edges=False)
    return nodes_proj.unary_union.convex_hull.area/10**6

def get_coverage(G, buffer):
    '''
    Get the coverage area in square kilometers for the bicycle layer
    G_bike: nx.MultiDiGraph
    buffer: radius in meters of the buffer (float or integer)

    returns:
    area: float. Area in square km
    '''
    nodes, edges = ox.graph_to_gdfs(G_bike)
    circles = nodes.buffer(buffer)
    squares = edges.buffer(buffer)
    buffers = squares.append(circles)
    cover = buffers.unary_union
    return cover.area/10**6

def main(name):
    for algorithm in algorithms:
        start = time.time()
        print('Starting with {}'.format(name))
        G_bike, G_drive = load_graphs(name)
        df = load_df(name, algorithm)
        data_path = '../Data/WCC/new/'
        assure_path_exists(data_path)
        print(' + Data loaded in {}\n + Starting the calculations:'.format(round(time.time()-start,3)))
        area_total = area(G_drive)
        coverage = []
        for i,row in df.iterrows():
            try:
                G_bike.add_edge(row['i'], row['j'])
                coverage.append(get_coverage(G_bike,200)/area_total)
                n+=1
                print(' {}: {}/{}'.format(name,n,len(df)))
            except:
                coverage.append(get_coverage(G_bike,200)/area_total)
                n+=1
                print(' {}: {}/{} Elapsed time: {} seg.'.format(name,i+1,len(df),round(time.time()-start,3)))
        df['coverage'] = coverage
        df.to_csv(data_path+'{}_{}.csv'.format(name,algorithm), sep=",", na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='n', chunksize=None, tupleize_cols=None, date_format=None, doublequote=True, escapechar=None, decimal='.')
        print('{} {} done in {} min.\n------------\n------------\n\n'.format(name, algorithm,round((time.time()-start)/60,3)))

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
