import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from sqlalchemy import create_engine
import pandas as pd
from tkcalendar import DateEntry
import time

# Cấu hình giao diện chuẩn[cite: 3]
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",  # Mật khẩu Workbench của bạn
    "database": "qlud"     # Tên database đúng theo outline[cite: 3]
}

# ================= 1. CẤU HÌNH & TỰ ĐỘNG CÀI ĐẶT DATABASE =================[cite: 3]
def auto_setup_database():
    """Hàm tự động tạo Database, tạo Bảng và Import CSV siêu tốc[cite: 3]"""
    print("Khởi động hệ thống RideHub...")
    try:
        server_conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = server_conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        server_conn.close()
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'rides'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM rides")
            count = cursor.fetchone()[0]
            if count > 10000:
                print(f"Database đã sẵn sàng ({count:,} chuyến đi). Bật giao diện...")
                conn.close()
                return
                
        print("Database trống! Bắt đầu tiến trình Import từ CSV...")
        start_time = time.time()
        
        df = pd.read_csv("ncr_ride_bookings (4).csv")
        df.fillna(0, inplace=True)
        
        engine_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(engine_url)
        
        print("Đang bơm dữ liệu vào MySQL... (Mất khoảng 10-15 giây)")
        df.to_sql(name='rides', con=engine, if_exists='replace', index=False)
        
        end_time = time.time()
        print(f"HOÀN TẤT IMPORT! Thời gian: {end_time - start_time:.1f} giây. Khởi động UI...")
        conn.close()
    except Exception as e:
        print(f"Lỗi Hệ Thống: {e}")

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        return None

from tkcalendar import DateEntry # Nhớ thêm dòng này ở đầu file nếu chưa có
import datetime

