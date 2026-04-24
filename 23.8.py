import folium
import random
import math
trung_tam = [10.7769, 106.7009]
khach_hang = [[trung_tam[0] + (random.random() - 0.5) * 0.04,
               trung_tam[1] + (random.random() - 0.5) * 0.04] for _ in range(5)]
tai_xe = [[trung_tam[0] + (random.random() - 0.5) * 0.05,
           trung_tam[1] + (random.random() - 0.5) * 0.05] for _ in range(5)]
ket_qua_gan = []
tai_xe_ranh = list(range(5))
for kh_idx, toa_do_kh in enumerate(khach_hang):
    khoang_cach_ngan_nhat = float('inf')
    tx_phu_hop_nhat = -1
    for tx_idx in tai_xe_ranh:
        toa_do_tx = tai_xe[tx_idx]
        khoang_cach = math.hypot(toa_do_kh[0] - toa_do_tx[0], toa_do_kh[1] - toa_do_tx[1])
        if khoang_cach < khoang_cach_ngan_nhat:
            khoang_cach_ngan_nhat = khoang_cach
            tx_phu_hop_nhat = tx_idx
    ket_qua_gan.append((kh_idx, tx_phu_hop_nhat))
    tai_xe_ranh.remove(tx_phu_hop_nhat)
m = folium.Map(location=trung_tam, zoom_start=14)
for i, toa_do in enumerate(khach_hang):
    folium.Marker(toa_do, popup=f"Khách hàng {i+1}", icon=folium.Icon(color='blue', icon='user', prefix='fa')).add_to(m)
for i, toa_do in enumerate(tai_xe):
    folium.Marker(toa_do, popup=f"Tài xế {i+1}", icon=folium.Icon(color='green', icon='car', prefix='fa')).add_to(m)
for kh_idx, tx_idx in ket_qua_gan:
    toa_do_kh = khach_hang[kh_idx]
    toa_do_tx = tai_xe[tx_idx]
    folium.PolyLine(locations=[toa_do_tx, toa_do_kh], color='red', weight=3, popup=f"TX {tx_idx+1} đón KH {kh_idx+1}").add_to(m)
m