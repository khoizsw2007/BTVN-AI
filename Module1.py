import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import time
import math
from datetime import datetime, timedelta

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ================= 1. DATABASE CONFIGURATION =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "X456208a*",  # <--- ĐỔI MẬT KHẨU TẠI ĐÂY
    "database": "qlud"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except:
        return None

def auto_setup_database():
    print("⏳ Starting RideHub system...")
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
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM rides")
            count = cursor.fetchone()[0]
            if count > 10000:
                print(f"✅ Database ready ({count:,} rides).")
                conn.close()
                return

        print("⚠️ Importing CSV...")
        start_time = time.time()
        df = pd.read_csv("ncr_ride_bookings (4).csv")
        for col in df.columns:
            df[col] = df[col].fillna("") if df[col].dtype == 'object' else df[col].fillna(0)
        engine_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(engine_url)
        df.to_sql(name='rides', con=engine, if_exists='replace', index=False)
        print(f"✅ Done in {time.time()-start_time:.1f}s.")
        conn.close()
    except FileNotFoundError:
        print("❌ CSV not found!"); exit()
    except Exception as e:
        print(f"❌ Error: {e}"); exit()


STATUS_COLORS = {
    "Completed":             "#10B981",
    "Cancelled by Customer": "#EF4444",
    "Cancelled by Driver":   "#F59E0B",
    "Incomplete":            "#6B7280",
    "No Driver Found":       "#9CA3AF",
}
DEFAULT_COLOR = "#CBD5E1"
BAR_COLORS = ["#3B82F6","#10B981","#F59E0B","#8B5CF6","#EF4444","#14B8A6"]

# ─────────────────────────────────────────────────────────────────
# MODERN TABLE HELPER (Auto-hiding scrollbar & Perfect Alignment)
# ─────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# MODERN TABLE HELPER (Fixed Width & Auto Alignment)
# ─────────────────────────────────────────────────────────────────
class ModernTable(ctk.CTkFrame):
    ROW_H  = 42
    HEAD_H = 38

    def __init__(self, parent, col_defs, data_rows, totals_row=None, max_scroll_rows=10, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._tip_win    = None
        self._tip_timer  = None
        n = len(col_defs)

        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color="#F9FAFB", height=self.HEAD_H, corner_radius=0, border_width=1, border_color="#E5E7EB")
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        
        # 2 Cột đệm (weight=1) ở 2 bên để căn giữa bảng, các cột nội dung (weight=0)
        hdr.grid_columnconfigure(0, weight=1)
        for c, (txt, w, anc) in enumerate(col_defs):
            hdr.grid_columnconfigure(c+1, weight=0)
            ctk.CTkLabel(hdr, text=txt, width=w, font=("Arial", 10, "bold"), text_color="#6B7280", anchor=anc).grid(row=0, column=c+1, sticky="ew", padx=10)
        hdr.grid_columnconfigure(n+1, weight=1)

        # ── Auto-Switching Frame ──
        if len(data_rows) <= max_scroll_rows:
            sf = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            sf.pack(fill="x")
        else:
            visible_h = max_scroll_rows * self.ROW_H
            sf = ctk.CTkScrollableFrame(self, fg_color="transparent", height=visible_h, corner_radius=0)
            sf.pack(fill="x")
            
        sf.grid_columnconfigure(0, weight=1)

        # ── Rows ──
        for r_idx, row_cells in enumerate(data_rows):
            bg = "#FFFFFF" if r_idx % 2 == 0 else "#F9FAFB"
            row_f = ctk.CTkFrame(sf, fg_color=bg, height=self.ROW_H, corner_radius=0)
            row_f.pack(fill="x")
            row_f.pack_propagate(False)
            
            row_f.grid_columnconfigure(0, weight=1)
            for c, (col_txt, w, anc) in enumerate(col_defs):
                row_f.grid_columnconfigure(c+1, weight=0)
            row_f.grid_columnconfigure(n+1, weight=1)

            for c, (cell_txt, fg, fw) in enumerate(row_cells):
                _, w, anc = col_defs[c]
                lbl = ctk.CTkLabel(row_f, text=cell_txt, width=w, font=("Arial", 11, fw), text_color=fg, anchor=anc)
                lbl.grid(row=0, column=c+1, sticky="ew", padx=10)
                lbl.bind("<Enter>", lambda e, ri=r_idx, ci=c: self._schedule_tip(e, data_rows, ri, ci, col_defs))
                lbl.bind("<Leave>", self._cancel_tip)
            row_f.bind("<Enter>", lambda e, ri=r_idx: self._schedule_tip(e, data_rows, ri, None, col_defs))
            row_f.bind("<Leave>", self._cancel_tip)

        # ── Fixed TOTALS row ──
        if totals_row:
            sep = ctk.CTkFrame(self, fg_color="#E5E7EB", height=2)
            sep.pack(fill="x")
            tot_f = ctk.CTkFrame(self, fg_color="#F3F4F6", height=self.ROW_H, corner_radius=0, border_width=1, border_color="#E5E7EB")
            tot_f.pack(fill="x")
            tot_f.pack_propagate(False)
            
            tot_f.grid_columnconfigure(0, weight=1)
            for c, (col_txt, w, anc) in enumerate(col_defs):
                tot_f.grid_columnconfigure(c+1, weight=0)
            tot_f.grid_columnconfigure(n+1, weight=1)

            for c, (cell_txt, fg, fw) in enumerate(totals_row):
                _, w, anc = col_defs[c]
                ctk.CTkLabel(tot_f, text=cell_txt, width=w, font=("Arial", 11, fw), text_color=fg, anchor=anc).grid(row=0, column=c+1, sticky="ew", padx=10)

    # ── Tooltips ──
    def _schedule_tip(self, event, data_rows, ri, ci, col_defs):
        self._cancel_tip()
        self._tip_timer = self.after(350, lambda: self._show_tip(event.x_root, event.y_root, data_rows, ri, ci, col_defs))

    def _show_tip(self, x, y, data_rows, ri, ci, col_defs):
        self._hide_tip()
        row = data_rows[ri]
        if ci is None:
            lines = [f"{col_defs[c][0]}: {row[c][0]}" for c in range(len(row))]
            tip_text = "\n".join(lines)
        else:
            tip_text = f"{col_defs[ci][0]}\n{row[ci][0]}"

        tw = ctk.CTkToplevel(self)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.geometry(f"+{x+14}+{y+14}")
        f = ctk.CTkFrame(tw, fg_color="#1F2937", corner_radius=8)
        f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text=tip_text, font=("Arial", 11), text_color="#F9FAFB", justify="left").pack(padx=12, pady=8)
        self._tip_win = tw

    def _cancel_tip(self, event=None):
        if self._tip_timer:
            self.after_cancel(self._tip_timer)
            self._tip_timer = None
        self._hide_tip()

    def _hide_tip(self):
        if self._tip_win:
            try: self._tip_win.destroy()
            except: pass
            self._tip_win = None