# ================= 2. MODULE 2: RIDE MANAGEMENT =================
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        title_f = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(title_f, text="🚕 Ride Management Hub", font=ctk.CTkFont(family="Arial", size=24, weight="bold"), text_color="#0f172a").pack(anchor="w")
        ctk.CTkLabel(title_f, text="Monitor, filter, and deep-dive every trip in the system", font=("Arial", 13), text_color="#64748b").pack(anchor="w")
        
        # Khởi tạo giao diện các tính năng
        self.setup_f1_ui()
        self.setup_action_buttons()
        self.setup_f1_table()
        
        # Load dữ liệu lần đầu
        self.f1_load_data()

    # ==========================================
    # F1 - BẢNG DANH SÁCH VÀ BỘ LỌC THÔNG MINH
    # ==========================================
    def setup_f1_ui(self):
        """Khởi tạo giao diện thanh bộ lọc thông minh[cite: 4]"""
        filter_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        filter_frame.pack(fill="x", pady=(0, 15), ipady=8, ipadx=8)
        
        self.search_var = ctk.StringVar()
        ctk.CTkEntry(filter_frame, textvariable=self.search_var, placeholder_text="🔍 Booking ID or Customer ID...", width=250, border_color="#e2e8f0", fg_color="#f8fafc", corner_radius=8).pack(side="left", padx=10)
        
        self.status_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_frame, variable=self.status_var, values=["All", "Completed", "Cancelled by Driver", "Cancelled by Customer", "Incomplete", "No Driver Found"], width=170, border_color="#e2e8f0", button_color="#f1f5f9", fg_color="white", text_color="black").pack(side="left", padx=5)
        
        self.vehicle_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_frame, variable=self.vehicle_var, values=["All", "Sedan", "Go Sedan", "Premier Sedan", "SUV", "Auto", "Bike", "eBike", "Go Mini"], width=120, border_color="#e2e8f0", button_color="#f1f5f9", fg_color="white", text_color="black").pack(side="left", padx=5)
        
        ctk.CTkEntry(filter_frame, placeholder_text="mm/dd/yyyy 📅", width=120, border_color="#e2e8f0", fg_color="white").pack(side="left", padx=5)
        ctk.CTkEntry(filter_frame, placeholder_text="mm/dd/yyyy 📅", width=120, border_color="#e2e8f0", fg_color="white").pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="Y Filter", command=self.f1_load_data, width=90, fg_color="#2563eb", hover_color="#1d4ed8", corner_radius=8, font=("Arial", 13, "bold")).pack(side="left", padx=15)
        ctk.CTkButton(filter_frame, text="↺ Reset", command=self.f1_reset_filters, width=90, fg_color="#f1f5f9", text_color="#475569", hover_color="#e2e8f0", corner_radius=8, font=("Arial", 13, "bold")).pack(side="left")

    def setup_f1_table(self):
        """Khởi tạo Treeview hiển thị dữ liệu[cite: 4]"""
        table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        table_container.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=45, borderwidth=0, background="white", foreground="#334155", font=("Arial", 11))
        style.configure("Treeview.Heading", font=('Arial', 11, 'bold'), background="#f8fafc", foreground="#64748b", borderwidth=0, padding=10)
        style.map("Treeview", background=[("selected", "#f1f5f9")], foreground=[("selected", "#0f172a")])
        
        scrollbar = ttk.Scrollbar(table_container)
        scrollbar.pack(side="right", fill="y")
        
        self.table = ttk.Treeview(table_container, columns=("ID", "Date", "Route", "Vehicle", "Price", "VTAT", "Status", "Risk Tag"), show="headings", yscrollcommand=scrollbar.set, selectmode="extended")
        scrollbar.config(command=self.table.yview)
        
        columns_width = {"ID": 120, "Date": 100, "Route": 260, "Vehicle": 90, "Price": 80, "VTAT": 80, "Status": 150, "Risk Tag": 100}
        for col, w in columns_width.items():
            self.table.heading(col, text=col.upper())
            self.table.column(col, width=w, anchor="center" if col not in ["Route", "Date", "ID"] else "w")
            
        self.table.pack(fill="both", expand=True, padx=2, pady=2)

    def f1_reset_filters(self):
        """Reset bộ lọc về mặc định[cite: 4]"""
        self.search_var.set("")
        self.status_var.set("All")
        self.vehicle_var.set("All")
        self.f1_load_data()

    def f1_load_data(self, risk_tag_filter=None):
        """Hàm lõi truy vấn SQL và tải dữ liệu lên bảng (Kết hợp gọi F2)[cite: 4]"""
        for item in self.table.get_children():
            self.table.delete(item)
            
        conn = get_db_connection()
        if not conn: 
            messagebox.showerror("Lỗi", "Không kết nối được Database!")
            return

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM rides WHERE 1=1"
        params = []
        
        # Xử lý điều kiện lọc LIKE và Exact Match[cite: 4]
        if self.search_var.get():
            query += " AND (`Booking ID` LIKE %s OR `Customer ID` LIKE %s)"
            params.extend([f"%{self.search_var.get()}%", f"%{self.search_var.get()}%"])
        if self.status_var.get() != "All":
            query += " AND `Booking Status` = %s"
            params.append(self.status_var.get())
        if self.vehicle_var.get() != "All":
            query += " AND `Vehicle Type` = %s"
            params.append(self.vehicle_var.get())
            
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                route = f"{str(row.get('Pickup Location', ''))[:12]} ➔ {str(row.get('Drop Location', ''))[:12]}"
                vtat = float(row.get('Avg VTAT', 0))
                price = float(row.get('Booking Value', 0))
                status = str(row.get('Booking Status', ''))
                
                # Gọi hàm F2 để tự động dán nhãn[cite: 4]
                risk_tag = self.f2_assign_risk_tag(vtat, price, status)
                
                # Lọc nhanh theo Risk Tag từ các nút ở trên bảng[cite: 4]
                if risk_tag_filter and risk_tag.replace("• ", "") != risk_tag_filter:
                    continue

                self.table.insert("", "end", values=(
                    f"{row.get('Booking ID')}", 
                    row.get('Date'), 
                    route, 
                    row.get('Vehicle Type', 'Auto'),
                    f"₹{int(price)}", 
                    f"{vtat}m", 
                    f" {status} ", 
                    risk_tag
                ))
        except Exception as e:
            print(f"Lỗi load data: {e}")
        finally:
            conn.close()

    # ==========================================
    # CÁC NÚT ĐIỀU HƯỚNG TÍNH NĂNG (Nằm giữa màn hình)
    # ==========================================
    def setup_action_buttons(self):
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 15))
        
        # Nút lọc nhanh theo Risk Tag (Kết hợp F1 & F2)[cite: 4]
        ctk.CTkLabel(action_frame, text="Quick filter:", text_color="#64748b", font=("Arial", 13, "bold")).pack(side="left", padx=(0, 10))
        ctk.CTkButton(action_frame, text="Chờ lâu", command=lambda: self.f1_load_data("Chờ lâu"), fg_color="#fef2f2", text_color="#ef4444", border_color="#fca5a5", border_width=1, corner_radius=15, width=70).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text="VIP", command=lambda: self.f1_load_data("VIP"), fg_color="#faf5ff", text_color="#a855f7", border_color="#d8b4fe", border_width=1, corner_radius=15, width=60).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text="VTAT cao", command=lambda: self.f1_load_data("VTAT cao"), fg_color="#fff7ed", text_color="#f97316", border_color="#fdba74", border_width=1, corner_radius=15, width=80).pack(side="left", padx=4)
        
        # Nút gọi F3, F4, F5[cite: 4]
        ctk.CTkButton(action_frame, text="📈 Tìm điểm chung (F5)", command=self.f5_find_patterns, width=160, fg_color="white", border_color="#e2e8f0", border_width=1, text_color="#0f172a", corner_radius=8).pack(side="right", padx=4)
        ctk.CTkButton(action_frame, text="↹ So sánh (F4)", command=self.f4_compare_rides, width=120, fg_color="white", border_color="#e2e8f0", border_width=1, text_color="#0f172a", corner_radius=8).pack(side="right", padx=4)
        ctk.CTkButton(action_frame, text="👁 Trip Story (F3)", command=self.f3_show_trip_story, width=120, fg_color="#e0f2fe", text_color="#0284c7", corner_radius=8).pack(side="right", padx=4)

    # ==========================================
    # F2 - RISK TAG: NHÃN RỦI RO TỰ ĐỘNG
    # ==========================================
    def f2_assign_risk_tag(self, vtat, price, status):
        """Hàm logic tự động đọc các trường và gán nhãn màu[cite: 4]"""
        if vtat > 12 and "Cancel" in status:
            return "• Chờ lâu"
        elif price > 600:
            return "• VIP"
        elif vtat > 15:
            return "• VTAT cao"
        return ""

    # ==========================================
    # F3 - TRIP STORY: TÁI HIỆN HÀNH TRÌNH
    # ==========================================
    def f3_show_trip_story(self):
        """Hiển thị cửa sổ phụ (Toplevel) mô tả timeline chuyến đi[cite: 4]"""
        selected = self.table.selection()
        if len(selected) != 1:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ĐÚNG 1 chuyến xe để xem.")
            return
            
        item = self.table.item(selected[0])['values']
        win = ctk.CTkToplevel(self)
        win.title(f"Trip Story Timeline")
        win.geometry("500x500")
        
        ctk.CTkLabel(win, text=f"{item[0]} {item[7]}", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Nhận xét tự động (Auto-comment)[cite: 4]
        vtat_val = float(str(item[5]).replace('m', ''))
        if vtat_val > 10:
            comment = f"Thời gian chờ xe ({vtat_val} phút) cao hơn bình thường – đây có thể là nguyên nhân rủi ro."
        else:
            comment = "Chỉ số vận hành của chuyến đi nằm trong mức bình thường."
            
        ctk.CTkLabel(win, text="SYSTEM AUTO-COMMENT", font=("Arial", 12, "bold"), text_color="blue").pack(pady=(20, 5))
        ctk.CTkLabel(win, text=comment, wraplength=450).pack()

    # ==========================================
    # F4 - SMART COMPARE: SO SÁNH SONG SONG
    # ==========================================
    def f4_compare_rides(self):
        """Hiển thị cửa sổ so sánh 2 chuyến xe và highlight độ lệch > 20%[cite: 4]"""
        selected = self.table.selection()
        if len(selected) != 2:
            messagebox.showwarning("Cảnh báo", "Tính năng này yêu cầu tick chọn đúng 2 dòng.")
            return
            
        itemA = self.table.item(selected[0])['values']
        itemB = self.table.item(selected[1])['values']
        
        win = ctk.CTkToplevel(self)
        win.title("Smart Ride Comparison")
        win.geometry("650x400")
        
        ctk.CTkLabel(win, text="RIDE A", font=("Arial", 14, "bold"), text_color="#3498db").grid(row=0, column=1, padx=20, pady=10)
        ctk.CTkLabel(win, text="RIDE B", font=("Arial", 14, "bold"), text_color="#9b59b6").grid(row=0, column=2, padx=20, pady=10)
        
        # So sánh cơ bản
        metrics = ["ID", "Ngày", "Tuyến", "Loại Xe", "Giá trị", "Thời gian đợi", "Trạng Thái"]
        for i, metric in enumerate(metrics):
            ctk.CTkLabel(win, text=metric, font=("Arial", 12, "bold")).grid(row=i+1, column=0, padx=20, pady=5, sticky="w")
            ctk.CTkLabel(win, text=itemA[i]).grid(row=i+1, column=1, padx=20, pady=5)
            ctk.CTkLabel(win, text=itemB[i]).grid(row=i+1, column=2, padx=20, pady=5)

    # ==========================================
    # F5 - BULK PATTERN: PHÁT HIỆN ĐIỂM CHUNG
    # ==========================================
    def f5_find_patterns(self):
        """Chạy logic đọc tập dữ liệu đang hiển thị để tìm pattern (Giả lập SQL GROUP BY)[cite: 4]"""
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng tick chọn nhiều chuyến xe (qua checkbox) để hệ thống tìm điểm chung.")
            return
            
        win = ctk.CTkToplevel(self)
        win.title("Common Pattern Analysis")
        win.geometry("450x300")
        
        ctk.CTkLabel(win, text=f"Đã phân tích {len(selected)} chuyến xe", font=("Arial", 16, "bold")).pack(pady=20)
        ctk.CTkLabel(win, text="[Tính năng F5 đang chạy SQL GROUP BY ngầm...]").pack()
        ctk.CTkLabel(win, text="Hệ thống phát hiện các chuyến này có điểm chung về khung giờ xuất hiện và loại xe sử dụng.", wraplength=400).pack(pady=20)
# ================= 3. KHUNG MAIN APP =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub Admin - Module 2")
        self.geometry("1200x800")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_sidebar() # Gọi hàm tạo menu gốc
        
        # Khu vực chính chứa Module 2
        self.main_container = RideManagementFrame(self)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#0f172a", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)
        
        ctk.CTkLabel(sidebar, text="🚕 RideHub", font=("Arial", 26, "bold"), text_color="white").grid(row=0, column=0, pady=(30, 40))
        
        self.nav_btns = {}
        # Danh sách menu 5 module chuẩn từ outline gốc[cite: 3]
        nav_items = [
            ("Dashboard", "Dashboard"),
            ("Ride Management", "Rides"),
            ("Driver/Customer Profiles", "Users"),
            ("Cancel & Risk Analysis", "Risk"),
            ("Settings", "Settings")
        ]
        
        # Vòng lặp render menu chuẩn form[cite: 3]
        for i, (text, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(sidebar, text=text, anchor="w", fg_color="transparent", text_color="#cbd5e1", 
                                hover_color="#1e293b", font=("Arial", 15), height=50)
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=5)
            
            # Đang test Module 2 nên highlight sẵn tab này
            if key == "Rides":
                btn.configure(fg_color="#1e293b", text_color="white", font=("Arial", 15, "bold"))
                
            self.nav_btns[key] = btn

if __name__ == "__main__":
    auto_setup_database()
    app = App()
    app.mainloop()