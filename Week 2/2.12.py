import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import matplotlib.pyplot as plt

rating = ctrl.Antecedent(np.arange(0, 5.1, 0.1), 'rating')
sales = ctrl.Antecedent(np.arange(0, 1001, 1), 'sales')
margin = ctrl.Antecedent(np.arange(0, 101, 1), 'margin')
event = ctrl.Antecedent(np.arange(0, 11, 1), 'event')
comp_discount = ctrl.Antecedent(np.arange(0, 101, 1), 'comp_discount')

discount = ctrl.Consequent(np.arange(0, 71, 1), 'discount')

rating['thap'] = fuzz.trapmf(rating.universe, [0, 0, 3.5, 4.0])
rating['trung_binh'] = fuzz.trimf(rating.universe, [3.8, 4.25, 4.6])
rating['cao'] = fuzz.trapmf(rating.universe, [4.4, 4.8, 5.0, 5.0])

sales['thap'] = fuzz.trapmf(sales.universe, [0, 0, 200, 400])
sales['trung_binh'] = fuzz.trimf(sales.universe, [300, 500, 700])
sales['cao'] = fuzz.trapmf(sales.universe, [600, 800, 1000, 1000])

margin['thap'] = fuzz.trapmf(margin.universe, [0, 0, 15, 30])
margin['trung_binh'] = fuzz.trimf(margin.universe, [20, 45, 70])
margin['cao'] = fuzz.trapmf(margin.universe, [60, 80, 100, 100])

event['khong_co'] = fuzz.trapmf(event.universe, [0, 0, 2, 4])
event['trung_binh'] = fuzz.trimf(event.universe, [3, 5, 7])
event['cao'] = fuzz.trapmf(event.universe, [6, 8, 10, 10])

comp_discount['thap'] = fuzz.trapmf(comp_discount.universe, [0, 0, 10, 25])
comp_discount['trung_binh'] = fuzz.trimf(comp_discount.universe, [15, 30, 50])
comp_discount['cao'] = fuzz.trapmf(comp_discount.universe, [40, 60, 100, 100])

discount['rat_thap'] = fuzz.trimf(discount.universe, [0, 2.5, 6])
discount['thap'] = fuzz.trimf(discount.universe, [4, 7.5, 12])
discount['trung_binh'] = fuzz.trimf(discount.universe, [8, 15, 22])
discount['cao'] = fuzz.trimf(discount.universe, [18, 30, 42])
discount['rat_cao'] = fuzz.trapmf(discount.universe, [38, 55, 70, 70])

rule1 = ctrl.Rule(rating['cao'] & sales['cao'] & margin['cao'], discount['rat_thap'])
rule2 = ctrl.Rule(rating['thap'] & sales['thap'] & margin['cao'], discount['cao'])
rule3 = ctrl.Rule(event['cao'] & comp_discount['cao'], discount['rat_cao'])
rule4 = ctrl.Rule(rating['trung_binh'] & sales['trung_binh'] & margin['trung_binh'], discount['trung_binh'])
rule5 = ctrl.Rule(comp_discount['thap'] & margin['thap'] & sales['cao'], discount['rat_thap'])
rule6 = ctrl.Rule(rating['thap'] & event['khong_co'] & margin['thap'], discount['thap'])
rule7 = ctrl.Rule(sales['thap'] & margin['thap'], discount['rat_cao'])

discount_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7])
discount_sim = ctrl.ControlSystemSimulation(discount_ctrl)

r_in = 4.2
s_in = 250
m_in = 50
e_in = 9
c_in = 65

discount_sim.input['rating'] = r_in
discount_sim.input['sales'] = s_in
discount_sim.input['margin'] = m_in
discount_sim.input['event'] = e_in
discount_sim.input['comp_discount'] = c_in

discount_sim.compute()

print("=" * 50)
print("THÔNG SỐ ĐẦU VÀO TỪ CỬA HÀNG SHOPEE:")
print(f"- Đánh giá cửa hàng: {r_in} sao")
print(f"- Lượng đơn hàng: {s_in} đơn/tháng")
print(f"- Biên lợi nhuận: {m_in}%")
print(f"- Mức độ sự kiện (0-10): {e_in}")
print(f"- Đối thủ chiết khấu: {c_in}%")
print("-" * 50)
print(f"=> HỆ THỐNG ĐỀ XUẤT MỨC GIẢM GIÁ: {discount_sim.output['discount']:.2f} %")
print("=" * 50)

discount.view(sim=discount_sim)
plt.title('Biểu đồ Giải mờ: Mức chiết khấu đề xuất (%)')
plt.tight_layout()
plt.show()