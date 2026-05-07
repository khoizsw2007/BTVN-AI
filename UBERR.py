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
    "password": "X456208a*",  # <--- ENTER YOUR PASSWORD HERE
    "database": "qlud"
}

def auto_setup_database():
    print("⏳ Booting up RideHub System...")
    try:
        server_conn = mysql.connector.connect(
            host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"]
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
                print(f"✅ Database ready ({count:,} rides). Launching UI...")
                conn.close()
                return

        print("⚠️ Database empty! Starting Import of 150,000 rows from CSV...")
        start_time = time.time()
        print("📥 Reading ncr_ride_bookings (4).csv...")
        df = pd.read_csv("ncr_ride_bookings (4).csv")
        
        # Smart NaN handling
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


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        return None


# ================= 2. MAIN MODULES =================

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

        ctk.CTkLabel(header, text="Executive Operations & Revenue Dashboard",
                     font=ctk.CTkFont(family="Arial", size=26, weight="bold"), 
                     text_color="#111827").pack(side="left")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        filter_box = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=10, 
                                  border_width=1, border_color="#E5E7EB")
        filter_box.pack(side="left", padx=(0, 15), pady=2)

        ctk.CTkLabel(filter_box, text="From:", font=("Arial", 12, "bold"), text_color="#6B7280").pack(side="left", padx=(15, 5), pady=8)
        self.start_var = ctk.StringVar()
        ctk.CTkEntry(filter_box, textvariable=self.start_var, width=105, height=32,
                     placeholder_text="YYYY-MM-DD", border_width=0, fg_color="#F3F4F6").pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filter_box, text="To:", font=("Arial", 12, "bold"), text_color="#6B7280").pack(side="left", padx=(0, 5))
        self.end_var = ctk.StringVar()
        ctk.CTkEntry(filter_box, textvariable=self.end_var, width=105, height=32,
                     placeholder_text="YYYY-MM-DD", border_width=0, fg_color="#F3F4F6").pack(side="left", padx=(0, 15))

        ctk.CTkButton(right, text="🔄 Generate Report",
                      font=("Arial", 13, "bold"),
                      fg_color="#4F46E5", hover_color="#4338CA", 
                      text_color="#FFFFFF", corner_radius=8, width=160, height=40,
                      command=self.generate_report).pack(side="left")

    def generate_report(self):
        for w in self.scroll.winfo_children():
            w.destroy()
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

        prev_params = []
        prev_filter = ""
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d")
            e = datetime.strptime(end_date, "%Y-%m-%d")
            delta = e - s
            pe = s - timedelta(days=1)
            ps = pe - delta
            prev_filter = "WHERE `Date` BETWEEN %s AND %s"
            prev_params = [ps.strftime("%Y-%m-%d"), pe.strftime("%Y-%m-%d")]
        except Exception:
            pass

        cursor.execute(
            f"SELECT COUNT(*) as total, SUM(`Booking Value`) as revenue, "
            f"AVG(`Driver Ratings`) as avg_rate, AVG(`Avg VTAT`) as avg_vtat "
            f"FROM rides {date_filter}", params
        )
        kpi = cursor.fetchone()

        completed_q = (
            f"SELECT COUNT(*) as cnt FROM rides {date_filter}"
            f"{' AND' if date_filter else ' WHERE'} `Booking Status`='Completed'"
        )
        cursor.execute(completed_q, params)
        completed = cursor.fetchone()['cnt']

        total            = int(kpi['total'] or 0)
        revenue          = float(kpi['revenue'] or 0)
        avg_rate         = float(kpi['avg_rate'] or 0)
        avg_vtat         = float(kpi['avg_vtat'] or 0)
        completion_rate  = (completed / total * 100) if total > 0 else 0
        avg_rev_per_ride = (revenue / total) if total > 0 else 0

        prev_kpi = {"total": 0, "revenue": 0}
        if prev_params:
            try:
                cursor.execute(
                    f"SELECT COUNT(*) as total, SUM(`Booking Value`) as revenue "
                    f"FROM rides {prev_filter}", prev_params
                )
                row = cursor.fetchone()
                if row: prev_kpi = row
            except Exception: pass

        cursor.execute(f"SELECT `Booking Status`, COUNT(*) as cnt FROM rides {date_filter} GROUP BY `Booking Status`", params)
        status_dist = {r['Booking Status']: r['cnt'] for r in cursor.fetchall()}

        payment_dist = {}
        try:
            cursor.execute(f"SELECT `Payment Method`, COUNT(*) as cnt FROM rides {date_filter} GROUP BY `Payment Method`", params)
            payment_dist = {r['Payment Method']: r['cnt'] for r in cursor.fetchall()}
        except Exception: pass

        vehicle_rev = []
        try:
            cursor.execute(f"SELECT `Vehicle Type`, SUM(`Booking Value`) as rev FROM rides {date_filter} GROUP BY `Vehicle Type` ORDER BY rev DESC", params)
            vehicle_rev = cursor.fetchall()
        except Exception: pass

        daily_data = []
        try:
            cursor.execute(
                f"""SELECT `Date`, COUNT(*) as total_rides, SUM(`Booking Value`) as revenue,
                       AVG(`Driver Ratings`) as avg_rating,
                       SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN `Booking Status` LIKE '%Cancel%' THEN 1 ELSE 0 END) as cancellations
                    FROM rides {date_filter} GROUP BY `Date` ORDER BY `Date`""", params
            )
            daily_data = cursor.fetchall()
        except Exception: pass

        top_vehicles = []
        try:
            cursor.execute(
                f"""SELECT `Vehicle Type`, COUNT(*) as total_rides, SUM(`Booking Value`) as total_revenue,
                       AVG(`Booking Value`) as avg_rev_per_ride, AVG(`Driver Ratings`) as avg_rating,
                       SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END)/COUNT(*)*100 as completion_rate
                    FROM rides {date_filter} GROUP BY `Vehicle Type` ORDER BY total_revenue DESC""", params
            )
            top_vehicles = cursor.fetchall()
        except Exception: pass

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
        if previous and previous > 0:
            return (current - previous) / previous * 100
        return 0.0

    # ================== MAIN KPI SECTION ==================
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

    # ================== CHARTS ROW 1 ==================
    def _build_charts_row1(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        # 1. LINE CHART (Actual vs Forecast with Hover)
        trend_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(trend_card, text="📈 Revenue Trend vs Forecast", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        daily = data.get("daily_data", [])
        if daily:
            dates   = [str(r["Date"]) for r in daily]
            actuals = [float(r["revenue"] or 0) for r in daily]
            
            # Forecast Logic Restored
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
            
            # --- Hover Interaction ---
            annot = ax.annotate("", xy=(0,0), xytext=(-20,20), textcoords="offset points",
                                bbox=dict(boxstyle="round4", fc="#111827", ec="none", alpha=0.8),
                                arrowprops=dict(arrowstyle="->", color="#111827"), color="white", fontsize=9, fontweight="bold")
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

        # 2. DONUT CHART (Ride Status with Colors and Hover)
        donut_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        donut_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(donut_card, text="🍩 Ride Status Distribution", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        status_dist = data.get("status_dist", {})
        if status_dist:
            COLOR_MAP = {
                "Completed": "#10B981",            
                "Cancelled by Customer": "#EF4444",
                "Cancelled by Driver": "#F59E0B",  
                "No Driver Found": "#9CA3AF",      
                "Incomplete": "#6B7280"            
            }
            labels = list(status_dist.keys())
            sizes  = list(status_dist.values())
            colors = [COLOR_MAP.get(l, "#CBD5E1") for l in labels]
            
            fig2, ax2 = plt.subplots(figsize=(4.2, 3.5), dpi=92)
            fig2.patch.set_facecolor("white")
            wedges, _, autotexts = ax2.pie(
                sizes, colors=colors, autopct="%1.1f%%",
                pctdistance=0.78, startangle=90,
                wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2)
            )
            for at in autotexts:
                at.set_fontsize(9)
                at.set_fontweight("bold")
                
            ax2.legend(labels, loc="lower center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, -0.08), frameon=False)
            
            # --- Hover Interaction ---
            annot2 = ax2.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                                  bbox=dict(boxstyle="round4", fc="#111827", ec="none", alpha=0.8),
                                  color="white", fontsize=9, fontweight="bold")
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

    # ================== CHARTS ROW 2 ==================
    def _build_charts_row2(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=2)

        # 1. PIE CHART (Payments)
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
            wedges3, _, _ = ax3.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
                                    startangle=90, textprops={"fontsize": 9, "fontweight": "bold"},
                                    wedgeprops={"edgecolor": "white", "linewidth": 2})
            fig3.tight_layout()
            canvas3 = FigureCanvasTkAgg(fig3, pay_card)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(pay_card, text="No Data Available", text_color="#9CA3AF").pack(expand=True, pady=40)

        # 2. BAR CHART (Revenue by Vehicle)
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
            
            # --- Hover Interaction ---
            annot4 = ax4.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points",
                                  bbox=dict(boxstyle="round4", fc="#111827", ec="none", alpha=0.8),
                                  color="white", fontsize=9, fontweight="bold", ha="center")
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

    # ================== RANKING SECTION ==================
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
            tree.insert("", "end", values=(
                medals[i] if i < 3 else f"#{i+1}",
                r.get("Vehicle Type", "N/A"),
                f"{int(r.get('total_rides') or 0):,}",
                f"₹{float(r.get('total_revenue') or 0):,.0f}",
                f"₹{arpu:.0f}", f"⭐ {rat:.2f}", f"✅ {cr:.1f}%", f"{eff:.3f}"
            ))
        tree.pack(fill="x", padx=20, pady=(0, 20))

    # ================== DAILY TABLE WITH TOTALS ==================
  # ================== DAILY TABLE WITH STICKY TOTALS ==================
    def _build_daily_table(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card, text="📅 Performance Summary Table", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 10))

        daily_data = data.get("daily_data", [])
        if not daily_data:
            ctk.CTkLabel(card, text="No Data Available", text_color="#9CA3AF").pack(pady=12)
            return

        self._daily_data = daily_data

        style = ttk.Style()
        # --- FIX: Cấu hình Style khóa hiệu ứng Click ---
        style.configure("Daily.Treeview", rowheight=36, borderwidth=0, font=("Arial", 11), background="#FFFFFF", foreground="#111827")
        style.configure("Daily.Treeview.Heading", font=("Arial", 11, "bold"), background="#F3F4F6", foreground="#4B5563")
        # Ép màu nền trắng, chữ đen khi bị click (selected)
        style.map("Daily.Treeview", 
                  background=[('selected', '#FFFFFF')], 
                  foreground=[('selected', '#111827')])

        style.configure("Total.Treeview", rowheight=36, borderwidth=0, font=("Arial", 12, "bold"), background="#F9FAFB", fieldbackground="#F9FAFB", foreground="#111827")
        # Ép màu nền xám nhạt, chữ đen khi bị click (selected)
        style.map("Total.Treeview", 
                  background=[('selected', '#F9FAFB')], 
                  foreground=[('selected', '#111827')])
        # ----------------------------------------------

        # --- TẠO KHUNG CHỨA BẢNG ---
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

        # --- NẠP DỮ LIỆU ---
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
                sum_rate += rat
                count += 1

            if prev_rev is not None:
                diff = rev - prev_rev
                if diff > 0: delta_str = f"📈 +₹{diff:,.0f}"
                elif diff < 0: delta_str = f"📉 -₹{abs(diff):,.0f}"
                else: delta_str = "—"
            else:
                delta_str = "—"
            prev_rev = rev

            cr_str = f"🟢 {cr:.1f}%" if cr >= 80 else f"🔴 {cr:.1f}%"
            rat_str = f"⭐ {rat:.1f}" if rat > 0 else "N/A"
            can_str = f"🚫 {can:,}" if can > 0 else f"{can:,}"

            tree_main.insert("", "end", values=(
                str(r["Date"]), f"{total:,}", f"₹{rev:,.0f}",
                cr_str, rat_str, can_str, delta_str
            ))

        avg_cr_total = (sum_comp / sum_rides * 100) if sum_rides > 0 else 0
        avg_rate_total = (sum_rate / count) if count > 0 else 0
        
        tree_total.insert("", "end", values=(
            "TOTALS / AVG", 
            f"{sum_rides:,}", 
            f"₹{sum_rev:,.0f}",
            f"✅ {avg_cr_total:.1f}%", 
            f"⭐ {avg_rate_total:.2f}", 
            f"🚫 {sum_can:,}", 
            "—"
        ))

        tree_main.pack(fill="x")
        tree_total.pack(fill="x")

