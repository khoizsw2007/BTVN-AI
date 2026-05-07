import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
import math
from datetime import datetime, timedelta

# Standard UI Configuration
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ================= 1. DATABASE CONFIGURATION & AUTO-SETUP =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "X456208a*",  # <--- ENTER YOUR DB PASSWORD HERE
    "database": "qlud"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        return None

def auto_setup_database():
    print("⏳ Booting up RideHub System...")
    try:
        # Create DB if not exists
        server_conn = mysql.connector.connect(
            host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"]
        )
        cursor = server_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        server_conn.close()

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Setup Admin Tables (Module 3 & Settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(50) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        if cursor.fetchone()[0] == 0:
            users = [("admin", "admin123", "Admin User", "Manager")]
            for i in range(1, 4): users.append((f"sup{i}", "123456", f"Supervisor {i}", "Supervisor"))
            for i in range(1, 11): users.append((f"head{i}", "123456", f"Department Head {i}", "Head"))
            cursor.executemany("INSERT INTO admin_users VALUES (%s, %s, %s, %s)", users)
        
        cursor.execute("CREATE TABLE IF NOT EXISTS flagged_users (uid VARCHAR(100) PRIMARY KEY)")
        cursor.execute("CREATE TABLE IF NOT EXISTS suspended_users (uid VARCHAR(100) PRIMARY KEY)")
        conn.commit()

        # Setup Rides Table
        cursor.execute("SHOW TABLES LIKE 'rides'")
        table_exists = cursor.fetchone()
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM rides")
            count = cursor.fetchone()[0]
            if count > 10000:
                print(f"✅ Database ready ({count:,} rides). Launching UI...")
                conn.close()
                return

        print("⚠️ Database empty! Starting Import of 150,000 rows from CSV...")
        start_time = time.time()
        print("📥 Reading ncr_ride_bookings (4).csv...")
        df = pd.read_csv("ncr_ride_bookings (4).csv")
        
        for col in df.columns:
            if df[col].dtype == 'object' or str(df[col].dtype) == 'string':
                df[col] = df[col].fillna("")
            else:
                df[col] = df[col].fillna(0)
                
        engine_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(engine_url)
        print("🚀 Pumping data into MySQL... (Takes ~10-15 seconds)")
        df.to_sql(name='rides', con=engine, if_exists='replace', index=False)
        end_time = time.time()
        print(f"✅ IMPORT COMPLETE! Time: {end_time - start_time:.1f}s. Launching UI...")
        conn.close()
    except FileNotFoundError:
        print("❌ ERROR: CSV file not found!")
        exit()
    except Exception as e:
        print(f"❌ System Error: {e}")
        exit()


# ================= 2. LOGIN WINDOW =================
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub - Login")
        self.geometry("450x550")
        self.configure(fg_color="#F3F4F6")
        self.eval('tk::PlaceWindow . center')

        card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color="#E5E7EB")
        card.pack(expand=True, padx=40, pady=40, fill="both")

        ctk.CTkLabel(card, text="🚕", font=("Arial", 40)).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="Welcome to RideHub", font=("Arial", 22, "bold"), text_color="#111827").pack()
        ctk.CTkLabel(card, text="Please sign in to your account", font=("Arial", 13), text_color="#6B7280").pack(pady=(0, 20))

        self.txt_user = ctk.CTkEntry(card, placeholder_text="Username", height=45, corner_radius=8, fg_color="#F9FAFB", border_color="#D1D5DB", text_color="#111827")
        self.txt_user.pack(fill="x", padx=30, pady=10)

        self.txt_pwd = ctk.CTkEntry(card, placeholder_text="Password", height=45, corner_radius=8, fg_color="#F9FAFB", border_color="#D1D5DB", text_color="#111827", show="*")
        self.txt_pwd.pack(fill="x", padx=30, pady=10)

        btn_login = ctk.CTkButton(card, text="Sign In", font=("Arial", 14, "bold"), height=45, corner_radius=8, fg_color="#4F46E5", hover_color="#4338CA", command=self.check_login)
        btn_login.pack(fill="x", padx=30, pady=(20, 10))
        
        self.bind('<Return>', lambda e: self.check_login())

    def check_login(self):
        u, p = self.txt_user.get(), self.txt_pwd.get()
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Database connection failed!")
            return
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username=%s AND password=%s", (u, p))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.destroy()
            app = MainApp(user)
            app.mainloop()
        else:
            messagebox.showerror("Error", "Invalid username or password!")


# ================= 3. APP MODULES =================

