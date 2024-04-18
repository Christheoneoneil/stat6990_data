import networkx as nx
import matplotlib.pyplot as plt 
import pandas as pd
import pathpyG as pp
import torch
from torch_geometric.data import TemporalData

pp.config['torch']['device'] = 'cpu'
# import graph_tool.all as gt

# import phasik as pk
import os 


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


def build_edge_list_time_series(graph:nx.Graph, date_at:str):
    """build lists of edge lists that simulate a time series

    Args:
        graph (networkx.Graph): graph to read in and build edge list time series
        date_at (str): name of node ettribute with date

    Returns:
    edge_list_ts (list): list of edges with time continuity 
    """
    graph = graph.copy()
    dts = dict(nx.get_node_attributes(graph, date_at))
    node_ts = pd.DataFrame.from_dict(dts, orient="index").reset_index().rename(columns={"index":"source",
                                                                                        0:date_at})
    
    node_ts.loc[:, date_at] = node_ts.loc[:, date_at].apply(lambda x: pd.to_datetime(x).replace(day=1))
    node_ts = node_ts.sort_values(by=date_at).groupby(by=date_at)

    df_ts_grouped = list([pd.DataFrame(node_ts.get_group(group)) for group in node_ts.groups])
    cumlative_ts  = [df_ts_grouped[0]]
    for df in df_ts_grouped:
        cumlative_ts.append(pd.concat([cumlative_ts[-1], df]).drop_duplicates())
    
    edge_list_ts = []
    for i, df in enumerate(cumlative_ts):
        edgelist_df = nx.to_pandas_edgelist(graph.subgraph(df["source"]))
        edgelist_df["Time"] = i
        edge_list_ts.append(edgelist_df)
    edge_list_ts = pd.concat(edge_list_ts)
    return edge_list_ts
    
    # node_list_ts = [graph.subgraph(df["source"]).nodes() for df in cumlative_ts]
    # return node_list_ts, edge_list_ts


if os.path.exists("largest_comp.gml"):
    largest_component = nx.read_gml("largest_comp.gml")

else: 
    G = nx.read_gml("network.gml")
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    largest_component  = G.subgraph(components[0])
    nx.write_gml(largest_component, path="largest_comp.gml")
print(largest_component)
ts_edge_lists = build_edge_list_time_series(graph=largest_component, date_at="release_date")
edge_list = list(ts_edge_lists[["source", "target", "Time"]].itertuples(index=False, name=None))

tn = pp.TemporalGraph.from_edge_list(edge_list=edge_list)
pp.plot(tn, delta=1000, start=4, end=65, node_labels=list(tn.nodes), filename="netvis.html")
m = pp.MultiOrderModel.from_temporal_graph(tn, delta=1)
pp.plot(m.layers[1], filename="multiorder.html")
