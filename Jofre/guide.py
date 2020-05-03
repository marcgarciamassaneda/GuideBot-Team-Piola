import osmnx as ox
import networkx as nx
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
            raise TypeError("Incorrect parameter to define a place")
        ox.geo_utils.add_edge_bearings(graph)
        return graph

    def save_graph(graph, filename):
        nx.write_gpickle(graph, filename)

    def load_graph(filename):
        graph = nx.read_gpickle(filename)
        return graph

    def print_graph(graph):
        ox.plot_graph(graph)

    def _euclidean_dist(node1, node2):
        point1 = math.pow((node2[1] - node1[1]), 2)
        point2 = math.pow((node2[0] - node1[0]), 2)
        return math.sqrt(point1 + point2)

    def _get_angle(src, mid):
        src_y = src[0]
        src_x = src[1]
        mid_y = src[0]
        mid_x = src[1]
        return math.atan2(mid_y - src_y, mid_x - src_x)

    def _update_node_info(graph, route, i, source_location,
                          destination_location):
        node_info = dict.fromkeys(['angle', 'current_name', 'dst', 'length',
                                  'mid', 'next_name', 'src'])
        node_info['src'] = (graph.nodes[route[i]]['y'],
                            graph.nodes[route[i]]['x'])
        node_info['mid'] = (graph.nodes[route[i+1]]['y'],
                            graph.nodes[route[i+1]]['x'])
        if i < len(route)-2:
            node_info['dst'] = (graph.nodes[route[i+2]]['y'],
                                graph.nodes[route[i+2]]['x'])
            next_edge = graph.adj[route[i+1]][route[i+2]][0]
            node_info['next_name'] = next_edge['name']
        else:
            node_info['dst'] = (destination_location[0],
                                destination_location[1])
            node_info['next_name'] = None
        edge = graph.adj[route[i]][route[i+1]][0]
        node_info['current_name'] = edge['name']
        node_info['length'] = edge['length']
        node_info['angle'] = guide._get_angle(node_info['src'],
                                              node_info['mid'])
        return node_info

    def _update_first_node_info(graph, route, source_location):
        node_info = dict.fromkeys(['angle', 'current_name', 'dst', 'length',
                                  'mid', 'next_name', 'src'])
        node_info['src'] = (source_location[0], source_location[1])
        node_info['mid'] = (graph.nodes[route[0]]['y'],
                            graph.nodes[route[0]]['x'])
        node_info['dst'] = (graph.nodes[route[1]]['y'],
                            graph.nodes[route[1]]['x'])
        node_info['current_name'] = None
        node_info['length'] = None
        next_edge = graph.adj[route[0]][route[1]][0]
        node_info['next_name'] = next_edge['name']
        node_info['angle'] = None

        return node_info

    def _update_dest_node_info(graph, route, destination_location):
        node_info = dict.fromkeys(['angle', 'current_name', 'dst', 'length',
                                  'mid', 'next_name', 'src'])
        node_info['src'] = (graph.nodes[route[-1]]['y'],
                            graph.nodes[route[-1]]['x'])
        node_info['mid'] = (destination_location[0], destination_location[1])
        node_info['dst'] = None
        node_info['current_name'] = None
        node_info['length'] = None
        node_info['next_name'] = None
        node_info['angle'] = None

        return node_info

    def _get_route_info(graph, route, source_location, destination_location):
        route_info = []
        for i in range(len(route) - 2):
            node_info = guide._update_node_info(graph, route, i,
                                                source_location,
                                                destination_location)
            route_info.append(node_info)

        node_info = guide._update_node_info(graph, route, len(route)-2,
                                            source_location,
                                            destination_location)
        route_info.append(node_info)
        source_node_info = guide._update_first_node_info(graph, route,
                                                         source_location)
        route_info.insert(0, source_node_info)

        dest_node_info = guide._update_dest_node_info(graph,
                                                      route,
                                                      destination_location)
        route_info.append(dest_node_info)
        return route_info

    def get_directions(graph, source_location, destination_location):
        _nearest_node_s = ox.geo_utils.get_nearest_node(graph, source_location)
        _nearest_node_d = ox.geo_utils.get_nearest_node(graph,
                                                        destination_location)
        route = nx.shortest_path(graph, _nearest_node_s, _nearest_node_d)
        route_info = guide._get_route_info(graph, route, source_location,
                                           destination_location)
        return (route_info, route)

    def plot_directions(graph, source_location, destination_location,
                        directions, filename, width=400, height=400):
        ox.plot_graph_route(graph, directions,
                            origin_point=source_location,
                            destination_point=destination_location)

    def _recorregut(graph):  # for each node and its information...
        for node1, info1 in graph.nodes.items():
            print(node1, info1)
            # for each adjacent node and its information...
            for node2, info2 in graph.adj[node1].items():
                print('    ', node2)
                # osmnx graphs are multigraphs, but we will just consider
                # their first edge
                edge = info2[0]
                # we remove geometry information from edges because we don't
                # need it and take a lot of space
                if 'geometry' in edge:
                    del(edge['geometry'])
                print('        ', edge)
