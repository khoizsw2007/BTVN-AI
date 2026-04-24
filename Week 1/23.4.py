import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
url_34_tinh = "https://raw.githubusercontent.com/lamngockhuong/vietnam-3d-map/main/data/vietnam-provinces.geojson"
vn_map_34 = gpd.read_file(url_34_tinh)
np.random.seed(42)
vn_map_34['doanh_thu'] = np.random.randint(100, 1000, size=len(vn_map_34))
fig, ax = plt.subplots(1, 1, figsize=(10, 12))
vn_map_34.plot(column='doanh_thu', cmap='Blues', legend=True, legend_kwds={'label': "Doanh thu (Tỷ VNĐ)", 'shrink': 0.5}, ax=ax, edgecolor='gray', linewidth=0.5)
plt.title('Phân bổ doanh thu 34 Tỉnh thành', fontsize=16)
plt.axis('off')
plt.show()