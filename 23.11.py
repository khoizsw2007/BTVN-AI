import osmnx as ox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import matplotlib.patches as mpatches
place = "Thủ Đức, Ho Chi Minh City, Vietnam"
G = ox.graph_from_place(place, network_type="drive")
nodes, edges = ox.graph_to_gdfs(G)
n = 2000
data = pd.DataFrame({
    "lat": np.random.uniform(nodes["y"].min(), nodes["y"].max(), n),
    "lon": np.random.uniform(nodes["x"].min(), nodes["x"].max(), n),
    "hour": np.random.randint(0, 24, n),
})
def true_demand(hour, lat):
    base = np.random.randint(10, 30)
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        base += 50
    if lat > data["lat"].mean():
        base += 10
    return base
data["demand"] = data.apply(lambda x: true_demand(x["hour"], x["lat"]), axis=1)
print("Đang huấn luyện AI...")
X = data[["lat", "lon", "hour"]]
y = data["demand"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)
data["predicted"] = model.predict(X)
print("Đang dựng bản đồ và điểm ảnh...")
fig, ax = ox.plot_graph(
    G,
    node_size=0,
    edge_color="lightgray",
    edge_linewidth=0.5,
    bgcolor="white",
    show=False,
    close=False
)
for _, row in data.iterrows():
    if row["predicted"] > 70:
        color = "red"
        size = 40
    elif row["predicted"] > 40:
        color = "orange"
        size = 25
    else:
        color = "green"
        size = 15
    ax.scatter(row["lon"], row["lat"], c=color, s=size, alpha=0.6)
red_patch = mpatches.Patch(color='red', label='Nhu cầu rất cao (>70)')
orange_patch = mpatches.Patch(color='orange', label='Nhu cầu cao (>40)')
green_patch = mpatches.Patch(color='green', label='Nhu cầu trung bình (<=40)')
ax.legend(handles=[red_patch, orange_patch, green_patch], loc='upper right', title='Mức độ nhu cầu')
ax.set_title("Demand Prediction Map (ML) - Thu Duc City")
plt.show()
score = model.score(X_test, y_test)
print("Model R^2 score:", score)