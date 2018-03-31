
# coding: utf-8

# In[17]:

import fiona
import numpy as np
import pandas as pd
import networkx as nx


# In[18]:

f = fiona.open("road_data/Senegal_Roads.shp")
roads_w_floods = pd.read_csv('road_data/RoadSum.csv', header=None, sep=',')
edge_dict = {}
flood_cols = [i for i in range(2, 11)]
dates = ['2013-06-18', '2013-07-02', '2013-07-16', '2013-07-30', 
               '2013-08-13', '2013-08-27', '2013-09-10', '2013-09-24', '2013-10-08']
for i,row in enumerate(f):
    properties = row["properties"]
    uid, road_condition = properties['UNIFORM_ID'], properties['ROAD_COND_']
    geom_type = row["geometry"]["type"]
    coordinates = row["geometry"]["coordinates"]
    if geom_type == "LineString":
        start_node = (coordinates[0][1], coordinates[0][0])
        end_node = (coordinates[-1][1], coordinates[-1][0])
        batch = roads_w_floods.loc[roads_w_floods[0] == uid]
        flood_of_batch = batch[flood_cols]
        flood_of_batch = flood_of_batch.fillna(0)
        flood_ocurrences = flood_of_batch.astype(float)
        flood_risk = flood_ocurrences.values
        temp_dict = dict(zip(dates, flood_risk[0]))
        #print(temp_dict)
        edge_dict[(start_node, end_node)] = (temp_dict, road_condition)
    #Multi-line string case
    elif geom_type == "MultiLineString":
        batch = roads_w_floods.loc[roads_w_floods[0] == uid]
        flood_of_batch = batch[flood_cols]
        flood_of_batch = flood_of_batch.fillna(0)
        flood_ocurrences = flood_of_batch.astype(float)
        flood_risk = flood_ocurrences.values
        temp_dict = dict(zip(dates, flood_risk[0]))
        for j, coordinate_list in enumerate(coordinates):
            start_node = (coordinate_list[0][1], coordinate_list[0][0])
            end_node = (coordinate_list[-1][1], coordinate_list[-1][0])
            edge_dict[(start_node, end_node)] = (temp_dict, road_condition)
f.close()
np.save('edge_flood_dictionary.npy', edge_dict)

