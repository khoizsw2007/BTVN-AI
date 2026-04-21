import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time

# Cấu hình giao diện chuẩn
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ================= 1. CẤU HÌNH & TỰ ĐỘNG CÀI ĐẶT DATABASE =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Baolam080907*",  # <--- ĐIỀN MẬT KHẨU CỦA BẠN VÀO ĐÂY
    "database": "qlud"
}

def auto_setup_database():
    """Hàm tự động tạo Database, tạo Bảng và Import CSV siêu tốc"""
    print("⏳ Khởi động hệ thống RideHub...")
    
    try:
        # 1. Kết nối thẳng vào MySQL Server (Chưa cần biết có DB hay chưa)
        server_conn = mysql.connector.connect(
            host=DB_CONFIG["host"], 
            user=DB_CONFIG["user"], 
            password=DB_CONFIG["password"]
        )
        cursor = server_conn.cursor()
        
        # 2. Tạo Database mới tinh
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        server_conn.close()
        
        # 3. Kết nối vào DB vừa tạo để kiểm tra dữ liệu
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES LIKE 'rides'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM rides")
            count = cursor.fetchone()[0]
            if count > 10000:
                print(f"✅ Database đã sẵn sàng ({count:,} chuyến đi). Bật giao diện...")
                conn.close()
                return

        # 4. Tiền hành Import từ đầu nếu DB trống
        print("⚠️ Database trống! Bắt đầu tiến trình Import 150.000 dòng từ CSV...")
        start_time = time.time()
        
        # Đọc CSV bằng Pandas
        print("📥 Đang đọc file ncr_ride_bookings (4).csv...")
        df = pd.read_csv("ncr_ride_bookings (4).csv")
        df.fillna(0, inplace=True) # Dọn dẹp dữ liệu rác

        # Tạo động cơ kết nối SQLAlchemy
        engine_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(engine_url)
        
        # Đổ thẳng DataFrame vào MySQL (Tự động tạo bảng 'rides')
        print("🚀 Đang bơm dữ liệu vào MySQL... (Mất khoảng 10-15 giây)")
        df.to_sql(name='rides', con=engine, if_exists='replace', index=False)
        
        end_time = time.time()
        print(f"✅ HOÀN TẤT IMPORT! Thời gian: {end_time - start_time:.1f} giây. Khởi động UI...")
        conn.close()

    except FileNotFoundError:
        print("❌ LỖI: Không tìm thấy file CSV! Đảm bảo file 'ncr_ride_bookings (4).csv' nằm chung thư mục với app.py.")
        exit()
    except Exception as e:
        print(f"❌ Lỗi Hệ Thống: {e}")
        exit()

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        return None

# ================= 2. CÁC MODULE GIAO DIỆN CHÍNH =================

