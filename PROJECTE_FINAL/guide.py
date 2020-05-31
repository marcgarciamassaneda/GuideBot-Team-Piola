import osmnx as ox
import networkx as nx
from staticmap import StaticMap, CircleMarker, Line
from haversine import haversine


class guide:
    '''Class with all the code related to getting the graphs corresponding to
    maps and calculating routes.'''

    def download_graph(place):
        '''Download the graph of the place given as parameter. The place can
        be given in different formats: a string, a list of places represented
        as strings or a tuple with a point(the graph generated will be 750
        meters around that point).'''
        if isinstance(place, str):
            graph = ox.graph_from_place(place, network_type='all',
                                        simplify=True)
        elif isinstance(place, list):
            graph = ox.gdf_from_places(place, network_type='all',
                                       simplify=True)
        elif isinstance(place, tuple):
            graph = ox.graph_from_point(place, distance=750,
                                        network_type='all',
                                        simplify=True)
        else:
            raise TypeError('Incorrect parameter to define a place')
        # bearings included in the graph to improve orientation
        ox.geo_utils.add_edge_bearings(graph)
        return graph

    def save_graph(graph, filename):
        '''Save the graph in your system with the filename given.'''
        nx.write_gpickle(graph, filename)

    def load_graph(filename):
        '''Load the graph with the filename given. It must have been
        saved previously in your system.'''
        graph = nx.read_gpickle(filename)
        return graph

    def print_graph(graph):
        '''Print all the nodes of the graph with their respective edges.'''
        for node1, info1 in graph.nodes.items():
            print("Node:", node1, info1, "\nEdges:")
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
            print("\n")

    def _first_checkpoint_check(graph, directions, source_location,
                                destination_location):
        '''Determine if the first checkpoint is further or the same distance
        from the destination node than the source node. In such case, the first
         checkpoint is useless and should be removed.'''
        first_checkpoint = (graph.nodes[directions[0]]['y'],
                            graph.nodes[directions[0]]['x'])
        return (haversine(source_location, destination_location) <=
                haversine(first_checkpoint, destination_location))

    def _route_particular_case(graph, directions, node, source_location,
                               destination_location):
        '''Return the fragment of route of the cases that work differently:
        the first part, the penultimate part and the last part. The reason is
        that they contain nodes that are not in the graph.'''
        node_info = dict.fromkeys(['angle', 'current_name', 'dst', 'length',
                                  'mid', 'next_name', 'src'])
        node_info['angle'] = None
        if node == 0:  # first part
            node_info['src'] = (source_location[0], source_location[1])
            node_info['mid'] = (graph.nodes[directions[node]]['y'],
                                graph.nodes[directions[node]]['x'])
            node_info['dst'] = (graph.nodes[directions[node + 1]]['y'],
                                graph.nodes[directions[node + 1]]['x'])
            node_info['current_name'] = None
            node_info['length'] = None
            next_edge = graph.adj[directions[0]][directions[1]][0]
            if 'name' in next_edge:  # next_edge may not have name
                node_info['next_name'] = next_edge['name']
            else:
                node_info['next_name'] = None
            # name may be a list of names, so only the first one is kept
            if isinstance(node_info['next_name'], list):
                node_info['next_name'] = node_info['next_name'][0]
        if node == len(directions) - 2:  # penultimate part
            node_info['src'] = (graph.nodes[directions[node]]['y'],
                                graph.nodes[directions[node]]['x'])
            node_info['mid'] = (graph.nodes[directions[node + 1]]['y'],
                                graph.nodes[directions[node + 1]]['x'])
            node_info['dst'] = (destination_location[0],
                                destination_location[1])
            edge = graph.adj[directions[node]][directions[node+1]][0]
            if 'name' in edge:  # edge may not have name
                node_info['current_name'] = edge['name']
            else:
                node_info['current_name'] = None
            node_info['length'] = edge['length']
            node_info['next_name'] = None
            # name may be a list of names, so only the first one is kept
            if isinstance(node_info['current_name'], list):
                node_info['current_name'] = node_info['current_name'][0]
        if node == len(directions) - 1:  # last part
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
        '''Transform the list of nodes of directions to a route format with the
        following fields for each part of the route:
        - angle
        - current name
        - destination node
        - length
        - mid node
        - next name
        - source node
        '''
        route = []
        if guide._first_checkpoint_check(graph, directions, source_location,
           destination_location):
            directions.pop(0)  # first checkpoint removed
        for i in range(len(directions)-2):
            node_info = dict.fromkeys(['angle', 'current_name', 'dst',
                                       'length', 'mid', 'next_name', 'src'])
            node_info['src'] = (graph.nodes[directions[i]]['y'],
                                graph.nodes[directions[i]]['x'])
            node_info['mid'] = (graph.nodes[directions[i+1]]['y'],
                                graph.nodes[directions[i+1]]['x'])
            node_info['dst'] = (graph.nodes[directions[i+2]]['y'],
                                graph.nodes[directions[i+2]]['x'])
            # edge -> edge that connects source and mid
            edge = graph.adj[directions[i]][directions[i+1]][0]
            if 'name' in edge:  # edge may not have name
                node_info['current_name'] = edge['name']
            else:
                node_info['current_name'] = None
            node_info['length'] = edge['length']
            # next_edge -> edge that connects mid and destination
            next_edge = graph.adj[directions[i+1]][directions[i+2]][0]
            if 'name' in next_edge:  # next_edge may not have name
                node_info['next_name'] = next_edge['name']
            else:
                node_info['next_name'] = None
            # angle -> the angle formed by the lines
            # source-mid and mid-destination
            node_info['angle'] = next_edge['bearing'] - edge['bearing']
            # name may be a list of names, so only the first one is kept
            if isinstance(node_info['current_name'], list):
                node_info['current_name'] = node_info['current_name'][0]
            if isinstance(node_info['next_name'], list):
                node_info['next_name'] = node_info['next_name'][0]
            route.append(node_info)
        # the first node, the penultimate and the last one are treated
        # differently
        route.insert(0, guide._route_particular_case(graph, directions,
                     0, source_location, destination_location))
        route.append(guide._route_particular_case(graph, directions,
                     len(directions)-2, source_location, destination_location))
        route.append(guide._route_particular_case(graph, directions,
                     len(directions)-1, source_location, destination_location))
        return route

    def get_directions(graph, source_location, destination_location):
        '''Get the best route from the source location to the destination
        location.'''
        new_src = ox.geo_utils.get_nearest_node(graph, source_location)
        new_dst = ox.geo_utils.get_nearest_node(graph, destination_location)
        # directions is a list of nodes of the shortest path between
        # the nearest node from the source node and the nearest node
        # from the destination node
        directions = nx.shortest_path(graph, new_src,
                                      new_dst)
        # route is the transformation of directions to a structure with
        # more information to enrich the guidance system quality
        route = guide._get_route(graph, directions, source_location,
                                 destination_location)
        return route

    def plot_directions(graph, source_location, destination_location,
                        directions, filename, width=400, height=400):
        '''Draw the route from a source location to a destination location
        in a map.'''
        mapa = StaticMap(width, height)
        # the source location and the destination location are marked in the
        # map as big blue circles
        mapa.add_marker(CircleMarker((source_location[1], source_location[0]),
                                     'blue', 20))
        mapa.add_marker(CircleMarker((destination_location[1],
                                     destination_location[0]), 'blue', 20))
        # the rest of the nodes are marked as red circles and the edges between
        # them are also marked in the same colour
        for i in range(len(directions)-2):
            coordinates_first = (directions[i]['mid'][1],
                                 directions[i]['mid'][0])
            coordinates_second = (directions[i]['dst'][1],
                                  directions[i]['dst'][0])
            mapa.add_marker(CircleMarker(coordinates_first, 'red', 10))
            coordinates = (coordinates_first, coordinates_second)
            mapa.add_line(Line(coordinates, 'red', 4))
        # the last checkpoint is marked and the lines between the big blue
        # circles and the red circle next to them is marked in blue
        penultimate_coordinates = (directions[-1]['src'][1],
                                   directions[-1]['src'][0])
        mapa.add_marker(CircleMarker(penultimate_coordinates, 'red', 10))
        last_line_coordinates = (penultimate_coordinates,
                                 (destination_location[1],
                                  destination_location[0]))
        mapa.add_line(Line(last_line_coordinates, 'blue', 4))
        second_coordinates = (directions[0]['mid'][1], directions[0]['mid'][0])
        first_line_coordinates = (second_coordinates,
                                  (source_location[1], source_location[0]))
        mapa.add_line(Line(first_line_coordinates, 'blue', 4))
        picture = mapa.render()
        picture.save(filename)
        # the map is returned for further use
        return mapa
