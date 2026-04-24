import folium
kho_hang_coords = [10.7760, 106.6670]
m = folium.Map(location=kho_hang_coords, zoom_start=12)
folium.Marker(location=kho_hang_coords, popup="<b>Kho hàng Trung tâm (Q10)</b>", icon=folium.Icon(color="red", icon="home")).add_to(m)
folium.Circle(location=kho_hang_coords, radius=3000, color='green', fill=True, fill_color='green', fill_opacity=0.3, popup="Vùng 1: 3km (Giao hỏa tốc)").add_to(m)
folium.Circle(location=kho_hang_coords, radius=5000, color='orange',fill=True, fill_color='orange', fill_opacity=0.15, popup="Vùng 2: 5km (Giao tiêu chuẩn)").add_to(m)
folium.Circle(location=kho_hang_coords, radius=10000, color='blue', fill=False, weight=2, popup="Vùng 3: 10km (Phạm vi tối đa)").add_to(m)
m