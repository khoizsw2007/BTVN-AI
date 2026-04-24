import numpy as np
import pandas as pd
import folium
from sklearn.cluster import KMeans
np.random.seed(42)
n_rides = 1000
lats = np.random.uniform(10.74, 10.85, n_rides)
lons = np.random.uniform(106.65, 106.78, n_rides)
fares = np.random.randint(30000, 100000, n_rides) 
df = pd.DataFrame({'lat': lats, 'lon': lons, 'fare': fares})
for i in range(n_rides):
    lat, lon = df.loc[i, 'lat'], df.loc[i, 'lon']
    if (10.76 < lat < 10.79 and 106.69 < lon < 106.72) or (10.79 < lat < 10.81 and 106.72 < lon < 106.75):
        if np.random.rand() > 0.4: 
            df.loc[i, 'fare'] = np.random.randint(150000, 400000)
vip_rides = df[df['fare'] >= 150000].copy()
X_vip = vip_rides[['lat', 'lon']]
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
vip_rides['cluster'] = kmeans.fit_predict(X_vip)
profit_hubs = kmeans.cluster_centers_
m = folium.Map(location=[10.78, 106.70], zoom_start=13, tiles='CartoDB dark_matter') # Dùng nền Dark Mode cho ngầu
for i, row in df[df['fare'] < 150000].iterrows():
    folium.CircleMarker( location=[row['lat'], row['lon']], radius=2, color='gray', opacity=0.3).add_to(m)
for i, row in vip_rides.iterrows():
    folium.CircleMarker(location=[row['lat'], row['lon']], radius=5, color='#00aaff', weight=1.5, fill=True, fill_color='#00aaff', fill_opacity=0.6, tooltip=f"Giá cước: {row['fare']:,} đ").add_to(m)
colors = ['#FFD700', '#FF4500', '#00FF7F']
for idx, hub in enumerate(profit_hubs):
    folium.Circle(location=[hub[0], hub[1]], radius=800, color=colors[idx], weight=2, fill=True, fill_opacity=0.1, dash_array='5,5').add_to(m)
    folium.Marker(location=[hub[0], hub[1]], tooltip=f"<b>PROFIT HUB {idx+1}</b><br>Gợi ý: Tài xế VIP di chuyển đến đây chờ khách",  icon=folium.Icon(color='black', icon_color=colors[idx], icon='star', prefix='fa')).add_to(m)
m