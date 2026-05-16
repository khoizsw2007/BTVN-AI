import folium, random
from folium.plugins import HeatMap

m = folium.Map(location=[10.7769, 106.7009], zoom_start=12, tiles="CartoDB dark_matter")

data = [[random.gauss(10.77, 0.02), random.gauss(106.70, 0.02)] for _ in range(300)] + \
       [[random.gauss(10.75, 0.015), random.gauss(106.66, 0.015)] for _ in range(200)]
HeatMap(data, radius=15, blur=10).add_to(m)
m