# --- MODULE 1: DASHBOARD ---
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Executive Operations Dashboard", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM rides")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(`Booking Value`) as rev FROM rides WHERE `Booking Status`='Completed'")
            rev = cursor.fetchone()['rev'] or 0
            
            cursor.execute("SELECT AVG(`Driver Ratings`) as rate FROM rides WHERE `Driver Ratings` > 0")
            rate = cursor.fetchone()['rate'] or 0
            
            cursor.execute("SELECT AVG(`Avg VTAT`) as vtat FROM rides")
            vtat = cursor.fetchone()['vtat'] or 0
            conn.close()
        else:
            total, rev, rate, vtat = 0, 0, 0, 0

        self.create_card(stats_frame, "TOTAL RIDES", f"{total:,}", 0, "#3498db")
        self.create_card(stats_frame, "TOTAL REVENUE", f"₹{rev:,.0f}", 1, "#2ecc71")
        self.create_card(stats_frame, "AVG RATING", f"{rate:.2f} ⭐", 2, "#f1c40f")
        self.create_card(stats_frame, "AVG WAIT (VTAT)", f"{vtat:.1f} min", 3, "#e74c3c")

        charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, pady=10)
        self.draw_line_chart(charts_frame)

    def create_card(self, parent, title, value, col, color):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=10, width=220, height=100)
        card.grid(row=0, column=col, padx=(0, 15))
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Arial", 11, "bold"), text_color="gray").place(x=15, y=15)
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"), text_color=color).place(x=15, y=40)

    def draw_line_chart(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
        fig.patch.set_facecolor('white')
        ax.plot(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [120, 150, 130, 180, 210, 190, 230], marker='o', color="#2ecc71", linewidth=2)
        ax.set_title("Revenue Trend vs. Forecast", loc="left", fontsize=12, fontweight="bold")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

# --- MODULE 2: RIDE MANAGEMENT ---
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Ride Management Hub", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 10))

        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=35, borderwidth=0)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#f1f2f6")

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        self.table = ttk.Treeview(table_frame, columns=("ID", "Date", "Route", "Price", "VTAT", "Status"), show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.table.yview)

        for col in self.table["columns"]:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="center")
        self.table.column("Route", width=250)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_data()

    def load_data(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT `Booking ID`, `Date`, `Pickup Location`, `Drop Location`, `Booking Value`, `Avg VTAT`, `Booking Status` FROM rides LIMIT 150")
        for row in cursor.fetchall():
            route = f"{row['Pickup Location'][:15]} -> {row['Drop Location'][:15]}"
            self.table.insert("", "end", values=(row['Booking ID'], row['Date'], route, f"₹{row['Booking Value']}", f"{row['Avg VTAT']}m", row['Booking Status']))
        conn.close()

# --- MODULE 3: USER PROFILES (DRIVER & CUSTOMER) ---
class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="User Management Hub", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 10))

        control_panel = ctk.CTkFrame(self, fg_color="transparent")
        control_panel.pack(fill="x", pady=(0, 20))

        # 1. Tab Chọn Drivers / Customers
        self.user_type_var = ctk.StringVar(value="Drivers")
        self.tab_menu = ctk.CTkSegmentedButton(control_panel, values=["Drivers", "Customers"], 
                                               command=self.refresh_list, variable=self.user_type_var,
                                               font=("Arial", 13, "bold"), height=35)
        self.tab_menu.pack(side="left", padx=(0, 20))

        # 2. Lọc Rating
        self.rating_filter = ctk.CTkComboBox(control_panel, values=["Tất cả Rating", "⭐ 4.0+", "⭐ 4.5+", "⭐ 4.8+"], width=130)
        self.rating_filter.set("Tất cả Rating")
        self.rating_filter.pack(side="left", padx=5)

        # 3. MỚI: Đổi lọc số chuyến đi thành 5 10 15
        self.trip_filter = ctk.CTkComboBox(control_panel, values=["Tất cả chuyến", "> 5 chuyến", "> 10 chuyến", "> 15 chuyến"], width=130)
        self.trip_filter.set("Tất cả chuyến")
        self.trip_filter.pack(side="left", padx=5)

        ctk.CTkButton(control_panel, text="Lọc dữ liệu", width=100, fg_color="#2ecc71", hover_color="#27ae60", 
                      command=self.refresh_list).pack(side="left", padx=10)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.left_side = ctk.CTkFrame(self.main_container, width=300, fg_color="white", corner_radius=10)
        self.left_side.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.left_side, placeholder_text="Tìm ID...", height=35, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=15, padx=15)
        # Gõ đến đâu tìm đến đó (Tự động tìm trên toàn bộ DB)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())
        
        self.scroll_list = ctk.CTkScrollableFrame(self.left_side, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.right_side = ctk.CTkFrame(self.main_container, fg_color="white", corner_radius=10)
        self.right_side.grid(row=0, column=1, sticky="nsew")
        
        self.show_placeholder()
        self.refresh_list()

    def show_placeholder(self):
        for widget in self.right_side.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.right_side, text="Chọn tài xế hoặc khách hàng để xem chi tiết", text_color="gray").place(relx=0.5, rely=0.5, anchor="center")

    def refresh_list(self, *args):
        user_type = self.user_type_var.get()
        for widget in self.scroll_list.winfo_children(): widget.destroy()

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor(dictionary=True)

        id_col = "Driver ID" if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"
        
        # 1. Lọc Rating
        rate_filter_val = self.rating_filter.get()
        rate_limit = 0
        if "4.8" in rate_filter_val: rate_limit = 4.8
        elif "4.5" in rate_filter_val: rate_limit = 4.5
        elif "4.0" in rate_filter_val: rate_limit = 4.0

        # 2. Lọc Số chuyến (Sửa lỗi thứ tự kiểm tra)
        trip_filter_val = self.trip_filter.get()
        trip_limit = 0
        if "15" in trip_filter_val: trip_limit = 15
        elif "10" in trip_filter_val: trip_limit = 10
        elif "5" in trip_filter_val: trip_limit = 5

        search_text = self.search_var.get().strip()

        # SQL Query
        query = f"""
            SELECT `{id_col}` as uid, AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips
            FROM rides
            WHERE `{id_col}` IS NOT NULL AND `{id_col}` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')
        """
        params = []
        if search_text:
            query += f" AND `{id_col}` LIKE %s"
            params.append(f"%{search_text}%")

        query += f" GROUP BY `{id_col}`"
        
        having_clauses = []
        if rate_limit > 0: having_clauses.append(f"AVG(`{rate_col}`) >= {rate_limit}")
        if trip_limit > 0: having_clauses.append(f"COUNT(*) >= {trip_limit}")
        
        if having_clauses:
            query += " HAVING " + " AND ".join(having_clauses)

        query += " ORDER BY total_trips DESC LIMIT 100"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            ctk.CTkLabel(self.scroll_list, text="❌ Không tìm thấy ai phù hợp", text_color="gray").pack(pady=20)
        else:
            # Hiển thị số lượng tìm thấy thực tế để bạn không thắc mắc "sao ít vậy"
            print(f"DEBUG: Tìm thấy {len(rows)} đối tượng thỏa mãn điều kiện > {trip_limit} chuyến.")
            
            for user in rows:
                uid, stars, trips = user['uid'], user['avg_rate'] or 0, user['total_trips']
                btn = ctk.CTkButton(self.scroll_list, text=f"👤 {uid}\n⭐ {stars:.1f} | 🏁 {trips} chuyến", 
                                    anchor="w", height=55, fg_color="#f8f9fa", text_color="black", 
                                    hover_color="#dfe4ea", command=lambda u=uid: self.display_detail(u, user_type))
                btn.pack(fill="x", pady=4, padx=10)
        
        conn.close()

    # Các hàm display_detail và add_stat_card giữ nguyên như bản hoàn thiện nhất
    # ... (Giống code bạn đã gửi)

    def display_detail(self, uid, user_type):
        for widget in self.right_side.winfo_children(): widget.destroy()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        id_col = "Driver ID" if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"
        
        cursor.execute(f"SELECT AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips, SUM(`Booking Value`) as total_val FROM rides WHERE `{id_col}` = %s", (uid,))
        stats = cursor.fetchone()
        
        cursor.execute(f"SELECT `Booking ID`, `Date`, `Booking Value`, `Booking Status` FROM rides WHERE `{id_col}` = %s ORDER BY `Date` DESC LIMIT 5", (uid,))
        history = cursor.fetchall()
        conn.close()

        color = "#3498db" if user_type == "Drivers" else "#9b59b6"
        header = ctk.CTkFrame(self.right_side, fg_color=color, height=120, corner_radius=10)
        header.pack(fill="x", padx=25, pady=25)
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=uid, font=("Arial", 30, "bold"), text_color="white").place(x=30, y=25)
        ctk.CTkLabel(header, text=f"Account Type: {user_type[:-1]} | Status: Active", text_color="white").place(x=30, y=70)

        kpi_frame = ctk.CTkFrame(self.right_side, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=25)
        self.add_stat_card(kpi_frame, "AVG RATING", f"{stats['avg_rate']:.2f} ⭐", 0)
        self.add_stat_card(kpi_frame, "TOTAL TRIPS", f"{stats['total_trips']:,}", 1)
        self.add_stat_card(kpi_frame, "TOTAL VALUE", f"₹{stats['total_val'] or 0:,.0f}", 2)

        ctk.CTkLabel(self.right_side, text="Lịch sử 5 chuyến đi gần nhất", font=("Arial", 16, "bold")).pack(anchor="w", padx=30, pady=(20, 10))
        table = ttk.Treeview(self.right_side, columns=("ID", "Date", "Price", "Status"), show="headings", height=5)
        for col in table["columns"]: table.heading(col, text=col); table.column(col, width=120, anchor="center")
        table.pack(fill="x", padx=30, pady=10)
        for trip in history: table.insert("", "end", values=(trip['Booking ID'], trip['Date'], f"₹{trip['Booking Value']}", trip['Booking Status']))

    def add_stat_card(self, parent, title, val, col):
        card = ctk.CTkFrame(parent, fg_color="#f8f9fa", border_width=1, border_color="#dee2e6", height=90, width=220)
        card.grid(row=0, column=col, padx=(0, 20), pady=10)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Arial", 11, "bold"), text_color="gray").place(x=15, y=15)
        ctk.CTkLabel(card, text=val, font=("Arial", 22, "bold"), text_color="#2c3e50").place(x=15, y=45)
