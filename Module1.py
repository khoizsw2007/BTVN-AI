import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
from datetime import datetime, timedelta

# Cấu hình giao diện chuẩn
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ================= 1. CẤU HÌNH & TỰ ĐỘNG CÀI ĐẶT DATABASE =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "X456208a*",  # <--- ĐIỀN MẬT KHẨU CỦA BẠN VÀO ĐÂY
    "database": "qlud"
}

def auto_setup_database():
    print("⏳ Khởi động hệ thống RideHub...")
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
                print(f"✅ Database đã sẵn sàng ({count:,} chuyến đi). Bật giao diện...")
                conn.close()
                return

        print("⚠️ Database trống! Bắt đầu tiến trình Import 150.000 dòng từ CSV...")
        start_time = time.time()
        print("📥 Đang đọc file ncr_ride_bookings (4).csv...")
        df = pd.read_csv("ncr_ride_bookings (4).csv")
        
        # Xử lý ô trống thông minh để tránh lỗi
        for col in df.columns:
            if df[col].dtype == 'object' or str(df[col].dtype) == 'string':
                df[col] = df[col].fillna("")
            else:
                df[col] = df[col].fillna(0)
                
        engine_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(engine_url)
        print("🚀 Đang bơm dữ liệu vào MySQL... (Mất khoảng 10-15 giây)")
        df.to_sql(name='rides', con=engine, if_exists='replace', index=False)
        end_time = time.time()
        print(f"✅ HOÀN TẤT IMPORT! Thời gian: {end_time - start_time:.1f} giây. Khởi động UI...")
        conn.close()
    except FileNotFoundError:
        print("❌ LỖI: Không tìm thấy file CSV!")
        exit()
    except Exception as e:
        print(f"❌ Lỗi Hệ Thống: {e}")
        exit()


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        return None


# ================= 2. CÁC MODULE CHÍNH =================

