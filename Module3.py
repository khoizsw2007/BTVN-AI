import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ================= 1. DATABASE CONFIG =================
DB_CONFIG = {"host": "localhost", "user": "root", "password": "Baolam080907*", "database": "qlud"}

def get_db_connection():
    try: return mysql.connector.connect(**DB_CONFIG)
    except: return None

# ================= 2. MAIN APP (SAAS LAYOUT) =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub SaaS - Strict Data Edition")
        self.geometry("1450x850")
        self.configure(fg_color="#F3F4F6")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(25, 30), padx=20, sticky="w")
        ctk.CTkLabel(logo_frame, text="🚕", font=("Arial", 28)).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" RideHub", font=("Arial", 22, "bold"), text_color="#111827").pack(side="left", padx=5)

        nav_items = [
            ("📊 Dashboard", "disabled"), 
            ("🛣️ Ride Management", "disabled"),
            ("👤 Driver & Customer Profiles", "active"), 
            ("📈 Analytics", "disabled"),
            ("⚙️ Settings", "disabled")
        ]

        for i, (text, status) in enumerate(nav_items, start=1):
            if status == "active":
                btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="#EEF2FF", text_color="#4F46E5", 
                                    font=("Arial", 14, "bold"), height=45, corner_radius=8, hover=False)
            else:
                btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", text_color="#6B7280", 
                                    font=("Arial", 14), height=45, corner_radius=8, hover_color="#F9FAFB")
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=5)

        # --- RIGHT AREA ---
        self.right_area = ctk.CTkFrame(self, fg_color="transparent")
        self.right_area.grid(row=0, column=1, sticky="nsew")
        self.right_area.grid_rowconfigure(1, weight=1)
        self.right_area.grid_columnconfigure(0, weight=1)

        # TOPBAR
        self.topbar = ctk.CTkFrame(self.right_area, height=70, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.topbar.grid(row=0, column=0, sticky="ew")
        
        user_frame = ctk.CTkFrame(self.topbar, fg_color="transparent")
        user_frame.pack(side="right", padx=30, pady=15)
        ctk.CTkLabel(user_frame, text="🔔", font=("Arial", 18), text_color="#6B7280").pack(side="left", padx=15)
        ctk.CTkLabel(user_frame, text="Admin System", font=("Arial", 14, "bold"), text_color="#111827").pack(side="left", padx=10)
        ctk.CTkLabel(user_frame, text="👨‍💻", font=("Arial", 24)).pack(side="left")

        # MAIN CONTENT
        self.main_content = UserProfileFrame(self.right_area)
        self.main_content.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)

