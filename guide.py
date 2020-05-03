import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import math


class guide:

    def download_graph(place):
        if isinstance(place, str):
            graph = ox.graph_from_place(place, network_type='drive',
                                        simplify=True)
        elif isinstance(place, list):
            graph = ox.gdf_from_places(place, network_type='drive',
                                       simplify=True)
        elif isinstance(place, tuple):
            graph = ox.graph_from_point(place, distance=750,
                                        network_type='drive',
                                        simplify=True)
        else:
            raise TypeError('Incorrect parameter to define a place')
        ox.geo_utils.add_edge_bearings(graph)
        return graph

    def save_graph(graph, filename):
        nx.write_gpickle(graph, filename)

    def load_graph(filename):
        graph = nx.read_gpickle(filename)
        return graph

    def print_graph(graph):
        ox.plot_graph(graph)

    def _distancia(x, y, x2, y2):
        return math.sqrt((x-x2)**2 + (y-y2)**2)

    def _modul(vector):
        vector_y = vector[0]
        vector_x = vector[1]
        return math.sqrt(vector_y**2 + vector_x**2)

    def _get_angle(src, mid, dst):
        src_y = src[0]
        src_x = src[1]
        mid_y = mid[0]
        mid_x = mid[1]
        dst_y = dst[0]
        dst_x = dst[1]
        v = (src_y-mid_y, src_x-mid_x)
        u = (dst_y-mid_y, dst_x-mid_x)
        return math.degrees(math.acos(abs(u[0]*v[0] + u[1]*v[1]) /
                            (guide._modul(u) * guide._modul(v))))

    def _get_route(graph, directions, source_location, destination_location):
        route = []
        for i in range(len(directions) - 2):
            node_info = dict.fromkeys(['angle', 'current_name', 'dst',
                                       'length', 'mid', 'next_name', 'src'])
            node_info['src'] = (graph.nodes[directions[i]]['y'],
                                graph.nodes[directions[i]]['x'])
            node_info['mid'] = (graph.nodes[directions[i+1]]['y'],
                                graph.nodes[directions[i+1]]['x'])
            node_info['dst'] = (graph.nodes[directions[i+2]]['y'],
                                graph.nodes[directions[i+2]]['x'])
            edge = graph.adj[directions[i]][directions[i+1]][0]
            node_info['current_name'] = edge['name']
            node_info['length'] = edge['length']
            next_edge = graph.adj[directions[i+1]][directions[i+2]][0]
            node_info['next_name'] = next_edge['name']
            node_info['angle'] = guide._get_angle(node_info['src'],
                                                  node_info['mid'],
                                                  node_info['dst'])
            route.append(node_info)
        return route

    def get_directions(graph, source_location, destination_location):
        src_y = source_location[0]
        src_x = source_location[1]
        dst_y = destination_location[0]
        dst_x = destination_location[1]
        src_min_dist = math.inf
        dst_min_dist = math.inf
        for node, info in graph.nodes.items():
            y = info['y']
            x = info['x']
            dist = guide._distancia(x, y, src_x, src_y)
            if dist < src_min_dist:
                new_src = node
                src_min_dist = dist
            dist2 = guide._distancia(x, y, dst_x, dst_y)
            if dist2 < dst_min_dist:
                new_dst = node
                dst_min_dist = dist2
        directions = nx.shortest_path(graph, new_src,
                                      new_dst)
        route = guide._get_route(graph, directions, source_location,
                                 destination_location)
        return route

    def plot_directions(graph, source_location, destination_location,
                        directions, filename, width=400, height=400):
        ox.plot_graph_route(graph, directions)

    def yolo(graph):
        # for each node and its information...
        for node1, info1 in graph.nodes.items():
            print(node1, info1)
            # for each adjacent node and its information...
            for node2, info2 in graph.adj[node1].items():
                print('    ', node2)
                # osmnx graphs are multigraphs, but we will just consider their first edge
                edge = info2[0]
                # we remove geometry information from edges because we don't need it and take a lot of space
                if 'geometry' in edge:
                    del(edge['geometry'])
                print('        ', edge)
