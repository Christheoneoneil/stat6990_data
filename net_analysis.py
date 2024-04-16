import networkx as nx
import matplotlib.pyplot as plt 

def vis_network(G):
    """
    using networkx visualize network 

    Params: 

    Reuturns:
    None
    """
    plt.figure(figsize=(15, 10))
    nx.draw_kamada_kawai(G, alpha=.3)
    plt.show()

graph = nx.read_gml(path="network.gml")
