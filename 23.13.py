import folium
import random
m = folium.Map(location=[10.775, 106.695], zoom_start=14)
layer_vung = folium.FeatureGroup(name=" Vùng nhân giá (Surge Zones)", show=True)
layer_tuyen = folium.FeatureGroup(name=" Chuyến xe đang chạy (Active Routes)", show=True)
layer_diem_tx = folium.FeatureGroup(name=" Tài xế rảnh (Available Drivers)", show=True)
layer_diem_kh = folium.FeatureGroup(name=" Khách chờ đón (Waiting Users)", show=False) # Tắt mặc định cho đỡ rối
surge_polygon = [
    [10.785, 106.685], [10.785, 106.705], 
    [10.765, 106.710], [10.760, 106.690]
]
folium.Polygon(locations=surge_polygon, color='red', weight=2, fill=True, fill_color='red', fill_opacity=0.15, tooltip="<b>Vùng Cao Điểm</b><br>Nhân giá: x1.5<br>Trạng thái: Cầu vượt Cung").add_to(layer_vung)
route_1 = [[10.770, 106.680], [10.775, 106.690], [10.780, 106.700]]
route_2 = [[10.765, 106.705], [10.770, 106.700], [10.772, 106.695]]
folium.PolyLine(route_1, color='#3388FF', weight=4, dash_array='8, 8', tooltip="Trip #102: Đang chở khách (ETA: 5 mins)").add_to(layer_tuyen)
folium.PolyLine(route_2, color='#3388FF', weight=4, dash_array='8, 8', tooltip="Trip #103: Đang chở khách (ETA: 2 mins)").add_to(layer_tuyen)
random.seed(42)
for i in range(5):
    lat = 10.775 + random.uniform(-0.015, 0.015)
    lon = 106.695 + random.uniform(-0.015, 0.015)
    folium.Marker(location=[lat, lon], icon=folium.Icon(color='green', icon='car', prefix='fa'), tooltip=f"Tài xế TX-{100+i}<br>Trạng thái: Sẵn sàng").add_to(layer_diem_tx)
khach_hang = [[10.780, 106.695], [10.775, 106.700], [10.760, 106.680]]
for i, kh in enumerate(khach_hang):
    folium.CircleMarker(location=kh, radius=8, color='orange', weight=2, fill=True, fill_color='yellow', fill_opacity=0.8, tooltip=f"Khách hàng KH-{800+i}<br>Đang tìm xe...").add_to(layer_diem_kh)
layer_vung.add_to(m)
layer_tuyen.add_to(m)
layer_diem_tx.add_to(m)
layer_diem_kh.add_to(m)
folium.LayerControl(position='topright', collapsed=False).add_to(m)
m