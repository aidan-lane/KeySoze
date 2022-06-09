import cmd
from collections import defaultdict
from queue import Queue

import networkx as nx
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import matplotlib.pyplot as plt

scope = "user-library-read"

mappings = [[7, 21], [8, 22], [9, 23], [10, 12], [11, 13], [0, 14], [1, 15], [2, 16], [3, 17], [4, 18], [5, 19], [6, 20],
            [19, 3], [20, 4], [21, 5], [22, 6], [23, 7], [12, 8], [13, 19], [14, 10], [15, 11], [16, 0], [17, 1], [18, 2]]


def get_furthest_from_source(G, source):
    Q = Queue()
    visited = set()
    furthest = 0
    furthest_node = None

    Q.put((source, 0))
    visited.add(source)
    while not Q.empty():
        top = Q.get()
        if top[1] > furthest:
            furthest_node = top[0]
            furthest = top[1]

        for n in G.neighbors(top[0]):
            if n in visited:
                continue
            Q.put((n, top[1] + 1))
            visited.add(n)
    
    return furthest_node


def get_group_order(G):
    D = G.to_directed(G)
    
    start = list(D.nodes)[0]
    for node in D.nodes:
        if D.in_degree(node) == 1:
            start = node
            break
        
    Q = Queue()
    visited = set()

    Q.put(start)
    visited.add(start)
    while not Q.empty():
        top = Q.get()
        for node in D.successors(top):
            D.remove_edge(node, top)
            if node not in visited:
                visited.add(node)
                Q.put(node)   

    path = nx.dag_longest_path(D)
    disjoint = set()
    for node in G.nodes:
        if node not in path:
            disjoint.add(node)

    new_path = []

    for i in range(0, len(path) - 1):
        max_path = None

        for node in G.neighbors(path[i]):
            if node not in disjoint:
                continue

            max_length = 0
            for simple_path in nx.all_simple_paths(nx.subgraph(
                    G, disjoint.union(set([path[i], path[i + 1]]))), path[i], path[i + 1]):
                if len(simple_path) > max_length:
                    max_length = len(simple_path)
                    max_path = simple_path
        
        if max_path:
            G.remove_nodes_from(max_path[:-1])
            new_path.extend(max_path[:-1])
        else:
            G.remove_node(path[i])
            new_path.append(path[i])

    new_path.append(path[-1])
    G.remove_node(path[-1])

    for wcc in nx.connected_components(G):
        if len(wcc) <= 2:
            new_path.extend(wcc)
            continue

        max_path = []
        for start in wcc:
            simple_paths = list(nx.all_simple_paths(G, start, wcc))
            if len(simple_paths) < 1:
                continue

            m = max(simple_paths, key=lambda x: len(x))
            if len(m) > len(max_path):
                max_path = m
            if len(m) == len(wcc):
                break
        
        new_path.extend(max_path)
        new_path.extend(wcc - set(max_path))

    return new_path


class AppShell(cmd.Cmd):
    intro = "KeySoze v1.0. Type help or ? to list commands.\n"
    prompt = ">>> "

    def __init__(self, line=None):
        super().__init__(line)

    def do_convert(self, line):
        "Reorganizes playlist in key order. May specify a starting key (Default C Major)."

        # Get command arguments
        args = line.split(" ")
        if len(args) != 1 or not args[0]:
            print("Invalid arguments. Usage: convert [playlist URL]\n")
            return

        playlist = sp.playlist(args[0])
        playlist_id = playlist["uri"]

        uid = 0
        G = nx.Graph()

        uri_list = []
        tracks = defaultdict(lambda: [])
        for item in playlist["tracks"]["items"]:
            uri = item["track"]["uri"]
            features = sp.audio_features(uri)[0]

            offset = 12 if features["mode"] == 0 else 0
            key = int(features["key"]) + offset
            energy = float(features["energy"])
            
            G.add_node(uid, uri=uri, key=key, energy=energy)

            uri_list.append(uri)
            tracks[key].append(uid)
            uid += 1

        sp.playlist_remove_all_occurrences_of_items(playlist_id, uri_list)

        for node in G.nodes(data=True):
            id = node[0]
            key = node[1]["key"]

            for assoc_key in mappings[key] + [key]:
                for neighbor in tracks[assoc_key]:
                    if neighbor == id: 
                        continue
                    G.add_edge(id, neighbor)
        
        wcc = sorted(list(nx.connected_components(G)), key=lambda x: len(x), reverse=True)
        attribs = nx.get_node_attributes(G, "uri")
        for c in wcc:
            D = nx.subgraph(G, c).copy()
            path = get_group_order(D)
            sp.playlist_add_items(playlist_id, map(lambda n: attribs[n], path))

        print("Converted!\n")

if __name__ == "__main__":
    AppShell().cmdloop()
