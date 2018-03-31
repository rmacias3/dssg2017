import networkx as nx
import numpy as np
import pandas as pd
import random as r
import operator

def order_check(e):
    if e in graph.edges():
        return e
    else:
        return (e[1], e[0])
    
def calculate_cost(path):
    pop = 0
    dist = 0
    num_edges = len(path) - 1
    for t in range(num_edges):
        v1, v2 = path[t], path[t + 1]
        e = graph.edge[v1][v2]
        pop += sum(e[t] for t in e if t != 'weight')
        dist += e['weight']
    pop = pop/num_edges
    return pop, dist

#So far, this function calculates the weighted population of each edge
# and if rel=True, then it calculates the penalty for flooding an edge across a batch of shortest paths. 
#this penalty is just the difference in distance traveled weighted by population
#calculated as follows: population traveling through path * (dist_new_path - dist_orig_path)
#this can also be done across a particular date
def calculate_importances(edges, orig_paths, rel_importance_dict, new_path_dict):
    paths_no_date = [k[0] for k in orig_paths]
    for path in paths_no_date:
        for e in edges:
            if e[0] in path and e[1] in path:
                if abs(path.index(e[0]) - path.index(e[1])) == 1:
                    e_dict = graph.edge[e[0]][e[1]]
                    pop, dist = calculate_cost(path)
                    old_cost = pop * dist
                    graph.remove_edge(e[0], e[1])
                    if nx.has_path(graph, path[0], path[-1]):
                        new_path = nx.dijkstra_path(graph, path[0], path[-1])
                        _, new_dist = calculate_cost(new_path)
                        rel_cost = pop * new_dist - old_cost
                        rel_importance_dict[e] += np.log(rel_cost)
                        new_path_dict[e].append(new_path)
                    else:
                        new_path_dict[e].append(-1)
                        rel_importance_dict[e] += np.log(2*old_cost)
                    graph.add_edge(e[0], e[1], e_dict)
    return rel_importance_dict, new_path_dict                  

def construct_imp_dicts(edges):
    reg_importance_dict = {}
    rel_importance_dict = {}
    new_path_dict = {}
    e_dict = {}
    for edge in edges:
        e_dict = graph.edge[edge[0]][edge[1]]
        importance_weighing = (1.0/e_dict['weight']) * sum([e_dict[k] for k in e_dict if k != 'weight'])
        reg_importance_dict[edge] = importance_weighing
        rel_importance_dict[edge] = 0
        new_path_dict[edge] = []
    return reg_importance_dict, rel_importance_dict, new_path_dict

def give_n_riskiest_edges(flood_risk_dict, n=20):
    sorted_flood_edges = sorted(flood_risk_dict.items(), key=lambda (k, v): sum(v[0][k] for k in v[0]), reverse=True)
    top_20_at_risk = [(str(k[0][0]), str(k[0][1])) for k in sorted_flood_edges[:n]]
    return [order_check(e) for e in top_20_at_risk] 
if __name__ == "__main__":
    graph = nx.read_graphml('all_users_senegal_gml.graphml')
    flood_risk_dict = np.load('edge_flood_dictionary.npy').item()

    #We sorted here by the sum of the historical flood data 
    #v[0] is the dictionary that holds the flood risk value for each date. v[1] (unused) is the road condition
    #so we sum over the flood risk for each date inside of the lambda expression
    #We wanted the riskiest edges at the top, so we did "Reverse=True"
    
    top_20_at_risk = give_n_riskiest_edges(flood_risk_dict)
    reg_imp_dict, rel_imp_dict, path_dict = construct_imp_dicts(top_20_at_risk)

    paths_dir = 'file_paths/paths_for_file_'
    for k in range(1, 26):
        cur_dir = paths_dir + str(k) + '/'
        for j in range(1, 33):
            paths = np.load(cur_dir + str(j) + '.npy')
            rel_imps, new_paths = calculate_importances(top_20_at_risk, paths, rel_imp_dict, path_dict)
        np.save('rel_imp_dictionary' + str(k) + '.npy', rel_imps)
        np.save('new_paths_dictionary' + str(k) + '.npy', new_paths)
        reg_imp_dict, rel_imp_dict, path_dict = construct_imp_dicts(top_20_at_risk)