# ─────────────────────────────────────────────────────────────────
# IN-DEVELOPMENT MODULES
# ─────────────────────────────────────────────────────────────────
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Ride Management Hub", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature in development...", text_color="#6B7280").pack()

class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Driver & Customer Profiles", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature in development...", text_color="#6B7280").pack()

class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Cancel & Risk Analysis", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature in development...", text_color="#6B7280").pack()

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="System Settings", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature in development...", text_color="#6B7280").pack()


# ================= 3. MAIN APP =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
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

        topbar = ctk.CTkFrame(self.right_area, height=70, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        topbar.grid(row=0, column=0, sticky="ew")

        user_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        user_frame.pack(side="right", padx=30, pady=15)
        ctk.CTkLabel(user_frame, text="🔔", font=("Arial", 18), text_color="#6B7280").pack(side="left", padx=15)
        ctk.CTkLabel(user_frame, text="Admin System", font=("Arial", 14, "bold"), text_color="#111827").pack(side="left", padx=10)
        ctk.CTkLabel(user_frame, text="👨‍💻", font=("Arial", 24)).pack(side="left")

        self.main_container = ctk.CTkFrame(self.right_area, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=25)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {
            "Dashboard": DashboardFrame(self.main_container),
            "Rides":     RideManagementFrame(self.main_container),
            "Users":     UserProfileFrame(self.main_container),
            "Risk":      RiskAnalysisFrame(self.main_container),
            "Settings":  SettingsFrame(self.main_container),
        }
        self.show_frame("Dashboard")

    def show_frame(self, frame_key):
        for key, btn in self.nav_btns.items():
            if key == frame_key:
                btn.configure(fg_color="#EEF2FF", text_color="#4F46E5", hover=False)
            else:
                btn.configure(fg_color="transparent", text_color="#6B7280", hover_color="#F9FAFB")

        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_key].grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    auto_setup_database()
    app = App()
    app.mainloop()