# ─────────────────────────────────────────────────────────────────
# MODULE 1: DASHBOARD (Dashboard + Báo cáo doanh thu tổng hợp)
# ─────────────────────────────────────────────────────────────────
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

    # SECTION 1 – Date Range Control & Report Gen
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(header, text="Executive Operations Dashboard",
                     font=ctk.CTkFont(family="Arial", size=26, weight="bold"), 
                     text_color="#111827").pack(side="left")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        # Khung chứa bộ lọc với viền bo góc hiện đại
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

        # Nút Generate hiện đại, to bản
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
            messagebox.showerror("Lỗi tải dữ liệu", str(e))
            return
        
        self._build_kpi_section(self.scroll, data)
        self._build_charts_row1(self.scroll, data)
        self._build_charts_row2(self.scroll, data)
        self._build_top_vehicles(self.scroll, data)
        self._build_daily_table(self.scroll, data)
        self._build_aggregated_summary(self.scroll, data)

    def _load_all_data(self, start_date, end_date):
        conn = get_db_connection()
        if not conn:
            return {}
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
                if row:
                    prev_kpi = row
            except Exception:
                pass

        cursor.execute(
            f"SELECT `Booking Status`, COUNT(*) as cnt FROM rides {date_filter} "
            f"GROUP BY `Booking Status`", params
        )
        status_dist = {r['Booking Status']: r['cnt'] for r in cursor.fetchall()}

        payment_dist = {}
        try:
            cursor.execute(
                f"SELECT `Payment Method`, COUNT(*) as cnt FROM rides {date_filter} "
                f"GROUP BY `Payment Method`", params
            )
            payment_dist = {r['Payment Method']: r['cnt'] for r in cursor.fetchall()}
        except Exception:
            pass

        vehicle_rev = []
        try:
            cursor.execute(
                f"SELECT `Vehicle Type`, SUM(`Booking Value`) as rev FROM rides {date_filter} "
                f"GROUP BY `Vehicle Type` ORDER BY rev DESC", params
            )
            vehicle_rev = cursor.fetchall()
        except Exception:
            pass

        daily_data = []
        try:
            cursor.execute(
                f"""SELECT `Date`,
                       COUNT(*) as total_rides,
                       SUM(`Booking Value`) as revenue,
                       AVG(`Driver Ratings`) as avg_rating,
                       SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN `Booking Status` LIKE '%Cancel%' THEN 1 ELSE 0 END) as cancellations
                    FROM rides {date_filter}
                    GROUP BY `Date`
                    ORDER BY `Date`""", params
            )
            daily_data = cursor.fetchall()
        except Exception:
            pass

        top_vehicles = []
        try:
            cursor.execute(
                f"""SELECT `Vehicle Type`,
                       COUNT(*) as total_rides,
                       SUM(`Booking Value`) as total_revenue,
                       AVG(`Booking Value`) as avg_rev_per_ride,
                       AVG(`Driver Ratings`) as avg_rating,
                       SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END)/COUNT(*)*100 as completion_rate
                    FROM rides {date_filter}
                    GROUP BY `Vehicle Type`
                    ORDER BY total_revenue DESC""", params
            )
            top_vehicles = cursor.fetchall()
        except Exception:
            pass

        conn.close()
        return {
            "total": total, "revenue": revenue, "avg_rate": avg_rate,
            "avg_vtat": avg_vtat, "completion_rate": completion_rate,
            "avg_rev_per_ride": avg_rev_per_ride,
            "prev_total": int(prev_kpi.get("total") or 0),
            "prev_revenue": float(prev_kpi.get("revenue") or 0),
            "status_dist": status_dist, "payment_dist": payment_dist,
            "vehicle_rev": vehicle_rev, "daily_data": daily_data,
            "top_vehicles": top_vehicles,
        }

    @staticmethod
    def _pct(current, previous):
        if previous and previous > 0:
            return (current - previous) / previous * 100
        return 0.0

    # SECTION 2 – Executive KPI Overview
    def _build_kpi_section(self, parent, data):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 15))

        pct_rides = self._pct(data["total"],   data["prev_total"])
        pct_rev   = self._pct(data["revenue"], data["prev_revenue"])

        cards = [
            ("🚗 Total Rides",        f"{data['total']:,}",
             f"{pct_rides:+.1f}% vs kỳ trước",   "#3B82F6"),
            ("💰 Total Revenue",       f"₹{data['revenue']:,.0f}",
             f"{pct_rev:+.1f}% vs kỳ trước",      "#10B981"),
            ("✅ Completion Rate",     f"{data['completion_rate']:.1f}%",
             "của tổng số chuyến",                 "#8B5CF6"),
            ("⭐ Avg Driver Rating",   f"{data['avg_rate']:.2f}",
             "trên thang 5.0",                     "#F59E0B"),
            ("📈 Avg Revenue / Ride",  f"₹{data['avg_rev_per_ride']:.0f}",
             "doanh thu mỗi chuyến",               "#14B8A6"),
            ("⏱ Avg Pickup Time",     f"{data['avg_vtat']:.1f} min",
             "thời gian tài xế đến",               "#EF4444"),
        ]

        for i, (title, value, sub, color) in enumerate(cards):
            card = ctk.CTkFrame(frame, fg_color="#FFFFFF", corner_radius=12, height=125,
                                border_width=1, border_color="#E5E7EB")
            card.grid(row=0, column=i, padx=(0, 15), sticky="ew")
            card.grid_propagate(False)
            frame.grid_columnconfigure(i, weight=1)
            
            # Thanh line màu nổi bật
            ctk.CTkFrame(card, fg_color=color, height=6, corner_radius=3).place(x=0, y=0, relwidth=1)
            
            ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"),
                         text_color="#6B7280").place(x=15, y=20)
            ctk.CTkLabel(card, text=value,
                         font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
                         text_color="#111827").place(x=15, y=48)
            
            # Icon mũi tên tăng giảm
            arrow = "▲" if "+" in sub else ("▼" if "-" in sub else "")
            trend_color = "#10B981" if "+" in sub else ("#EF4444" if "-" in sub else "#9CA3AF")
            ctk.CTkLabel(card, text=f"{arrow} {sub}", font=("Arial", 11, "bold"),
                         text_color=trend_color).place(x=15, y=88)

    # SECTION 3 & 4 – Charts Row 1
    def _build_charts_row1(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        trend_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(trend_card, text="📈 Revenue Trend vs Forecast",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        daily = data.get("daily_data", [])
        if daily:
            dates   = [str(r["Date"]) for r in daily]
            actuals = [float(r["revenue"] or 0) for r in daily]
            avg_rev = sum(actuals) / len(actuals) if actuals else 0
            forecasts = [avg_rev * (1 + 0.015 * (i - len(actuals) / 2)) for i in range(len(actuals))]
            total_actual   = sum(actuals)
            total_forecast = sum(forecasts)
            delta_pct      = self._pct(total_actual, total_forecast)
            arrow          = "▲" if delta_pct >= 0 else "▼"
            badge_color    = "#10B981" if delta_pct >= 0 else "#EF4444"

            info = ctk.CTkFrame(trend_card, fg_color="#F3F4F6", corner_radius=8)
            info.pack(fill="x", padx=20, pady=(10, 0))
            ctk.CTkLabel(
                info,
                text=(f"  Actual: ₹{total_actual:,.0f}   │   "
                      f"Forecast: ₹{total_forecast:,.0f}   │   "
                      f"{arrow} {abs(delta_pct):.1f}% vs forecast"),
                font=("Arial", 11, "bold"), text_color=badge_color
            ).pack(pady=8)

            fig, ax = plt.subplots(figsize=(7, 3), dpi=92)
            fig.patch.set_facecolor("white")
            xs = range(len(dates))
            ax.fill_between(xs, actuals, alpha=0.12, color="#3B82F6")
            ax.plot(xs, actuals,   marker="o", color="#3B82F6", lw=2, markersize=5, label="Actual")
            ax.plot(xs, forecasts, linestyle="--", color="#EF4444", lw=2, label="Forecast")
            step = max(1, len(dates) // 8)
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i][-5:] for i in range(0, len(dates), step)], rotation=40, fontsize=8)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax.set_ylabel("Revenue", fontsize=9)
            ax.legend(fontsize=9, loc="upper left")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, trend_card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(5, 15))
        else:
            ctk.CTkLabel(trend_card, text="Không có dữ liệu", text_color="#9CA3AF").pack(expand=True, pady=40)

        donut_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        donut_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(donut_card, text="🍩 Ride Status Distribution",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        status_dist = data.get("status_dist", {})
        if status_dist:
            COLORS = {"Completed": "#10B981", "Cancelled": "#EF4444", "Cancelled by Driver": "#F59E0B"}
            labels = list(status_dist.keys())
            sizes  = list(status_dist.values())
            colors = [COLORS.get(l, "#9CA3AF") for l in labels]
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
            ax2.legend(labels, loc="lower center", ncol=2, fontsize=8,
                       bbox_to_anchor=(0.5, -0.08), frameon=False)
            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, donut_card)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(donut_card, text="Không có dữ liệu", text_color="#9CA3AF").pack(expand=True, pady=40)

    # SECTION 5 & 6 – Charts Row 2
    def _build_charts_row2(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=2)

        pay_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        pay_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ctk.CTkLabel(pay_card, text="💳 Payment Distribution",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        payment_dist = data.get("payment_dist", {})
        if payment_dist:
            labels = [k for k in payment_dist if k and str(k) not in ("0", "None", "nan")]
            sizes  = [payment_dist[k] for k in labels]
            colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6"][:len(labels)]
            fig3, ax3 = plt.subplots(figsize=(4, 3.5), dpi=92)
            fig3.patch.set_facecolor("white")
            ax3.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
                    startangle=90, textprops={"fontsize": 9, "fontweight": "bold"},
                    wedgeprops={"edgecolor": "white", "linewidth": 2})
            fig3.tight_layout()
            canvas3 = FigureCanvasTkAgg(fig3, pay_card)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(pay_card, text="Không có dữ liệu", text_color="#9CA3AF").pack(expand=True, pady=40)

        veh_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        veh_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(veh_card, text="🚙 Revenue by Vehicle Type",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 0))

        vehicle_rev = data.get("vehicle_rev", [])
        if vehicle_rev:
            v_types = [str(r["Vehicle Type"]) for r in vehicle_rev]
            v_revs  = [float(r["rev"] or 0) for r in vehicle_rev]
            bar_colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6"][:len(v_types)]
            fig4, ax4 = plt.subplots(figsize=(6, 3.5), dpi=92)
            fig4.patch.set_facecolor("white")
            bars = ax4.bar(v_types, v_revs, color=bar_colors, width=0.6,
                           edgecolor="white", linewidth=1.5)
            ax4.spines["top"].set_visible(False)
            ax4.spines["right"].set_visible(False)
            ax4.set_ylabel("Revenue (₹)", fontsize=9)
            ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax4.tick_params(axis="x", labelsize=9)
            max_rev = max(v_revs) if v_revs else 1
            for bar, val in zip(bars, v_revs):
                ax4.text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + max_rev * 0.015,
                         f"₹{val/1000:.0f}k", ha="center", fontsize=8.5,
                         fontweight="bold", color="#111827")
            fig4.tight_layout()
            canvas4 = FigureCanvasTkAgg(fig4, veh_card)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 15))
        else:
            ctk.CTkLabel(veh_card, text="Không có dữ liệu", text_color="#9CA3AF").pack(expand=True, pady=40)

    # SECTION 7 – Top Performing Vehicles
    def _build_top_vehicles(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(card, text="🏆 Top Performing Vehicles — Ranking System",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 10))

        top_vehicles = data.get("top_vehicles", [])
        if not top_vehicles:
            ctk.CTkLabel(card, text="Không có dữ liệu", text_color="#9CA3AF").pack(pady=12)
            return

        max_avg = max((float(r.get("avg_rev_per_ride") or 0) for r in top_vehicles), default=1) or 1
        style = ttk.Style()
        style.configure("TopVeh.Treeview",         rowheight=36, borderwidth=0, font=("Arial", 11), background="#FFFFFF")
        style.configure("TopVeh.Treeview.Heading", font=("Arial", 11, "bold"), background="#F3F4F6", foreground="#4B5563")

        cols   = ("Rank", "Vehicle Type", "Total Rides", "Total Revenue",
                  "Rev / Ride", "Avg Rating", "Completion %", "Efficiency Score")
        widths = (70, 140, 110, 140, 120, 110, 120, 140)
        tree   = ttk.Treeview(card, columns=cols, show="headings",
                              height=min(len(top_vehicles), 7), style="TopVeh.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        medals     = ["🥇", "🥈", "🥉"]
        sorted_veh = sorted(top_vehicles,
                            key=lambda r: float(r.get("total_revenue") or 0), reverse=True)
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
                f"₹{arpu:.0f}", f"{rat:.2f} ⭐", f"{cr:.1f}%", f"{eff:.3f}"
            ))
        tree.pack(fill="x", padx=20, pady=(0, 20))

    # SECTION 8 – Performance Summary Table (Daily)
    def _build_daily_table(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(card, text="📅 Performance Summary Table — Daily Level",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 10))

        daily_data = data.get("daily_data", [])
        if not daily_data:
            ctk.CTkLabel(card, text="Không có dữ liệu", text_color="#9CA3AF").pack(pady=12)
            return

        style = ttk.Style()
        style.configure("Daily.Treeview",         rowheight=34, borderwidth=0, font=("Arial", 10), background="#FFFFFF")
        style.configure("Daily.Treeview.Heading", font=("Arial", 10, "bold"), background="#F3F4F6", foreground="#4B5563")

        sb   = ttk.Scrollbar(card)
        sb.pack(side="right", fill="y", pady=15, padx=(0, 5))
        cols   = ("Date", "Total Rides", "Revenue", "Completion Rate",
                  "Avg Rating", "Cancellations", "Rev Change Δ")
        widths = (110, 105, 120, 125, 100, 120, 120)
        tree   = ttk.Treeview(card, columns=cols, show="headings",
                              height=min(len(daily_data), 10),
                              yscrollcommand=sb.set, style="Daily.Treeview")
        sb.config(command=tree.yview)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        prev_rev = None
        for r in daily_data:
            rev   = float(r["revenue"] or 0)
            total = int(r["total_rides"] or 0)
            comp  = int(r["completed"] or 0)
            cr    = (comp / total * 100) if total > 0 else 0
            rat   = float(r["avg_rating"] or 0)
            can   = int(r["cancellations"] or 0)
            delta_str = (f"{self._pct(rev, prev_rev):+.1f}%"
                         if prev_rev and prev_rev > 0 else "—")
            prev_rev = rev
            tree.insert("", "end", values=(
                str(r["Date"]), f"{total:,}", f"₹{rev:,.0f}",
                f"{cr:.1f}%", f"{rat:.2f}", f"{can:,}", delta_str
            ))
        tree.pack(fill="x", padx=20, pady=(0, 20))

    # SECTION 9 – Aggregated Summary
    def _build_aggregated_summary(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 25))
        ctk.CTkLabel(card, text="📊 Aggregated Summary — Tổng kết toàn kỳ",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 10))

        daily   = data.get("daily_data", [])
        t_rides = sum(int(r["total_rides"] or 0)    for r in daily)
        t_rev   = sum(float(r["revenue"] or 0)       for r in daily)
        t_can   = sum(int(r["cancellations"] or 0)   for r in daily)
        t_comp  = sum(int(r["completed"] or 0)       for r in daily)
        avg_cr  = (t_comp / t_rides * 100) if t_rides > 0 else 0

        summaries = [
            ("📦 Total Rides",        f"{t_rides:,}",         "#3B82F6"),
            ("💵 Total Revenue",       f"₹{t_rev:,.0f}",       "#10B981"),
            ("✅ Avg Completion Rate", f"{avg_cr:.1f}%",        "#8B5CF6"),
            ("⭐ Avg Driver Rating",   f"{data['avg_rate']:.2f}","#F59E0B"),
            ("❌ Total Cancellations", f"{t_can:,}",            "#EF4444"),
        ]

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 20))
        for i, (title, val, color) in enumerate(summaries):
            c = ctk.CTkFrame(row, fg_color="#F9FAFB", corner_radius=10, height=95)
            c.grid(row=0, column=i, padx=(0, 15), sticky="ew")
            c.grid_propagate(False)
            row.grid_columnconfigure(i, weight=1)
            ctk.CTkFrame(c, fg_color=color, height=4, corner_radius=2).place(x=0, y=0, relwidth=1)
            ctk.CTkLabel(c, text=title, font=("Arial", 11, "bold"),
                         text_color="#6B7280").place(x=15, y=15)
            ctk.CTkLabel(c, text=val, font=("Arial", 22, "bold"),
                         text_color="#111827").place(x=15, y=45)


