
# coding: utf-8

# In[1]:

import networkx as nx
import numpy as np
import pandas as pd
import random as r
import operator
import knapsack

def order_check(e):
    e_s = (str(e[0]), str(e[1]))
    if e_s in graph.edges():
        flood_risk_dict[e_s] = flood_risk_dict[e]
        return e_s
    else:
        e_s = (e_s[1], e_s[0])
        flood_risk_dict[e_s] = flood_risk_dict[e]
        return e_s

def compute_properties():
    num_nodes = nx.number_of_nodes(graph)
    betweenness_centrality = nx.betweenness_centrality(graph)
    avg_bet = sum([k[1] for k in betweenness_centrality.items()])/float(num_nodes)
    closeness_centrality = nx.closeness_centrality(graph)
    avg_clo = sum([k[1] for k in closeness_centrality.items()])/float(num_nodes)
    communicability_centrality = nx.communicability_centrality(graph)
    global_efficiency = (1.0/(num_nodes - 1))*sum([1.0/graph.edge[e[0]][e[1]]['weight'] for e in graph.edges()])    

# In[5]:
if __name__ == "__main__":   
    graph = nx.read_graphml('all_users_senegal_gml.graphml')
    flood_risk_dict = np.load('edge_flood_dictionary.npy').item()
    path = 'road_importances/rel_imp_dictionary'
    avg_rel_imp= np.load(path + '1'+ '.npy').item()
    for i in range(2, 25):
        temp = np.load(path + str(i) + '.npy').item()
        for k in temp:
            avg_rel_imp[k] += temp[k] 
    for k in avg_rel_imp:
        avg_rel_imp[k] /= 24

    sorted_flood_edges = sorted(flood_risk_dict.items(), key=lambda (k, v): sum(v[0][k] for k in v[0]), reverse=True)
    top_20_at_risk = [(k[0][0], k[0][1]) for k in sorted_flood_edges[:20]]
    top_20_at_risk = [order_check(e) for e in top_20_at_risk]
    risk_dict = {}
    for k in top_20_at_risk:
        risk_dict[k] =  int(sum([flood_risk_dict[k][0][t] for t in flood_risk_dict[k][0]]))

    params_for_knapsack = [(graph.edge[k[0]][k[1]]['weight'], avg_rel_imp[k], risk_dict[k], k) for k in risk_dict]

    size, value = [k[0] for k in knapsack], [k[1]* k[2] for k in information]
    #let this be the number of kms available to repair
    capacity = 50
    results = knapsack.knapsack(size, value).solve(capacity)