# ================= 3. MODULE 3: USER PROFILES =================
class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.current_limit = 30
        self.max_display_limit = 100
        self.tooltip_window = None
        self.tooltip_timer = None
        
        self.setup_flag_table()

        # --- CONTROL PANEL ---
        control_panel = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        control_panel.pack(fill="x", pady=(0, 20))

        top_controls = ctk.CTkFrame(control_panel, fg_color="transparent")
        top_controls.pack(fill="x", padx=15, pady=(15, 5))

        self.user_type_var = ctk.StringVar(value="Drivers")
        self.tab_menu = ctk.CTkSegmentedButton(top_controls, values=["Drivers", "Customers"], 
                                               command=self.reset_and_refresh, variable=self.user_type_var,
                                               font=("Arial", 13, "bold"), height=35,
                                               selected_color="#4F46E5", selected_hover_color="#4338CA")
        self.tab_menu.pack(side="left")

        # Search box with Placeholder
        search_frame = ctk.CTkFrame(top_controls, fg_color="#F3F4F6", corner_radius=8, height=35)
        search_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter ID...", height=35, 
                                         textvariable=self.search_var, fg_color="transparent", border_width=0, 
                                         text_color="#111827", placeholder_text_color="#9CA3AF")
        self.search_entry.pack(fill="x", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.reset_and_refresh())

        bottom_controls = ctk.CTkFrame(control_panel, fg_color="transparent")
        bottom_controls.pack(fill="x", padx=15, pady=(5, 5))

        # Filter UI
        cb_kwargs = {"text_color": "#111827", "font": ("Arial", 12, "bold"), "fg_color": "#F3F4F6", 
                     "button_color": "#F3F4F6", "button_hover_color": "#E5E7EB", "border_width": 0, "corner_radius": 6,
                     "dropdown_fg_color": "#FFFFFF", "dropdown_hover_color": "#F3F4F6", "dropdown_text_color": "#111827",
                     "state": "readonly", "command": self.reset_and_refresh}

        bottom_controls.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.rating_filter = ctk.CTkComboBox(bottom_controls, values=["All Ratings", "⭐ 4.0+", "⭐ 4.5+", "⭐ 4.8+"], **cb_kwargs)
        self.rating_filter.set("All Ratings")
        self.rating_filter.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.trip_filter = ctk.CTkComboBox(bottom_controls, values=["All Trips", "> 3 Trips", "> 5 Trips", "> 10 Trips"], **cb_kwargs)
        self.trip_filter.set("All Trips")
        self.trip_filter.grid(row=0, column=1, padx=5, sticky="ew")

        self.risk_filter = ctk.CTkComboBox(bottom_controls, values=["All Statuses", "🔴 High Risk", "🟠 Warning", "🟢 Safe", "📌 Flagged"], **cb_kwargs)
        self.risk_filter.set("All Statuses")
        self.risk_filter.grid(row=0, column=2, padx=5, sticky="ew")
        
        ctk.CTkButton(bottom_controls, text="🔄 Clear Filters", fg_color="#F3F4F6", hover_color="#E5E7EB", border_width=0,
                      text_color="#4B5563", font=("Arial", 12, "bold"), height=30, corner_radius=6, command=self.clear_filters).grid(row=0, column=3, padx=(5, 0), sticky="ew")

        # Colored Legend
        legend_frame = ctk.CTkFrame(control_panel, fg_color="transparent")
        legend_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(legend_frame, text="💡 Status Legend: ", font=("Arial", 11, "bold"), text_color="#111827").pack(side="left")
        ctk.CTkLabel(legend_frame, text="🔴 High Risk (≥ 40%)", font=("Arial", 11, "bold"), text_color="#EF4444").pack(side="left", padx=(5, 0))
        ctk.CTkLabel(legend_frame, text="   |   ", font=("Arial", 11), text_color="#D1D5DB").pack(side="left")
        ctk.CTkLabel(legend_frame, text="🟠 Warning (20% - 39%)", font=("Arial", 11, "bold"), text_color="#F59E0B").pack(side="left")
        ctk.CTkLabel(legend_frame, text="   |   ", font=("Arial", 11), text_color="#D1D5DB").pack(side="left")
        ctk.CTkLabel(legend_frame, text="🟢 Safe (< 20%)", font=("Arial", 11, "bold"), text_color="#10B981").pack(side="left")

        # --- MAIN CONTAINER ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # LEFT SIDE (LIST)
        self.left_side = ctk.CTkFrame(self.main_container, width=340, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        self.left_side.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self.left_side.grid_propagate(False)
        
        list_header = ctk.CTkFrame(self.left_side, fg_color="transparent")
        list_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(list_header, text="ID List", font=("Arial", 15, "bold"), text_color="#111827").pack(side="left")

        self.scroll_list = ctk.CTkScrollableFrame(self.left_side, fg_color="#FFFFFF", corner_radius=0)
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        # RIGHT SIDE (DETAILS)
        self.right_side = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_side.grid(row=0, column=1, sticky="nsew")
        
        self.refresh_list()

    # ================= LOGIC =================
    def setup_flag_table(self):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS flagged_users (uid VARCHAR(100) PRIMARY KEY)")
            conn.commit()
            conn.close()

    def toggle_flag(self, uid):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flagged_users WHERE uid = %s", (uid,))
        if cursor.fetchone(): cursor.execute("DELETE FROM flagged_users WHERE uid = %s", (uid,))
        else: cursor.execute("INSERT INTO flagged_users (uid) VALUES (%s)", (uid,))
        conn.commit()
        conn.close()
        self.refresh_list()
        self.display_detail(uid, self.user_type_var.get())

    def clear_filters(self):
        self.rating_filter.set("All Ratings")
        self.trip_filter.set("All Trips")
        self.risk_filter.set("All Statuses")
        self.search_var.set("")
        self.reset_and_refresh()

    def reset_and_refresh(self, *args):
        self.current_limit = 30
        self.refresh_list()

    def load_more(self):
        self.current_limit += 30
        if self.current_limit > self.max_display_limit: self.current_limit = self.max_display_limit
        self.refresh_list()

    def refresh_list(self):
        user_type = self.user_type_var.get()
        for widget in self.scroll_list.winfo_children(): widget.destroy()
        self.cancel_tooltip()

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor(dictionary=True)

        id_col = "Driver ID" if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"
        cancel_col = "Cancelled Rides by Driver" if user_type == "Drivers" else "Cancelled Rides by Customer"
        
        cancel_rate_expr = f"COALESCE((SUM(`{cancel_col}`) / NULLIF(SUM(CASE WHEN `Booking Status` != 'No Driver Found' THEN 1 ELSE 0 END), 0)) * 100, 0)"

        cursor.execute("SELECT uid FROM flagged_users")
        flagged_set = {row['uid'] for row in cursor.fetchall()}

        where_clauses = [f"`{id_col}` IS NOT NULL", f"`{id_col}` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')"]
        params = []
        if self.search_var.get().strip():
            where_clauses.append(f"`{id_col}` LIKE %s")
            params.append(f"%{self.search_var.get().strip()}%")
        if "Flagged" in self.risk_filter.get():
            where_clauses.append(f"`{id_col}` IN (SELECT uid FROM flagged_users)")

        query = f"SELECT `{id_col}` as uid, AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips, {cancel_rate_expr} as cancel_rate FROM rides WHERE {' AND '.join(where_clauses)} GROUP BY `{id_col}`"
        
        having_clauses = []
        if "4.8" in self.rating_filter.get(): having_clauses.append(f"AVG(`{rate_col}`) >= 4.8")
        elif "4.5" in self.rating_filter.get(): having_clauses.append(f"AVG(`{rate_col}`) >= 4.5")
        elif "4.0" in self.rating_filter.get(): having_clauses.append(f"AVG(`{rate_col}`) >= 4.0")

        if "10" in self.trip_filter.get(): having_clauses.append("COUNT(*) > 10")
        elif "5" in self.trip_filter.get(): having_clauses.append("COUNT(*) > 5")
        elif "3" in self.trip_filter.get(): having_clauses.append("COUNT(*) > 3")

        risk = self.risk_filter.get()
        if "High Risk" in risk: having_clauses.append(f"{cancel_rate_expr} >= 40")
        elif "Warning" in risk: having_clauses.append(f"{cancel_rate_expr} >= 20 AND {cancel_rate_expr} < 40")
        elif "Safe" in risk: having_clauses.append(f"{cancel_rate_expr} < 20")

        if having_clauses: query += " HAVING " + " AND ".join(having_clauses)
        query += f" ORDER BY total_trips DESC LIMIT {self.current_limit + 1}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        has_more_in_db = len(rows) > self.current_limit
        display_rows = rows[:self.current_limit]

        if not display_rows:
            ctk.CTkLabel(self.scroll_list, text="Empty", text_color="#9CA3AF").pack(pady=20)
        else:
            for user in display_rows:
                uid, stars, trips, c_rate = user['uid'], user['avg_rate'] or 0, user['total_trips'], float(user['cancel_rate'])
                is_flagged = uid in flagged_set
                
                item_frame = ctk.CTkFrame(self.scroll_list, fg_color="#F9FAFB", corner_radius=8, height=65)
                item_frame.pack(fill="x", pady=4, padx=5)
                item_frame.pack_propagate(False)
                
                val_color = "#EF4444" if c_rate >= 40 else ("#F59E0B" if c_rate >= 20 else "#111827")

                # CẬP NHẬT: Xóa vòng tròn đỏ/cam, dùng chung icon 👤
                ctk.CTkLabel(item_frame, text="👤", font=("Arial", 20), text_color="#6B7280").place(x=15, y=18)
                
                # Màu text ID sẽ thể hiện mức độ rủi ro (val_color)
                ctk.CTkLabel(item_frame, text=uid, font=("Arial", 13, "bold"), text_color=val_color).place(x=50, y=10)
                ctk.CTkLabel(item_frame, text=f"⭐ {stars:.1f}  |  🏁 {trips}  |  🚫 {c_rate:.0f}%", font=("Arial", 11), text_color="#6B7280").place(x=50, y=32)

                if is_flagged:
                    # Ghim ở góc phải
                    ctk.CTkLabel(item_frame, text="📌", font=("Arial", 14)).place(relx=0.88, y=10)

                for w in [item_frame] + item_frame.winfo_children():
                    w.bind("<Button-1>", lambda e, u=uid: self.display_detail(u, user_type))
                    w.bind("<Enter>", lambda e, u=uid, s=stars, t=trips, c=c_rate, f=is_flagged: self.schedule_tooltip(e, u, s, t, c, f))
                    w.bind("<Leave>", self.cancel_tooltip)

            if has_more_in_db:
                if self.current_limit < self.max_display_limit:
                    ctk.CTkButton(self.scroll_list, text="Show More", fg_color="#EEF2FF", text_color="#4F46E5", hover_color="#E0E7FF", corner_radius=8, command=self.load_more).pack(pady=10, fill="x")
                else:
                    ctk.CTkButton(self.scroll_list, text="Limit Reached (100)", fg_color="#FEE2E2", text_color="#EF4444", hover_color="#FECACA", corner_radius=8, command=lambda: messagebox.showinfo("Info", "Use filters to narrow down.")).pack(pady=10, fill="x")
            
            self.display_detail(display_rows[0]['uid'], user_type)

    # --- TOOLTIP ---
    def schedule_tooltip(self, event, uid, stars, trips, cancel_rate, is_flagged):
        self.cancel_tooltip()
        self.tooltip_timer = self.after(300, lambda: self.show_tooltip(event.x_root, event.y_root, uid, stars, trips, cancel_rate, is_flagged))

    def show_tooltip(self, x, y, uid, stars, trips, cancel_rate, is_flagged):
        self.cancel_tooltip()
        self.tooltip_window = ctk.CTkToplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.attributes("-topmost", True)
        self.tooltip_window.geometry(f"+{x+15}+{y+15}")
        
        frame = ctk.CTkFrame(self.tooltip_window, fg_color="#111827", corner_radius=8)
        frame.pack(fill="both", expand=True)
        
        flag_text = "📌 FLAGGED\n" if is_flagged else ""
        c_color = "#EF4444" if cancel_rate >= 40 else ("#F59E0B" if cancel_rate >= 20 else "#10B981")

        ctk.CTkLabel(frame, text=f"{flag_text}ID: {uid}", font=("Arial", 12, "bold"), text_color="#FFFFFF").pack(padx=12, pady=(8,2), anchor="w")
        ctk.CTkLabel(frame, text=f"⭐ Avg Rating: {stars:.1f}", font=("Arial", 11), text_color="#D1D5DB").pack(padx=12, anchor="w")
        ctk.CTkLabel(frame, text=f"🏁 Total Trips: {trips}", font=("Arial", 11), text_color="#D1D5DB").pack(padx=12, anchor="w")
        ctk.CTkLabel(frame, text=f"🚫 Cancel Rate: {cancel_rate:.1f}%", font=("Arial", 11, "bold"), text_color=c_color).pack(padx=12, pady=(0,8), anchor="w")

    def cancel_tooltip(self, event=None):
        if self.tooltip_timer: self.after_cancel(self.tooltip_timer); self.tooltip_timer = None
        if self.tooltip_window: self.tooltip_window.destroy(); self.tooltip_window = None

    def display_detail(self, uid, user_type):
        for widget in self.right_side.winfo_children(): widget.destroy()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        id_col = "Driver ID" if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"
        cancel_col = "Cancelled Rides by Driver" if user_type == "Drivers" else "Cancelled Rides by Customer"
        
        cancel_rate_expr = f"COALESCE((SUM(`{cancel_col}`) / NULLIF(SUM(CASE WHEN `Booking Status` != 'No Driver Found' THEN 1 ELSE 0 END), 0)) * 100, 0)"
        cursor.execute(f"SELECT AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips, SUM(`Booking Value`) as total_val, {cancel_rate_expr} as cancel_rate FROM rides WHERE `{id_col}` = %s", (uid,))
        stats = cursor.fetchone()
        
        cursor.execute(f"SELECT `Booking ID`, `Date`, `Booking Value`, `Booking Status` FROM rides WHERE `{id_col}` = %s ORDER BY `Date` DESC LIMIT 5", (uid,))
        history = cursor.fetchall()
        
        cursor.execute("SELECT * FROM flagged_users WHERE uid = %s", (uid,))
        is_flagged = cursor.fetchone() is not None
        conn.close()

        c_rate = float(stats['cancel_rate'])

        # --- 1. HEADER (Gradient Card) ---
        bg_color = "#4F46E5" if user_type == "Drivers" else "#9333EA" 
        header_card = ctk.CTkFrame(self.right_side, fg_color=bg_color, corner_radius=16, height=160)
        header_card.pack(fill="x", pady=(0, 20))
        header_card.pack_propagate(False)

        ava_lbl = ctk.CTkLabel(header_card, text="👤", font=("Arial", 60), fg_color="transparent", width=90, height=90)
        ava_lbl.place(x=20, y=30)

        info_x = 120
        ctk.CTkLabel(header_card, text=uid, font=("Arial", 28, "bold"), text_color="#FFFFFF").place(x=info_x, y=25)

        badge_container = ctk.CTkFrame(header_card, fg_color="transparent")
        badge_container.place(x=info_x, y=68)

        ctk.CTkLabel(badge_container, text="● Active", font=("Arial", 11, "bold"), text_color="#FFFFFF", fg_color="#34D399", corner_radius=10, padx=10, pady=3).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(badge_container, text=user_type[:-1], font=("Arial", 11, "bold"), text_color=bg_color, fg_color="#FFFFFF", corner_radius=10, padx=10, pady=3).pack(side="left", padx=(0, 10))

        if is_flagged:
            ctk.CTkLabel(badge_container, text="📌 Flagged", font=("Arial", 11, "bold"), text_color="#FFFFFF", fg_color="#F59E0B", corner_radius=10, padx=10, pady=3).pack(side="left")

        risk_text = "🚨 High Cancel Rate!" if c_rate >= 40 else ("⚠️ Needs Monitoring" if c_rate >= 20 else "✅ Safe Profile")
        ctk.CTkLabel(header_card, text=f"Status: {risk_text}", font=("Arial", 13), text_color="#E0E7FF").place(x=info_x, y=105)

        btn_flag = ctk.CTkButton(header_card, text="Unflag" if is_flagged else "📌 Flag", 
                                 fg_color="#FFFFFF", text_color="#EF4444" if is_flagged else bg_color, 
                                 hover_color="#F3F4F6", font=("Arial", 12, "bold"), width=120,
                                 command=lambda u=uid: self.toggle_flag(u))
        btn_flag.place(relx=0.96, rely=0.5, anchor="e")

        # --- 2. STATS CARDS ---
        stats_frame = ctk.CTkFrame(self.right_side, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.create_stat_card(stats_frame, "Total Trips", f"{stats['total_trips']}", "🚗", 0)
        self.create_stat_card(stats_frame, "Revenue", f"₹{stats['total_val'] or 0:,.0f}", "💰", 1)
        self.create_stat_card(stats_frame, "Cancel Rate", f"{c_rate:.1f}%", "🚫", 2, is_danger=(c_rate >= 20))
        self.create_stat_card(stats_frame, "Avg Rating", f"{stats['avg_rate']:.1f} ⭐" if stats['avg_rate'] else "N/A", "⭐", 3)

        # --- 3. HISTORY TABLE ---
        table_container = ctk.CTkFrame(self.right_side, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        table_container.pack(fill="both", expand=True)
        
        ctk.CTkLabel(table_container, text="Ride History", font=("Arial", 16, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 5))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#111827", borderwidth=0, rowheight=40, font=("Arial", 12))
        style.configure("Treeview.Heading", background="#F9FAFB", foreground="#6B7280", borderwidth=0, font=('Arial', 11, 'bold'))
        style.map("Treeview", background=[("selected", "#EEF2FF")], foreground=[("selected", "#4F46E5")])

        table = ttk.Treeview(table_container, columns=("ID", "Date", "Price", "Status"), show="headings", height=5)
        for col in table["columns"]: 
            table.heading(col, text=col.upper())
            table.column(col, width=150, anchor="center")
        table.pack(fill="both", expand=True, padx=2, pady=(0, 10))
        
        for trip in history: 
            table.insert("", "end", values=(trip['Booking ID'], trip['Date'], f"₹{trip['Booking Value']}", trip['Booking Status']))

    def create_stat_card(self, parent, title, val, icon, col, is_danger=False):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB", height=100)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col==0 else 15, 0))
        card.grid_propagate(False)
        
        icon_bg = "#FEE2E2" if is_danger else "#EEF2FF"
        icon_fg = "#EF4444" if is_danger else "#4F46E5"
        
        icon_lbl = ctk.CTkLabel(card, text=icon, font=("Arial", 22), fg_color=icon_bg, text_color=icon_fg, width=46, height=46, corner_radius=12)
        icon_lbl.place(relx=0.15, rely=0.5, anchor="w")
        
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.place(relx=0.45, rely=0.5, anchor="w")
        
        ctk.CTkLabel(text_frame, text=title, font=("Arial", 12), text_color="#6B7280").pack(anchor="w")
        val_color = "#EF4444" if is_danger else "#111827"
        ctk.CTkLabel(text_frame, text=val, font=("Arial", 22, "bold"), text_color=val_color).pack(anchor="w", pady=(2, 0))

if __name__ == "__main__":
    app = App()
    app.mainloop()