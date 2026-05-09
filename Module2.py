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

from tkcalendar import DateEntry # Nhớ thêm dòng này ở đầu file nếu chưa có
import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox

# Giả định có hàm get_db_connection, bạn nhớ giữ nguyên hàm này của bạn ở trên nhé
# def get_db_connection(): ...

from tkcalendar import DateEntry 
import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox
import re # Thư viện hỗ trợ bóc tách số để tính toán cho F4

# ================= 2. MODULE 2: RIDE MANAGEMENT =================
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#f8fafc")
        
        self.total_db_rows = 0
        self.stats = {"cho_lau": 0, "vip": 0, "su_co": 0, "vtat_cao": 0}
        
        # Lấy số liệu đếm từ DB trước khi vẽ UI
        self.fetch_database_stats()
        
        # Khởi tạo giao diện theo từng Module con
        self.setup_header()
        self.setup_f1_ui()
        self.setup_action_buttons()
        self.setup_f1_table()
        
        # Load toàn bộ dữ liệu lần đầu (KHÔNG LIMIT)
        self.f1_load_data()
        
        # Cập nhật trạng thái nút bấm F4, F5 ban đầu (Xám chìm)
        self.update_button_states()

    def fetch_database_stats(self):
        """Chạy ngầm để đếm tổng số dòng và số liệu cho Quick Filters (F2)"""
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) as total FROM rides")
            self.total_db_rows = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as c FROM rides WHERE `Avg VTAT` > 12 AND `Booking Status` LIKE '%Cancel%'")
            self.stats["cho_lau"] = cursor.fetchone()['c']
            
            cursor.execute("SELECT COUNT(*) as c FROM rides WHERE `Booking Value` > 600")
            self.stats["vip"] = cursor.fetchone()['c']
            
            cursor.execute("SELECT COUNT(*) as c FROM rides WHERE `Booking Status` LIKE '%Incomplete%'")
            self.stats["su_co"] = cursor.fetchone()['c']
            
            cursor.execute("SELECT COUNT(*) as c FROM rides WHERE `Avg VTAT` > 15")
            self.stats["vtat_cao"] = cursor.fetchone()['c']
        except Exception as e:
            print("Lỗi đếm số liệu:", e)
        finally:
            conn.close()

    def setup_header(self):
        """Khởi tạo Tiêu đề và Badge Total"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_f = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(title_f, text="🚕 Ride Management Hub", font=ctk.CTkFont(family="Arial", size=24, weight="bold"), text_color="#0f172a").pack(anchor="w")
        ctk.CTkLabel(title_f, text="Monitor, filter, and deep-dive every trip in the system", font=("Arial", 13), text_color="#94a3b8").pack(anchor="w")
        
        # Badge góc phải: Chỉ hiện TOTAL theo đúng Figma
        badge_frame = ctk.CTkFrame(header_frame, fg_color="white", corner_radius=20, border_width=1, border_color="#e2e8f0")
        badge_frame.pack(side="right", padx=10, ipady=3, ipadx=5)
        ctk.CTkLabel(badge_frame, text=f"{self.total_db_rows:,} total", font=("Arial", 13, "bold"), text_color="#475569").pack(padx=12)

    # ==========================================
    # F1 - BẢNG DANH SÁCH VÀ BỘ LỌC THÔNG MINH
    # ==========================================
    def setup_f1_ui(self):
        """Khởi tạo thanh bộ lọc y hệt Figma Ảnh 2 (Có Reset, Custom Date, Dàn đều)"""
        filter_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        filter_frame.pack(fill="x", pady=(0, 15), ipady=8, ipadx=8)
        
        # ĐÃ FIX: Bỏ textvariable, dùng trực tiếp biến search_entry để placeholder hiển thị 100%
        # Ô Tìm kiếm
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="🔍 Booking ID...", border_color="#e2e8f0", fg_color="#f8fafc", corner_radius=8, text_color="black")
        self.search_entry.pack(side="left", padx=(5, 10), fill="x", expand=True)
        
        # Dropdowns
        self.status_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_frame, variable=self.status_var, values=["All", "Completed", "Cancelled", "Incomplete"], width=120, border_color="#e2e8f0", button_color="#f1f5f9", fg_color="white", text_color="black").pack(side="left", padx=5)
        
        self.vehicle_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_frame, variable=self.vehicle_var, values=["All", "Sedan", "SUV", "Auto", "Bike", "Luxury"], width=110, border_color="#e2e8f0", button_color="#f1f5f9", fg_color="white", text_color="black").pack(side="left", padx=5)
        
        # Bộ chọn lịch Date 1
        date1_container = ctk.CTkFrame(filter_frame, fg_color="white", corner_radius=6, border_width=1, border_color="#e2e8f0")
        date1_container.pack(side="left", padx=5)
        self.date_start = ctk.CTkEntry(date1_container, placeholder_text="mm/dd/yyyy", width=95, border_width=0, fg_color="transparent", text_color="black")
        self.date_start.pack(side="left", padx=(5, 0), pady=2)
        cal_icon1 = ctk.CTkLabel(date1_container, text="📅", text_color="#64748b", cursor="hand2")
        cal_icon1.pack(side="left", padx=(0, 8))
        cal_icon1.bind("<Button-1>", lambda e: self.open_calendar(self.date_start))
        
        # Bộ chọn lịch Date 2
        date2_container = ctk.CTkFrame(filter_frame, fg_color="white", corner_radius=6, border_width=1, border_color="#e2e8f0")
        date2_container.pack(side="left", padx=5)
        self.date_end = ctk.CTkEntry(date2_container, placeholder_text="mm/dd/yyyy", width=95, border_width=0, fg_color="transparent", text_color="black")
        self.date_end.pack(side="left", padx=(5, 0), pady=2)
        cal_icon2 = ctk.CTkLabel(date2_container, text="📅", text_color="#64748b", cursor="hand2")
        cal_icon2.pack(side="left", padx=(0, 8))
        cal_icon2.bind("<Button-1>", lambda e: self.open_calendar(self.date_end))
        
        # Nút Filter & Reset
        ctk.CTkButton(filter_frame, text="⧨ Filter", command=self.f1_load_data, width=90, fg_color="#2563eb", hover_color="#1d4ed8", corner_radius=8, font=("Arial", 13, "bold")).pack(side="left", padx=(10, 5))
        ctk.CTkButton(filter_frame, text="↺ Reset", command=self.f1_reset_filters, width=90, fg_color="#f1f5f9", text_color="#475569", hover_color="#e2e8f0", corner_radius=8, font=("Arial", 13, "bold")).pack(side="left", padx=(0, 5))
    def open_calendar(self, entry_widget):
        """Hàm popup hiển thị Lịch khi bấm vào icon 📅"""
        from tkcalendar import Calendar
        top = ctk.CTkToplevel(self)
        top.title("Chọn ngày")
        top.geometry("280x280")
        top.attributes('-topmost', True) 
        
        cal = Calendar(top, selectmode='day', date_pattern='mm/dd/yyyy', showweeknumbers=False)
        cal.pack(pady=10, padx=10, fill="both", expand=True)
        
        def set_date():
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, cal.get_date())
            top.destroy()
            
        ctk.CTkButton(top, text="Xác nhận", command=set_date, fg_color="#2563eb").pack(pady=(0, 10))

    def setup_action_buttons(self):
        """Thanh tính năng nhanh nằm giữa màn hình"""
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(action_frame, text="Quick filter:", text_color="#64748b", font=("Arial", 13, "bold")).pack(side="left", padx=(0, 10))
        
        # Quick filters (Hiển thị số liệu động từ DB)
        ctk.CTkButton(action_frame, text=f"Chờ lâu  {self.stats['cho_lau']}", command=lambda: self.f1_load_data("Chờ lâu"), fg_color="#fef2f2", text_color="#ef4444", border_color="#fca5a5", border_width=1, corner_radius=15, width=100).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text=f"VIP trip  {self.stats['vip']}", command=lambda: self.f1_load_data("VIP"), fg_color="#faf5ff", text_color="#a855f7", border_color="#d8b4fe", border_width=1, corner_radius=15, width=100).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text=f"Sự cố  {self.stats['su_co']}", command=lambda: self.f1_load_data("Sự cố"), fg_color="#f8fafc", text_color="#475569", border_color="#cbd5e1", border_width=1, corner_radius=15, width=90).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text=f"VTAT cao  {self.stats['vtat_cao']}", command=lambda: self.f1_load_data("VTAT cao"), fg_color="#fff7ed", text_color="#f97316", border_color="#fdba74", border_width=1, corner_radius=15, width=110).pack(side="left", padx=4)
        
        # Nút tính năng F4, F5 (Đã xóa Export CSV)
        self.btn_pattern = ctk.CTkButton(action_frame, text="📈 Find Common Patterns", command=self.f5_find_patterns, width=170, corner_radius=8, border_width=1)
        self.btn_pattern.pack(side="right", padx=4)
        
        self.btn_compare = ctk.CTkButton(action_frame, text="↹ Compare 2 Rides", command=self.f4_compare_rides, width=140, corner_radius=8, border_width=1)
        self.btn_compare.pack(side="right", padx=4)

    def setup_f1_table(self):
        """Khởi tạo Treeview hiển thị danh sách chuyến xe"""
        table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        table_container.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=45, borderwidth=0, background="white", foreground="#334155", font=("Arial", 11))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#f8fafc", foreground="#64748b", borderwidth=0, padding=10)
        style.map("Treeview", background=[("selected", "#e2e8f0")], foreground=[("selected", "#0f172a")])
        
        scrollbar = ttk.Scrollbar(table_container)
        scrollbar.pack(side="right", fill="y")
        
        self.table = ttk.Treeview(table_container, columns=("Booking ID", "Date / Time", "ROUTE", "Vehicle", "Price", "VTAT", "Status", "RISK TAG", "STORY"), show="headings", yscrollcommand=scrollbar.set, selectmode="extended")
        scrollbar.config(command=self.table.yview)
        
        columns_width = {"Booking ID": 110, "Date / Time": 130, "ROUTE": 250, "Vehicle": 90, "Price": 80, "VTAT": 80, "Status": 120, "RISK TAG": 110, "STORY": 60}
        for col, w in columns_width.items():
            self.table.heading(col, text=col.upper())
            self.table.column(col, width=w, anchor="center" if col not in ["ROUTE", "Date / Time", "Booking ID"] else "w")
            
        self.table.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Bắt sự kiện click để điều khiển F3, F4, F5
        self.table.bind("<<TreeviewSelect>>", self.update_button_states)
        self.table.bind("<Double-1>", self.f3_show_trip_story) # Kích đúp mở F3

    def update_button_states(self, event=None):
        """Logic kiểm soát trạng thái Tắt/Bật của F4 và F5 dựa vào số lượng dòng được chọn"""
        selected_count = len(self.table.selection())
        
        if selected_count == 2:
            # Chọn 2 dòng: Bật cả Compare (Xanh) và Pattern (Tím)
            self.btn_compare.configure(state="normal", fg_color="white", border_color="#bfdbfe", text_color="#2563eb")
            self.btn_pattern.configure(state="normal", fg_color="white", border_color="#e9d5ff", text_color="#9333ea")
        elif selected_count >= 3:
            # Chọn >=3 dòng: Tắt Compare (Xám), Bật Pattern (Tím)
            self.btn_compare.configure(state="disabled", fg_color="transparent", border_color="#e2e8f0", text_color="#94a3b8")
            self.btn_pattern.configure(state="normal", fg_color="white", border_color="#e9d5ff", text_color="#9333ea")
        else:
            # Chọn <2 dòng: Tắt cả 2
            self.btn_compare.configure(state="disabled", fg_color="transparent", border_color="#e2e8f0", text_color="#94a3b8")
            self.btn_pattern.configure(state="disabled", fg_color="transparent", border_color="#e2e8f0", text_color="#94a3b8")

    def f1_reset_filters(self):
        """Xóa trắng bộ lọc và tải lại từ đầu"""
        self.search_entry.delete(0, 'end') # ĐÃ FIX: Xóa trắng text trong ô Search
        self.status_var.set("All")
        self.vehicle_var.set("All")
        self.date_start.delete(0, 'end')
        self.date_end.delete(0, 'end')
        
        # Tự động trỏ con trỏ chuột ra chỗ khác để Placeholder hiện lại
        self.focus_set() 
        self.f1_load_data()

    def f1_load_data(self, risk_tag_filter=None):
        """
        Truy vấn DB và load toàn bộ dữ liệu (KHÔNG LIMIT). 
        """
        for item in self.table.get_children():
            self.table.delete(item)
            
        conn = get_db_connection()
        if not conn: 
            messagebox.showerror("Lỗi", "Không kết nối được Database!")
            return

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM rides WHERE 1=1"
        params = []
        
        # ĐÃ FIX: Thay self.search_var.get() bằng self.search_entry.get()
        search_text = self.search_entry.get().strip()
        if search_text:
            query += " AND (`Booking ID` LIKE %s OR `Customer ID` LIKE %s)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
            
        if self.status_var.get() != "All":
            query += " AND `Booking Status` = %s"
            params.append(self.status_var.get())
        if self.vehicle_var.get() != "All":
            query += " AND `Vehicle Type` = %s"
            params.append(self.vehicle_var.get())
            
        try:
            cursor.execute(query, params)
            for row in cursor.fetchall():
                route = f"{str(row.get('Pickup Location', ''))[:10]} ➔ {str(row.get('Drop Location', ''))[:10]}"
                vtat = float(row.get('Avg VTAT', 0))
                price = float(row.get('Booking Value', 0))
                status = str(row.get('Booking Status', ''))
                
                # F2 - Đính kèm nhãn tự động
                risk_tag = self.f2_assign_risk_tag(vtat, price, status)
                if risk_tag_filter and risk_tag.replace("• ", "") != risk_tag_filter:
                    continue

                status_icon = "⦾ Completed" if status == "Completed" else "ⓧ Cancelled" if "Cancel" in status else "⚠ Incomplete"

                self.table.insert("", "end", values=(
                    f"#{row.get('Booking ID')}", 
                    row.get('Date'), 
                    route, 
                    row.get('Vehicle Type', 'Auto'),
                    f"₹{int(price)}", 
                    f"{int(vtat)}m", 
                    status_icon, 
                    risk_tag,
                    "👁"  
                ))
        except Exception as e:
            print("Lỗi Load:", e)
        finally:
            conn.close()
            self.update_button_states()

    # ==========================================
    # F2 - RISK TAG: NHÃN RỦI RO TỰ ĐỘNG
    # ==========================================
    def f2_assign_risk_tag(self, vtat, price, status):
        """Hệ thống đánh giá tự động dựa trên quy tắc nghiệp vụ[cite: 4]"""
        if vtat > 12 and "Cancel" in status: 
            return "• Chờ lâu"
        elif price > 600: 
            return "• VIP"
        elif "Incomplete" in status: 
            return "• Sự cố"
        elif vtat > 15: 
            return "• VTAT cao"
        return ""

    # ==========================================
    # F3 - TRIP STORY: TÁI HIỆN HÀNH TRÌNH
    # ==========================================
    def f3_show_trip_story(self, event=None):
        """Dựng lại dòng thời gian của chuyến đi khi người dùng nhấp đúp vào dòng[cite: 4]"""
        selected = self.table.selection()
        if not selected: return
        item = self.table.item(selected[0])['values']
        
        win = ctk.CTkToplevel(self)
        win.title("Trip Story Timeline")
        win.geometry("500x550")
        
        ctk.CTkLabel(win, text=f"Timeline Chuyến {item[0]}", font=("Arial", 18, "bold"), text_color="#0f172a").pack(pady=(20, 10))
        
        # Dựng Layout Timeline mô phỏng
        timeline_f = ctk.CTkFrame(win, fg_color="transparent")
        timeline_f.pack(fill="x", padx=40, pady=10)
        
        steps = [
            ("Booking Confirmed", f"Nhận đơn từ hệ thống. Phương tiện yêu cầu: {item[3]}"),
            (f"Wait Time: {item[5]}", "Tài xế đang di chuyển đến điểm đón."),
            ("Trip Started", f"Lộ trình: {item[2]}"),
            ("Trip Finished / Cancelled", f"Trạng thái: {item[6]} | Tổng tiền: {item[4]}")
        ]
        
        for title, desc in steps:
            step_f = ctk.CTkFrame(timeline_f, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0")
            step_f.pack(fill="x", pady=5)
            ctk.CTkLabel(step_f, text=title, font=("Arial", 13, "bold"), text_color="#2563eb").pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(step_f, text=desc, text_color="#64748b").pack(anchor="w", padx=10, pady=(0,5))
            
        # Logic Auto-comment thông minh (Không dùng AI)[cite: 4]
        vtat_val = float(str(item[5]).replace('m', ''))
        if vtat_val > 10:
            comment = f"Thời gian chờ xe ({vtat_val} phút) vượt ngưỡng trung bình của hệ thống. Đây là rủi ro chính dẫn đến trải nghiệm kém hoặc hủy chuyến."
        else:
            comment = "Các chỉ số vận hành của chuyến đi (thời gian chờ, loại xe) nằm trong mức an toàn."
            
        ctk.CTkLabel(win, text="SYSTEM AUTO-COMMENT", font=("Arial", 12, "bold"), text_color="#9333ea").pack(pady=(20, 5))
        ctk.CTkLabel(win, text=comment, wraplength=400, text_color="#475569").pack()

    # ==========================================
    # F4 - SMART COMPARE: SO SÁNH SONG SONG
    # ==========================================
    def f4_compare_rides(self):
        """So sánh 2 chuyến và tự động tô màu Đỏ/Xanh nếu lệch > 20%[cite: 4]"""
        selected = self.table.selection()
        if len(selected) != 2: return
            
        itemA = self.table.item(selected[0])['values']
        itemB = self.table.item(selected[1])['values']
        
        win = ctk.CTkToplevel(self)
        win.title("Smart Ride Comparison")
        win.geometry("650x450")
        
        ctk.CTkLabel(win, text="RIDE A", font=("Arial", 14, "bold"), text_color="#2563eb").grid(row=0, column=1, padx=20, pady=15)
        ctk.CTkLabel(win, text="RIDE B", font=("Arial", 14, "bold"), text_color="#9333ea").grid(row=0, column=2, padx=20, pady=15)
        
        metrics = ["Mã Chuyến", "Ngày giờ", "Tuyến đường", "Loại Xe", "Cước phí (Price)", "Thời gian đợi (VTAT)", "Trạng Thái"]
        for i, metric in enumerate(metrics):
            ctk.CTkLabel(win, text=metric, font=("Arial", 12, "bold"), text_color="#475569").grid(row=i+1, column=0, padx=20, pady=8, sticky="w")
            
            valA, valB = str(itemA[i]), str(itemB[i])
            colorA = colorB = "#0f172a" # Màu đen mặc định
            
            # Logic highlight nếu lệch > 20% cho Price và VTAT[cite: 4]
            if metric in ["Cước phí (Price)", "Thời gian đợi (VTAT)"]:
                # Dùng regex bóc tách số khỏi chuỗi (VD: "₹680" -> 680.0, "12m" -> 12.0)
                numA = float(re.findall(r'\d+', valA)[0]) if re.findall(r'\d+', valA) else 0.0
                numB = float(re.findall(r'\d+', valB)[0]) if re.findall(r'\d+', valB) else 0.0
                
                if numA > 0 and numB > 0:
                    if numA > numB * 1.2: 
                        colorA, colorB = "#ef4444", "#16a34a" # A cao hơn 20% -> A đỏ (tệ), B xanh (tốt)
                    elif numB > numA * 1.2:
                        colorA, colorB = "#16a34a", "#ef4444"

            ctk.CTkLabel(win, text=valA, text_color=colorA, font=("Arial", 12)).grid(row=i+1, column=1, padx=20, pady=8)
            ctk.CTkLabel(win, text=valB, text_color=colorB, font=("Arial", 12)).grid(row=i+1, column=2, padx=20, pady=8)

    # ==========================================
    # F5 - BULK PATTERN: PHÁT HIỆN ĐIỂM CHUNG
    # ==========================================
    def f5_find_patterns(self):
        """Giả lập thuật toán đếm (GROUP BY) trên các chuyến xe được chọn để tìm Pattern[cite: 4]"""
        selected = self.table.selection()
        if not selected: return
            
        win = ctk.CTkToplevel(self)
        win.title("Common Pattern Analysis")
        win.geometry("500x400")
        
        ctk.CTkLabel(win, text=f"Phân tích nhanh {len(selected)} chuyến xe", font=("Arial", 16, "bold"), text_color="#0f172a").pack(pady=20)
        
        # Đếm (Gom nhóm) các tiêu chí[cite: 4]
        status_counts = {"Completed": 0, "Cancelled": 0, "Incomplete": 0}
        vehicle_counts = {}
        
        for s in selected:
            item = self.table.item(s)['values']
            status = item[6]
            vehicle = item[3]
            
            if "Completed" in status: status_counts["Completed"] += 1
            elif "Cancel" in status: status_counts["Cancelled"] += 1
            else: status_counts["Incomplete"] += 1
                
            vehicle_counts[vehicle] = vehicle_counts.get(vehicle, 0) + 1
            
        # Tìm phần tử phổ biến nhất
        top_vehicle = max(vehicle_counts, key=vehicle_counts.get)
        
        # Vẽ giao diện kết quả phân tích
        f = ctk.CTkFrame(win, fg_color="white", corner_radius=10, border_color="#e2e8f0", border_width=1)
        f.pack(fill="x", padx=40, pady=10, ipady=10)
        
        ctk.CTkLabel(f, text=f"• Hoàn thành: {status_counts['Completed']}", text_color="#16a34a", font=("Arial", 13, "bold")).pack(pady=5)
        ctk.CTkLabel(f, text=f"• Bị Hủy: {status_counts['Cancelled']}", text_color="#ef4444", font=("Arial", 13, "bold")).pack(pady=5)
        ctk.CTkLabel(f, text=f"• Sự cố: {status_counts['Incomplete']}", text_color="#f97316", font=("Arial", 13, "bold")).pack(pady=5)
        
        # Câu kết luận tự động[cite: 4]
        conclusion = f"Hệ thống phát hiện pattern: Trong tập dữ liệu này, loại xe được sử dụng nhiều nhất là '{top_vehicle}' ({vehicle_counts[top_vehicle]}/{len(selected)} chuyến)."
        ctk.CTkLabel(win, text="SYSTEM CONCLUSION", font=("Arial", 12, "bold"), text_color="#9333ea").pack(pady=(20, 5))
        ctk.CTkLabel(win, text=conclusion, wraplength=400, text_color="#475569").pack()
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