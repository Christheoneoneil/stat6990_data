import networkx as nx
import matplotlib.pyplot as plt 
import pandas as pd
import numpy as np
import seaborn as sns
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


def build_edge_list_time_series(graph:nx.Graph, date_at:str)->pd.DataFrame:
    """build lists of edge lists that simulate a time series

    Args:
        graph (networkx.Graph): graph to read in and build edge list time series
        date_at (str): name of node ettribute with date

    Returns:
    edge_list_ts (pd.DataFrame): edge list with time continuity
    """
    graph = graph.copy().to_directed()
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
        subgraph = graph.subgraph(df["source"]).copy()
        nx.set_edge_attributes(subgraph, values=df["release_date"].to_list()[-1], name="release_date")
        edgelist_df = nx.to_pandas_edgelist(subgraph)
        edgelist_df["Time"] = i
        
        edge_list_ts.append(edgelist_df)
    edge_list_ts = pd.concat(edge_list_ts)
    return edge_list_ts
    

def visualize_temp_net(edge_df:pd.DataFrame, tn_vars:list)->None:
    """visualizez a temporal netowrk by using a pandas data frame
    Args:
        edge_df (pd.DataFrame): data frame that contains an edge list columns source, traget and a time column
        tn_vars: list of variables refrencing temporal vars, must be in order: source_var, target_var, time unit

    Returns:
        None
    """
    import pathpyG as pp
    import torch
    from torch_geometric.data import TemporalData
    pp.config['torch']['device'] = 'cpu'
    edge_list = list(edge_df[tn_vars].itertuples(index=False, name=None))
    tn = pp.TemporalGraph.from_edge_list(edge_list=edge_list)
    pp.plot(tn, delta=1000, start=4, end=65, node_labels=list(tn.nodes), filename="netvis.html")


def format_df_fortn(edge_df:pd.DataFrame, tn_vars:str, time_offset:int=0)->pd.DataFrame:
    """formats dataframe to be used with teneto package

    Args
        edge_df (pd.DataFrame): edgelist data frame to be converted
        tn_vars (list): temporal netork variables to be remapped
        time_offset (int): value to offset times tomake sure time buckets start at 0 default: 0
    
    """

    edge_df = edge_df.rename(columns={tn_vars[0]:"i", tn_vars[1]:"j", tn_vars[2]:"t"})
    unique_nodes = set(edge_df["i"].tolist() + edge_df["j"].tolist())
    tranform_to_num_nodes = {node:num_rep for node, num_rep in zip(list(unique_nodes), [i for i in range(len(list(unique_nodes)))])}
    edge_df = edge_df.replace(tranform_to_num_nodes)
    edge_df.loc[:, "t"] = edge_df.loc[:,"t"].apply(lambda x: x-time_offset)
    return edge_df


def temp_degree_cent(edge_df:pd.DataFrame, true_time:str)->None:
    """calculate degree centrality overtime

    Args:
        edge_df (pd.DataFrame): data frame that contains an edge list columns source, traget and a time column
        true_time (str): edge attribute that holds the true timestamp for graphing

    Returns:
    None
    """ 

    import teneto
    tn = teneto.TemporalNetwork()
    edge_df = edge_df.copy()
    tn.network_from_df(edge_df)
    temporal_degree_cent = teneto.networkmeasures.temporal_degree_centrality(tn, calc="pertime")
    temporal_degree_cent[temporal_degree_cent==0.0] = np.nan
    avg_degree_over_time = np.nanmean(np.array(temporal_degree_cent), axis=0)
    sns.despine()
    plt.scatter(x=list(edge_df[true_time].unique()), y=avg_degree_over_time)
    plt.title("Average Degree Centrality Over Time")
    plt.xlabel("Months Betweeen Published Games")
    plt.ylabel("Average Degree Centrality")
    plt.savefig('avg_temporal_deg_cent.png')


def temporal_cluster_analysis(edge_df:pd.DataFrame):
    """applies tools from Louvain clustering to create a temporal cluster analysis
    
    Args:
        edge_df: dataframe that contains information for converting to temporal network
    Returns:
    None
    """
    import teneto
    if os.path.exists("communities.csv"):

        communities = pd.read_csv("communities.csv")
    else:
        tn = teneto.TemporalNetwork()
        edge_df = edge_df.copy()
        tn.network_from_df(edge_df)
        communities= teneto.communitydetection.temporal_louvain(tn, temporal_consensus=True, n_iter=50,
                                                                randomseed=32)
        pd.DataFrame(communities).to_csv("communities.csv")
    print(communities)

if os.path.exists("largest_comp.gml"):
    largest_component = nx.read_gml("largest_comp.gml")

else: 
    G = nx.read_gml("network.gml")
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    largest_component  = G.subgraph(components[0])
    nx.write_gml(largest_component, path="largest_comp.gml")

def volitalty(edge_df:pd.DataFrame, true_time:str):
    """calculates the volitalty over time of the network
    
    Args: 
        edge_df (pd.DataFrame): dataframe that is formatted for temporal network

    Returns: 
        None
    """
    import teneto
    tn = teneto.TemporalNetwork()
    edge_df = edge_df.copy()
    tn.network_from_df(edge_df)
    vol = teneto.networkmeasures.volatility(tn, calc="pertime", distance_func="hamming")
    sns.despine()
    plt.scatter(x=list(edge_df[true_time].unique())[1:], y=vol)
    plt.title("Volatility Over Time")
    plt.xlabel("Months Betweeen Published Games")
    plt.yticks(rotation=.45)
    plt.savefig('vol_time.png')

ts_edge_lists = build_edge_list_time_series(graph=largest_component, date_at="release_date")
tn_edge_lists = format_df_fortn(edge_df=ts_edge_lists, tn_vars=["source", "target", "Time"], time_offset=4)
# visualize_temp_net(edge_df=ts_edge_lists, tn_vars=["source", "target", "Time"])
# temp_degree_cent(edge_df=tn_edge_lists, true_time="release_date")
volitalty(edge_df=tn_edge_lists, true_time="release_date")
# temporal_cluster_analysis(edge_df=tn_edge_lists)
