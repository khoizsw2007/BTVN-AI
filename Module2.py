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
        
        badge_frame = ctk.CTkFrame(header_frame, fg_color="white", corner_radius=20, border_width=1, border_color="#e2e8f0")
        badge_frame.pack(side="right", padx=10, ipady=3, ipadx=5)
        
        # =========================================================
        # [CẬP NHẬT]: Tạo biến self.badge_label để thay đổi chữ linh hoạt
        # Ban đầu chưa lọc gì thì số shown = số total
        # =========================================================
        self.badge_label = ctk.CTkLabel(badge_frame, text=f"{self.total_db_rows:,} rides shown · {self.total_db_rows:,} total", font=("Arial", 13, "bold"), text_color="#475569")
        self.badge_label.pack(padx=12)

    # ==========================================
    # F1 - BẢNG DANH SÁCH VÀ BỘ LỌC THÔNG MINH
    # ==========================================
    def setup_f1_ui(self):
        """
        Khởi tạo giao diện thanh bộ lọc thông minh (F1)
        """
        filter_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        filter_frame.pack(fill="x", pady=(0, 15), ipady=8, ipadx=8)
        
        # 1. Ô tìm kiếm tự do 
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="🔍 Booking ID...", border_color="#e2e8f0", fg_color="#f8fafc", corner_radius=8, text_color="black")
        self.search_entry.pack(side="left", padx=(5, 10), fill="x", expand=True)
        
        # =========================================================
        # [TÍNH NĂNG MỚI]: Nhấn phím Enter trong ô Booking ID để chạy Filter
        # Lambda e: Tự động nuốt sự kiện nhấn phím và gọi thẳng hàm load data.
        # Hàm f1_load_data sẽ tự động đọc gom TẤT CẢ các điều kiện khác đang có.
        # =========================================================
        self.search_entry.bind("<Return>", lambda e: self.f1_load_data())
        
        # 2. Dropdown lọc theo Trạng thái (Đã thêm state="readonly" để cấm gõ phím)
        self.status_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_frame, variable=self.status_var, values=["All", "Completed", "Cancelled", "Incomplete"], width=120, border_color="#e2e8f0", button_color="#f1f5f9", fg_color="white", text_color="black", state="readonly").pack(side="left", padx=5)
        
        # 3. Dropdown lọc theo Loại xe (Đã cập nhật danh sách xe chuẩn & Thêm state="readonly")
        self.vehicle_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(filter_frame, variable=self.vehicle_var, values=["All", "Auto", "Bike", "eBike", "Go Mini", "Go Sedan", "Premier Sedan", "Uber XL"], width=130, border_color="#e2e8f0", button_color="#f1f5f9", fg_color="white", text_color="black", state="readonly").pack(side="left", padx=5)
        
        # 4. Khoảng thời gian: Ô nhập ngày bắt đầu 
        date1_container = ctk.CTkFrame(filter_frame, fg_color="white", corner_radius=6, border_width=1, border_color="#e2e8f0")
        date1_container.pack(side="left", padx=5)
        self.date_start = ctk.CTkEntry(date1_container, placeholder_text="mm/dd/yyyy", width=95, border_width=0, fg_color="transparent", text_color="black")
        self.date_start.pack(side="left", padx=(5, 0), pady=2)
        cal_icon1 = ctk.CTkLabel(date1_container, text="📅", text_color="#64748b", cursor="hand2")
        cal_icon1.pack(side="left", padx=(0, 8))
        cal_icon1.bind("<Button-1>", lambda e: self.open_calendar(self.date_start)) 
        self.date_start.bind("<FocusOut>", self.auto_format_date) 
        
        # 5. Khoảng thời gian: Ô nhập ngày kết thúc 
        date2_container = ctk.CTkFrame(filter_frame, fg_color="white", corner_radius=6, border_width=1, border_color="#e2e8f0")
        date2_container.pack(side="left", padx=5)
        self.date_end = ctk.CTkEntry(date2_container, placeholder_text="mm/dd/yyyy", width=95, border_width=0, fg_color="transparent", text_color="black")
        self.date_end.pack(side="left", padx=(5, 0), pady=2)
        cal_icon2 = ctk.CTkLabel(date2_container, text="📅", text_color="#64748b", cursor="hand2")
        cal_icon2.pack(side="left", padx=(0, 8))
        cal_icon2.bind("<Button-1>", lambda e: self.open_calendar(self.date_end))
        self.date_end.bind("<FocusOut>", self.auto_format_date)
        
        # 6. Các nút hành động
        ctk.CTkButton(filter_frame, text="⧨ Filter", command=self.f1_load_data, width=90, fg_color="#2563eb", hover_color="#1d4ed8", corner_radius=8, font=("Arial", 13, "bold")).pack(side="left", padx=(10, 5))
        ctk.CTkButton(filter_frame, text="↺ Reset", command=self.f1_reset_filters, width=90, fg_color="#f1f5f9", text_color="#475569", hover_color="#e2e8f0", corner_radius=8, font=("Arial", 13, "bold")).pack(side="left", padx=(0, 5))

        # Ép hệ thống nhả Focus khi click ra nền trống
        self.bind("<Button-1>", lambda e: self.focus_set())
        filter_frame.bind("<Button-1>", lambda e: self.focus_set())

    def auto_format_date(self, event):
        """
        [Tính năng thông minh UX/UI] - Tự động Format Ngày Tháng
        Hệ thống tự động kích hoạt khi người dùng gõ xong (vd: gõ "1/1/2024") 
        và click chuột sang ô khác (FocusOut).
        Giúp tự động chèn thêm số 0 thành định dạng chuẩn "01/01/2024".
        """
        entry = event.widget # Lấy ô nhập liệu mà người dùng vừa thao tác
        text = entry.get().strip()
        
        # Chỉ xử lý nếu ô có chữ và không phải là chữ mờ placeholder mặc định
        if text and text != "mm/dd/yyyy":
            try:
                # Dùng thư viện datetime phân tích chuỗi, nó sẽ hiểu "1/1" chính là ngày 1 tháng 1
                valid_date = datetime.datetime.strptime(text, "%m/%d/%Y")
                
                # Xóa chuỗi user vừa gõ và điền lại chuỗi đã được chuẩn hóa (có đủ số 0)
                entry.delete(0, 'end')
                entry.insert(0, valid_date.strftime("%m/%d/%Y"))
            except ValueError:
                # Nếu user gõ sai format bậy bạ (ví dụ gõ chữ cái), hệ thống tạm thời bỏ qua
                pass
    
    def open_calendar(self, entry_widget):
        """Hàm popup hiển thị Lịch dạng Dropdown (Đã FIX đồng bộ ngày cũ đang hiển thị)"""
        from tkcalendar import Calendar
        import datetime # Đảm bảo đã có thư viện datetime

        # Đóng lịch cũ nếu đang mở
        if hasattr(self, "cal_popup") and self.cal_popup.winfo_exists():
            self.cal_popup.destroy()

        self.cal_popup = ctk.CTkToplevel(self)
        self.cal_popup.overrideredirect(True) 
        self.cal_popup.attributes('-topmost', True) 
        
        # Căn tọa độ
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height() + 2
        self.cal_popup.geometry(f"250x220+{x}+{y}")
        
        # =========================================================
        # [FIX BUG ĐỒNG BỘ NGÀY]: Đọc ngày từ ô nhập để set mặc định
        # =========================================================
        current_text = entry_widget.get().strip()
        init_year, init_month, init_day = None, None, None
        
        if current_text and current_text != "mm/dd/yyyy":
            try:
                # Bóc tách chuỗi ra thành Năm, Tháng, Ngày
                d = datetime.datetime.strptime(current_text, "%m/%d/%Y")
                init_year, init_month, init_day = d.year, d.month, d.day
            except ValueError:
                pass # Lỗi thì bỏ qua, dùng ngày hiện tại của máy tính

        # Tham số cấu hình màu sắc chung
        cal_kwargs = {
            "selectmode": 'day', "date_pattern": 'mm/dd/yyyy', "showweeknumbers": False,
            "background": "white", "foreground": "black", "bordercolor": "#e2e8f0",
            "headersbackground": "white", "headersforeground": "black",
            "selectbackground": "#2563eb", "selectforeground": "white",
            "normalbackground": "white", "normalforeground": "black",
            "weekendbackground": "white", "weekendforeground": "black",
            "othermonthbackground": "white", "othermonthforeground": "#cbd5e1"
        }

        # Nếu đọc được ngày cũ -> Ép lịch mở ra ở ngày đó
        if init_year and init_month and init_day:
            cal = Calendar(self.cal_popup, year=init_year, month=init_month, day=init_day, **cal_kwargs)
        else:
            # Nếu ô đang trống -> Mở lịch mặc định (Hôm nay)
            cal = Calendar(self.cal_popup, **cal_kwargs)
                           
        cal.pack(fill="both", expand=True)
        
        def on_date_select(event):
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, cal.get_date())
            self.cal_popup.destroy()
            self.winfo_toplevel().focus_set()
            
        cal.bind("<<CalendarSelected>>", on_date_select)
        
        def handle_focus_out(event):
            def check_focus():
                if hasattr(self, "cal_popup") and self.cal_popup.winfo_exists():
                    focused_widget = self.focus_get()
                    if focused_widget is None or str(self.cal_popup) not in str(focused_widget):
                        self.cal_popup.destroy()
            self.after(50, check_focus)

        self.cal_popup.bind("<FocusOut>", handle_focus_out)
        self.cal_popup.focus_set()

    def setup_action_buttons(self):
        """
        Thanh tính năng nhanh nằm giữa màn hình.
        [CẬP NHẬT]: Đã xóa số đếm và chuẩn bị UI cho tính năng Toggle (Bật/Tắt viền).
        """
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(action_frame, text="Quick filter:", text_color="#64748b", font=("Arial", 13, "bold")).pack(side="left", padx=(0, 10))
        
        # Biến theo dõi xem nút nào đang được bật
        self.active_quick_filter = None 
        # Dictionary lưu trữ các nút để dễ dàng đổi màu viền sau này
        self.qf_btns = {}

        # Chờ lâu -> Long Wait
        btn_cholau = ctk.CTkButton(action_frame, text="Long Wait", command=lambda: self.toggle_quick_filter("Long Wait"), fg_color="#fef2f2", text_color="#ef4444", border_color="#fca5a5", border_width=1, corner_radius=15, width=90)
        btn_cholau.pack(side="left", padx=4)
        self.qf_btns["Long Wait"] = btn_cholau

        # VIP trip (Đã là tiếng Anh)
        btn_vip = ctk.CTkButton(action_frame, text="VIP trip", command=lambda: self.toggle_quick_filter("VIP"), fg_color="#faf5ff", text_color="#a855f7", border_color="#d8b4fe", border_width=1, corner_radius=15, width=90)
        btn_vip.pack(side="left", padx=4)
        self.qf_btns["VIP"] = btn_vip

        # Sự cố -> Incident
        btn_suco = ctk.CTkButton(action_frame, text="Incident", command=lambda: self.toggle_quick_filter("Incident"), fg_color="#f8fafc", text_color="#475569", border_color="#cbd5e1", border_width=1, corner_radius=15, width=80)
        btn_suco.pack(side="left", padx=4)
        self.qf_btns["Incident"] = btn_suco

        # VTAT cao -> High VTAT
        btn_vtat = ctk.CTkButton(action_frame, text="High VTAT", command=lambda: self.toggle_quick_filter("High VTAT"), fg_color="#fff7ed", text_color="#f97316", border_color="#fdba74", border_width=1, corner_radius=15, width=100)
        btn_vtat.pack(side="left", padx=4)
        self.qf_btns["High VTAT"] = btn_vtat
        
        # Các nút F4, F5 giữ nguyên
        self.btn_pattern = ctk.CTkButton(action_frame, text="📈 Find Common Patterns", command=self.f5_find_patterns, width=170, corner_radius=8, border_width=1)
        self.btn_pattern.pack(side="right", padx=4)
        self.btn_compare = ctk.CTkButton(action_frame, text="↹ Compare 2 Rides", command=self.f4_compare_rides, width=140, corner_radius=8, border_width=1)
        self.btn_compare.pack(side="right", padx=4)

    def toggle_quick_filter(self, filter_name):
        """
        [TÍNH NĂNG MỚI] - Xử lý logic Bật/Tắt Quick Filter.
        Nếu click vào nút đang bật -> Tắt nó đi (trả về bảng full).
        Nếu click vào nút mới -> Đậm viền nút đó lên và lọc.
        """
        # Kiểm tra xem có đang click lại vào chính nút đang bật không
        if self.active_quick_filter == filter_name:
            self.active_quick_filter = None  # Tắt filter
        else:
            self.active_quick_filter = filter_name # Bật filter mới

        # Quét qua toàn bộ 4 nút để cập nhật lại Giao diện (Viền và Font chữ)
        normal_font = ("Arial", 13)
        bold_font = ("Arial", 13, "bold")

        for name, btn in self.qf_btns.items():
            if name == self.active_quick_filter:
                # Nút đang Active: Tăng độ dày viền lên 2 và in đậm chữ
                btn.configure(border_width=2, font=bold_font)
            else:
                # Nút Inactive: Trả viền về 1 và chữ bình thường
                btn.configure(border_width=1, font=normal_font)

        # Tiến hành gọi hàm load data với biến filter hiện tại (có thể là tên bộ lọc hoặc None)
        self.f1_load_data(self.active_quick_filter)

    def setup_f1_table(self):
        """Khởi tạo Treeview hiển thị danh sách (Đã đổi CHỌN thành SELECT)"""
        table_container = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        table_container.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=45, borderwidth=0, background="white", foreground="#334155", font=("Arial", 11))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#f8fafc", foreground="#64748b", borderwidth=0, padding=10)
        style.map("Treeview", background=[("selected", "white")], foreground=[("selected", "#0f172a")])
        
        scrollbar = ttk.Scrollbar(table_container)
        scrollbar.pack(side="right", fill="y")
        
        # Đổi chữ CHỌN thành SELECT
        self.table = ttk.Treeview(table_container, columns=("SELECT", "Booking ID", "Date / Time", "ROUTE", "Vehicle", "Price", "VTAT", "Status", "STORY"), show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.table.yview)
        
        # Đổi key CHỌN thành SELECT trong dict độ rộng
        columns_width = {"SELECT": 60, "Booking ID": 110, "Date / Time": 130, "ROUTE": 250, "Vehicle": 90, "Price": 80, "VTAT": 80, "Status": 120, "STORY": 60}
        for col, w in columns_width.items():
            self.table.heading(col, text=col.upper())
            self.table.column(col, width=w, anchor="center" if col not in ["ROUTE", "Date / Time", "Booking ID"] else "w")
            
        self.table.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.table.bind("<ButtonRelease-1>", self.on_table_click)

    def on_table_click(self, event):
        """Xử lý việc Tích Checkbox và Click mở Story"""
        region = self.table.identify_region(event.x, event.y)
        if region == "cell":
            col = self.table.identify_column(event.x) 
            item_id = self.table.identify_row(event.y) 
            
            # Cột #1 là cột CHỌN (Checkbox)
            if col == '#1': 
                current_values = list(self.table.item(item_id, 'values'))
                if current_values[0] == '☐':
                    current_values[0] = '☑'
                else:
                    current_values[0] = '☐'
                self.table.item(item_id, values=current_values)
                self.update_button_states() 
                
            # [CẬP NHẬT]: Cột #9 hiện tại là cột STORY (Con mắt)
            elif col == '#9': 
                self.f3_show_trip_story(item_id)

    def update_button_states(self, event=None):
        """Logic kiểm soát trạng thái Tắt/Bật của F4 và F5 dựa vào số lượng Checkbox được tích"""
        # Quét xem có bao nhiêu dòng mang dấu tích ☑
        selected_items = [item for item in self.table.get_children() if self.table.item(item)['values'][0] == '☑']
        selected_count = len(selected_items)
        
        if selected_count == 2:
            self.btn_compare.configure(state="normal", fg_color="white", border_color="#bfdbfe", text_color="#2563eb")
            self.btn_pattern.configure(state="normal", fg_color="white", border_color="#e9d5ff", text_color="#9333ea")
        elif selected_count >= 3:
            self.btn_compare.configure(state="disabled", fg_color="transparent", border_color="#e2e8f0", text_color="#94a3b8")
            self.btn_pattern.configure(state="normal", fg_color="white", border_color="#e9d5ff", text_color="#9333ea")
        else:
            self.btn_compare.configure(state="disabled", fg_color="transparent", border_color="#e2e8f0", text_color="#94a3b8")
            self.btn_pattern.configure(state="disabled", fg_color="transparent", border_color="#e2e8f0", text_color="#94a3b8")

    def f1_reset_filters(self):
        """Xóa trắng bộ lọc và tải lại từ đầu (F1)"""
        # Dọn dẹp Text
        self.search_entry.delete(0, 'end')
        self.date_start.delete(0, 'end')
        self.date_end.delete(0, 'end')
        
        # Trả Dropdown về mặc định "All"
        self.status_var.set("All")
        self.vehicle_var.set("All")
        
        # [CẬP NHẬT] Tắt các viền đậm của Quick Filter
        self.active_quick_filter = None
        for btn in self.qf_btns.values():
            btn.configure(border_width=1, font=("Arial", 13))
        
        # Reset hiển thị Placeholder
        self.search_entry.configure(placeholder_text="🔍 Booking ID...")
        self.date_start.configure(placeholder_text="mm/dd/yyyy")
        self.date_end.configure(placeholder_text="mm/dd/yyyy")
        
        self.winfo_toplevel().focus_set() 
        self.f1_load_data()

    def f1_load_data(self, risk_tag_filter=None):
        """Hàm Lõi: Nhận điều kiện lọc từ F1/F2, build SQL và định dạng dữ liệu hiển thị (Date, Route, Price)."""
        import datetime # [FIX LỖI]: Đưa import datetime lên đầu hàm

        self.focus_set() 
        if not self.search_entry.get().strip():
            self.search_entry.configure(placeholder_text="🔍 Booking ID...")
        if not self.date_start.get().strip():
            self.date_start.configure(placeholder_text="mm/dd/yyyy")
        if not self.date_end.get().strip():
            self.date_end.configure(placeholder_text="mm/dd/yyyy")
            
        # Xóa dữ liệu cũ trên bảng
        for item in self.table.get_children():
            self.table.delete(item)
            
        conn = get_db_connection()
        if not conn: 
            messagebox.showerror("Error", "Database connection failed!")
            return

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM rides WHERE 1=1"
        params = []
        
        # 1. Lọc chữ (Search)
        search_text = self.search_entry.get().strip()
        if search_text:
            query += " AND (`Booking ID` LIKE %s OR `Customer ID` LIKE %s)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
            
        # 2. Lọc Trạng thái (Status)
        if self.status_var.get() != "All":
            if self.status_var.get() == "Cancelled":
                query += " AND `Booking Status` LIKE %s"
                params.append("%Cancel%")
            else:
                query += " AND `Booking Status` LIKE %s"
                params.append(f"%{self.status_var.get()}%")
            
        # 3. Lọc Loại xe (Vehicle)
        if self.vehicle_var.get() != "All":
            query += " AND `Vehicle Type` = %s"
            params.append(self.vehicle_var.get())
            
        # 4. Lọc Ngày tháng (Date Range)
        def parse_and_format_date(date_str, entry_widget):
            if date_str and date_str != "mm/dd/yyyy":
                try:
                    d = datetime.datetime.strptime(date_str, "%m/%d/%Y")
                    entry_widget.delete(0, 'end')
                    entry_widget.insert(0, d.strftime("%m/%d/%Y"))
                    return d.strftime("%Y-%m-%d") 
                except ValueError:
                    return None
            return None

        sql_start = parse_and_format_date(self.date_start.get().strip(), self.date_start)
        sql_end = parse_and_format_date(self.date_end.get().strip(), self.date_end)

        if sql_start:
            query += " AND `Date` >= %s"
            params.append(sql_start)
        if sql_end:
            query += " AND `Date` <= %s"
            params.append(sql_end)

        # 5. Lọc F2 Quick Filter
        active_tag = getattr(self, "active_quick_filter", None)

        if active_tag == "Long Wait":
            query += " AND `Avg VTAT` > 12 AND `Booking Status` LIKE %s"
            params.append("%Cancel%")
        elif active_tag == "VIP":
            query += " AND `Booking Value` > 600"
        elif active_tag == "Incident":
            query += " AND `Booking Status` LIKE %s"
            params.append("%Incomplete%")
        elif active_tag == "High VTAT":
            query += " AND `Avg VTAT` > 15"
            
        # LIMIT 100 để chống giật lag
        query += " LIMIT 100" 
            
        # 6. Chạy SQL và in kết quả
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall() 
            
            # Cập nhật số lượng hiển thị (Badge)
            shown_count = len(rows)
            self.badge_label.configure(text=f"{shown_count:,} rides shown · {self.total_db_rows:,} total")
            
            for row in rows:
                # =========================================================
                # [ĐỊNH DẠNG FRONT-END: Date, Route, Price, Status]
                # =========================================================
                
                # 6.1 Định dạng Date / Time (ĐÃ BỎ GIÂY)
                try:
                    raw_date = datetime.datetime.strptime(str(row.get('Date')), '%Y-%m-%d')
                    # Cắt chuỗi Time chỉ lấy 5 ký tự đầu (vd: "18:02:28" -> "18:02")
                    raw_time = str(row.get('Time'))[:5] 
                    formatted_dt = raw_date.strftime('%b %d, %Y') + f" | {raw_time}"
                except:
                    # Backup lỡ lỗi
                    formatted_dt = f"{row.get('Date')} {str(row.get('Time'))[:5]}"

                # 6.2 Định dạng Route (Gắn thêm km)
                dist = row.get('Ride Distance', 0)
                route_info = f"{str(row.get('Pickup Location'))[:12]} ➔ {str(row.get('Drop Location'))[:12]} [{dist} km]"

                # 6.3 Định dạng Price (Thêm dấu $)
                price_val = f"${int(row.get('Booking Value', 0))}"

                # 6.4 Định dạng Status (Gắn icon, BỎ tô màu dòng)
                status = str(row.get('Booking Status', ''))
                if status == "Completed":
                    status_display = "⦾ Completed"
                elif "Cancel" in status:
                    status_display = "ⓧ Cancelled"
                else:
                    status_display = "⚠ Incomplete"

                # Đổ dữ liệu vào bảng
                self.table.insert("", "end", values=(
                    "☐",  
                    f"#{row.get('Booking ID')}", 
                    formatted_dt, 
                    route_info, 
                    row.get('Vehicle Type'),
                    price_val, 
                    f"{int(row.get('Avg VTAT', 0))}m", 
                    status_display, 
                    "👁"  
                ))
                
        except Exception as e:
            print("Error Load:", e) 
        finally:
            conn.close()
            self.update_button_states()

    # ==========================================
    # F2 - RISK TAG: NHÃN RỦI RO TỰ ĐỘNG
    # ==========================================