# --- MODULE 1: DASHBOARD ---
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self._build_header()

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=(15, 0))

        end   = datetime.now()
        start = end - timedelta(days=30)
        self.start_var.set(start.strftime("%Y-%m-%d"))
        self.end_var.set(end.strftime("%Y-%m-%d"))
        self.generate_report()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(header, text="Executive Operations & Revenue", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(side="left")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        filter_box = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        filter_box.pack(side="left", padx=(0, 15), pady=2)

        ctk.CTkLabel(filter_box, text="From:", font=("Arial", 12, "bold"), text_color="#6B7280").pack(side="left", padx=(15, 5), pady=8)
        self.start_var = ctk.StringVar()
        ctk.CTkEntry(filter_box, textvariable=self.start_var, width=105, height=32, placeholder_text="YYYY-MM-DD", border_width=0, fg_color="#F3F4F6").pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filter_box, text="To:", font=("Arial", 12, "bold"), text_color="#6B7280").pack(side="left", padx=(0, 5))
        self.end_var = ctk.StringVar()
        ctk.CTkEntry(filter_box, textvariable=self.end_var, width=105, height=32, placeholder_text="YYYY-MM-DD", border_width=0, fg_color="#F3F4F6").pack(side="left", padx=(0, 15))

        ctk.CTkButton(right, text="🔄 Generate Report", font=("Arial", 13, "bold"), fg_color="#4F46E5", hover_color="#4338CA", text_color="#FFFFFF", corner_radius=8, width=160, height=40, command=self.generate_report).pack(side="left")

    def generate_report(self):
        for w in self.scroll.winfo_children(): w.destroy()
        plt.close("all")
        start = self.start_var.get().strip()
        end   = self.end_var.get().strip()
        try:
            data = self._load_all_data(start, end)
        except Exception as e:
            messagebox.showerror("Data Load Error", str(e))
            return
        
        self._build_kpi_section(self.scroll, data)
        self._build_charts_row1(self.scroll, data)
        self._build_charts_row2(self.scroll, data)
        self._build_top_vehicles(self.scroll, data)
        self._build_daily_table(self.scroll, data)

    def _load_all_data(self, start_date, end_date):
        conn = get_db_connection()
        if not conn: return {}
        cursor = conn.cursor(dictionary=True)

        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE `Date` BETWEEN %s AND %s"
            params = [start_date, end_date]

        prev_params, prev_filter = [], ""
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d")
            e = datetime.strptime(end_date, "%Y-%m-%d")
            pe = s - timedelta(days=1)
            ps = pe - (e - s)
            prev_filter = "WHERE `Date` BETWEEN %s AND %s"
            prev_params = [ps.strftime("%Y-%m-%d"), pe.strftime("%Y-%m-%d")]
        except: pass

        cursor.execute(f"SELECT COUNT(*) as total, SUM(`Booking Value`) as revenue, AVG(`Driver Ratings`) as avg_rate, AVG(`Avg VTAT`) as avg_vtat FROM rides {date_filter}", params)
        kpi = cursor.fetchone()

        cursor.execute(f"SELECT COUNT(*) as cnt FROM rides {date_filter}{' AND' if date_filter else ' WHERE'} `Booking Status`='Completed'", params)
        completed = cursor.fetchone()['cnt']

        total = int(kpi['total'] or 0)
        revenue = float(kpi['revenue'] or 0)
        avg_rate = float(kpi['avg_rate'] or 0)
        avg_vtat = float(kpi['avg_vtat'] or 0)
        completion_rate = (completed / total * 100) if total > 0 else 0
        avg_rev_per_ride = (revenue / total) if total > 0 else 0

        prev_kpi = {"total": 0, "revenue": 0}
        if prev_params:
            try:
                cursor.execute(f"SELECT COUNT(*) as total, SUM(`Booking Value`) as revenue FROM rides {prev_filter}", prev_params)
                row = cursor.fetchone()
                if row: prev_kpi = row
            except: pass

        cursor.execute(f"SELECT `Booking Status`, COUNT(*) as cnt FROM rides {date_filter} GROUP BY `Booking Status`", params)
        status_dist = {r['Booking Status']: r['cnt'] for r in cursor.fetchall()}

        payment_dist, vehicle_rev, daily_data, top_vehicles = {}, [], [], []
        try:
            cursor.execute(f"SELECT `Payment Method`, COUNT(*) as cnt FROM rides {date_filter} GROUP BY `Payment Method`", params)
            payment_dist = {r['Payment Method']: r['cnt'] for r in cursor.fetchall()}
            
            cursor.execute(f"SELECT `Vehicle Type`, SUM(`Booking Value`) as rev FROM rides {date_filter} GROUP BY `Vehicle Type` ORDER BY rev DESC", params)
            vehicle_rev = cursor.fetchall()
            
            cursor.execute(f"""SELECT `Date`, COUNT(*) as total_rides, SUM(`Booking Value`) as revenue, AVG(`Driver Ratings`) as avg_rating, SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END) as completed, SUM(CASE WHEN `Booking Status` LIKE '%Cancel%' THEN 1 ELSE 0 END) as cancellations FROM rides {date_filter} GROUP BY `Date` ORDER BY `Date`""", params)
            daily_data = cursor.fetchall()
            
            cursor.execute(f"""SELECT `Vehicle Type`, COUNT(*) as total_rides, SUM(`Booking Value`) as total_revenue, AVG(`Booking Value`) as avg_rev_per_ride, AVG(`Driver Ratings`) as avg_rating, SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END)/COUNT(*)*100 as completion_rate FROM rides {date_filter} GROUP BY `Vehicle Type` ORDER BY total_revenue DESC""", params)
            top_vehicles = cursor.fetchall()
        except: pass

        conn.close()
        return {
            "total": total, "revenue": revenue, "avg_rate": avg_rate, "avg_vtat": avg_vtat,
            "completion_rate": completion_rate, "avg_rev_per_ride": avg_rev_per_ride,
            "prev_total": int(prev_kpi.get("total") or 0), "prev_revenue": float(prev_kpi.get("revenue") or 0),
            "status_dist": status_dist, "payment_dist": payment_dist,
            "vehicle_rev": vehicle_rev, "daily_data": daily_data, "top_vehicles": top_vehicles,
        }

    @staticmethod
    def _pct(current, previous):
        if previous and previous > 0: return (current - previous) / previous * 100
        return 0.0

    def _build_kpi_section(self, parent, data):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 15))

        pct_rides = self._pct(data["total"], data["prev_total"])
        pct_rev   = self._pct(data["revenue"], data["prev_revenue"])

        cards = [
            ("🚗 Total Rides",        f"{data['total']:,}",              f"{pct_rides:+.1f}% vs last period", "#3B82F6"),
            ("💰 Total Revenue",     f"₹{data['revenue']:,.0f}",        f"{pct_rev:+.1f}% vs last period",   "#10B981"),
            ("✅ Completion Rate",   f"{data['completion_rate']:.1f}%", "of total rides booked",             "#8B5CF6"),
            ("⭐ Avg Rating",        f"{data['avg_rate']:.2f}",         "out of 5.0",                        "#F59E0B"),
            ("📈 Avg Rev / Ride",    f"₹{data['avg_rev_per_ride']:.0f}","per completed trip",                "#14B8A6"),
            ("⏱ Avg Pickup Time",   f"{data['avg_vtat']:.1f} min",     "average wait time",                 "#EF4444"),
        ]

        for i, (title, value, sub, color) in enumerate(cards):
            card = ctk.CTkFrame(frame, fg_color="#FFFFFF", corner_radius=12, height=125, border_width=1, border_color="#E5E7EB")
            card.grid(row=0, column=i, padx=(0, 15), sticky="ew")
            card.grid_propagate(False)
            frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkFrame(card, fg_color=color, height=6, corner_radius=3).place(x=0, y=0, relwidth=1)
            ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"), text_color="#6B7280").place(x=15, y=20)
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Arial", size=24, weight="bold"), text_color="#111827").place(x=15, y=48)
            
            arrow = "▲" if "+" in sub else ("▼" if "-" in sub else "")
            trend_color = "#10B981" if "+" in sub else ("#EF4444" if "-" in sub else "#9CA3AF")
            ctk.CTkLabel(card, text=f"{arrow} {sub}", font=("Arial", 11, "bold"), text_color=trend_color).place(x=15, y=88)

    def _build_charts_row1(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        trend_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(trend_card, text="📈 Revenue Trend vs Forecast", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        daily = data.get("daily_data", [])
        if daily:
            dates   = [str(r["Date"]) for r in daily]
            actuals = [float(r["revenue"] or 0) for r in daily]
            avg_rev = sum(actuals) / len(actuals) if actuals else 0
            forecasts = [avg_rev * (1 + 0.015 * (i - len(actuals) / 2)) for i in range(len(actuals))]
            
            fig, ax = plt.subplots(figsize=(7, 3.5), dpi=92)
            fig.patch.set_facecolor("white")
            xs = range(len(dates))
            
            ax.fill_between(xs, actuals, alpha=0.12, color="#3B82F6")
            line_actual, = ax.plot(xs, actuals, marker="o", color="#3B82F6", lw=2, markersize=5, label="Actual")
            line_forecast, = ax.plot(xs, forecasts, linestyle="--", color="#EF4444", lw=2, markersize=0, label="Forecast")
            
            step = max(1, len(dates) // 8)
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i][-5:] for i in range(0, len(dates), step)], rotation=40, fontsize=8)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax.set_ylabel("Revenue", fontsize=9)
            ax.legend(fontsize=9, loc="upper left", frameon=False)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            
            annot = ax.annotate("", xy=(0,0), xytext=(-20,20), textcoords="offset points", bbox=dict(boxstyle="round4", fc="#111827", ec="none", alpha=0.8), arrowprops=dict(arrowstyle="->", color="#111827"), color="white", fontsize=9, fontweight="bold")
            annot.set_visible(False)

            def hover_line(event):
                if event.inaxes == ax:
                    cont, ind = line_actual.contains(event)
                    if cont:
                        idx = ind["ind"][0]
                        annot.xy = (xs[idx], actuals[idx])
                        annot.set_text(f"Date: {dates[idx]}\nActual: ₹{actuals[idx]:,.0f}\nForecast: ₹{forecasts[idx]:,.0f}")
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if annot.get_visible():
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

            fig.canvas.mpl_connect("motion_notify_event", hover_line)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, trend_card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(5, 15))
        else:
            ctk.CTkLabel(trend_card, text="No Data Available", text_color="#9CA3AF").pack(expand=True, pady=40)

        donut_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        donut_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(donut_card, text="🍩 Ride Status Distribution", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        status_dist = data.get("status_dist", {})
        if status_dist:
            COLOR_MAP = {"Completed": "#10B981", "Cancelled by Customer": "#EF4444", "Cancelled by Driver": "#F59E0B", "No Driver Found": "#9CA3AF", "Incomplete": "#6B7280"}
            labels = list(status_dist.keys())
            sizes  = list(status_dist.values())
            colors = [COLOR_MAP.get(l, "#CBD5E1") for l in labels]
            
            fig2, ax2 = plt.subplots(figsize=(4.2, 3.5), dpi=92)
            fig2.patch.set_facecolor("white")
            wedges, _, autotexts = ax2.pie(sizes, colors=colors, autopct="%1.1f%%", pctdistance=0.78, startangle=90, wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2))
            for at in autotexts: at.set_fontsize(9); at.set_fontweight("bold")
            ax2.legend(labels, loc="lower center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, -0.08), frameon=False)
            
            annot2 = ax2.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points", bbox=dict(boxstyle="round4", fc="#111827", ec="none", alpha=0.8), color="white", fontsize=9, fontweight="bold")
            annot2.set_visible(False)

            def hover_pie(event):
                if event.inaxes == ax2:
                    for i, wedge in enumerate(wedges):
                        if wedge.contains(event)[0]:
                            ang = (wedge.theta2 - wedge.theta1) / 2.0 + wedge.theta1
                            y = math.sin(math.radians(ang)) * 0.5
                            x = math.cos(math.radians(ang)) * 0.5
                            annot2.xy = (x, y)
                            annot2.set_text(f"{labels[i]}\nRides: {sizes[i]:,}")
                            annot2.set_visible(True)
                            fig2.canvas.draw_idle()
                            return
                if annot2.get_visible():
                    annot2.set_visible(False)
                    fig2.canvas.draw_idle()

            fig2.canvas.mpl_connect("motion_notify_event", hover_pie)
            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, donut_card)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(donut_card, text="No Data Available", text_color="#9CA3AF").pack(expand=True, pady=40)

    def _build_charts_row2(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=2)

        pay_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        pay_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(pay_card, text="💳 Payment Methods", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        payment_dist = data.get("payment_dist", {})
        if payment_dist:
            labels = [k for k in payment_dist if k and str(k) not in ("0", "None", "nan")]
            sizes  = [payment_dist[k] for k in labels]
            colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6"][:len(labels)]
            fig3, ax3 = plt.subplots(figsize=(4, 3.5), dpi=92)
            fig3.patch.set_facecolor("white")
            ax3.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, textprops={"fontsize": 9, "fontweight": "bold"}, wedgeprops={"edgecolor": "white", "linewidth": 2})
            fig3.tight_layout()
            canvas3 = FigureCanvasTkAgg(fig3, pay_card)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(pay_card, text="No Data Available", text_color="#9CA3AF").pack(expand=True, pady=40)

        veh_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        veh_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(veh_card, text="🚙 Revenue by Vehicle Type", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        vehicle_rev = data.get("vehicle_rev", [])
        if vehicle_rev:
            v_types = [str(r["Vehicle Type"]) for r in vehicle_rev]
            v_revs  = [float(r["rev"] or 0) for r in vehicle_rev]
            bar_colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6"][:len(v_types)]
            fig4, ax4 = plt.subplots(figsize=(6, 3.5), dpi=92)
            fig4.patch.set_facecolor("white")
            bars = ax4.bar(v_types, v_revs, color=bar_colors, width=0.6, edgecolor="white", linewidth=1.5)
            ax4.spines["top"].set_visible(False)
            ax4.spines["right"].set_visible(False)
            ax4.set_ylabel("Revenue (₹)", fontsize=9)
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax4.tick_params(axis="x", labelsize=9)
            
            annot4 = ax4.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points", bbox=dict(boxstyle="round4", fc="#111827", ec="none", alpha=0.8), color="white", fontsize=9, fontweight="bold", ha="center")
            annot4.set_visible(False)

            def hover_bar(event):
                if event.inaxes == ax4:
                    for bar in bars:
                        if bar.contains(event)[0]:
                            annot4.xy = (bar.get_x() + bar.get_width() / 2, bar.get_height())
                            annot4.set_text(f"₹{bar.get_height():,.0f}")
                            annot4.set_visible(True)
                            fig4.canvas.draw_idle()
                            return
                if annot4.get_visible():
                    annot4.set_visible(False)
                    fig4.canvas.draw_idle()

            fig4.canvas.mpl_connect("motion_notify_event", hover_bar)
            fig4.tight_layout()
            canvas4 = FigureCanvasTkAgg(fig4, veh_card)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(veh_card, text="No Data Available", text_color="#9CA3AF").pack(expand=True, pady=40)

    def _build_top_vehicles(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(card, text="🏆 Top Performing Vehicles", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 10))

        top_vehicles = data.get("top_vehicles", [])
        if not top_vehicles:
            ctk.CTkLabel(card, text="No Data Available", text_color="#9CA3AF").pack(pady=12)
            return

        max_avg = max((float(r.get("avg_rev_per_ride") or 0) for r in top_vehicles), default=1) or 1
        style = ttk.Style()
        style.configure("TopVeh.Treeview", rowheight=36, borderwidth=0, font=("Arial", 11), background="#FFFFFF")
        style.configure("TopVeh.Treeview.Heading", font=("Arial", 11, "bold"), background="#F3F4F6", foreground="#4B5563")

        cols   = ("Rank", "Vehicle Type", "Total Rides", "Total Revenue", "Rev / Ride", "Avg Rating", "Completion %", "Efficiency Score")
        widths = (70, 140, 110, 140, 120, 110, 120, 140)
        tree   = ttk.Treeview(card, columns=cols, show="headings", height=min(len(top_vehicles), 7), style="TopVeh.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        medals = ["🥇", "🥈", "🥉"]
        sorted_veh = sorted(top_vehicles, key=lambda r: float(r.get("total_revenue") or 0), reverse=True)
        for i, r in enumerate(sorted_veh):
            cr   = float(r.get("completion_rate") or 0)
            rat  = float(r.get("avg_rating") or 0)
            arpu = float(r.get("avg_rev_per_ride") or 0)
            eff  = (cr / 100) * 0.4 + (rat / 5) * 0.3 + (arpu / max_avg) * 0.3
            tree.insert("", "end", values=(medals[i] if i < 3 else f"#{i+1}", r.get("Vehicle Type", "N/A"), f"{int(r.get('total_rides') or 0):,}", f"₹{float(r.get('total_revenue') or 0):,.0f}", f"₹{arpu:.0f}", f"⭐ {rat:.2f}", f"✅ {cr:.1f}%", f"{eff:.3f}"))
        tree.pack(fill="x", padx=20, pady=(0, 20))

    def _build_daily_table(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card, text="📅 Performance Summary Table", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 10))

        daily_data = data.get("daily_data", [])
        if not daily_data:
            ctk.CTkLabel(card, text="No Data Available", text_color="#9CA3AF").pack(pady=12)
            return

        style = ttk.Style()
        style.configure("Daily.Treeview", rowheight=36, borderwidth=0, font=("Arial", 11), background="#FFFFFF", foreground="#111827")
        style.configure("Daily.Treeview.Heading", font=("Arial", 11, "bold"), background="#F3F4F6", foreground="#4B5563")
        style.map("Daily.Treeview", background=[('selected', '#FFFFFF')], foreground=[('selected', '#111827')])
        style.configure("Total.Treeview", rowheight=36, borderwidth=0, font=("Arial", 12, "bold"), background="#F9FAFB", fieldbackground="#F9FAFB", foreground="#111827")
        style.map("Total.Treeview", background=[('selected', '#F9FAFB')], foreground=[('selected', '#111827')])

        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=(0, 20))

        left_col = ctk.CTkFrame(container, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True)
        sb = ttk.Scrollbar(container)
        sb.pack(side="right", fill="y", padx=(5, 0))

        cols   = ("DATE", "TOTAL RIDES", "REVENUE", "COMPLETION RATE", "AVG RATING", "CANCELLATIONS", "Δ REVENUE")
        widths = (110, 120, 130, 150, 130, 120, 140)

        tree_main = ttk.Treeview(left_col, columns=cols, show="headings", height=min(len(daily_data), 8), yscrollcommand=sb.set, style="Daily.Treeview")
        sb.config(command=tree_main.yview)
        tree_total = ttk.Treeview(left_col, columns=cols, show="", height=1, style="Total.Treeview")

        for col, w in zip(cols, widths):
            tree_main.heading(col, text=col)
            tree_main.column(col, width=w, anchor="center")
            tree_total.column(col, width=w, anchor="center")

        prev_rev = None
        sum_rides, sum_rev, sum_comp, sum_can, sum_rate, count = 0, 0, 0, 0, 0, 0

        for r in daily_data:
            rev   = float(r["revenue"] or 0)
            total = int(r["total_rides"] or 0)
            comp  = int(r["completed"] or 0)
            cr    = (comp / total * 100) if total > 0 else 0
            rat   = float(r["avg_rating"] or 0)
            can   = int(r["cancellations"] or 0)
            
            sum_rides += total
            sum_rev += rev
            sum_comp += comp
            sum_can += can
            if rat > 0:
                sum_rate += rat; count += 1

            if prev_rev is not None:
                diff = rev - prev_rev
                if diff > 0: delta_str = f"📈 +₹{diff:,.0f}"
                elif diff < 0: delta_str = f"📉 -₹{abs(diff):,.0f}"
                else: delta_str = "—"
            else: delta_str = "—"
            prev_rev = rev

            cr_str = f"🟢 {cr:.1f}%" if cr >= 80 else f"🔴 {cr:.1f}%"
            rat_str = f"⭐ {rat:.1f}" if rat > 0 else "N/A"
            can_str = f"🚫 {can:,}" if can > 0 else f"{can:,}"

            tree_main.insert("", "end", values=(str(r["Date"]), f"{total:,}", f"₹{rev:,.0f}", cr_str, rat_str, can_str, delta_str))

        avg_cr_total = (sum_comp / sum_rides * 100) if sum_rides > 0 else 0
        avg_rate_total = (sum_rate / count) if count > 0 else 0
        
        tree_total.insert("", "end", values=("TOTALS / AVG", f"{sum_rides:,}", f"₹{sum_rev:,.0f}", f"✅ {avg_cr_total:.1f}%", f"⭐ {avg_rate_total:.2f}", f"🚫 {sum_can:,}", "—"))
        tree_main.pack(fill="x")
        tree_total.pack(fill="x")

