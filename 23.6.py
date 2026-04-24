import osmnx as ox
place_name = "Thủ Đức, Ho Chi Minh City, Vietnam"
G = ox.graph_from_place(place_name, network_type='drive')
fig, ax = ox.plot_graph(G, node_size=0, edge_color='#FF5733', edge_linewidth=0.3, bgcolor='black')
stats = ox.basic_stats(G)
print(f"\n--- KẾT QUẢ PHÂN TÍCH HẠ TẦNG THỦ ĐỨC ---")
print(f"- Số lượng nút giao (Intersections): {stats['n']} nút")
print(f"- Tổng chiều dài mạng lưới đường bộ: {stats['street_length_total'] / 1000:.2f} km")
print(f"- Chiều dài trung bình mỗi đoạn đường: {stats['street_length_avg']:.2f} mét")