# ==========================================
    # F3 - TRIP STORY: BẢN HOÀN THIỆN (MULTIPLE TAGS + ALIGN CARDS)
    # ==========================================
    def f3_show_trip_story(self, item_id=None):
        """Tái hiện hành trình chi tiết, đa thẻ rủi ro, thời gian gộp vào thẻ 1 để align khung."""
        import re
        import datetime
        if not item_id: return
        
        # 1. Lấy Booking ID từ bảng
        item_table = self.table.item(item_id)['values']
        booking_id_raw = str(item_table[1]).replace("#", "") 
        
        # 2. Truy vấn Database để lấy toàn bộ dữ liệu gốc
        conn = get_db_connection()
        row = None
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rides WHERE `Booking ID` = %s", (booking_id_raw,))
            row = cursor.fetchone()
            conn.close()
        
        if not row: return

        # Khởi tạo cửa sổ phụ
        win = ctk.CTkToplevel(self)
        win.title(f"Trip Journey - {item_table[1]}")
        win.geometry("550")
        win.configure(fg_color="#f8fafc") 
        win.attributes('-topmost', True)

        # =========================================================
        # PHẦN HEADER: HIỂN THỊ ĐA THẺ RỦI RO (MULTIPLE TAGS)
        # =========================================================
        header_f = ctk.CTkFrame(win, fg_color="transparent")
        header_f.pack(fill="x", padx=30, pady=(25, 15))
        
        # Khung chứa các Badges
        badge_f = ctk.CTkFrame(header_f, fg_color="transparent")
        badge_f.pack(anchor="w")
        
        # Tag ID mặc định
        id_tag = ctk.CTkFrame(badge_f, fg_color="#eff6ff", corner_radius=6, border_width=1, border_color="#bfdbfe")
        id_tag.pack(side="left")
        ctk.CTkLabel(id_tag, text=f"#{row.get('Booking ID', '')}", font=("Arial", 11, "bold"), text_color="#2563eb").pack(padx=8, pady=2)
        
        # Logic tính toán và hiển thị TẤT CẢ các rủi ro thỏa mãn
        price_val = float(row.get('Booking Value', 0)) if row.get('Booking Value') else 0.0
        vtat_val = float(row.get('Avg VTAT', 0)) if row.get('Avg VTAT') else 0.0
        status_raw = str(row.get('Booking Status', ''))

        # Danh sách các thẻ rủi ro sẽ hiển thị
        risks = []
        if price_val > 600:
            risks.append(("• VIP Trip", "#fef9c3", "#fde047", "#854d0e")) # Vàng
        if vtat_val > 12 and "Cancel" in status_raw:
            risks.append(("• Long Wait", "#fecaca", "#fca5a5", "#b91c1c")) # Đỏ
        if vtat_val > 15:
            risks.append(("• High VTAT", "#fed7aa", "#fdba74", "#c2410c")) # Cam
        if "Incomplete" in status_raw:
            risks.append(("• Incident", "#f1f5f9", "#cbd5e1", "#334155")) # Xám

        # Vẽ từng thẻ rủi ro nếu có
        for text, bg, border, txt_color in risks:
            r_tag = ctk.CTkFrame(badge_f, fg_color=bg, corner_radius=12, border_width=1, border_color=border)
            r_tag.pack(side="left", padx=(10, 0))
            ctk.CTkLabel(r_tag, text=text, font=("Arial", 11, "bold"), text_color=txt_color).pack(padx=10, pady=2)

        # Tiêu đề và thông tin phụ
        ctk.CTkLabel(header_f, text="Trip Story Timeline", font=("Arial", 22, "bold"), text_color="#1e293b").pack(anchor="w", pady=(10, 2))
        subtitle = f"{row.get('Date', '')}  •  {row.get('Pickup Location', '')} ➔ {row.get('Drop Location', '')}"
        ctk.CTkLabel(header_f, text=subtitle, font=("Arial", 13), text_color="#94a3b8").pack(anchor="w")

        # =========================================================
        # PHẦN THÂN: TIMELINE CARD
        # =========================================================
        body_f = ctk.CTkFrame(win, fg_color="transparent")
        body_f.pack(fill="both", expand=True, padx=30)

        # Lấy giờ ở đây luôn để nhét vào khung đầu tiên
        time_str = str(row.get('Time', ''))[:5] if row.get('Time') else ""

        steps = [
            {"title": "Booking Confirmed", "desc": f"Via app • Payment: {row.get('Payment Method', 'N/A')} • Time: {time_str}", "icon": "✓", "color": "#10b981"},
            {"title": "Driver Assigned", "desc": f"Driver ID: {str(row.get('Customer ID', ''))} • Vehicle: {row.get('Vehicle Type', '')}", "icon": "🚗", "color": "#3b82f6"},
            {"title": f"Wait Time • VTAT: {int(vtat_val)} min", "desc": "Driver is approaching pickup point.", "icon": "⏳", "color": "#f59e0b" if vtat_val > 8 else "#3b82f6"},
            {"title": "Trip Started", "desc": f"{row.get('Pickup Location', '')} ➔ {row.get('Drop Location', '')} ({row.get('Ride Distance', 0)} km)", "icon": "📍", "color": "#6366f1"},
        ]
        
        if "Completed" in status_raw:
            steps.append({"title": "Trip Finished", "desc": f"Completed {row.get('Ride Distance', 0)}km • Price: ${int(price_val)} • Rating: {row.get('Customer Rating', 0)}★", "icon": "✓", "color": "#10b981"})
        else:
            steps.append({"title": "Trip Interrupted", "desc": f"Status: {status_raw} • Distance: {row.get('Ride Distance', 0)}km", "icon": "✕", "color": "#ef4444"})

        for i, step in enumerate(steps):
            item_f = ctk.CTkFrame(body_f, fg_color="transparent")
            item_f.pack(fill="x", pady=10)
            
            icon_f = ctk.CTkFrame(item_f, fg_color="transparent", width=40)
            icon_f.pack(side="left", fill="y")
            
            circle = ctk.CTkFrame(icon_f, width=32, height=32, corner_radius=16, fg_color="white", border_width=2, border_color=step['color'])
            circle.pack(pady=(0, 0))
            circle.pack_propagate(False)
            ctk.CTkLabel(circle, text=step['icon'], font=("Arial", 14, "bold"), text_color=step['color']).place(relx=0.5, rely=0.5, anchor="center")

            # Khung Card sẽ bung ra tận cùng bên phải do không còn cái time_label nào cản đường
            card = ctk.CTkFrame(item_f, fg_color="white", corner_radius=10, border_width=1, border_color="#e2e8f0")
            card.pack(side="left", fill="x", expand=True, padx=(15, 0))
            
            if i == 2 and vtat_val > 8:
                card.configure(border_color="#fde68a", fg_color="#fffbeb") 
                ctk.CTkLabel(card, text=f"⚠️ High wait detected! Driver arrived {int(vtat_val)} min after booking.", font=("Arial", 11, "italic"), text_color="#9a3412").pack(anchor="w", padx=15, pady=(2, 8))

            ctk.CTkLabel(card, text=step['title'], font=("Arial", 13, "bold"), text_color="#1e293b").pack(anchor="w", padx=15, pady=(8, 0))
            ctk.CTkLabel(card, text=step['desc'], font=("Arial", 12), text_color="#64748b").pack(anchor="w", padx=15, pady=(0, 8))

        # =========================================================
        # =========================================================
        # PHẦN CUỐI: SYSTEM AUTO-COMMENT (ĐÓNG KHUNG CHUẨN UI)
        # =========================================================
        # Khung Card bo góc, màu nền xanh dương siêu nhạt, viền mỏng
        # pady=(5, 20) giúp ép sát cái khung này lên phía trên, xóa bỏ khoảng trống thừa
        comment_f = ctk.CTkFrame(win, fg_color="#f4f8ff", corner_radius=12, border_width=1, border_color="#dbeafe")
        # Thêm thuộc tính side="top" để nó không bị rớt xuống đáy
        comment_f.pack(side="top", fill="x", padx=30, pady=(5, 20), ipady=5) 
        
        # Tiêu đề System Auto-Comment (Thêm icon tia sét, đổi sang màu xanh đậm)
        ctk.CTkLabel(comment_f, text="⚡ SYSTEM AUTO-COMMENT", font=("Arial", 12, "bold"), text_color="#2563eb").pack(anchor="w", padx=20, pady=(12, 0))
        
        # Thuật toán phân tích
        avg_sys = 6.0
        if vtat_val > avg_sys * 1.5:
            diff = int(vtat_val - avg_sys)
            # Thêm icon đồng hồ báo động cho trường hợp bị trễ
            analysis = f"⏰ Elevated wait time ({int(vtat_val)} min). Driver took {diff} min longer than the {int(avg_sys)} min zone benchmark. This is a major risk factor."
        else:
            # Thêm icon check xanh cho trường hợp an toàn
            analysis = "✅ Operational metrics are within safe system limits. No anomalies detected."
            
        # Nội dung nhận xét (Bỏ in nghiêng để dễ đọc hơn, căn lề chuẩn)
        ctk.CTkLabel(comment_f, text=analysis, font=("Arial", 13), text_color="#475569", wraplength=440, justify="left").pack(anchor="w", padx=20, pady=(5, 12))

    # ==========================================
    # F4 - SMART COMPARE: SO SÁNH SONG SONG
    # ==========================================
    def f4_compare_rides(self):
        """
        So sánh 2 chuyến xe và tự động tô màu Đỏ/Xanh nếu các chỉ số lệch nhau > 20%
        [CẬP NHẬT]: Điều chỉnh logic lấy dữ liệu do đã thêm cột Checkbox và đổi cách chọn.
        """
        # 1. Lấy danh sách các dòng đã được đánh dấu tích ☑ ở cột đầu tiên
        selected = [item for item in self.table.get_children() if self.table.item(item)['values'][0] == '☑']
        
        # Chỉ thực hiện so sánh khi người dùng chọn đúng 2 dòng, nếu không thì dừng hàm
        if len(selected) != 2: 
            return
            
        # 2. Lấy giá trị (values) của 2 dòng được chọn
        itemA = self.table.item(selected[0])['values']
        itemB = self.table.item(selected[1])['values']
        
        # 3. Tạo cửa sổ popup mới
        win = ctk.CTkToplevel(self)
        win.title("Smart Ride Comparison")
        win.geometry("650x450")
        
        # In tiêu đề 2 cột hiển thị (RIDE A và RIDE B)
        ctk.CTkLabel(win, text="RIDE A", font=("Arial", 14, "bold"), text_color="#2563eb").grid(row=0, column=1, padx=20, pady=15)
        ctk.CTkLabel(win, text="RIDE B", font=("Arial", 14, "bold"), text_color="#9333ea").grid(row=0, column=2, padx=20, pady=15)
        
        # 4. Danh sách các tiêu chí cần in ra để so sánh
        metrics = ["Mã Chuyến", "Ngày giờ", "Tuyến đường", "Loại Xe", "Cước phí (Price)", "Thời gian đợi (VTAT)", "Trạng Thái"]
        
        import re # Thư viện hỗ trợ bóc tách số
        
        # Vòng lặp duyệt qua từng tiêu chí để in ra giao diện
        for i, metric in enumerate(metrics):
            # In tên tiêu chí ở cột đầu tiên (Cột 0) - Căn lề trái (sticky="w")
            ctk.CTkLabel(win, text=metric, font=("Arial", 12, "bold"), text_color="#475569").grid(row=i+1, column=0, padx=20, pady=8, sticky="w")
            
            # [QUAN TRỌNG]: Lấy giá trị tương ứng từ itemA và itemB
            # Phải cộng thêm 1 (i+1) vì vị trí số 0 hiện tại là cột Checkbox, dữ liệu thật bắt đầu từ vị trí số 1
            valA, valB = str(itemA[i+1]), str(itemB[i+1])
            colorA = colorB = "#0f172a" # Màu chữ mặc định là màu đen/xám đậm
            
            # 5. Logic highlight (tô màu) thông minh: Nếu chênh lệch > 20% cho Price và VTAT
            if metric in ["Cước phí (Price)", "Thời gian đợi (VTAT)"]:
                # Dùng thư viện regex (re) để bóc tách con số ra khỏi chuỗi (VD: "₹680" -> 680.0, "12m" -> 12.0)
                numA = float(re.findall(r'\d+', valA)[0]) if re.findall(r'\d+', valA) else 0.0
                numB = float(re.findall(r'\d+', valB)[0]) if re.findall(r'\d+', valB) else 0.0
                
                # Tính toán chênh lệch %
                if numA > 0 and numB > 0:
                    if numA > numB * 1.2: 
                        colorA, colorB = "#ef4444", "#16a34a" # A cao hơn B > 20% -> A bị tô màu Đỏ (tệ), B Xanh (tốt)
                    elif numB > numA * 1.2:
                        colorA, colorB = "#16a34a", "#ef4444" # Ngược lại, B cao hơn A -> B Đỏ, A Xanh

            # 6. In kết quả của Ride A và Ride B lên lưới grid (cột 1 và cột 2) cùng với màu sắc đã tính toán
            ctk.CTkLabel(win, text=valA, text_color=colorA, font=("Arial", 12)).grid(row=i+1, column=1, padx=20, pady=8)
            ctk.CTkLabel(win, text=valB, text_color=colorB, font=("Arial", 12)).grid(row=i+1, column=2, padx=20, pady=8)

    # ==========================================
    # ==========================================
    # F5 - BULK PATTERN: PHÁT HIỆN ĐIỂM CHUNG
    # ==========================================
    def f5_find_patterns(self):
        """
        Giả lập thuật toán đếm (tương tự GROUP BY trong SQL) trên các chuyến xe được chọn để tìm ra quy luật (Pattern).
        [CẬP NHẬT]: Điều chỉnh logic đếm dựa trên dấu tích Checkbox và cập nhật lại Index cột.
        """
        # 1. Lấy danh sách các dòng đã được đánh dấu tích ☑ ở cột đầu tiên (Cột CHỌN)
        selected = [item for item in self.table.get_children() if self.table.item(item)['values'][0] == '☑']
        
        # Nếu chưa chọn dòng nào thì không làm gì cả
        if not selected: 
            return
            
        # 2. Tạo cửa sổ popup mới
        win = ctk.CTkToplevel(self)
        win.title("Common Pattern Analysis")
        win.geometry("500x400")
        
        # In tiêu đề số lượng chuyến xe đang được phân tích
        ctk.CTkLabel(win, text=f"Phân tích nhanh {len(selected)} chuyến xe", font=("Arial", 16, "bold"), text_color="#0f172a").pack(pady=20)
        
        # 3. Khởi tạo các biến để lưu trữ số lượng đếm được
        status_counts = {"Completed": 0, "Cancelled": 0, "Incomplete": 0} # Đếm trạng thái
        vehicle_counts = {} # Đếm loại xe (Dùng dictionary rỗng vì có nhiều loại xe khác nhau)
        
        # 4. Vòng lặp duyệt qua từng dòng đã chọn để tiến hành đếm
        for s in selected:
            item = self.table.item(s)['values']
            
            # [QUAN TRỌNG]: Lấy dữ liệu với Index mới (Do đã chèn cột Checkbox vào vị trí số 0)
            status = str(item[7])  # item[7] là cột Status
            vehicle = str(item[4]) # item[4] là cột Vehicle
            
            # Đếm Trạng thái
            if "Completed" in status: 
                status_counts["Completed"] += 1
            elif "Cancel" in status: 
                status_counts["Cancelled"] += 1
            else: 
                status_counts["Incomplete"] += 1
                
            # Đếm Loại xe: Hàm .get(vehicle, 0) nghĩa là nếu xe này chưa có trong từ điển thì cho số đếm mặc định là 0, sau đó + 1
            vehicle_counts[vehicle] = vehicle_counts.get(vehicle, 0) + 1
            
        # 5. Tìm phần tử phổ biến nhất (Loại xe được dùng nhiều nhất)
        # Hàm max() kết hợp với tham số key=vehicle_counts.get sẽ lôi ra cái tên xe có số đếm lớn nhất
        top_vehicle = max(vehicle_counts, key=vehicle_counts.get)
        
        # 6. Vẽ giao diện kết quả phân tích
        # Tạo một cái khung trắng chứa kết quả
        f = ctk.CTkFrame(win, fg_color="white", corner_radius=10, border_color="#e2e8f0", border_width=1)
        f.pack(fill="x", padx=40, pady=10, ipady=10)
        
        # In các con số đếm được ra màn hình kèm màu sắc xanh/đỏ/cam cho trực quan
        ctk.CTkLabel(f, text=f"• Hoàn thành: {status_counts['Completed']}", text_color="#16a34a", font=("Arial", 13, "bold")).pack(pady=5)
        ctk.CTkLabel(f, text=f"• Bị Hủy: {status_counts['Cancelled']}", text_color="#ef4444", font=("Arial", 13, "bold")).pack(pady=5)
        ctk.CTkLabel(f, text=f"• Sự cố: {status_counts['Incomplete']}", text_color="#f97316", font=("Arial", 13, "bold")).pack(pady=5)
        
        # 7. Câu kết luận tự động của hệ thống
        conclusion = f"Hệ thống phát hiện quy luật: Trong tập dữ liệu này, loại xe được sử dụng nhiều nhất là '{top_vehicle}' ({vehicle_counts[top_vehicle]}/{len(selected)} chuyến)."
        
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