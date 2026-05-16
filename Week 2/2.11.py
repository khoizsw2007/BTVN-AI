import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt
import numpy as np

distance = ctrl.Antecedent(np.arange(0, 51, 1), 'distance')
traffic = ctrl.Antecedent(np.arange(0, 101, 1), 'traffic')
fare = ctrl.Consequent(np.arange(1.0, 3.1, 0.1), 'fare')

distance['ngan'] = fuzz.trapmf(distance.universe, [0, 0, 2, 4])
distance['trung_binh'] = fuzz.trimf(distance.universe, [2, 5, 8])
distance['dai'] = fuzz.trapmf(distance.universe, [6, 10, 15, 20])
distance['rat_xa'] = fuzz.trapmf(distance.universe, [15, 25, 50, 50])

traffic['thap'] = fuzz.trapmf(traffic.universe, [0, 0, 20, 30])
traffic['trung_binh'] = fuzz.trimf(traffic.universe, [20, 45, 70])
traffic['cao'] = fuzz.trapmf(traffic.universe, [60, 80, 100, 100])

fare['thap'] = fuzz.trimf(fare.universe, [1.0, 1.0, 1.5])
fare['trung_binh'] = fuzz.trimf(fare.universe, [1.2, 1.6, 2.0])
fare['cao'] = fuzz.trimf(fare.universe, [1.8, 2.1, 2.5])
fare['rat_cao'] = fuzz.trapmf(fare.universe, [2.2, 2.6, 3.0, 3.0])

rule1 = ctrl.Rule(distance['ngan'] & traffic['thap'], fare['thap'])
rule2 = ctrl.Rule(distance['trung_binh'] & traffic['trung_binh'], fare['trung_binh'])
rule3 = ctrl.Rule(distance['rat_xa'] & traffic['cao'], fare['rat_cao'])
rule4 = ctrl.Rule(distance['ngan'] & traffic['cao'], fare['cao'])
rule5 = ctrl.Rule(distance['trung_binh'] & traffic['cao'], fare['cao'])
rule6 = ctrl.Rule(distance['dai'] & traffic['cao'], fare['rat_cao'])
rule7 = ctrl.Rule(distance['dai'] & traffic['thap'], fare['trung_binh'])

fare_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7])
fare_sim = ctrl.ControlSystemSimulation(fare_ctrl)

input_distance = 7.0
input_traffic = 85.0
fare_sim.input['distance'] = input_distance
fare_sim.input['traffic'] = input_traffic

fare_sim.compute()

print("-" * 50)
print(f"Khoảng cách chuyến đi: {input_distance} km")
print(f"Tình trạng kẹt xe: {input_traffic} %")
print(f"=> HỆ SỐ GIÁ CƯỚC ĐỀ XUẤT: {fare_sim.output['fare']:.2f}x")
print("-" * 50)
%matplotlib inline
fig, (ax0, ax1, ax2) = plt.subplots(nrows=3, figsize=(10, 15))
for label in distance.terms:
    ax0.plot(distance.universe, distance[label].mf, label=label, linewidth=2)
ax0.axvline(x=input_distance, color='black', linestyle='--', label='Giá trị nhập')
ax0.set_title('Biến đầu vào: Khoảng cách (km)')
ax0.legend()

for label in traffic.terms:
    ax1.plot(traffic.universe, traffic[label].mf, label=label, linewidth=2)
ax1.axvline(x=input_traffic, color='black', linestyle='--', label='Giá trị nhập')
ax1.set_title('Biến đầu vào: Lưu lượng Giao thông (%)')
ax1.legend()

for label in fare.terms:
    ax2.plot(fare.universe, fare[label].mf, label=label, linewidth=2)

if 'fare' in fare_sim.output:
    res_fare = fare_sim.output['fare']
    ax2.axvline(x=res_fare, color='red', linewidth=3, label=f'Kết quả: {res_fare:.2f}x')

ax2.set_title('Kết quả: Hệ số Giá cước (Giải mờ)')
ax2.legend()

plt.tight_layout()
plt.show()