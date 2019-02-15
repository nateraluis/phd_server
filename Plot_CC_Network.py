import os
import time
import datetime
import osmnx as ox
import networkx as nx
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors as mpcol
import matplotlib
matplotlib.use('Agg')


ox.config(data_folder='../Data', logs_folder='../logs',
          imgs_folder='../imgs', cache_folder='../cache',
          use_cache=True, log_console=False, log_name='osmnx',
          log_file=True, log_filename='osmnx')

cities = {'Amsterdam': 'Amsterdam, Netherlands',
          'Budapest': 'Budapest, Hungary',
          'Phoenix': 'Phoenix, Arizona, USA',
          'Detroit': 'Detroit, Michigan, USA',
          'Manhattan': 'Manhattan, New York City, New York, USA',
          'Mexico': 'DF, Mexico',
          'London': 'London, England',
          'Singapore': 'Singapore, Singapore',
          'Copenhagen': 'Copenhagen Municipality, Denmark',
          'Barcelona': 'Barcelona, Catalunya, Spain',
          'Portland': 'Portland, Oregon, USA',
          'Bogota': 'Bogotá, Colombia',
          'LA': 'Los Angeles, Los Angeles County, California, USA',
          'Jakarta': 'Daerah Khusus Ibukota Jakarta, Indonesia'}


def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)


def load_graph(name, layer):
    return ox.load_graphml('{}/{}_{}.graphml'.format(name, name, layer))


def get_colors(wcc):
    norm = mpcol.Normalize(vmin=0, vmax=len(wcc), clip=True)
    mapper = cm.ScalarMappable(norm=norm, cmap=cm.tab20b)
    colors = [mapper.to_rgba(x) for x in range(len(wcc))]
    return colors


def get_wcc(G_bike):
    wcc = [list(cc.edges())
           for cc in list(nx.weakly_connected.weakly_connected_component_subgraphs(G_bike))]
    wcc.sort(key=len, reverse=False)
    return wcc


def plot_wcc_graph(G, name, wcc, path_plot, filter_wcc=False, n_cc=0):
    if filter_wcc:
        del wcc[:-n_cc]

    colors = get_colors(wcc)
    color_dict = {}
    for n, cc in enumerate(wcc):
        for e in cc:
            color_dict[e] = colors[n]

    color_edge = []
    width = []
    for e in G.edges():
        if e in color_dict:
            color_edge.append(color_dict[e])
            width.append(1.55)
        else:
            color_edge.append('#c4c8ce')
            width.append(0.2)

    fig, ax = ox.plot_graph(G, node_size=0, edge_color=color_edge,
                            fig_height=10, edge_linewidth=width, show=False, close=False)
    ax.set_title('{} Connected Components'.format(n_cc), fontdict={'fontsize': 12})
    fig.suptitle('{} bicycle network\n'.format(name), y=0.94, fontsize=20)
    if n_cc == 0:
        plt.savefig(path_plot+'{}_AllCC.png'.format(name), dpi=200)
    elif n_cc < 100 and n_cc < 10 and n_cc > 0:
        plt.savefig(path_plot+'gif_{}_00{}.png'.format(name, n_cc), dpi=200)
    elif n_cc < 100:
        plt.savefig(path_plot+'gif_{}_0{}.png'.format(name, n_cc), dpi=200)
    else:
        plt.savefig(path_plot+'gif_{}_{}.png'.format(name, n_cc), dpi=200)


def main(cities):
    for name in cities:
        path_plot = '../imgs/ConnectedComponents/CCOverNetwork/{}/'.format(name)
        assure_path_exists(path_plot)

        st = time.time()
        G_bike = load_graph(name, 'bike')
        G_drive = load_graph(name, 'drive')
        G = nx.compose(G_bike, G_drive)
        print('{} loaded.'.format(name))

        wcc = get_wcc(G_bike)

        plot_wcc_graph(G, name, wcc, path_plot, filter_wcc=False, n_cc=0)
        print('  First plot done')
        for i in range(1, 31):
            time_temp = time.time()
            wcc = get_wcc(G_bike)
            plot_wcc_graph(G, name, wcc, path_plot, filter_wcc=True, n_cc=i)
            print('  {}/31 done in {} seg. Elapsed time: {} min'.format(i,
                                                                        round(time.time()-time_temp, 2), round((time.time()-st)/60, 2)))
        print('{} done in {} min.'.format(name, round((time.time()-st)/60, 2)))
    print('All cities done')


if __name__ == '__main__':
    main(cities)
