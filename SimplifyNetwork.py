import osmnx as ox
import networkx as nx

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
          'LA':'Los Angeles, Los Angeles County, California, USA',
          'Jakarta':'Daerah Khusus Ibukota Jakarta, Indonesia'}

ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')

layers = ['drive', 'walk', 'bike', 'rail']

for name, city in cities.items():
    print('Starting with {}'.format(name))
    for layer in layers:
        path = '../Data/{}/'.format(name)
        G = ox.load_graphml('{}_{}.graphml'.format(name, layer), folder=path)
        degree = list(G.degree())
        remove=[]
        for k in degree:
            n,v = k
            if v == 0:
                remove.append(n)
        G.remove_nodes_from(remove)
        ox.save_graphml(G, filename='{}_{}.graphml'.format(name, layer), folder=path)
        print('{} {} simplified.'.format(name, layer))
    print('Done with {}\n'.format(name))
print ('All cities done.')
