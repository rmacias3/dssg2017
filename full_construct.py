
import pandas as pd
import numpy as np
import networkx as nx
import itertools as it
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import MultiPoint, Point
from haversine import haversine
import gzip
import csv
import os

#The purpose of this method is to assign occupation to road intersections with respect to only one user's actions. 
def process_batch(batch):
    towers = np.squeeze(batch.as_matrix(columns=[2]))
    if np.ndim(towers) != 0:
        tower_ocurrences = [(k, sum(1 for _ in i)) for k, i in it.groupby(towers)]
        start = 0
        for k in tower_ocurrences:
            end = k[1] + start
            sequence = batch.iloc[start:end]
            tran_index = end
            if tran_index < (batch.shape)[0]:
                assign_population(sequence, batch.iloc[tran_index])
            else:
                assign_population(sequence, -1)
            start = end

#Assign occupancy to a road
def assign(road, time):
    if time not in road:
        road[time] = 1 
    else:
        road[time] += 1


#New population assignment model
def assign_population(sequence, transition):
    rows = (sequence.shape)[0]
    tower = sequence.iloc[0][2]
    roads = tower_id_inv[tower]
    num_roads = len(roads)
    if num_roads != 0:
        if not isinstance(transition, pd.core.series.Series):
            for k in range(rows):
                road = np.random.choice(roads)
                timestamp = sequence.iloc[k][1]
                day = timestamp[:10]
                assign(graph.node[road], day)
        else:
            road = None
            for k in range(rows):
                road = np.random.choice(roads)
                timestamp = sequence.iloc[k][1]
                day = timestamp[:10]
                assign(graph.node[road], day)
            dest_time = transition.iloc[1]
            dest = transition.iloc[2]
            destination_roads = tower_id_inv[dest]
            if len(destination_roads) != 0:
                random_dest = np.random.choice(destination_roads)
                if nx.has_path(graph, road, random_dest):
                    path = nx.dijkstra_path(graph, road, random_dest) 
                    shortest_paths.append((path, dest_time[:10]))


#Assigning flow to edges
def assign_flow(shortest_paths, g):
    flow_assigned = []
    for user_path in shortest_paths:
        path = user_path[0]
        time = user_path[1]
        path_length = len(path)
        for i in range(path_length - 1):
            A, B = path[i], path[i + 1]
            edge = g.edge[A][B]
            if time not in edge:
                edge[time] = 1
            else:
                edge[time] += 1

def create_tower_regions(nodes):
    nodesters = nodes
    locs = pd.read_csv('ContextData/SITE_ARR_LONLAT.CSV')
    tower_id_inv = {}
    coordinates = locs.as_matrix(columns=['lon', 'lat'])
    diagram = Voronoi(coordinates)

    for i in range(len(diagram.point_region)):
        tower_id_inv[i + 1] = []
        #Find region coordinates
        region_index = diagram.point_region[i]
        region_outline = diagram.regions[region_index]
        region_coords = diagram.vertices[region_outline]
        coords = [tuple(x) for x in region_coords]
        #Check which road vertices fall in region
        poly = MultiPoint(coords).convex_hull
        temp = []
        for k in nodesters:
            cur = k.split(', ')
            lat, lon = float(cur[0][1:]), float(cur[1][:-1])
            point = Point((lon, lat))
            if poly.contains(point):
                tower_id_inv[i + 1].append(k)
            else:
                temp.append(k)
        nodesters = temp
    return tower_id_inv
    
if __name__ == "__main__":
	shortest_paths = []
	graph = nx.read_graphml('senegal_roads.graphml')
	tower_id_inv = create_tower_regions(graph.nodes())
	path = 'SET2/SET2_P'
	for i in range(1, 26):
	    file_path = 'paths_for_file_' + str(i) + '/'
	    if not os.path.exists(file_path):
		os.makedirs(file_path)
	    current = '-1'
	    if i < 10:
	        current = path + '0' + str(i) + '.CSV.gz'
	    else:
	        current = path + str(i) + '.CSV.gz'
	    users = pd.read_csv(current, header=None, compression='gzip', sep=',')
	    num_users = users[0].max()
	    print num_users
	    for k in range(1, num_users + 1):
	        batch = users.loc[users[0] == k]
	        process_batch(batch)
	        if k % 10000 == 0:
	            assign_flow(shortest_paths)
	            shortest_paths = np.array(shortest_paths)
	            np.save(file_path + str((k / 10000)), shortest_paths)
	            shortest_paths = []
	    if shortest_paths:
	        assign_flow(shortest_paths, graph)
	        np.save(file_path + 'last_paths', shortest_paths)
	        shortest_paths = []

	nx.write_gexf(graph, 'All_users_senegal.gexf')
	nx.write_graphml(graph, 'all_users_senegal_gml.graphml')

