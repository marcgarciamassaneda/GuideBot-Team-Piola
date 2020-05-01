import osmnx as ox
import networkx as nx


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

    def get_directions(graph, source_location, destination_location):