# ─────────────────────────────────────────────────────────────────
# MODULE 2: QUẢN LÝ CHUYẾN XE (Đang phát triển)
# ─────────────────────────────────────────────────────────────────
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Ride Management Hub",
                     font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...", text_color="#6B7280").pack()


# ─────────────────────────────────────────────────────────────────
# MODULE 3: HỒ SƠ TÀI XẾ & KHÁCH HÀNG (Đang phát triển)
# ─────────────────────────────────────────────────────────────────
class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Driver & Customer Profiles",
                     font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...", text_color="#6B7280").pack()


# ─────────────────────────────────────────────────────────────────
# MODULE 4: PHÂN TÍCH HỦY CHUYẾN & RỦI RO (Đang phát triển)
# ─────────────────────────────────────────────────────────────────
class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Cancel & Risk Analysis",
                     font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...", text_color="#6B7280").pack()


# ─────────────────────────────────────────────────────────────────
# MODULE 5: CÀI ĐẶT (Đang phát triển)
# ─────────────────────────────────────────────────────────────────
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="System Settings",
                     font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...", text_color="#6B7280").pack()


# ================= 3. KHỞI CHẠY APP CHÍNH =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub Admin — Enterprise Edition")
        self.geometry("1450x850")
        self.configure(fg_color="#F3F4F6")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── SIDEBAR (white SaaS style) ──
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="#FFFFFF",
                                    corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(25, 30), padx=20, sticky="w")
        ctk.CTkLabel(logo_frame, text="🚕", font=("Arial", 28)).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" RideHub",
                     font=("Arial", 22, "bold"), text_color="#111827").pack(side="left", padx=5)

        self.nav_btns = {}
        # Đã cập nhật lại Menu đầy đủ 5 modules
        nav_items = [
            ("📊  Dashboard",                  "Dashboard"),
            ("🛣️  Ride Management",             "Rides"),
            ("👤  Driver & Customer Profiles",  "Users"),
            ("📈  Cancel & Risk Analysis",      "Risk"),
            ("⚙️  Settings",                    "Settings"),
        ]
        
        for i, (text, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=text, anchor="w",
                fg_color="transparent", text_color="#6B7280",
                font=("Arial", 14, "bold"), height=50, corner_radius=10,
                hover_color="#F9FAFB",
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=6)
            self.nav_btns[key] = btn

        # ── RIGHT AREA ──
        self.right_area = ctk.CTkFrame(self, fg_color="transparent")
        self.right_area.grid(row=0, column=1, sticky="nsew")
        self.right_area.grid_rowconfigure(1, weight=1)
        self.right_area.grid_columnconfigure(0, weight=1)

        # Topbar
        topbar = ctk.CTkFrame(self.right_area, height=70, fg_color="#FFFFFF",
                               corner_radius=0, border_width=1, border_color="#E5E7EB")
        topbar.grid(row=0, column=0, sticky="ew")

        user_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        user_frame.pack(side="right", padx=30, pady=15)
        ctk.CTkLabel(user_frame, text="🔔", font=("Arial", 18),
                     text_color="#6B7280").pack(side="left", padx=15)
        ctk.CTkLabel(user_frame, text="Admin System",
                     font=("Arial", 14, "bold"), text_color="#111827").pack(side="left", padx=10)
        ctk.CTkLabel(user_frame, text="👨‍💻", font=("Arial", 24)).pack(side="left")

        # Main content
        self.main_container = ctk.CTkFrame(self.right_area, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=25)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Khai báo lại đủ 5 frame
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