# ─────────────────────────────────────────────────────────────────
# DASHBOARD FRAME
# ─────────────────────────────────────────────────────────────────
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._canvas_refs = []
        self._build_header()
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=(15, 0))
        self.start_var.set("2024-04-09")
        self.end_var.set("2024-05-09")
        self.generate_report()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(header, text="Executive Operations Dashboard", font=("Arial", 26, "bold"), text_color="#111827").pack(side="left")
        
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")
        filter_box = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        filter_box.pack(side="left", padx=(0, 15), pady=2)
        ctk.CTkLabel(filter_box, text="From:", font=("Arial", 12, "bold"), text_color="#6B7280").pack(side="left", padx=(15,5), pady=8)
        self.start_var = ctk.StringVar()
        ctk.CTkEntry(filter_box, textvariable=self.start_var, width=105, height=32, border_width=0, fg_color="#F3F4F6").pack(side="left", padx=(0,15))
        ctk.CTkLabel(filter_box, text="To:", font=("Arial", 12, "bold"), text_color="#6B7280").pack(side="left", padx=(0,5))
        self.end_var = ctk.StringVar()
        ctk.CTkEntry(filter_box, textvariable=self.end_var, width=105, height=32, border_width=0, fg_color="#F3F4F6").pack(side="left", padx=(0,15))
        ctk.CTkButton(right, text="🔄 Generate Report", font=("Arial", 13, "bold"), fg_color="#4F46E5", hover_color="#4338CA", text_color="#FFFFFF", corner_radius=8, width=165, height=40, command=self.generate_report).pack(side="left")

    def generate_report(self):
        for w in self.scroll.winfo_children(): w.destroy()
        plt.close("all")
        self._canvas_refs.clear()
        start = self.start_var.get().strip()
        end   = self.end_var.get().strip()
        try: data = self._load_all_data(start, end)
        except Exception as e: messagebox.showerror("Data Load Error", str(e)); return
        self._build_kpi_section(self.scroll, data)
        self._build_charts_row1(self.scroll, data)
        self._build_charts_row2(self.scroll, data)
        self._build_top_vehicles(self.scroll, data)
        self._build_daily_table(self.scroll, data)

    def _load_all_data(self, start_date, end_date):
        conn = get_db_connection()
        if not conn: return {}
        cursor = conn.cursor(dictionary=True)
        date_filter, params = "", []
        if start_date and end_date:
            date_filter = "WHERE `Date` BETWEEN %s AND %s"
            params = [start_date, end_date]

        prev_params, prev_filter = [], ""
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d"); e = datetime.strptime(end_date, "%Y-%m-%d")
            delta = e - s; pe = s - timedelta(days=1); ps = pe - delta
            prev_filter = "WHERE `Date` BETWEEN %s AND %s"
            prev_params = [ps.strftime("%Y-%m-%d"), pe.strftime("%Y-%m-%d")]
        except: pass

        cursor.execute(f"SELECT COUNT(*) as total, SUM(`Booking Value`) as revenue, AVG(`Driver Ratings`) as avg_rate, AVG(`Avg VTAT`) as avg_vtat FROM rides {date_filter}", params)
        kpi = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(*) as cnt FROM rides {date_filter}{' AND' if date_filter else ' WHERE'} `Booking Status`='Completed'", params)
        completed = cursor.fetchone()['cnt']
        
        total = int(kpi['total'] or 0); revenue = float(kpi['revenue'] or 0)
        avg_rate = float(kpi['avg_rate'] or 0); avg_vtat = float(kpi['avg_vtat'] or 0)
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
            cursor.execute(f"SELECT `Date`, COUNT(*) as total_rides, SUM(`Booking Value`) as revenue, AVG(`Driver Ratings`) as avg_rating, SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END) as completed, SUM(CASE WHEN `Booking Status` LIKE '%Cancel%' OR `Booking Status`='Incomplete' THEN 1 ELSE 0 END) as cancellations FROM rides {date_filter} GROUP BY `Date` ORDER BY `Date`", params)
            daily_data = cursor.fetchall()
            cursor.execute(f"SELECT `Vehicle Type`, COUNT(*) as total_rides, SUM(`Booking Value`) as total_revenue, AVG(`Booking Value`) as avg_rev_per_ride, AVG(`Driver Ratings`) as avg_rating, SUM(CASE WHEN `Booking Status`='Completed' THEN 1 ELSE 0 END)/COUNT(*)*100 as completion_rate FROM rides {date_filter} GROUP BY `Vehicle Type` ORDER BY total_revenue DESC", params)
            top_vehicles = cursor.fetchall()
        except: pass
        conn.close()
        return {"total": total, "revenue": revenue, "avg_rate": avg_rate, "avg_vtat": avg_vtat, "completion_rate": completion_rate, "avg_rev_per_ride": avg_rev_per_ride, "prev_total": int(prev_kpi.get("total") or 0), "prev_revenue": float(prev_kpi.get("revenue") or 0), "status_dist": status_dist, "payment_dist": payment_dist, "vehicle_rev": vehicle_rev, "daily_data": daily_data, "top_vehicles": top_vehicles}

    @staticmethod
    def _pct(current, previous): return (current - previous) / previous * 100 if previous and previous > 0 else 0.0

    def _build_kpi_section(self, parent, data):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 15))
        pct_rides = self._pct(data["total"], data["prev_total"]); pct_rev = self._pct(data["revenue"], data["prev_revenue"])
        cards = [("🚗 Total Rides", f"{data['total']:,}", f"{pct_rides:+.1f}% vs last period", "#3B82F6"), ("💰 Total Revenue", f"₹{data['revenue']:,.0f}", f"{pct_rev:+.1f}% vs last period", "#10B981"), ("✅ Completion Rate", f"{data['completion_rate']:.1f}%", "of all rides", "#8B5CF6"), ("⭐ Avg Driver Rating", f"{data['avg_rate']:.2f}", "out of 5.0", "#F59E0B"), ("📈 Avg Rev / Ride", f"₹{data['avg_rev_per_ride']:.0f}", "per completed ride", "#14B8A6"), ("⏱ Avg Pickup Time", f"{data['avg_vtat']:.1f} min", "driver arrival time", "#EF4444")]
        for i, (title, value, sub, color) in enumerate(cards):
            card = ctk.CTkFrame(frame, fg_color="#FFFFFF", corner_radius=12, height=125, border_width=1, border_color="#E5E7EB")
            card.grid(row=0, column=i, padx=(0,15), sticky="ew")
            card.grid_propagate(False); frame.grid_columnconfigure(i, weight=1)
            ctk.CTkFrame(card, fg_color=color, height=6, corner_radius=3).place(x=0, y=0, relwidth=1)
            ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"), text_color="#6B7280").place(x=15, y=20)
            ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"), text_color="#111827").place(x=15, y=48)
            tc = "#10B981" if "+" in sub else ("#EF4444" if "-" in sub else "#9CA3AF")
            ctk.CTkLabel(card, text=f"{'▲' if '+' in sub else '▼' if '-' in sub else ''} {sub}".strip(), font=("Arial", 11, "bold"), text_color=tc).place(x=15, y=93)

    def _build_charts_row1(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=3); row.grid_columnconfigure(1, weight=2)
        trend_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0,15))
        ctk.CTkLabel(trend_card, text="📈 Revenue Trend vs Forecast", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15,0))
        daily = data.get("daily_data", [])
        if daily:
            dates = [str(r["Date"]) for r in daily]; actuals = [float(r["revenue"] or 0) for r in daily]
            avg_rev = sum(actuals) / len(actuals) if actuals else 0
            forecasts = [avg_rev * (1 + 0.015*(i-len(actuals)/2)) for i in range(len(actuals))]
            total_actual, total_forecast = sum(actuals), sum(forecasts)
            delta_pct = self._pct(total_actual, total_forecast)
            badge_color = "#10B981" if delta_pct >= 0 else "#EF4444"
            info = ctk.CTkFrame(trend_card, fg_color="#F3F4F6", corner_radius=8)
            info.pack(fill="x", padx=20, pady=(10,0))
            ctk.CTkLabel(info, text=(f"  Actual: ₹{total_actual:,.0f}   │   Forecast: ₹{total_forecast:,.0f}   │   {'▲' if delta_pct >= 0 else '▼'} {abs(delta_pct):.1f}% vs forecast"), font=("Arial", 11, "bold"), text_color=badge_color).pack(pady=8)
            fig, ax = plt.subplots(figsize=(7, 3), dpi=92); fig.patch.set_facecolor("white")
            xs = list(range(len(dates)))
            ax.fill_between(xs, actuals, alpha=0.12, color="#3B82F6")
            line_actual, = ax.plot(xs, actuals, marker="o", color="#3B82F6", lw=2, markersize=5, label="Actual")
            line_forecast, = ax.plot(xs, forecasts, linestyle="--", color="#EF4444", lw=2, label="Forecast")
            step = max(1, len(dates)//8)
            ax.set_xticks(range(0, len(dates), step)); ax.set_xticklabels([dates[i][-5:] for i in range(0, len(dates), step)], rotation=40, fontsize=8)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k"))
            ax.set_ylabel("Revenue", fontsize=9); ax.legend(fontsize=9, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
            fig.tight_layout(); canvas = FigureCanvasTkAgg(fig, trend_card); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(5,15)); self._canvas_refs.append(canvas)
            annot = ax.annotate("", xy=(0,0), xytext=(12,12), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc="#1F2937", ec="none", alpha=0.92), arrowprops=dict(arrowstyle="->", color="#1F2937"), fontsize=9, color="white"); annot.set_visible(False)
            _last_xi = [None]
            def on_hover_trend(event):
                if event.inaxes != ax or event.xdata is None:
                    if annot.get_visible(): annot.set_visible(False); canvas.draw_idle()
                    return
                xi = min(range(len(xs)), key=lambda i: abs(xs[i]-event.xdata))
                if xi == _last_xi[0]: return
                _last_xi[0] = xi
                annot.xy = (xs[xi], actuals[xi]); annot.set_text(f"📅 {dates[xi]}\nActual:   ₹{actuals[xi]:,.0f}\nForecast: ₹{forecasts[xi]:,.0f}"); annot.set_visible(True); canvas.draw_idle()
            fig.canvas.mpl_connect("motion_notify_event", on_hover_trend)
        else: ctk.CTkLabel(trend_card, text="No data available", text_color="#9CA3AF").pack(expand=True, pady=40)

        donut_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        donut_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(donut_card, text="🍩 Ride Status Distribution", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15,0))
        status_dist = data.get("status_dist", {})
        if status_dist:
            total_rides = sum(status_dist.values())
            ctk.CTkLabel(donut_card, text=f"Distribution across {total_rides:,} total rides", font=("Arial", 10), text_color="#9CA3AF").pack(anchor="w", padx=20, pady=(0,4))
            labels = list(status_dist.keys()); sizes = list(status_dist.values()); colors = [STATUS_COLORS.get(l, DEFAULT_COLOR) for l in labels]
            fig2, ax2 = plt.subplots(figsize=(4.2, 4.0), dpi=92); fig2.patch.set_facecolor("white")
            wedges, _ = ax2.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2.5))
            for i, (wedge, sz) in enumerate(zip(wedges, sizes)):
                pct = sz / total_rides * 100
                if pct < 3: continue
                mid_angle = math.radians((wedge.theta1 + wedge.theta2) / 2); r = 0.72
                ax2.text(r * math.cos(mid_angle), r * math.sin(mid_angle), f"{pct:.1f}%", ha="center", va="center", fontsize=8.5, fontweight="bold", color="white")
            ax2.text(0, 0.10, f"{total_rides:,}", ha="center", va="center", fontsize=15, fontweight="bold", color="#111827")
            ax2.text(0, -0.18, "Total Rides", ha="center", va="center", fontsize=8, color="#6B7280")
            patches = [mpatches.Patch(color=c, label=f"{l}  {status_dist[l]:,}  ({status_dist[l]/total_rides*100:.1f}%)") for c, l in zip(colors, labels)]
            ax2.legend(handles=patches, loc="lower center", ncol=1, fontsize=7.2, bbox_to_anchor=(0.5, -0.22), frameon=False, handlelength=1.0, handleheight=1.0)
            fig2.tight_layout(); canvas2 = FigureCanvasTkAgg(fig2, donut_card); canvas2.draw(); canvas2.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0,15)); self._canvas_refs.append(canvas2)
            annot2 = ax2.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc="#1F2937", ec="none", alpha=0.92), fontsize=9, color="white"); annot2.set_visible(False)
            _last_wi = [None]
            def on_hover_donut(event):
                if event.inaxes != ax2:
                    if _last_wi[0] is not None: wedges[_last_wi[0]].set_radius(1.0); _last_wi[0] = None
                    if annot2.get_visible(): annot2.set_visible(False); canvas2.draw_idle()
                    return
                for i, wedge in enumerate(wedges):
                    if wedge.contains(event)[0]:
                        if _last_wi[0] != i:
                            if _last_wi[0] is not None: wedges[_last_wi[0]].set_radius(1.0)
                            wedges[i].set_radius(1.07); _last_wi[0] = i
                        annot2.xy = (event.xdata, event.ydata); annot2.set_text(f"{labels[i]}\n{sizes[i]:,} rides  ({sizes[i]/total_rides*100:.1f}%)"); annot2.set_visible(True); canvas2.draw_idle(); return
                if _last_wi[0] is not None: wedges[_last_wi[0]].set_radius(1.0); _last_wi[0] = None
                if annot2.get_visible(): annot2.set_visible(False); canvas2.draw_idle()
            fig2.canvas.mpl_connect("motion_notify_event", on_hover_donut)
        else: ctk.CTkLabel(donut_card, text="No data available", text_color="#9CA3AF").pack(expand=True, pady=40)

    def _build_charts_row2(self, parent, data):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 15))
        row.grid_columnconfigure(0, weight=1); row.grid_columnconfigure(1, weight=2)
        pay_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        pay_card.grid(row=0, column=0, sticky="nsew", padx=(0,15))
        ctk.CTkLabel(pay_card, text="💳 Payment Methods", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15,0))
        payment_dist = data.get("payment_dist", {})
        if payment_dist:
            labels = [k for k in payment_dist if k and str(k) not in ("0","None","nan")]; sizes = [payment_dist[k] for k in labels]; total_pay = sum(sizes); colors = BAR_COLORS[:len(labels)]
            fig3, ax3 = plt.subplots(figsize=(4, 3.8), dpi=92); fig3.patch.set_facecolor("white")
            wedges3, _ = ax3.pie(sizes, colors=colors, startangle=90, wedgeprops={"edgecolor":"white","linewidth":2})
            for i, (wedge, sz) in enumerate(zip(wedges3, sizes)):
                pct = sz / total_pay * 100
                if pct < 5: continue
                mid_angle = math.radians((wedge.theta1 + wedge.theta2) / 2); r = 0.62
                ax3.text(r * math.cos(mid_angle), r * math.sin(mid_angle), f"{pct:.0f}%", ha="center", va="center", fontsize=9, fontweight="bold", color="white")
            ax3.legend([f"{l} ({s/total_pay*100:.0f}%)" for l, s in zip(labels, sizes)], loc="lower center", ncol=2, fontsize=8, bbox_to_anchor=(0.5,-0.12), frameon=False); fig3.tight_layout()
            canvas3 = FigureCanvasTkAgg(fig3, pay_card); canvas3.draw(); canvas3.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4,15)); self._canvas_refs.append(canvas3)
            annot3 = ax3.annotate("", xy=(0,0), xytext=(8,8), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc="#1F2937", ec="none", alpha=0.92), fontsize=9, color="white"); annot3.set_visible(False)
            _last_p = [None]
            def on_hover_pay(event):
                if event.inaxes != ax3:
                    if annot3.get_visible(): annot3.set_visible(False); canvas3.draw_idle()
                    return
                for i, w in enumerate(wedges3):
                    if w.contains(event)[0]:
                        if _last_p[0] == i: return
                        _last_p[0] = i; annot3.xy = (event.xdata, event.ydata); annot3.set_text(f"{labels[i]}\n{sizes[i]:,}  ({sizes[i]/total_pay*100:.1f}%)"); annot3.set_visible(True); canvas3.draw_idle(); return
                if annot3.get_visible(): annot3.set_visible(False); _last_p[0] = None; canvas3.draw_idle()
            fig3.canvas.mpl_connect("motion_notify_event", on_hover_pay)
        else: ctk.CTkLabel(pay_card, text="No data available", text_color="#9CA3AF").pack(expand=True, pady=40)

        veh_card = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        veh_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(veh_card, text="🚙 Revenue by Vehicle Type", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15,0))
        vehicle_rev = data.get("vehicle_rev", [])
        if vehicle_rev:
            v_types = [str(r["Vehicle Type"]) for r in vehicle_rev]; v_revs = [float(r["rev"] or 0) for r in vehicle_rev]; bar_colors = BAR_COLORS[:len(v_types)]
            fig4, ax4 = plt.subplots(figsize=(6, 3.5), dpi=92); fig4.patch.set_facecolor("white")
            bars = ax4.bar(v_types, v_revs, color=bar_colors, width=0.6, edgecolor="white", linewidth=1.5)
            ax4.spines[["top", "right"]].set_visible(False); ax4.set_ylabel("Revenue (₹)", fontsize=9); ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x/1000:.0f}k")); ax4.tick_params(axis="x", labelsize=9)
            max_rev = max(v_revs) if v_revs else 1
            for bar, val in zip(bars, v_revs): ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max_rev*0.015, f"₹{val/1000:.0f}k", ha="center", fontsize=8.5, fontweight="bold", color="#111827")
            fig4.tight_layout(); canvas4 = FigureCanvasTkAgg(fig4, veh_card); canvas4.draw(); canvas4.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4,15)); self._canvas_refs.append(canvas4)
            annot4 = ax4.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc="#1F2937", ec="none", alpha=0.92), fontsize=9, color="white", ha="center"); annot4.set_visible(False)
            _last_b = [None]
            def on_hover_bar(event):
                if event.inaxes != ax4:
                    if _last_b[0] is not None: bars[_last_b[0]].set_alpha(1.0); _last_b[0] = None
                    if annot4.get_visible(): annot4.set_visible(False); canvas4.draw_idle()
                    return
                for i, bar in enumerate(bars):
                    if bar.contains(event)[0]:
                        if _last_b[0] != i:
                            if _last_b[0] is not None: bars[_last_b[0]].set_alpha(1.0)
                            bars[i].set_alpha(0.72); _last_b[0] = i
                        annot4.xy = (bar.get_x()+bar.get_width()/2, bar.get_height()); annot4.set_text(f"{v_types[i]}\nRevenue: ₹{v_revs[i]:,.0f}"); annot4.set_visible(True); canvas4.draw_idle(); return
                if _last_b[0] is not None: bars[_last_b[0]].set_alpha(1.0); _last_b[0] = None
                if annot4.get_visible(): annot4.set_visible(False); canvas4.draw_idle()
            fig4.canvas.mpl_connect("motion_notify_event", on_hover_bar)
        else: ctk.CTkLabel(veh_card, text="No data available", text_color="#9CA3AF").pack(expand=True, pady=40)

    # ── Top Vehicles (Không có dòng Totals, dùng CTkFrame ôm khít dữ liệu) ──
    def _build_top_vehicles(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 15))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(15,4))
        ctk.CTkLabel(hdr, text="🏆 Top Performing Vehicles", font=("Arial", 14, "bold"), text_color="#111827").pack(side="left")
        ctk.CTkLabel(hdr, text="Ranked by total revenue", font=("Arial", 10), text_color="#9CA3AF").pack(side="left", padx=10)

        top_vehicles = data.get("top_vehicles", [])
        if not top_vehicles:
            ctk.CTkLabel(card, text="No data available", text_color="#9CA3AF").pack(pady=12)
            return

        max_avg = max((float(r.get("avg_rev_per_ride") or 0) for r in top_vehicles), default=1) or 1
        medals  = ["🥇","🥈","🥉"]
        sorted_veh = sorted(top_vehicles, key=lambda r: float(r.get("total_revenue") or 0), reverse=True)

        col_defs = [
            ("RANK",         60,  "center"),
            ("VEHICLE TYPE", 140, "w"),
            ("TOTAL RIDES",  110, "e"),
            ("TOTAL REVENUE",130, "e"),
            ("REV / RIDE",   110, "e"),
            ("AVG RATING",   110, "e"),
            ("COMPLETION",   110, "e"),
            ("EFFICIENCY",   110, "e"),
        ]

        data_rows = []
        for i, r in enumerate(sorted_veh):
            cr   = float(r.get("completion_rate") or 0)
            rat  = float(r.get("avg_rating") or 0)
            arpu = float(r.get("avg_rev_per_ride") or 0)
            eff  = (cr/100)*0.4 + (rat/5)*0.3 + (arpu/max_avg)*0.3
            cr_color  = "#10B981" if cr >= 90 else ("#F59E0B" if cr >= 75 else "#EF4444")
            eff_color = "#3B82F6"
            rank_str  = medals[i] if i < 3 else f"# {i+1}"

            data_rows.append([
                (rank_str,                              "#111827", "bold"),
                (r.get("Vehicle Type","N/A"),           "#111827", "normal"),
                (f"{int(r.get('total_rides') or 0):,}", "#374151", "normal"),
                (f"₹{float(r.get('total_revenue') or 0):,.0f}", "#111827", "bold"),
                (f"₹{arpu:.0f}",                        "#374151", "normal"),
                (f"⭐ {rat:.2f}",                        "#F59E0B", "bold"),
                (f"{cr:.1f}%",                          cr_color,  "bold"),
                (f"{eff:.3f}",                          eff_color, "bold"),
            ])

        # max_scroll_rows=10 sẽ tự chuyển thành Frame tĩnh không có thanh cuộn vì dữ liệu có 7 dòng
        tbl = ModernTable(card, col_defs, data_rows, totals_row=None, max_scroll_rows=10)
        tbl.pack(fill="x", padx=20, pady=(0,20))

    # ── Daily Table ──
    def _build_daily_table(self, parent, data):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E5E7EB")
        card.pack(fill="x", pady=(0, 25))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(15,4))
        ctk.CTkLabel(hdr, text="📅 Performance Summary", font=("Arial", 14, "bold"), text_color="#111827").pack(side="left")

        daily_data = data.get("daily_data", [])
        if not daily_data:
            ctk.CTkLabel(card, text="No data available", text_color="#9CA3AF").pack(pady=12)
            return

        today_str = datetime.now().strftime("%Y-%m-%d")
        col_defs = [
            ("DATE",            140, "w"),
            ("TOTAL RIDES",     120, "e"),
            ("REVENUE",         140, "e"),
            ("COMPLETION RATE", 140, "e"),
            ("AVG RATING",      120, "e"),
            ("CANCELLATIONS",   120, "e"),
            ("Δ REVENUE",       140, "e"),
        ]

        t_rides = t_rev = t_can = t_comp = t_rat_sum = rat_count = 0
        prev_rev = None
        data_rows = []

        for r in daily_data:
            date_str = str(r["Date"])
            rev   = float(r["revenue"] or 0)
            total = int(r["total_rides"] or 0)
            comp  = int(r["completed"] or 0)
            cr    = (comp / total * 100) if total > 0 else 0
            rat   = float(r["avg_rating"] or 0)
            can   = int(r["cancellations"] or 0)

            if prev_rev is not None and prev_rev > 0:
                diff = rev - prev_rev
                delta_str  = f"{'↗' if diff>=0 else '↘'}  {'+'if diff>=0 else ''}₹{abs(diff):,.0f}"
                delta_color = "#10B981" if diff >= 0 else "#EF4444"
            else:
                delta_str, delta_color = "—", "#9CA3AF"
            prev_rev = rev

            cr_color  = "#10B981" if cr >= 95 else ("#F59E0B" if cr >= 90 else "#EF4444")
            can_color = "#EF4444" if can >= 15 else "#374151"
            is_today  = date_str == today_str
            date_disp = (f"● {date_str}" if is_today else f"    {date_str}")
            date_color = "#10B981" if is_today else "#111827"
            can_disp  = f"⚠ {can}" if can >= 15 else str(can)

            data_rows.append([
                (date_disp,       date_color,  "bold" if is_today else "normal"),
                (f"{total:,}",    "#374151",   "normal"),
                (f"₹{rev:,.0f}", "#111827",   "bold"),
                (f"{cr:.1f}%",    cr_color,    "bold"),
                (f"★ {rat:.1f}",  "#F59E0B",   "bold"),
                (can_disp,        can_color,   "bold" if can >= 15 else "normal"),
                (delta_str,       delta_color, "bold"),
            ])

            t_rides += total; t_rev += rev; t_can += can; t_comp += comp
            if rat > 0: t_rat_sum += rat; rat_count += 1

        avg_cr3 = (t_comp / t_rides * 100) if t_rides > 0 else 0
        avg_rat3 = (t_rat_sum / rat_count) if rat_count > 0 else 0
        cr3_color = "#10B981" if avg_cr3 >= 95 else ("#F59E0B" if avg_cr3 >= 90 else "#EF4444")

        totals = [
            ("TOTALS / AVG",    "#111827", "bold"),
            (f"{t_rides:,}",    "#111827", "bold"),
            (f"₹{t_rev:,.0f}", "#111827", "bold"),
            (f"{avg_cr3:.1f}%", cr3_color, "bold"),
            (f"★ {avg_rat3:.2f}","#F59E0B","bold"),
            (f"{t_can:,}",      "#374151", "bold"),
            ("—",               "#9CA3AF", "normal"),
        ]

        tbl = ModernTable(card, col_defs, data_rows, totals_row=totals, max_scroll_rows=10)
        tbl.pack(fill="x", padx=20, pady=(0,8))


