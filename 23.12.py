import folium
import numpy as np
import math
import random
def tinh_khoang_cach(coord1, coord2):
    R = 6371.0 
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
kho_hang = {
    "Kho A (Thủ Đức)": [10.850, 106.750],
    "Kho B (Quận 1)":  [10.770, 106.700]
}
random.seed(42)
diem_giao = [[random.uniform(10.75, 10.87), random.uniform(106.68, 106.78)] for _ in range(15)]
diem_giao_random = diem_giao.copy()
random.shuffle(diem_giao_random)
diem_kho_A_random = diem_giao_random[:8]
diem_kho_B_random = diem_giao_random[8:]

def tinh_quang_duong_random(kho_coord, danh_sach_diem):
    quang_duong = 0
    hien_tai = kho_coord
    for diem in danh_sach_diem:
        quang_duong += tinh_khoang_cach(hien_tai, diem)
        hien_tai = diem
    quang_duong += tinh_khoang_cach(hien_tai, kho_coord) # Quay về kho
    return quang_duong
chi_phi_random_A = tinh_quang_duong_random(kho_hang["Kho A (Thủ Đức)"], diem_kho_A_random)
chi_phi_random_B = tinh_quang_duong_random(kho_hang["Kho B (Quận 1)"], diem_kho_B_random)
tong_chi_phi_random = chi_phi_random_A + chi_phi_random_B
phan_cum = {ten_kho: [] for ten_kho in kho_hang}
for diem in diem_giao:
    kho_gan_nhat = min(kho_hang.keys(), key=lambda k: tinh_khoang_cach(kho_hang[k], diem))
    phan_cum[kho_gan_nhat].append(diem)
lo_trinh_toi_uu = {}
tong_chi_phi_toi_uu = 0
for ten_kho, cac_diem in phan_cum.items():
    chua_giao = cac_diem.copy()
    diem_hien_tai = kho_hang[ten_kho]
    lo_trinh = [diem_hien_tai]
    quang_duong_xe = 0
    while chua_giao:
        diem_tiep_theo = min(chua_giao, key=lambda x: tinh_khoang_cach(diem_hien_tai, x))
        quang_duong_xe += tinh_khoang_cach(diem_hien_tai, diem_tiep_theo)
        lo_trinh.append(diem_tiep_theo)
        chua_giao.remove(diem_tiep_theo)
        diem_hien_tai = diem_tiep_theo
    quang_duong_xe += tinh_khoang_cach(diem_hien_tai, kho_hang[ten_kho])
    lo_trinh.append(kho_hang[ten_kho])
    
    lo_trinh_toi_uu[ten_kho] = lo_trinh
    tong_chi_phi_toi_uu += quang_duong_xe
print("ĐÁNH GIÁ HIỆU QUẢ THUẬT TOÁN ĐỊNH TUYẾN")
print(f"1. Phương án KHÔNG TỐI ƯU (Giao ngẫu nhiên):")
print(f"   - Tổng quãng đường: {tong_chi_phi_random:.2f} km")
print(f"\n2. Phương án TỐI ƯU (Thuật toán Heuristic):")
print(f"   - Tổng quãng đường: {tong_chi_phi_toi_uu:.2f} km")
print(f"\n=> KẾT LUẬN: AI giúp giảm {tong_chi_phi_random - tong_chi_phi_toi_uu:.2f} km ")
print(f"   (Tiết kiệm {(1 - tong_chi_phi_toi_uu/tong_chi_phi_random)*100:.1f}% chi phí xăng xe và thời gian!)")
m = folium.Map(location=[10.81, 106.72], zoom_start=12, tiles='CartoDB positron')
mau_sac_xe = {"Kho A (Thủ Đức)": "#FF5733", "Kho B (Quận 1)": "#3388FF"}
for i, diem in enumerate(diem_giao):
    folium.CircleMarker(location=diem, radius=6, color='black', weight=1, fill=True, fill_color='white', fill_opacity=1, popup=f"Điểm giao {i+1}").add_to(m)
for ten_kho, lo_trinh in lo_trinh_toi_uu.items():
    mau = mau_sac_xe[ten_kho]
    folium.Marker(location=kho_hang[ten_kho], popup=f"<b>{ten_kho}</b>", icon=folium.Icon(color='red' if 'A' in ten_kho else 'blue', icon='home')).add_to(m)
    folium.PolyLine(locations=lo_trinh, color=mau, weight=4, opacity=0.8, tooltip=f"Lộ trình xe {ten_kho}").add_to(m)

m