import folium, time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
center = (10.7610472, 106.6681269)
m = folium.Map(location=center, zoom_start=15)
folium.Marker([10.7610472, 106.6681269], popup='UEH Cơ sở B', icon=folium.Icon(color='red')).add_to(m)
places = ["Chợ Bến Thành, HCM", "Dinh Độc Lập, HCM", "Landmark 81, HCM", "Sân bay Tân Sơn Nhất, HCM", "Bến Nhà Rồng, HCM", "Chợ Bình Tây, HCM", "Thảo Cầm Viên, HCM", "Suối Tiên, HCM", "Đầm Sen, HCM", "Bảo tàng Mỹ Thuật, HCM"]
geo = Nominatim(user_agent="app_khoi")
for p in places:
    loc = geo.geocode(p)
    if loc:
        pt = (loc.latitude, loc.longitude)
        folium.Marker(pt, popup=f"{p}<br>{geodesic(center, pt).km:.1f} km").add_to(m)
        folium.PolyLine([center, pt], color='red').add_to(m)
m