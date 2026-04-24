import osmnx as ox
import networkx as nx
import folium
from folium.plugins import TimestampedGeoJson
import datetime
toa_do_trung_tam = (10.773, 106.701)
G = ox.graph_from_point(toa_do_trung_tam, dist=1500, network_type='drive')
largest_cc = max(nx.strongly_connected_components(G), key=len)
G = G.subgraph(largest_cc).copy()
nodes = list(G.nodes())
path_xe_1 = nx.shortest_path(G, nodes[20], nodes[-20], weight='length')
path_xe_2 = nx.shortest_path(G, nodes[80], nodes[-80], weight='length')
features = []
thoi_gian_bat_dau = datetime.datetime.now()
def tao_mo_phong_xe(path, ma_xe, mau_chu_dao):
    for i, node in enumerate(path):
        lon = G.nodes[node]['x']
        lat = G.nodes[node]['y']
        thoi_gian_hien_tai = thoi_gian_bat_dau + datetime.timedelta(seconds=i*15)
        if i == 0:
            trang_thai = "Đang đến điểm đón"
            mau_sac = "#FFA500" 
        elif i == len(path) - 1:
            trang_thai = "Đã hoàn thành chuyến"
            mau_sac = "#00FF00" 
        else:
            trang_thai = f"Đang chở khách (Trạm {i}/{len(path)-1})"
            mau_sac = mau_chu_dao
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            },
            'properties': {
                'time': thoi_gian_hien_tai.strftime('%Y-%m-%dT%H:%M:%S'),
                'popup': f"<div style='width: 160px; font-family: sans-serif;'>"
                         f"<b> ID Xe:</b> {ma_xe}<br>"
                         f"<b>Trạng thái:</b> {trang_thai}<br>"
                         f"<b>Cập nhật:</b> {thoi_gian_hien_tai.strftime('%H:%M:%S')}</div>",
                'icon': 'circle',
                'iconstyle': {
                    'fillColor': mau_sac,
                    'fillOpacity': 0.9,
                    'stroke': 'true',
                    'color': 'white',
                    'radius': 9
                }
            }
        }
        features.append(feature)
tao_mo_phong_xe(path_xe_1, "TX-888", "#3388FF") 
tao_mo_phong_xe(path_xe_2, "TX-999", "#8A2BE2") 
print("Đang dựng mô phỏng động...")
m = folium.Map(location=toa_do_trung_tam, zoom_start=15)
folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_xe_1], color='#3388FF', weight=3, opacity=0.3, dash_array='5,5').add_to(m)
folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_xe_2], color='#8A2BE2', weight=3, opacity=0.3, dash_array='5,5').add_to(m)
TimestampedGeoJson(
    {'type': 'FeatureCollection', 'features': features},
    period='PT15S',            
    add_last_point=False,      
    auto_play=True,             
    loop=True,                  
    max_speed=1,
    loop_button=True,
    date_options='HH:mm:ss',    
    time_slider_drag_update=True
).add_to(m)
m