# --- MODULE 4: RISK ---
class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Risk & Fraud Analysis", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...").pack()

# --- MODULE 5: SETTINGS ---
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="System Settings", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...").pack()

# ================= 3. KHỞI CHẠY APP CHÍNH =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub Admin - Enterprise Edition Final")
        self.geometry("1400x850")
        self.configure(fg_color="#f4f6f9")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {
            "Dashboard": DashboardFrame(self.main_container),
            "Rides": RideManagementFrame(self.main_container),
            "Users": UserProfileFrame(self.main_container),
            "Risk": RiskAnalysisFrame(self.main_container),
            "Settings": SettingsFrame(self.main_container)
        }
        self.show_frame("Dashboard")

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#0f172a", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(sidebar, text="☁️ RideHub", font=("Arial", 26, "bold"), text_color="white").grid(row=0, column=0, pady=(30, 40))

        self.nav_btns = {}
        nav_items = [
            ("Dashboard", "Dashboard"), 
            ("Ride Management", "Rides"),
            ("Driver/Customer Profiles", "Users"),
            ("Cancel & Risk Analysis", "Risk"),
            ("Settings", "Settings")
        ]

        for i, (text, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(sidebar, text=text, anchor="w", fg_color="transparent", text_color="#cbd5e1", 
                                hover_color="#1e293b", font=("Arial", 15), height=50,
                                command=lambda k=key: self.show_frame(k))
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=5)
            self.nav_btns[key] = btn

    def show_frame(self, frame_key):
        for key, btn in self.nav_btns.items():
            if key == frame_key:
                btn.configure(fg_color="#1e293b", text_color="white", font=("Arial", 15, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#cbd5e1", font=("Arial", 15))

        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_key].grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    # BƯỚC QUAN TRỌNG: Gọi hàm kiểm tra và nạp database tự động
    auto_setup_database()
    app = App()
    app.mainloop()


    print("hello world")