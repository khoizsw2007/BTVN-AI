import folium
import numpy as np
from sklearn.cluster import KMeans
np.random.seed(42)
khu_vuc_1 = np.random.randn(50, 2) * 0.02 + [10.80, 106.75] # Nhóm Thủ Đức
khu_vuc_2 = np.random.randn(50, 2) * 0.015 + [10.75, 106.65] # Nhóm Q5/Q10
khu_vuc_3 = np.random.randn(50, 2) * 0.025 + [10.72, 106.72] # Nhóm Q7
du_lieu_khach_hang = np.vstack([khu_vuc_1, khu_vuc_2, khu_vuc_3])
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
nhan_cum = kmeans.fit_predict(du_lieu_khach_hang)
toa_do_tram_xe = kmeans.cluster_centers_
m = folium.Map(location=[10.76, 106.70], zoom_start=12)
mau_sac = ['blue', 'green', 'purple']
for i in range(len(du_lieu_khach_hang)):
    folium.CircleMarker(location=[du_lieu_khach_hang[i][0], du_lieu_khach_hang[i][1]], radius=4, color=mau_sac[nhan_cum[i]], fill=True, fill_opacity=0.7).add_to(m)
for i, toa_do in enumerate(toa_do_tram_xe):
    folium.Marker(location=[toa_do[0], toa_do[1]], popup=f"<b>Trạm Trung Chuyển {i+1}</b>", icon=folium.Icon(color='red', icon='star')).add_to(m)
m