# --- MODULE 3: USER PROFILES ---
class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.current_limit = 30
        self.max_display_limit = 100
        self.tooltip_window = None
        self.tooltip_timer = None

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

        search_frame = ctk.CTkFrame(top_controls, fg_color="#F3F4F6", corner_radius=8, height=35)
        search_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter ID...", height=35, 
                                         textvariable=self.search_var, fg_color="transparent", border_width=0, 
                                         text_color="#111827", placeholder_text_color="#9CA3AF")
        self.search_entry.pack(fill="x", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.reset_and_refresh())

        bottom_controls = ctk.CTkFrame(control_panel, fg_color="transparent")
        bottom_controls.pack(fill="x", padx=15, pady=(5, 15))

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

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.left_side = ctk.CTkFrame(self.main_container, width=340, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        self.left_side.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self.left_side.grid_propagate(False)
        
        list_header = ctk.CTkFrame(self.left_side, fg_color="transparent")
        list_header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(list_header, text="ID List", font=("Arial", 15, "bold"), text_color="#111827").pack(side="left")

        self.scroll_list = ctk.CTkScrollableFrame(self.left_side, fg_color="#FFFFFF", corner_radius=0)
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.right_side = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_side.grid(row=0, column=1, sticky="nsew")
        
        self.refresh_list()

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

    def toggle_suspend(self, uid):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suspended_users WHERE uid = %s", (uid,))
        if cursor.fetchone(): cursor.execute("DELETE FROM suspended_users WHERE uid = %s", (uid,))
        else: cursor.execute("INSERT INTO suspended_users (uid) VALUES (%s)", (uid,))
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
        if self.user_type_var.get() == "Customers":
            self.risk_filter.set("All Statuses")
            self.risk_filter.configure(state="disabled")
        else:
            self.risk_filter.configure(state="readonly")
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
        cursor.execute("SELECT uid FROM suspended_users")
        suspended_set = {row['uid'] for row in cursor.fetchall()}

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

        if user_type == "Drivers":
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
                is_suspended = uid in suspended_set
                
                item_frame = ctk.CTkFrame(self.scroll_list, fg_color="#F9FAFB", corner_radius=8, height=65)
                item_frame.pack(fill="x", pady=4, padx=5)
                item_frame.pack_propagate(False)
                
                if user_type == "Drivers":
                    alert_text = "🔴" if c_rate >= 40 else ("🟠" if c_rate >= 20 else "👤")
                    val_color = "#EF4444" if c_rate >= 40 else ("#F59E0B" if c_rate >= 20 else "#111827")
                    stats_text = f"⭐ {stars:.1f}  |  🏁 {trips}  |  🚫 {c_rate:.0f}%"
                else:
                    alert_text = "👤"
                    val_color = "#111827"
                    stats_text = f"⭐ {stars:.1f}  |  🏁 {trips} Trips"

                ctk.CTkLabel(item_frame, text=alert_text, font=("Arial", 18)).place(x=15, y=18)
                ctk.CTkLabel(item_frame, text=uid, font=("Arial", 13, "bold"), text_color=val_color).place(x=50, y=10)
                ctk.CTkLabel(item_frame, text=stats_text, font=("Arial", 11), text_color="#6B7280").place(x=50, y=32)

                icon_x = 0.88
                if is_suspended:
                    ctk.CTkLabel(item_frame, text="⛔", font=("Arial", 14)).place(relx=icon_x, y=10)
                    icon_x -= 0.1
                if is_flagged:
                    ctk.CTkLabel(item_frame, text="📌", font=("Arial", 14)).place(relx=icon_x, y=10)

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
        c_color   = "#EF4444" if cancel_rate >= 40 else ("#F59E0B" if cancel_rate >= 20 else "#10B981")

        ctk.CTkLabel(frame, text=f"{flag_text}ID: {uid}", font=("Arial", 12, "bold"), text_color="#FFFFFF").pack(padx=12, pady=(8, 2), anchor="w")
        ctk.CTkLabel(frame, text=f"⭐ Avg Rating: {stars:.1f}", font=("Arial", 11), text_color="#D1D5DB").pack(padx=12, anchor="w")
        ctk.CTkLabel(frame, text=f"🏁 Total Trips: {trips}", font=("Arial", 11), text_color="#D1D5DB").pack(padx=12, anchor="w")
        ctk.CTkLabel(frame, text=f"🚫 Cancel Rate: {cancel_rate:.1f}%", font=("Arial", 11, "bold"), text_color=c_color).pack(padx=12, pady=(0, 8), anchor="w")

    def cancel_tooltip(self, event=None):
        if self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def display_detail(self, uid, user_type):
        for widget in self.right_side.winfo_children(): widget.destroy()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        id_col = "Driver ID" if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"
        cancel_col = "Cancelled Rides by Driver" if user_type == "Drivers" else "Cancelled Rides by Customer"
        history_rating_col = "Customer Rating" if user_type == "Drivers" else "Driver Ratings"

        cancel_rate_expr = f"COALESCE((SUM(`{cancel_col}`) / NULLIF(SUM(CASE WHEN `Booking Status` != 'No Driver Found' THEN 1 ELSE 0 END), 0)) * 100, 0)"
        cursor.execute(f"SELECT AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips, SUM(`Booking Value`) as total_val, {cancel_rate_expr} as cancel_rate FROM rides WHERE `{id_col}` = %s", (uid,))
        stats = cursor.fetchone()
        
        cursor.execute(f"SELECT `Booking ID`, `Date`, `Booking Value`, `Booking Status`, `{history_rating_col}` as trip_rating FROM rides WHERE `{id_col}` = %s ORDER BY `Date` DESC LIMIT 5", (uid,))
        history = cursor.fetchall()
        
        cursor.execute("SELECT * FROM flagged_users WHERE uid = %s", (uid,))
        is_flagged = cursor.fetchone() is not None
        
        cursor.execute("SELECT * FROM suspended_users WHERE uid = %s", (uid,))
        is_suspended = cursor.fetchone() is not None
        
        conn.close()

        c_rate = float(stats['cancel_rate'])
        bg_color = "#4F46E5" if user_type == "Drivers" else "#9333EA" 

        header_card = ctk.CTkFrame(self.right_side, fg_color=bg_color, corner_radius=16, height=160)
        header_card.pack(fill="x", pady=(0, 20))
        header_card.pack_propagate(False)

        ctk.CTkLabel(header_card, text="👤", font=("Arial", 60), fg_color="transparent", width=90, height=90).place(x=20, y=30)
        info_x = 120
        ctk.CTkLabel(header_card, text=uid, font=("Arial", 28, "bold"), text_color="#FFFFFF").place(x=info_x, y=25)

        badge_container = ctk.CTkFrame(header_card, fg_color="transparent")
        badge_container.place(x=info_x, y=68)

        status_text = "Suspended" if is_suspended else "Active"
        status_color = "#EF4444" if is_suspended else "#34D399"
        ctk.CTkLabel(badge_container, text=f"● {status_text}", font=("Arial", 11, "bold"), text_color="#FFFFFF", fg_color=status_color, corner_radius=10, padx=10, pady=3).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(badge_container, text=user_type[:-1], font=("Arial", 11, "bold"), text_color=bg_color, fg_color="#FFFFFF", corner_radius=10, padx=10, pady=3).pack(side="left", padx=(0, 10))

        if is_flagged:
            ctk.CTkLabel(badge_container, text="📌 Flagged", font=("Arial", 11, "bold"), text_color="#FFFFFF", fg_color="#F59E0B", corner_radius=10, padx=10, pady=3).pack(side="left")

        if user_type == "Drivers":
            risk_text = "🚨 High Cancel Rate!" if c_rate >= 40 else ("⚠️ Needs Monitoring" if c_rate >= 20 else "✅ Safe Profile")
            ctk.CTkLabel(header_card, text=f"Status: {risk_text}", font=("Arial", 13), text_color="#E0E7FF").place(x=info_x, y=105)

        btn_flag = ctk.CTkButton(header_card, text="Unflag" if is_flagged else "📌 Flag", fg_color="#FFFFFF", text_color="#F59E0B" if is_flagged else bg_color, hover_color="#F3F4F6", font=("Arial", 12, "bold"), width=110, command=lambda u=uid: self.toggle_flag(u))
        btn_flag.place(relx=0.96, rely=0.3, anchor="e")

        if user_type == "Drivers":
            btn_suspend = ctk.CTkButton(header_card, text="Unsuspend" if is_suspended else "⛔ Suspend", fg_color="#EF4444" if not is_suspended else "#FFFFFF", text_color="#FFFFFF" if not is_suspended else "#EF4444", hover_color="#DC2626", font=("Arial", 12, "bold"), width=110, command=lambda u=uid: self.toggle_suspend(u))
            btn_suspend.place(relx=0.96, rely=0.7, anchor="e")

        stats_frame = ctk.CTkFrame(self.right_side, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.create_stat_card(stats_frame, "Total Trips", f"{stats['total_trips']}", "🚗", 0)
        self.create_stat_card(stats_frame, "Total Spent" if user_type == "Customers" else "Revenue", f"₹{stats['total_val'] or 0:,.0f}", "💰", 1)
        self.create_stat_card(stats_frame, "Avg Rating", f"{stats['avg_rate']:.1f} ⭐" if stats['avg_rate'] else "N/A", "⭐", 2)
        if user_type == "Drivers":
            self.create_stat_card(stats_frame, "Cancel Rate", f"{c_rate:.1f}%", "🚫", 3, is_danger=(c_rate >= 20))

        table_container = ctk.CTkFrame(self.right_side, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        table_container.pack(fill="both", expand=True)
        ctk.CTkLabel(table_container, text="Ride History (5 Recent)", font=("Arial", 16, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 5))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#111827", borderwidth=0, rowheight=40, font=("Arial", 12))
        style.configure("Treeview.Heading", background="#F9FAFB", foreground="#6B7280", borderwidth=0, font=('Arial', 11, 'bold'))
        style.map("Treeview", background=[("selected", "#EEF2FF")], foreground=[("selected", "#4F46E5")])

        table = ttk.Treeview(table_container, columns=("ID", "Date", "Price", "Status", "Rating"), show="headings", height=5)
        for col in table["columns"]: 
            table.heading(col, text=col.upper())
            table.column(col, width=150 if col == "ID" else 100, anchor="center")
        table.pack(fill="both", expand=True, padx=2, pady=(0, 10))
        
        for trip in history: 
            r_str = f"{trip['trip_rating']} ⭐" if trip['trip_rating'] else "N/A"
            table.insert("", "end", values=(trip['Booking ID'], trip['Date'], f"₹{trip['Booking Value']}", trip['Booking Status'], r_str))

    def create_stat_card(self, parent, title, val, icon, col, is_danger=False):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB", height=100)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col==0 else 15, 0))
        card.grid_propagate(False)
        
        icon_bg = "#FEE2E2" if is_danger else "#EEF2FF"
        icon_fg = "#EF4444" if is_danger else "#4F46E5"
        
        ctk.CTkLabel(card, text=icon, font=("Arial", 22), fg_color=icon_bg, text_color=icon_fg, width=46, height=46, corner_radius=12).place(relx=0.15, rely=0.5, anchor="w")
        
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.place(relx=0.45, rely=0.5, anchor="w")
        ctk.CTkLabel(text_frame, text=title, font=("Arial", 12), text_color="#6B7280").pack(anchor="w")
        val_color = "#EF4444" if is_danger else "#111827"
        ctk.CTkLabel(text_frame, text=val, font=("Arial", 22, "bold"), text_color=val_color).pack(anchor="w", pady=(2, 0))


# --- MODULE 5: SETTINGS & USER MGT ---
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color="transparent")
        self.current_user = current_user
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Column: Profile
        left_col = ctk.CTkFrame(self, width=360, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_col.grid_propagate(False)
        
        ctk.CTkLabel(left_col, text="My Profile", font=("Arial", 20, "bold"), text_color="#111827").pack(anchor="w", pady=(0, 15))
        profile_card = ctk.CTkFrame(left_col, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        profile_card.pack(fill="both", expand=True)

        ctk.CTkLabel(profile_card, text="👨‍💼", font=("Arial", 60), fg_color="#EEF2FF", corner_radius=16, width=100, height=100).pack(pady=(30, 10))
        ctk.CTkLabel(profile_card, text=self.current_user['full_name'], font=("Arial", 18, "bold"), text_color="#111827").pack()
        
        role_color = "#10B981" if self.current_user['role'] == "Manager" else "#F59E0B"
        ctk.CTkLabel(profile_card, text=self.current_user['role'], font=("Arial", 12, "bold"), text_color="#FFFFFF", fg_color=role_color, corner_radius=10, padx=10, pady=2).pack(pady=(5, 20))

        form_frame = ctk.CTkFrame(profile_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(form_frame, text="Username", font=("Arial", 12, "bold"), text_color="#6B7280").pack(anchor="w")
        ctk.CTkEntry(form_frame, textvariable=ctk.StringVar(value=self.current_user['username']), state="readonly", height=40, fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#111827").pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(form_frame, text="Email Address", font=("Arial", 12, "bold"), text_color="#6B7280").pack(anchor="w")
        ctk.CTkEntry(form_frame, textvariable=ctk.StringVar(value=f"{self.current_user['username']}@ridehub.com"), state="readonly", height=40, fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#111827").pack(fill="x", pady=(5, 25))

        ctk.CTkButton(profile_card, text="🔑 Change Password", fg_color="#F3F4F6", text_color="#4F46E5", hover_color="#E0E7FF", font=("Arial", 12, "bold"), height=40, command=self.change_password_popup).pack(fill="x", padx=30, pady=(0, 20))

        # Right Column: Access Management
        right_col = ctk.CTkFrame(self, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right_col, text="System Access Management", font=("Arial", 20, "bold"), text_color="#111827").pack(anchor="w", pady=(0, 15))
        mg_card = ctk.CTkFrame(right_col, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        mg_card.pack(fill="both", expand=True)

        top_mg = ctk.CTkFrame(mg_card, fg_color="transparent")
        top_mg.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(top_mg, text="Authorized Personnel", font=("Arial", 16, "bold"), text_color="#111827").pack(side="left")
        
        if self.current_user['role'] == "Manager":
            ctk.CTkButton(top_mg, text="➕ Add New User", font=("Arial", 12, "bold"), fg_color="#4F46E5", hover_color="#4338CA", command=self.add_user_popup).pack(side="right")
        else:
            ctk.CTkLabel(top_mg, text="👀 View Only Mode", font=("Arial", 12, "italic", "bold"), text_color="#9CA3AF").pack(side="right")

        header_tbl = ctk.CTkFrame(mg_card, fg_color="#F9FAFB", height=40, corner_radius=0)
        header_tbl.pack(fill="x", padx=20)
        header_tbl.pack_propagate(False)
        ctk.CTkLabel(header_tbl, text="Name & Role", font=("Arial", 12, "bold"), text_color="#6B7280").place(x=60, y=10)
        ctk.CTkLabel(header_tbl, text="Username", font=("Arial", 12, "bold"), text_color="#6B7280").place(x=350, y=10)
        ctk.CTkLabel(header_tbl, text="Action", font=("Arial", 12, "bold"), text_color="#6B7280").place(relx=0.9, y=10)

        self.list_frame = ctk.CTkScrollableFrame(mg_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.load_users()

    def change_password_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Change Password")
        popup.geometry("380x420")
        popup.attributes("-topmost", True)
        
        ctk.CTkLabel(popup, text="Change Password", font=("Arial", 18, "bold")).pack(pady=20)

        old_pw, new_pw, confirm_pw = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()

        ctk.CTkLabel(popup, text="Current Password:", font=("Arial", 11, "bold"), text_color="#4B5563").pack(anchor="w", padx=50)
        ctk.CTkEntry(popup, textvariable=old_pw, show="*", width=280).pack(pady=(5, 15))

        ctk.CTkLabel(popup, text="New Password:", font=("Arial", 11, "bold"), text_color="#4B5563").pack(anchor="w", padx=50)
        ctk.CTkEntry(popup, textvariable=new_pw, show="*", width=280).pack(pady=(5, 15))

        ctk.CTkLabel(popup, text="Confirm New Password:", font=("Arial", 11, "bold"), text_color="#4B5563").pack(anchor="w", padx=50)
        ctk.CTkEntry(popup, textvariable=confirm_pw, show="*", width=280).pack(pady=(5, 20))

        def save_pw():
            if old_pw.get() != self.current_user['password']:
                messagebox.showerror("Error", "Incorrect current password!")
                return
            if new_pw.get() != confirm_pw.get():
                messagebox.showerror("Error", "New passwords do not match!")
                return
            if len(new_pw.get()) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters!")
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE admin_users SET password=%s WHERE username=%s", (new_pw.get(), self.current_user['username']))
            conn.commit()
            conn.close()

            self.current_user['password'] = new_pw.get()
            messagebox.showinfo("Success", "Password updated successfully!")
            popup.destroy()

        ctk.CTkButton(popup, text="Update Password", fg_color="#10B981", hover_color="#059669", width=280, height=40, font=("Arial", 12, "bold"), command=save_pw).pack()

    def load_users(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users ORDER BY role, full_name")
        for u in cursor.fetchall():
            row = ctk.CTkFrame(self.list_frame, fg_color="#FFFFFF", border_color="#E5E7EB", border_width=1, corner_radius=8, height=60)
            row.pack(fill="x", pady=4, padx=5)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text="👤", font=("Arial", 24)).place(x=15, y=15)
            ctk.CTkLabel(row, text=u['full_name'], font=("Arial", 14, "bold"), text_color="#111827").place(x=60, y=10)
            
            r_color = "#10B981" if u['role'] == "Manager" else ("#3B82F6" if u['role'] == "Supervisor" else "#6B7280")
            ctk.CTkLabel(row, text=u['role'], font=("Arial", 10, "bold"), text_color=r_color).place(x=60, y=32)
            
            ctk.CTkLabel(row, text=u['username'], font=("Arial", 13), text_color="#4B5563").place(x=350, y=20)
            
            if self.current_user['role'] == "Manager":
                if u['username'] != self.current_user['username']:
                    ctk.CTkButton(row, text="Revoke ❌", width=80, fg_color="#FEE2E2", text_color="#EF4444", hover_color="#FECACA", command=lambda x=u['username']: self.delete_user(x)).place(relx=0.88, y=15)
                else:
                    ctk.CTkLabel(row, text="Current User", font=("Arial", 12, "italic"), text_color="#9CA3AF").place(relx=0.88, y=20)
            else:
                if u['username'] == self.current_user['username']:
                    ctk.CTkLabel(row, text="You", font=("Arial", 13, "bold"), text_color="#4F46E5").place(relx=0.88, y=20)
                else:
                    ctk.CTkLabel(row, text="🔒 Restricted", font=("Arial", 12), text_color="#D1D5DB").place(relx=0.88, y=20)
        conn.close()

    def delete_user(self, username):
        if messagebox.askyesno("Confirm", f"Are you sure you want to revoke access for '{username}'?"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admin_users WHERE username=%s", (username,))
            conn.commit()
            conn.close()
            self.load_users()

    def add_user_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add New User")
        popup.geometry("400x550")
        popup.attributes("-topmost", True)
        
        ctk.CTkLabel(popup, text="Create Account", font=("Arial", 18, "bold")).pack(pady=20)
        
        u_var, p_var, n_var = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()
        r_var = ctk.StringVar(value="Supervisor")
        
        ctk.CTkLabel(popup, text="Username (Used for login, no spaces):", font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkEntry(popup, textvariable=u_var, placeholder_text="e.g. johndoe", width=280).pack(pady=(2, 15))
        
        ctk.CTkLabel(popup, text="Password (Minimum 6 characters):", font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkEntry(popup, textvariable=p_var, placeholder_text="e.g. secret123", width=280).pack(pady=(2, 15))
        
        ctk.CTkLabel(popup, text="Full Legal Name:", font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkEntry(popup, textvariable=n_var, placeholder_text="e.g. John Doe", width=280).pack(pady=(2, 15))
        
        ctk.CTkLabel(popup, text="System Role (Defines access level):", font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkComboBox(popup, variable=r_var, values=["Manager", "Supervisor", "Head"], width=280).pack(pady=(2, 25))
        
        def save():
            if not u_var.get() or not p_var.get() or not n_var.get(): 
                messagebox.showwarning("Warning", "All fields are required!")
                return
            if len(p_var.get()) < 6:
                messagebox.showwarning("Warning", "Password must be at least 6 characters!")
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO admin_users VALUES (%s, %s, %s, %s)", (u_var.get(), p_var.get(), n_var.get(), r_var.get()))
                conn.commit()
                self.load_users()
                messagebox.showinfo("Success", "User added successfully!")
                popup.destroy()
            except:
                messagebox.showerror("Error", "Username already exists!")
            conn.close()

        ctk.CTkButton(popup, text="Save User", fg_color="#10B981", hover_color="#059669", width=280, height=40, font=("Arial", 12, "bold"), command=save).pack()


# --- PLACEHOLDER FRAMES ---
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Ride Management Hub", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature in development...", text_color="#6B7280").pack()

class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Cancel & Risk Analysis", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature in development...", text_color="#6B7280").pack()


# ================= 4. MAIN APP ROUTING =================
class MainApp(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.title("RideHub Admin — Enterprise Edition")
        self.geometry("1450x850")
        self.configure(fg_color="#F3F4F6")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── SIDEBAR ──
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(25, 30), padx=20, sticky="w")
        ctk.CTkLabel(logo_frame, text="🚕", font=("Arial", 28)).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" RideHub", font=("Arial", 22, "bold"), text_color="#111827").pack(side="left", padx=5)

        self.nav_btns = {}
        nav_items = [
            ("📊  Dashboard",                  "Dashboard"),
            ("🛣️  Ride Management",             "Rides"),
            ("👤  Driver & Customer Profiles",  "Users"),
            ("📈  Cancel & Risk Analysis",      "Risk"),
            ("⚙️  System Settings",             "Settings"),
        ]
        
        for i, (text, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=text, anchor="w",
                fg_color="transparent", text_color="#6B7280",
                font=("Arial", 14, "bold"), height=50, corner_radius=10, hover_color="#F9FAFB",
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=6)
            self.nav_btns[key] = btn

        # ── RIGHT AREA ──
        self.right_area = ctk.CTkFrame(self, fg_color="transparent")
        self.right_area.grid(row=0, column=1, sticky="nsew")
        self.right_area.grid_rowconfigure(1, weight=1)
        self.right_area.grid_columnconfigure(0, weight=1)

        self.topbar = ctk.CTkFrame(self.right_area, height=70, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.topbar.grid(row=0, column=0, sticky="ew")

        user_frame = ctk.CTkFrame(self.topbar, fg_color="transparent")
        user_frame.pack(side="right", padx=30, pady=15)
        
        self.user_btn = ctk.CTkButton(user_frame, text=f"{self.current_user['full_name']}  👨‍💻 ▼", 
                                      font=("Arial", 14, "bold"), fg_color="transparent", 
                                      text_color="#111827", hover_color="#F3F4F6", height=40,
                                      command=self.toggle_user_menu)
        self.user_btn.pack(side="left")

        self.main_container = ctk.CTkFrame(self.right_area, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=25)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {
            "Dashboard": DashboardFrame(self.main_container),
            "Rides":     RideManagementFrame(self.main_container),
            "Users":     UserProfileFrame(self.main_container),
            "Risk":      RiskAnalysisFrame(self.main_container),
            "Settings":  SettingsFrame(self.main_container, self.current_user),
        }
        
        self.user_menu = None
        self.show_frame("Dashboard")

    def toggle_user_menu(self):
        if self.user_menu and self.user_menu.winfo_exists():
            self.close_user_menu()
            return
            
        x = self.user_btn.winfo_rootx()
        y = self.user_btn.winfo_rooty() + self.user_btn.winfo_height() + 5
        
        self.user_menu = ctk.CTkToplevel(self)
        self.user_menu.wm_overrideredirect(True)
        self.user_menu.geometry(f"160x95+{x}+{y}")
        self.user_menu.attributes("-topmost", True)
        
        menu_frame = ctk.CTkFrame(self.user_menu, fg_color="#FFFFFF", border_width=1, border_color="#E5E7EB", corner_radius=8)
        menu_frame.pack(fill="both", expand=True)
        
        btn_profile = ctk.CTkButton(menu_frame, text="👤 My Profile", font=("Arial", 13, "bold"), fg_color="transparent", text_color="#111827", hover_color="#F3F4F6", anchor="w", command=self.go_to_profile)
        btn_profile.pack(fill="x", padx=5, pady=(5, 2))
        
        btn_logout = ctk.CTkButton(menu_frame, text="🚪 Logout", font=("Arial", 13, "bold"), fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2", anchor="w", command=self.logout)
        btn_logout.pack(fill="x", padx=5, pady=(2, 5))
        
        self.user_menu.bind("<FocusOut>", lambda e: self.close_user_menu())
        self.user_menu.focus_set()

    def close_user_menu(self):
        if self.user_menu and self.user_menu.winfo_exists():
            self.user_menu.destroy()
            self.user_menu = None

    def go_to_profile(self):
        self.close_user_menu()
        self.show_frame("Settings")
        
    def logout(self):
        self.close_user_menu()
        self.destroy()
        app = LoginWindow()
        app.mainloop()

    def show_frame(self, frame_key):
        for key, btn in self.nav_btns.items():
            if key == frame_key:
                btn.configure(fg_color="#EEF2FF", text_color="#4F46E5", hover=False)
            else:
                btn.configure(fg_color="transparent", text_color="#6B7280", hover_color="#F9FAFB")

        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_key].grid(row=0, column=0, sticky="nsew")


# ================= 5. START APP =================
if __name__ == "__main__":
    auto_setup_database()
    app = LoginWindow()
    app.mainloop()