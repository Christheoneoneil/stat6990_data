import pandas as pd 
import consts as c
from itertools import combinations
import networkx as nx

import numpy as np
import datetime

NXGraph = nx.classes.graph.Graph
def read_json(filepath)->pd.DataFrame:
   """
   read in raw json and convert to pandas data frame 
   and get transpose to follow tidy data practices 

   Params: 
   filepath: path to file in local directory 

   Returns:
   read in json pandas dataframe 
   """
   return pd.read_json(filepath).T


def to_network_struct(raw_data:pd.DataFrame, node:str, edge_at:str, dates:str)->NXGraph:
    """
    converts pandas data frame to a network structure 

    Params:
    raw_data: raw inprocessed data from pandas dataframe 
    node: column containing node information 
    edge_at: column containg edge attribute that will be used to 'link' nodes
    dates: date that detemine order of how nodes populate graph

    Returns: 
    G: graph from provided raw pandas dataframe
    """

    read_data = raw_data.copy()
    raw_data = read_data[[node, edge_at]].explode(column=edge_at).drop_duplicates()
    # Get all combos between source and target nodes
    dt_data = read_data[[node, dates]]
    

    unconnected_data = raw_data[(raw_data[edge_at]=="") & 
                                (raw_data[edge_at]=="-") & 
                                (raw_data[edge_at]=="(none)") &
                                (raw_data[edge_at] =='0')]
    raw_data = raw_data[(raw_data[edge_at]!="") & 
                        (raw_data[edge_at]!="-") & 
                        (raw_data[edge_at]!="(none)") &
                        (raw_data[edge_at]!='0')]
    
    combos = lambda combs: pd.DataFrame([sorted(e) for e in list(combinations(combs[node].values, 2))], columns=['source', 'target'])
    edge_list = raw_data.groupby(edge_at).apply(combos).reset_index().drop(columns=["level_1"])
    unconnected_data = unconnected_data.rename(columns={node: "source"})
    unconnected_data.loc[:, "target"] = [np.nan for _ in range(len(unconnected_data))]
    edge_list = pd.concat([edge_list, unconnected_data], axis=0)

    G = nx.from_pandas_edgelist(df=edge_list, source="source", target="target", edge_attr=edge_at)
    unique_source = dt_data.drop_duplicates(subset=node).set_index(node)[dates].to_dict()
    
    nx.set_node_attributes(G, values=unique_source, name=dates)
    nx.write_gml(G, path="network.gml")

    return G


def build_network_card(G:NXGraph, update_dict:dict={}, out_name:str="network_card.json"):
    """
    builds a network card with provided network, and updates based on any 
    passed updates to the card to fill possible null values 

    Params: 
    G: graph to generate network card from 
    update_dict: a dictionary for keys and values for updating 
    the missing network card values
    out_name: name of output json file

    Returns: 
    None
    """
    import network_cards as nc
    init_card = nc.NetworkCard(G)
    print(init_card)
    init_card.update_metainfo(update_dict)
    print(init_card)
    init_card.to_json(out_name)


raw_data = read_json("reproduction_files/games.json")
graph = to_network_struct(raw_data=raw_data, node="name", edge_at="publishers", dates="release_date")
print(graph)
# publishers = nx.get_edge_attributes(graph, "publishers")
# top_3 = pd.Series(publishers.values()).value_counts().keys()[:3]

# for pub in top_3: 
#     sub_edges = [key for key, value in publishers.items() if value == pub]
#     print(sub_edges)
#     sub_graph = graph.edge_subgraph(sub_edges)
#     print(sub_graph)
#     nx.write_edgelist(sub_graph, path=pub + "_network.tsv", delimiter="\t")

# build_network_card(G=graph, update_dict={"Name" : "Video Game Publishers Network",
#                                          "Nodes are": "Games",
#                                          "Links are": "Publishers Orderd by Release Date",
#                                          "Considerations": "Not all games were able to be scrpaed from steam",
#                                          "Node metadata": "Name of video game",
#                                          "Link metadata": "Name of video game publisher",
#                                          "Date of creation": str(datetime.date.today()),
#                                          "Data generating process": "Data is gathered using SteamGamesSCraper API",
#                                          "Ethics": "n/a",
#                                          "Citation": "2022 Martin Bustos",
#                                          "Funding": "n/a",
#                                          "Access": "n/a"})
# print(graph)
