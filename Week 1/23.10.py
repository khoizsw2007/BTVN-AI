import osmnx as ox
import networkx as nx
import folium
import random
place = "Phường Linh Xuân, Thủ Đức, Ho Chi Minh City, Vietnam"
G = ox.graph_from_place(place, network_type='drive')
largest_cc = max(nx.strongly_connected_components(G), key=len)
G = G.subgraph(largest_cc).copy()
random.seed(42)
for u, v, k, data in G.edges(keys=True, data=True):
    congestion_level = random.random()
    data['congestion'] = congestion_level
    if congestion_level > 0.7:
        data['color'] = '#FF0000'
        data['ai_weight'] = data['length'] * 10
    elif congestion_level > 0.4:
        data['color'] = '#FFA500'
        data['ai_weight'] = data['length'] * 2
    else:
        data['color'] = '#00FF00'
        data['ai_weight'] = data['length']
nodes = list(G.nodes())
orig = nodes[15]
dest = nodes[-15]
path_shortest = nx.shortest_path(G, orig, dest, weight='length')
path_ai = nx.shortest_path(G, orig, dest, weight='ai_weight')
dist_shortest = nx.path_weight(G, path_shortest, weight='length')
eta_shortest  = nx.path_weight(G, path_shortest, weight='ai_weight')
dist_ai = nx.path_weight(G, path_ai, weight='length')
eta_ai  = nx.path_weight(G, path_ai, weight='ai_weight')
print("\n" + "="*50)
print("BẢNG PHÂN TÍCH TỐI ƯU HÓA LỘ TRÌNH (ETA VS DISTANCE)")
print("="*50)
print("\n  TUYẾN 1: ĐƯỜNG NGẮN NHẤT")
print(f"   - Khoảng cách vật lý: {dist_shortest:.1f} mét")
print(f"   - Chi phí thời gian:  {eta_shortest:.1f} đơn vị ETA")
print("\n  TUYẾN 2: ĐƯỜNG AI")
print(f"   - Khoảng cách vật lý: {dist_ai:.1f} mét")
print(f"   - Chi phí thời gian:  {eta_ai:.1f} đơn vị ETA")
m = folium.Map(location=[G.nodes[orig]['y'], G.nodes[orig]['x']], zoom_start=15)
for u, v, k, data in G.edges(keys=True, data=True):
    if data['congestion'] > 0.4:
        locs = [(G.nodes[u]['y'], G.nodes[u]['x']), (G.nodes[v]['y'], G.nodes[v]['x'])]
        folium.PolyLine(locs, color=data['color'], weight=3, opacity=0.3).add_to(m)
coords_shortest = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_shortest]
folium.PolyLine(coords_shortest, color='black', weight=5, opacity=0.6, dash_array='10, 10', popup=f'Ngắn nhất: {dist_shortest:.0f}m').add_to(m)
coords_ai = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_ai]
folium.PolyLine(coords_ai, color='#0000FF', weight=7, opacity=0.9, popup=f'AI Đề xuất: Tiết kiệm {(eta_shortest - eta_ai):.0f} ETA').add_to(m)
folium.Marker(coords_shortest[0], popup="Điểm Đón", icon=folium.Icon(color='green', icon='play')).add_to(m)
folium.Marker(coords_shortest[-1], popup="Điểm Trả", icon=folium.Icon(color='red', icon='stop')).add_to(m)
m