# ─────────────────────────────────────────────────────────────────
# PLACEHOLDERS
# ─────────────────────────────────────────────────────────────────
class RideManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Ride Management Hub", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature under development...", text_color="#6B7280").pack()

class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Driver & Customer Profiles", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature under development...", text_color="#6B7280").pack()

class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Cancel & Risk Analysis", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature under development...", text_color="#6B7280").pack()

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="System Settings", font=ctk.CTkFont(family="Arial", size=26, weight="bold"), text_color="#111827").pack(anchor="w", pady=20)
        ctk.CTkLabel(self, text="Feature under development...", text_color="#6B7280").pack()

import sys

# ─────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub Admin — Enterprise Edition")
        self.geometry("1450x850")
        self.configure(fg_color="#F3F4F6")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, pady=(25,30), padx=20, sticky="w")
        ctk.CTkLabel(logo, text="🚕", font=("Arial", 28)).pack(side="left")
        ctk.CTkLabel(logo, text=" RideHub", font=("Arial", 22, "bold"), text_color="#111827").pack(side="left", padx=5)

        self.nav_btns = {}
        nav_items = [
            ("📊  Dashboard",                "Dashboard"),
            ("🛣️  Ride Management",           "Rides"),
            ("👤  Driver & Customer Profiles","Users"),
            ("📈  Cancel & Risk Analysis",    "Risk"),
            ("⚙️  Settings",                  "Settings"),
        ]
        for i, (text, key) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=text, anchor="w",
                fg_color="transparent", text_color="#6B7280",
                font=("Arial", 14, "bold"), height=50, corner_radius=10,
                hover_color="#F9FAFB", command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=6)
            self.nav_btns[key] = btn

        # Right area
        self.right_area = ctk.CTkFrame(self, fg_color="transparent")
        self.right_area.grid(row=0, column=1, sticky="nsew")
        self.right_area.grid_rowconfigure(1, weight=1)
        self.right_area.grid_columnconfigure(0, weight=1)

        topbar = ctk.CTkFrame(self.right_area, height=70, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        topbar.grid(row=0, column=0, sticky="ew")
        uf = ctk.CTkFrame(topbar, fg_color="transparent")
        uf.pack(side="right", padx=30, pady=15)
        ctk.CTkLabel(uf, text="🔔", font=("Arial", 18), text_color="#6B7280").pack(side="left", padx=15)
        ctk.CTkLabel(uf, text="Admin System", font=("Arial", 14, "bold"), text_color="#111827").pack(side="left", padx=10)
        ctk.CTkLabel(uf, text="👨‍💻", font=("Arial", 24)).pack(side="left")

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

    def show_frame(self, key):
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color="#EEF2FF", text_color="#4F46E5", hover=False)
            else:
                btn.configure(fg_color="transparent", text_color="#6B7280", hover_color="#F9FAFB")
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[key].grid(row=0, column=0, sticky="nsew")

    def on_closing(self):
        self.quit()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    auto_setup_database()
    app = App()
    app.mainloop()