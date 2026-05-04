import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
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
    """Hàm tự động tạo Database, tạo Bảng và Import CSV siêu tốc"""
    print("⏳ Khởi động hệ thống RideHub...")
    
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
                print(f"✅ Database đã sẵn sàng ({count:,} chuyến đi). Bật giao diện...")
                conn.close()
                return

        print("⚠️ Database trống! Bắt đầu tiến trình Import 150.000 dòng từ CSV...")
        start_time = time.time()
        print("📥 Đang đọc file ncr_ride_bookings (4).csv...")
        df = pd.read_csv("ncr_ride_bookings (4).csv")
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


# ================= 2. CÁC MODULE GIAO DIỆN CHÍNH =================

# ─────────────────────────────────────────────────────────────────
# MODULE 1: DASHBOARD (tổng hợp Dashboard + Báo cáo doanh thu)
# ─────────────────────────────────────────────────────────────────
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._daily_data = []       # dữ liệu ngày để export

        # ── Header + Date range control ──
        self._build_header()

        # ── Vùng nội dung cuộn ──
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=(8, 0))

        # Load mặc định 30 ngày gần nhất
        end   = datetime.now()
        start = end - timedelta(days=30)
        self.start_var.set(start.strftime("%Y-%m-%d"))
        self.end_var.set(end.strftime("%Y-%m-%d"))
        self.generate_report()

    # ──────────────────────────────────────────────
    # SECTION 1 – Date Range Control & Report Gen
    # ──────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            header, text="Executive Operations Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkLabel(right, text="From:", font=("Arial", 12)).pack(side="left", padx=(0, 4))
        self.start_var = ctk.StringVar()
        ctk.CTkEntry(right, textvariable=self.start_var, width=115,
                     placeholder_text="YYYY-MM-DD").pack(side="left", padx=(0, 12))

        ctk.CTkLabel(right, text="To:", font=("Arial", 12)).pack(side="left", padx=(0, 4))
        self.end_var = ctk.StringVar()
        ctk.CTkEntry(right, textvariable=self.end_var, width=115,
                     placeholder_text="YYYY-MM-DD").pack(side="left", padx=(0, 14))

        ctk.CTkButton(
            right, text="🔄  Generate Report",
            fg_color="#3498db", hover_color="#2980b9", width=150,
            command=self.generate_report
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            right, text="📊  Export Excel",
            fg_color="#27ae60", hover_color="#219a52", width=130,
            command=self.export_excel
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            right, text="📄  Export PDF",
            fg_color="#e74c3c", hover_color="#c0392b", width=120,
            command=self.export_pdf
        ).pack(side="left")

    # ──────────────────────────────
    # Sinh báo cáo theo khoảng ngày
    # ──────────────────────────────
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

        # Vẽ từng section theo thứ tự
        self._build_kpi_section(self.scroll, data)        # Section 2
        self._build_charts_row1(self.scroll, data)        # Section 3 + 4
        self._build_charts_row2(self.scroll, data)        # Section 5 + 6
        self._build_top_vehicles(self.scroll, data)       # Section 7
        self._build_daily_table(self.scroll, data)        # Section 8
        self._build_aggregated_summary(self.scroll, data) # Section 9

    # ─────────────────────────────
    # Truy vấn toàn bộ dữ liệu DB
    # ─────────────────────────────
    def _load_all_data(self, start_date, end_date):
        conn = get_db_connection()
        if not conn:
            return {}
        cursor = conn.cursor(dictionary=True)

        # Bộ lọc ngày chính
        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE `Date` BETWEEN %s AND %s"
            params = [start_date, end_date]

        # Kỳ trước để tính % thay đổi
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

        # ── KPI tổng thể ──
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

        # ── KPI kỳ trước ──
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

        # ── Phân bổ trạng thái ──
        cursor.execute(
            f"SELECT `Booking Status`, COUNT(*) as cnt FROM rides {date_filter} "
            f"GROUP BY `Booking Status`", params
        )
        status_dist = {r['Booking Status']: r['cnt'] for r in cursor.fetchall()}

        # ── Phân bổ phương thức thanh toán ──
        payment_dist = {}
        try:
            cursor.execute(
                f"SELECT `Payment Method`, COUNT(*) as cnt FROM rides {date_filter} "
                f"GROUP BY `Payment Method`", params
            )
            payment_dist = {r['Payment Method']: r['cnt'] for r in cursor.fetchall()}
        except Exception:
            pass

        # ── Doanh thu theo loại xe ──
        vehicle_rev = []
        try:
            cursor.execute(
                f"SELECT `Vehicle Type`, SUM(`Booking Value`) as rev FROM rides {date_filter} "
                f"GROUP BY `Vehicle Type` ORDER BY rev DESC", params
            )
            vehicle_rev = cursor.fetchall()
        except Exception:
            pass

        # ── Dữ liệu theo ngày ──
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

        # ── Top phương tiện theo hiệu suất ──
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
            "total": total,
            "revenue": revenue,
            "avg_rate": avg_rate,
            "avg_vtat": avg_vtat,
            "completion_rate": completion_rate,
            "avg_rev_per_ride": avg_rev_per_ride,
            "prev_total": int(prev_kpi.get("total") or 0),
            "prev_revenue": float(prev_kpi.get("revenue") or 0),
            "status_dist": status_dist,
            "payment_dist": payment_dist,
            "vehicle_rev": vehicle_rev,
            "daily_data": daily_data,
            "top_vehicles": top_vehicles,
        }

    # ─────────────────────────────────
    # Helper: tính % thay đổi so với kỳ trước
    # ─────────────────────────────────
    @staticmethod
    def _pct(current, previous):
        if previous and previous > 0:
            return (current - previous) / previous * 100
        return 0.0

    # ──────────────────────────────────────────────────────
    # SECTION 2 – Executive KPI Overview (6 thẻ chỉ số)
    # ──────────────────────────────────────────────────────
    def _build_kpi_section(self, parent, data):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 14))

        pct_rides = self._pct(data["total"],   data["prev_total"])
        pct_rev   = self._pct(data["revenue"], data["prev_revenue"])

        cards = [
            ("🚗  Total Rides",        f"{data['total']:,}",
             f"{pct_rides:+.1f}% vs kỳ trước",   "#3498db"),
            ("💰  Total Revenue",       f"₹{data['revenue']:,.0f}",
             f"{pct_rev:+.1f}% vs kỳ trước",      "#2ecc71"),
            ("✅  Completion Rate",     f"{data['completion_rate']:.1f}%",
             "của tổng số chuyến",                 "#9b59b6"),
            ("⭐  Avg Driver Rating",   f"{data['avg_rate']:.2f}",
             "trên thang 5.0",                     "#f39c12"),
            ("📈  Avg Revenue / Ride",  f"₹{data['avg_rev_per_ride']:.0f}",
             "doanh thu mỗi chuyến",               "#1abc9c"),
            ("⏱  Avg Pickup Time",     f"{data['avg_vtat']:.1f} min",
             "thời gian tài xế đến",               "#e74c3c"),
        ]

        for i, (title, value, sub, color) in enumerate(cards):
            card = ctk.CTkFrame(frame, fg_color="white", corner_radius=12, height=115)
            card.grid(row=0, column=i, padx=(0, 12), sticky="ew")
            card.grid_propagate(False)
            frame.grid_columnconfigure(i, weight=1)

            # Thanh màu trên đầu card
            accent = ctk.CTkFrame(card, fg_color=color, height=5, corner_radius=2)
            accent.place(x=0, y=0, relwidth=1)

            ctk.CTkLabel(card, text=title, font=("Arial", 11, "bold"),
                         text_color="#7f8c8d").place(x=14, y=16)
            ctk.CTkLabel(card, text=value,
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=color).place(x=14, y=44)
            ctk.CTkLabel(card, text=sub, font=("Arial", 10),
                         text_color="#95a5a6").place(x=14, y=88)

    # ──────────────────────────────────────────────────────
    # SECTION 3 – Revenue Trend vs Forecast  (line chart)
    # SECTION 4 – Ride Status Distribution   (donut chart)
    # ──────────────────────────────────────────────────────
    def _build_charts_row1(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        # ── Revenue Trend vs Forecast ──
        trend_card = ctk.CTkFrame(row, fg_color="white", corner_radius=12)
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(trend_card, text="📈  Revenue Trend vs Forecast",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 0))

        daily = data.get("daily_data", [])
        if daily:
            dates   = [str(r["Date"]) for r in daily]
            actuals = [float(r["revenue"] or 0) for r in daily]
            avg_rev = sum(actuals) / len(actuals) if actuals else 0
            # Forecast = đường xu hướng tuyến tính nhẹ quanh trung bình
            forecasts = [avg_rev * (1 + 0.015 * (i - len(actuals) / 2))
                         for i in range(len(actuals))]

            # Tóm tắt Actual vs Forecast
            total_actual   = sum(actuals)
            total_forecast = sum(forecasts)
            delta_pct      = self._pct(total_actual, total_forecast)
            arrow          = "▲" if delta_pct >= 0 else "▼"
            badge_color    = "#27ae60" if delta_pct >= 0 else "#e74c3c"

            info = ctk.CTkFrame(trend_card, fg_color="#f0f4f8", corner_radius=8)
            info.pack(fill="x", padx=16, pady=(6, 0))
            ctk.CTkLabel(
                info,
                text=(f"  Actual: ₹{total_actual:,.0f}   │   "
                      f"Forecast: ₹{total_forecast:,.0f}   │   "
                      f"{arrow} {abs(delta_pct):.1f}% vs forecast"),
                font=("Arial", 10, "bold"), text_color=badge_color
            ).pack(pady=6)

            fig, ax = plt.subplots(figsize=(7, 3), dpi=92)
            fig.patch.set_facecolor("white")
            xs = range(len(dates))
            ax.fill_between(xs, actuals, alpha=0.12, color="#3498db")
            ax.plot(xs, actuals,   marker="o", color="#3498db", lw=2,
                    markersize=4, label="Actual")
            ax.plot(xs, forecasts, linestyle="--", color="#e74c3c", lw=1.8,
                    label="Forecast")

            # Nhãn trục X
            step = max(1, len(dates) // 8)
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i][-5:] for i in range(0, len(dates), step)],
                               rotation=40, fontsize=8)
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax.set_ylabel("Revenue", fontsize=9)
            ax.legend(fontsize=9, loc="upper left")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, trend_card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(4, 12))
        else:
            ctk.CTkLabel(trend_card, text="Không có dữ liệu",
                         text_color="gray").pack(expand=True, pady=40)

        # ── Ride Status Distribution (Donut) ──
        donut_card = ctk.CTkFrame(row, fg_color="white", corner_radius=12)
        donut_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(donut_card, text="🍩  Ride Status Distribution",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 0))

        status_dist = data.get("status_dist", {})
        if status_dist:
            COLORS = {
                "Completed": "#2ecc71",
                "Cancelled": "#e74c3c",
                "Cancelled by Driver": "#e67e22",
            }
            labels = list(status_dist.keys())
            sizes  = list(status_dist.values())
            colors = [COLORS.get(l, "#95a5a6") for l in labels]

            fig2, ax2 = plt.subplots(figsize=(4.2, 3.5), dpi=92)
            fig2.patch.set_facecolor("white")
            wedges, _, autotexts = ax2.pie(
                sizes, colors=colors, autopct="%1.1f%%",
                pctdistance=0.78, startangle=90,
                wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2)
            )
            for at in autotexts:
                at.set_fontsize(9)
            ax2.legend(labels, loc="lower center", ncol=2, fontsize=8,
                       bbox_to_anchor=(0.5, -0.08), frameon=False)
            fig2.tight_layout()

            canvas2 = FigureCanvasTkAgg(fig2, donut_card)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 12))
        else:
            ctk.CTkLabel(donut_card, text="Không có dữ liệu",
                         text_color="gray").pack(expand=True, pady=40)

    # ──────────────────────────────────────────────────────
    # SECTION 5 – Payment Distribution   (pie chart)
    # SECTION 6 – Revenue by Vehicle Type (bar chart)
    # ──────────────────────────────────────────────────────
    def _build_charts_row2(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=2)

        # ── Payment Distribution ──
        pay_card = ctk.CTkFrame(row, fg_color="white", corner_radius=12)
        pay_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(pay_card, text="💳  Payment Distribution",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 0))

        payment_dist = data.get("payment_dist", {})
        if payment_dist:
            labels = [k for k in payment_dist if k and str(k) not in ("0", "None", "nan")]
            sizes  = [payment_dist[k] for k in labels]
            colors = ["#3498db", "#2ecc71", "#f39c12", "#9b59b6",
                      "#e74c3c", "#1abc9c"][:len(labels)]

            fig3, ax3 = plt.subplots(figsize=(4, 3.5), dpi=92)
            fig3.patch.set_facecolor("white")
            ax3.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
                    startangle=90, textprops={"fontsize": 9},
                    wedgeprops={"edgecolor": "white", "linewidth": 2})
            fig3.tight_layout()

            canvas3 = FigureCanvasTkAgg(fig3, pay_card)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 12))
        else:
            ctk.CTkLabel(pay_card, text="Không có dữ liệu",
                         text_color="gray").pack(expand=True, pady=40)

        # ── Revenue by Vehicle Type ──
        veh_card = ctk.CTkFrame(row, fg_color="white", corner_radius=12)
        veh_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(veh_card, text="🚙  Revenue by Vehicle Type",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 0))

        vehicle_rev = data.get("vehicle_rev", [])
        if vehicle_rev:
            v_types = [str(r["Vehicle Type"]) for r in vehicle_rev]
            v_revs  = [float(r["rev"] or 0) for r in vehicle_rev]
            bar_colors = ["#3498db", "#2ecc71", "#f39c12",
                          "#9b59b6", "#e74c3c", "#1abc9c"][:len(v_types)]

            fig4, ax4 = plt.subplots(figsize=(6, 3.5), dpi=92)
            fig4.patch.set_facecolor("white")
            bars = ax4.bar(v_types, v_revs, color=bar_colors, width=0.6,
                           edgecolor="white", linewidth=1.5)
            ax4.spines["top"].set_visible(False)
            ax4.spines["right"].set_visible(False)
            ax4.set_ylabel("Revenue (₹)", fontsize=9)
            ax4.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax4.tick_params(axis="x", labelsize=9)

            max_rev = max(v_revs) if v_revs else 1
            for bar, val in zip(bars, v_revs):
                ax4.text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + max_rev * 0.015,
                         f"₹{val/1000:.0f}k", ha="center", fontsize=8.5,
                         fontweight="bold", color="#2c3e50")
            fig4.tight_layout()

            canvas4 = FigureCanvasTkAgg(fig4, veh_card)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4, 12))
        else:
            ctk.CTkLabel(veh_card, text="Không có dữ liệu",
                         text_color="gray").pack(expand=True, pady=40)

    # ──────────────────────────────────────────────────────
    # SECTION 7 – Top Performing Vehicles (Ranking System)
    # ──────────────────────────────────────────────────────
    def _build_top_vehicles(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(card, text="🏆  Top Performing Vehicles — Ranking System",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        top_vehicles = data.get("top_vehicles", [])
        if not top_vehicles:
            ctk.CTkLabel(card, text="Không có dữ liệu",
                         text_color="gray").pack(pady=12)
            return

        max_avg = max((float(r.get("avg_rev_per_ride") or 0) for r in top_vehicles),
                      default=1) or 1

        style = ttk.Style()
        style.configure("TopVeh.Treeview",    rowheight=34, borderwidth=0, font=("Arial", 10))
        style.configure("TopVeh.Treeview.Heading", font=("Arial", 10, "bold"),
                        background="#eaf2fb")

        cols = ("Rank", "Vehicle Type", "Total Rides", "Total Revenue",
                "Rev / Ride", "Avg Rating", "Completion %", "Efficiency Score")
        widths = (60, 130, 105, 130, 110, 100, 115, 135)

        tree = ttk.Treeview(card, columns=cols, show="headings",
                            height=min(len(top_vehicles), 7),
                            style="TopVeh.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        medals = ["🥇", "🥈", "🥉"]
        sorted_veh = sorted(top_vehicles,
                            key=lambda r: float(r.get("total_revenue") or 0),
                            reverse=True)

        for i, r in enumerate(sorted_veh):
            cr   = float(r.get("completion_rate") or 0)
            rat  = float(r.get("avg_rating") or 0)
            arpu = float(r.get("avg_rev_per_ride") or 0)
            # Efficiency = completion 40% + rating 30% + rev_per_ride 30%
            eff  = (cr / 100) * 0.4 + (rat / 5) * 0.3 + (arpu / max_avg) * 0.3
            rank_str = medals[i] if i < 3 else f"#{i + 1}"
            tree.insert("", "end", values=(
                rank_str,
                r.get("Vehicle Type", "N/A"),
                f"{int(r.get('total_rides') or 0):,}",
                f"₹{float(r.get('total_revenue') or 0):,.0f}",
                f"₹{arpu:.0f}",
                f"{rat:.2f} ⭐",
                f"{cr:.1f}%",
                f"{eff:.3f}"
            ))

        tree.pack(fill="x", padx=16, pady=(0, 14))

    # ──────────────────────────────────────────────────────
    # SECTION 8 – Performance Summary Table (Daily Level)
    # ──────────────────────────────────────────────────────
    def _build_daily_table(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(card, text="📅  Performance Summary Table — Daily Level",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        daily_data = data.get("daily_data", [])
        if not daily_data:
            ctk.CTkLabel(card, text="Không có dữ liệu",
                         text_color="gray").pack(pady=12)
            return

        self._daily_data = daily_data   # lưu để export

        style = ttk.Style()
        style.configure("Daily.Treeview",    rowheight=30, borderwidth=0, font=("Arial", 9))
        style.configure("Daily.Treeview.Heading", font=("Arial", 9, "bold"),
                        background="#eaf2fb")

        sb = ttk.Scrollbar(card)
        sb.pack(side="right", fill="y", pady=14)

        cols   = ("Date", "Total Rides", "Revenue", "Completion Rate",
                  "Avg Rating", "Cancellations", "Rev Change Δ")
        widths = (110, 105, 120, 125, 100, 120, 120)

        tree = ttk.Treeview(card, columns=cols, show="headings",
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
                str(r["Date"]),
                f"{total:,}",
                f"₹{rev:,.0f}",
                f"{cr:.1f}%",
                f"{rat:.2f}",
                f"{can:,}",
                delta_str
            ))

        tree.pack(fill="x", padx=16, pady=(0, 14))

    # ──────────────────────────────────────────────────────
    # SECTION 9 – Aggregated Summary (Totals / Avg)
    # ──────────────────────────────────────────────────────
    def _build_aggregated_summary(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(card, text="📊  Aggregated Summary — Tổng kết toàn kỳ",
                     font=("Arial", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        daily = data.get("daily_data", [])
        t_rides  = sum(int(r["total_rides"] or 0) for r in daily)
        t_rev    = sum(float(r["revenue"] or 0) for r in daily)
        t_can    = sum(int(r["cancellations"] or 0) for r in daily)
        t_comp   = sum(int(r["completed"] or 0) for r in daily)
        avg_cr   = (t_comp / t_rides * 100) if t_rides > 0 else 0

        summaries = [
            ("📦  Total Rides",          f"{t_rides:,}",         "#3498db"),
            ("💵  Total Revenue",         f"₹{t_rev:,.0f}",       "#2ecc71"),
            ("✅  Avg Completion Rate",   f"{avg_cr:.1f}%",        "#9b59b6"),
            ("⭐  Avg Driver Rating",     f"{data['avg_rate']:.2f}","#f39c12"),
            ("❌  Total Cancellations",   f"{t_can:,}",            "#e74c3c"),
        ]

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))

        for i, (title, val, color) in enumerate(summaries):
            c = ctk.CTkFrame(row, fg_color="#f4f6f8", corner_radius=10, height=85)
            c.grid(row=0, column=i, padx=(0, 12), sticky="ew")
            c.grid_propagate(False)
            row.grid_columnconfigure(i, weight=1)

            bar = ctk.CTkFrame(c, fg_color=color, height=4, corner_radius=2)
            bar.place(x=0, y=0, relwidth=1)

            ctk.CTkLabel(c, text=title, font=("Arial", 10, "bold"),
                         text_color="#7f8c8d").place(x=12, y=12)
            ctk.CTkLabel(c, text=val, font=("Arial", 18, "bold"),
                         text_color=color).place(x=12, y=40)

    # ────────────────────
    # Export helpers
    # ────────────────────
    def export_excel(self):
        if not self._daily_data:
            messagebox.showwarning("Cảnh báo", "Hãy Generate Report trước!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Lưu báo cáo Excel"
        )
        if not path:
            return
        try:
            df = pd.DataFrame(self._daily_data)
            df.to_excel(path, index=False)
            messagebox.showinfo("✅ Thành công", f"Đã xuất:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def export_pdf(self):
        messagebox.showinfo(
            "📄 Export PDF",
            "Tính năng Export PDF đang phát triển.\n"
            "Vui lòng dùng 'Export Excel' để tải dữ liệu."
        )


# ─────────────────────────────────────────────────────────────────
# MODULE 2: QUẢN LÝ CHUYẾN XE
# ─────────────────────────────────────────────────────────────────
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Ride Management Hub",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 10))

        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=35, borderwidth=0)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"),
                        background="#f1f2f6")

        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        self.table = ttk.Treeview(
            table_frame,
            columns=("ID", "Date", "Route", "Price", "VTAT", "Status"),
            show="headings", yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.table.yview)

        for col in self.table["columns"]:
            self.table.heading(col, text=col)
            self.table.column(col, width=120, anchor="center")
        self.table.column("Route", width=250)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_data()

    def load_data(self):
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT `Booking ID`, `Date`, `Pickup Location`, `Drop Location`, "
            "`Booking Value`, `Avg VTAT`, `Booking Status` FROM rides LIMIT 150"
        )
        for row in cursor.fetchall():
            route = f"{row['Pickup Location'][:15]} → {row['Drop Location'][:15]}"
            self.table.insert("", "end", values=(
                row["Booking ID"], row["Date"], route,
                f"₹{row['Booking Value']}", f"{row['Avg VTAT']}m",
                row["Booking Status"]
            ))
        conn.close()


# ─────────────────────────────────────────────────────────────────
# MODULE 3: HỒ SƠ TÀI XẾ & KHÁCH HÀNG
# ─────────────────────────────────────────────────────────────────
class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="User Management Hub",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 10))

        control_panel = ctk.CTkFrame(self, fg_color="transparent")
        control_panel.pack(fill="x", pady=(0, 20))

        self.user_type_var = ctk.StringVar(value="Drivers")
        self.tab_menu = ctk.CTkSegmentedButton(
            control_panel, values=["Drivers", "Customers"],
            command=self.refresh_list, variable=self.user_type_var,
            font=("Arial", 13, "bold"), height=35
        )
        self.tab_menu.pack(side="left", padx=(0, 20))

        self.rating_filter = ctk.CTkComboBox(
            control_panel,
            values=["Tất cả Rating", "⭐ 4.0+", "⭐ 4.5+", "⭐ 4.8+"], width=130
        )
        self.rating_filter.set("Tất cả Rating")
        self.rating_filter.pack(side="left", padx=5)

        self.trip_filter = ctk.CTkComboBox(
            control_panel,
            values=["Tất cả chuyến", "> 5 chuyến", "> 10 chuyến", "> 15 chuyến"],
            width=130
        )
        self.trip_filter.set("Tất cả chuyến")
        self.trip_filter.pack(side="left", padx=5)

        ctk.CTkButton(
            control_panel, text="Lọc dữ liệu", width=100,
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self.refresh_list
        ).pack(side="left", padx=10)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.left_side = ctk.CTkFrame(self.main_container, width=300,
                                      fg_color="white", corner_radius=10)
        self.left_side.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.left_side, placeholder_text="Tìm ID...",
                                         height=35, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=15, padx=15)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        self.scroll_list = ctk.CTkScrollableFrame(self.left_side, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.right_side = ctk.CTkFrame(self.main_container, fg_color="white",
                                       corner_radius=10)
        self.right_side.grid(row=0, column=1, sticky="nsew")

        self.show_placeholder()
        self.refresh_list()

    def show_placeholder(self):
        for w in self.right_side.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.right_side,
            text="Chọn tài xế hoặc khách hàng để xem chi tiết",
            text_color="gray"
        ).place(relx=0.5, rely=0.5, anchor="center")

    def refresh_list(self, *args):
        user_type = self.user_type_var.get()
        for w in self.scroll_list.winfo_children():
            w.destroy()

        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor(dictionary=True)

        id_col   = "Driver ID"   if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"

        rate_filter_val = self.rating_filter.get()
        rate_limit = 0
        if "4.8" in rate_filter_val: rate_limit = 4.8
        elif "4.5" in rate_filter_val: rate_limit = 4.5
        elif "4.0" in rate_filter_val: rate_limit = 4.0

        trip_filter_val = self.trip_filter.get()
        trip_limit = 0
        if "15" in trip_filter_val: trip_limit = 15
        elif "10" in trip_filter_val: trip_limit = 10
        elif "5"  in trip_filter_val: trip_limit = 5

        search_text = self.search_var.get().strip()

        query = (
            f"SELECT `{id_col}` as uid, AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips "
            f"FROM rides "
            f"WHERE `{id_col}` IS NOT NULL "
            f"AND `{id_col}` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')"
        )
        params = []
        if search_text:
            query += f" AND `{id_col}` LIKE %s"
            params.append(f"%{search_text}%")

        query += f" GROUP BY `{id_col}`"
        having = []
        if rate_limit > 0: having.append(f"AVG(`{rate_col}`) >= {rate_limit}")
        if trip_limit > 0: having.append(f"COUNT(*) >= {trip_limit}")
        if having: query += " HAVING " + " AND ".join(having)
        query += " ORDER BY total_trips DESC LIMIT 100"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            ctk.CTkLabel(self.scroll_list, text="❌ Không tìm thấy ai phù hợp",
                         text_color="gray").pack(pady=20)
        else:
            for user in rows:
                uid, stars, trips = user["uid"], user["avg_rate"] or 0, user["total_trips"]
                ctk.CTkButton(
                    self.scroll_list,
                    text=f"👤 {uid}\n⭐ {stars:.1f} | 🏁 {trips} chuyến",
                    anchor="w", height=55, fg_color="#f8f9fa",
                    text_color="black", hover_color="#dfe4ea",
                    command=lambda u=uid: self.display_detail(u, user_type)
                ).pack(fill="x", pady=4, padx=10)

        conn.close()

    def display_detail(self, uid, user_type):
        for w in self.right_side.winfo_children():
            w.destroy()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        id_col   = "Driver ID"      if user_type == "Drivers" else "Customer ID"
        rate_col = "Driver Ratings" if user_type == "Drivers" else "Customer Rating"

        cursor.execute(
            f"SELECT AVG(`{rate_col}`) as avg_rate, COUNT(*) as total_trips, "
            f"SUM(`Booking Value`) as total_val FROM rides WHERE `{id_col}` = %s",
            (uid,)
        )
        stats = cursor.fetchone()

        cursor.execute(
            f"SELECT `Booking ID`, `Date`, `Booking Value`, `Booking Status` "
            f"FROM rides WHERE `{id_col}` = %s ORDER BY `Date` DESC LIMIT 5",
            (uid,)
        )
        history = cursor.fetchall()
        conn.close()

        color = "#3498db" if user_type == "Drivers" else "#9b59b6"
        header = ctk.CTkFrame(self.right_side, fg_color=color, height=120, corner_radius=10)
        header.pack(fill="x", padx=25, pady=25)
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=uid, font=("Arial", 30, "bold"),
                     text_color="white").place(x=30, y=25)
        ctk.CTkLabel(header,
                     text=f"Account Type: {user_type[:-1]} | Status: Active",
                     text_color="white").place(x=30, y=70)

        kpi_frame = ctk.CTkFrame(self.right_side, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=25)
        self.add_stat_card(kpi_frame, "AVG RATING",  f"{stats['avg_rate']:.2f} ⭐", 0)
        self.add_stat_card(kpi_frame, "TOTAL TRIPS",  f"{stats['total_trips']:,}", 1)
        self.add_stat_card(kpi_frame, "TOTAL VALUE",
                           f"₹{stats['total_val'] or 0:,.0f}", 2)

        ctk.CTkLabel(self.right_side, text="Lịch sử 5 chuyến đi gần nhất",
                     font=("Arial", 16, "bold")).pack(anchor="w", padx=30, pady=(20, 10))
        table = ttk.Treeview(self.right_side,
                             columns=("ID", "Date", "Price", "Status"),
                             show="headings", height=5)
        for col in table["columns"]:
            table.heading(col, text=col)
            table.column(col, width=120, anchor="center")
        table.pack(fill="x", padx=30, pady=10)
        for trip in history:
            table.insert("", "end", values=(
                trip["Booking ID"], trip["Date"],
                f"₹{trip['Booking Value']}", trip["Booking Status"]
            ))

    def add_stat_card(self, parent, title, val, col):
        card = ctk.CTkFrame(parent, fg_color="#f8f9fa",
                            border_width=1, border_color="#dee2e6",
                            height=90, width=220)
        card.grid(row=0, column=col, padx=(0, 20), pady=10)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Arial", 11, "bold"),
                     text_color="gray").place(x=15, y=15)
        ctk.CTkLabel(card, text=val, font=("Arial", 22, "bold"),
                     text_color="#2c3e50").place(x=15, y=45)


