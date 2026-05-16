import osmnx as ox
import networkx as nx
import folium
import time
import math
place = "Phường Linh Xuân, Thủ Đức, Ho Chi Minh City, Vietnam"
G = ox.graph_from_place(place, network_type='drive')
nodes = list(G.nodes())
orig = nodes[10]
dest = nodes[-10]
def heuristic_chim_bay(n1, n2):
    x1, y1 = G.nodes[n1]['x'], G.nodes[n1]['y']
    x2, y2 = G.nodes[n2]['x'], G.nodes[n2]['y']
    return math.hypot(x2 - x1, y2 - y1) * 111139
start_dijkstra = time.time()
path_dijkstra = nx.dijkstra_path(G, orig, dest, weight='length')
time_dijkstra = time.time() - start_dijkstra
length_dijkstra = nx.path_weight(G, path_dijkstra, weight='length')
start_astar = time.time()
path_astar = nx.astar_path(G, orig, dest, heuristic=heuristic_chim_bay, weight='length')
time_astar = time.time() - start_astar
length_astar = nx.path_weight(G, path_astar, weight='length')
print("\n--- BẢNG SO SÁNH KẾT QUẢ ---")
print("1. Thuật toán Dijkstra:")
print(f"   - Chiều dài lộ trình : {length_dijkstra:.2f} mét")
print(f"   - Thời gian xử lý    : {time_dijkstra:.6f} giây")
print("\n2. Thuật toán A* (A-Star):")
print(f"   - Chiều dài lộ trình : {length_astar:.2f} mét")
print(f"   - Thời gian xử lý    : {time_astar:.6f} giây")
route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path_astar]
m = folium.Map(location=route_coords[0], zoom_start=15)
folium.Marker(route_coords[0], popup="Điểm đón khách", icon=folium.Icon(color='green', icon='play')).add_to(m)
folium.Marker(route_coords[-1], popup="Điểm trả khách", icon=folium.Icon(color='red', icon='stop')).add_to(m)
folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.8).add_to(m)
m