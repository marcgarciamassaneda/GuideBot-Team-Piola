import osmnx as ox
import networkx as nx
from staticmap import StaticMap, CircleMarker, Line


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

    def _get_angle(angle):
        if angle is None:
            return "Go straight through"
        if angle < 0:
            angle += 360
        if angle < 22.5 or angle > 337.5:
            return "Go straight through"
        elif angle < 67.5:
            return "Turn half right and go straight through"
        elif angle < 112.5:
            return "Turn right and go straight through"
        elif angle < 180:
            return "Turn strong right and go straight through"
        elif angle < 247.5:
            return "Turn strong left and go straight through"
        elif angle < 292.5:
            return "Turn left and go straight through"
        else:
            return "Turn half left and go straight through"

    def _route_particular_case(graph, directions, node, source_location,
                               destination_location):
        node_info = dict.fromkeys(['angle', 'current_name', 'dst', 'length',
                                  'mid', 'next_name', 'src'])
        node_info['angle'] = None
        if node == 0:
            node_info['src'] = (source_location[0], source_location[1])
            node_info['mid'] = (graph.nodes[directions[node]]['y'],
                                graph.nodes[directions[node]]['x'])
            node_info['dst'] = (graph.nodes[directions[node + 1]]['y'],
                                graph.nodes[directions[node + 1]]['x'])
            node_info['current_name'] = None
            node_info['length'] = None
            next_edge = graph.adj[directions[0]][directions[1]][0]
            node_info['next_name'] = next_edge['name']
        if node == len(directions) - 2:
            node_info['src'] = (graph.nodes[directions[node]]['y'],
                                graph.nodes[directions[node]]['x'])
            node_info['mid'] = (graph.nodes[directions[node + 1]]['y'],
                                graph.nodes[directions[node + 1]]['x'])
            node_info['dst'] = (destination_location[0],
                                destination_location[1])
            edge = graph.adj[directions[node]][directions[node+1]][0]
            node_info['current_name'] = edge['name']
            node_info['length'] = edge['length']
            node_info['next_name'] = None
        if node == len(directions) - 1:
            node_info['src'] = (graph.nodes[directions[node]]['y'],
                                graph.nodes[directions[node]]['x'])
            node_info['mid'] = (destination_location[0],
                                destination_location[1])
            node_info['dst'] = None
            node_info['current_name'] = None
            node_info['length'] = None
            node_info['next_name'] = None
        return node_info

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
            node_info['angle'] = next_edge['bearing'] - edge['bearing']
            route.append(node_info)
        route.insert(0, guide._route_particular_case(graph, directions, 0,
                     source_location, destination_location))
        route.append(guide._route_particular_case(graph, directions, len(directions) - 2, source_location, destination_location))
        route.append(guide._route_particular_case(graph, directions, len(directions) - 1, source_location, destination_location))
        return route

    def get_directions(graph, source_location, destination_location):
        new_src = ox.geo_utils.get_nearest_node(graph, source_location)
        new_dst = ox.geo_utils.get_nearest_node(graph, destination_location)
        directions = nx.shortest_path(graph, new_src,
                                      new_dst)
        route = guide._get_route(graph, directions, source_location,
                                 destination_location)
        return route

    def plot_directions(graph, source_location, destination_location,
                        directions, filename, width=400, height=400):
        mapa = StaticMap(width, height)
        mapa.add_marker(CircleMarker((source_location[1], source_location[0]), 'blue', 20))
        mapa.add_marker(CircleMarker((destination_location[1], destination_location[0]), 'blue', 20))
        for i in range(len(directions) - 2):
            coordinates_first = (directions[i]['mid'][1], directions[i]['mid'][0])
            coordinates_second = (directions[i]['dst'][1], directions[i]['dst'][0])
            mapa.add_marker(CircleMarker(coordinates_first, 'red', 10))
            coordinates = (coordinates_first, coordinates_second)
            mapa.add_line(Line(coordinates, 'red', 4))
        penultimate_coordinates = (directions[-1]['src'][1], directions[-1]['src'][0])
        mapa.add_marker(CircleMarker(penultimate_coordinates, 'red', 10))
        last_line_coordinates = (penultimate_coordinates, (destination_location[1], destination_location[0]))
        mapa.add_line(Line(last_line_coordinates, 'blue', 4))
        second_coordinates = (directions[0]['mid'][1], directions[0]['mid'][0])
        first_line_coordinates = (second_coordinates, (source_location[1], source_location[0]))
        mapa.add_line(Line(first_line_coordinates, 'blue', 4))
        imatge = mapa.render()
        imatge.save(filename)
        return mapa

    def _mark_edge(mapa, directions, node, filename):
        coordinates_first = (directions[node]['src'][1], directions[node]['src'][0])
        coordinates_second = (directions[node]['mid'][1], directions[node]['mid'][0])
        coordinates = (coordinates_first, coordinates_second)
        mapa.add_line(Line(coordinates, 'green', 4))
        if (node != len(directions)-1):
            mapa.add_marker(CircleMarker(coordinates_second, 'green', 10))
        imatge = mapa.render()
        imatge.save(filename)
        return mapa

    def _go_particular_case(route, node, destination_name):
        if node == len(route)-2:
            mid_lat = route[node]['dst'][0]
            mid_lon = route[node]['dst'][1]
            message = "Go to your destination: %s, %s (%s)." % (mid_lat, mid_lon, destination_name)
            return message
        if node == len(route)-1:
            message = "Congratulations! You have reached your destination: %s.\n🏁🏁🏁" % (destination_name)
            return message

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