# ─────────────────────────────────────────────────────────────────
# MODULE 4: PHÂN TÍCH HỦY CHUYẾN & SỰ CỐ
# ─────────────────────────────────────────────────────────────────
class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Risk & Fraud Analysis",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...").pack()


# ─────────────────────────────────────────────────────────────────
# MODULE 5: CÀI ĐẶT
# ─────────────────────────────────────────────────────────────────
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="System Settings",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Tính năng đang phát triển...").pack()


# ================= 3. KHỞI CHẠY APP CHÍNH =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub Admin — Enterprise Edition")
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
            "Rides":     RideManagementFrame(self.main_container),
            "Users":     UserProfileFrame(self.main_container),
            "Risk":      RiskAnalysisFrame(self.main_container),
            "Settings":  SettingsFrame(self.main_container),
        }
        self.show_frame("Dashboard")

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#0f172a", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(sidebar, text="☁️  RideHub",
                     font=("Arial", 26, "bold"), text_color="white"
                     ).grid(row=0, column=0, pady=(30, 40))

        self.nav_btns = {}
        nav_items = [
            ("Dashboard",                "Dashboard"),
            ("Ride Management",          "Rides"),
            ("Driver / Customer Profiles","Users"),
            ("Cancel & Risk Analysis",   "Risk"),
            ("Settings",                 "Settings"),
        ]
        for i, (text, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                sidebar, text=text, anchor="w",
                fg_color="transparent", text_color="#cbd5e1",
                hover_color="#1e293b", font=("Arial", 15), height=50,
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=5)
            self.nav_btns[key] = btn

    def show_frame(self, frame_key):
        for key, btn in self.nav_btns.items():
            if key == frame_key:
                btn.configure(fg_color="#1e293b", text_color="white",
                              font=("Arial", 15, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#cbd5e1",
                              font=("Arial", 15))
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_key].grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    auto_setup_database()
    app = App()
    app.mainloop()