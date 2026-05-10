import calendar
import math
import threading
from datetime import datetime, timedelta, date
from tkinter import messagebox, ttk

import customtkinter as ctk
import matplotlib.pyplot as plt
import mysql.connector
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

try:
    import __main__ as main_app

    if hasattr(main_app, "get_db_connection"):
        get_db_connection = main_app.get_db_connection
        auto_setup_database = getattr(main_app, "auto_setup_database", None)
    else:
        from UBER import auto_setup_database, get_db_connection
except ImportError:
    auto_setup_database = None
    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "Tuan23321@",
        "database": "qlud",
    }

    def get_db_connection():
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Exception:
            return None


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

FONT_FAMILY = "Segoe UI"

COLORS = {
    "page": "#f7f8fa",
    "surface": "#ffffff",
    "border": "#e8e8e8",
    "subtle": "#f5f5f5",
    "text": "#1a1a1a",
    "muted": "#888888",
    "muted_light": "#aaaaaa",
    "primary": "#6C63FF",
    "primary_dark": "#4F46E5",
    "primary_light": "#EEF2FF",
    "orange": "#F97316",
    "orange_bg": "#FFF0E6",
    "yellow": "#FCD34D",
    "yellow_bg": "#FEF3C7",
    "red": "#EF4444",
    "red_bg": "#FEE2E2",
    "green": "#10B981",
    "green_bg": "#D1FAE5",
    "blue": "#3B82F6",
    "sky_bg": "#E0F2FE",
    "purple": "#7C3AED",
    "purple_bg": "#F3E8FF",
}

STATUS_CANCEL_CUSTOMER = ("Cancelled by Customer", "Cancelled")
STATUS_CANCEL_DRIVER = ("Cancelled by Driver",)
STATUS_INCOMPLETE = ("Incomplete", "No Completed", "No Complete")
STATUS_COMPLETED = ("Completed",)


def font(size, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def sql_in(values):
    return "(" + ",".join(["%s"] * len(values)) + ")"


def sql_literals(values):
    return "(" + ",".join("'" + str(value).replace("'", "''") + "'" for value in values) + ")"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def pct_delta(current, previous):
    current = safe_float(current)
    previous = safe_float(previous)
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return (current - previous) / previous * 100


def make_card(parent, **kwargs):
    options = {
        "fg_color": COLORS["surface"],
        "corner_radius": 14,
        "border_width": 1,
        "border_color": COLORS["border"],
    }
    options.update(kwargs)
    return ctk.CTkFrame(parent, **options)


class DateRangePicker(ctk.CTkFrame):
    def __init__(self, parent, on_change=None, default_start=None, default_end=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_change = on_change
        self.start_date = default_start
        self.end_date = default_end
        self._popup = None
        self._sel_start = default_start
        self._sel_end = default_end
        self._view_year = (default_start or date.today()).year
        self._view_month = (default_start or date.today()).month

        # From field
        self.from_frame = ctk.CTkFrame(self, fg_color="white", border_width=1,
                                       border_color="#E2E8F0", corner_radius=8)
        self.from_frame.pack(side="left", fill="x", expand=True)

        self.cal_btn = ctk.CTkButton(
            self.from_frame, text="📅", width=32, height=36,
            fg_color="transparent", hover_color="#F1F5F9",
            text_color="#475569", corner_radius=8,
            command=self._toggle_popup
        )
        self.cal_btn.pack(side="left", padx=(2, 0))

        self.from_entry = ctk.CTkEntry(
            self.from_frame, font=("Segoe UI", 12), text_color="#64748B",
            fg_color="transparent", border_width=0, width=100, justify="center"
        )
        self.from_entry.pack(side="left", padx=(4, 8))
        self.from_entry.bind("<Return>", lambda e: self._on_entry_commit("start"))
        self.from_entry.bind("<FocusOut>", lambda e: self._on_entry_commit("start"))

        # Separator
        ctk.CTkLabel(self, text="→", font=("Segoe UI", 14),
                      text_color="#94A3B8").pack(side="left", padx=6)

        # To field
        self.to_frame = ctk.CTkFrame(self, fg_color="white", border_width=1,
                                     border_color="#E2E8F0", corner_radius=8)
        self.to_frame.pack(side="left", fill="x", expand=True)

        self.to_cal_btn = ctk.CTkButton(
            self.to_frame, text="📅", width=32, height=36,
            fg_color="transparent", hover_color="#F1F5F9",
            text_color="#475569", corner_radius=8,
            command=self._toggle_popup
        )
        self.to_cal_btn.pack(side="left", padx=(2, 0))

        self.to_entry = ctk.CTkEntry(
            self.to_frame, font=("Segoe UI", 12), text_color="#64748B",
            fg_color="transparent", border_width=0, width=100, justify="center"
        )
        self.to_entry.pack(side="left", padx=(8, 4))
        self.to_entry.bind("<Return>", lambda e: self._on_entry_commit("end"))
        self.to_entry.bind("<FocusOut>", lambda e: self._on_entry_commit("end"))

        self._update_display()

    def _toggle_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
        else:
            self._show_popup()

    def _show_popup(self):
        self._popup = ctk.CTkToplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.configure(fg_color="white")
        self._popup.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        self._popup.geometry(f"300x320+{x}+{y}")

        ref = self._sel_start or self._sel_end or date.today()
        self._view_year = ref.year
        self._view_month = ref.month
        self._build_calendar()

    def _build_calendar(self):
        for w in self._popup.winfo_children():
            w.destroy()

        nav = ctk.CTkFrame(self._popup, fg_color="transparent")
        nav.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkButton(nav, text="◀", width=28, height=28, fg_color="transparent",
                      text_color="#475569", hover_color="#F1F5F9", corner_radius=6,
                      command=self._prev_month).pack(side="left")
        ctk.CTkLabel(nav, text=f"{calendar.month_name[self._view_month]} {self._view_year}",
                     font=("Segoe UI", 13, "bold"), text_color="#1E293B").pack(side="left", expand=True)
        ctk.CTkButton(nav, text="▶", width=28, height=28, fg_color="transparent",
                      text_color="#475569", hover_color="#F1F5F9", corner_radius=6,
                      command=self._next_month).pack(side="right")

        days_frame = ctk.CTkFrame(self._popup, fg_color="transparent")
        days_frame.pack(fill="x", padx=10, pady=(4, 0))
        for i, d in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            ctk.CTkLabel(days_frame, text=d, font=("Segoe UI", 10),
                         text_color="#94A3B8", width=36).grid(row=0, column=i, padx=1)

        cal = calendar.monthcalendar(self._view_year, self._view_month)
        grid = ctk.CTkFrame(self._popup, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(4, 0))
        today = date.today()
        for r, week in enumerate(cal):
            for c, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(grid, text="", width=36, height=28).grid(row=r, column=c, padx=1)
                    continue
                d = date(self._view_year, self._view_month, day_num)
                is_start = self._sel_start and d == self._sel_start
                is_end = self._sel_end and d == self._sel_end
                in_range = self._sel_start and self._sel_end and self._sel_start <= d <= self._sel_end
                is_today = d == today

                if is_start or is_end:
                    bg, fg = "#3B82F6", "white"
                elif in_range:
                    bg, fg = "#DBEAFE", "#1E293B"
                elif is_today:
                    bg, fg = "#F8FAFC", "#1E293B"
                else:
                    bg, fg = "transparent", "#1E293B"

                btn = ctk.CTkButton(grid, text=str(day_num), width=36, height=28,
                                    fg_color=bg, text_color=fg, hover_color="#E2E8F0",
                                    corner_radius=6, font=("Segoe UI", 11))
                btn.configure(command=lambda dd=d: self._select_date(dd))
                btn.grid(row=r, column=c, padx=1)

        bottom = ctk.CTkFrame(self._popup, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(8, 10))
        ctk.CTkButton(bottom, text="Today", width=60, height=28, fg_color="#F1F5F9",
                      text_color="#475569", hover_color="#E2E8F0", corner_radius=6,
                      command=lambda: self._select_date(today)).pack(side="left", padx=(0, 4))
        ctk.CTkButton(bottom, text="Clear", width=60, height=28, fg_color="#F1F5F9",
                      text_color="#475569", hover_color="#E2E8F0", corner_radius=6,
                      command=self._clear_dates).pack(side="left")
        ctk.CTkButton(bottom, text="Apply", width=60, height=28,
                      fg_color="#3B82F6", text_color="white", hover_color="#2563EB",
                      corner_radius=6, command=self._apply_selection).pack(side="right")

    def _select_date(self, d):
        if not self._sel_start or (self._sel_start and self._sel_end):
            self._sel_start = d
            self._sel_end = None
        else:
            if d < self._sel_start:
                self._sel_start = d
            else:
                self._sel_end = d
        self._build_calendar()

    def _apply_selection(self):
        self.start_date = self._sel_start
        self.end_date = self._sel_end
        self._update_display()
        if self._popup:
            self._popup.destroy()
            self._popup = None
        if self.on_change:
            self.on_change(self.start_date, self.end_date)

    def _clear_dates(self):
        self._sel_start = self._sel_end = self.start_date = self.end_date = None
        self._update_display()
        self._build_calendar()
        if self.on_change:
            self.on_change(None, None)

    def _prev_month(self):
        self._view_month = 12 if self._view_month == 1 else self._view_month - 1
        self._view_year -= 1 if self._view_month == 12 else 0
        self._build_calendar()

    def _next_month(self):
        self._view_month = 1 if self._view_month == 12 else self._view_month + 1
        self._view_year += 1 if self._view_month == 1 else 0
        self._build_calendar()

    def _parse_date(self, raw):
        raw = raw.strip()
        if not raw:
            return None
        parts_d = raw.split("/")
        if len(parts_d) != 3:
            return None
        day = parts_d[0].zfill(2)
        month = parts_d[1].zfill(2)
        year = parts_d[2]
        if len(year) == 4:
            year = year[2:]
        elif len(year) == 1:
            year = "0" + year
        normalized = f"{day}/{month}/{year}"
        try:
            return datetime.strptime(normalized, "%d/%m/%y").date()
        except ValueError:
            return None

    def _on_entry_commit(self, field):
        if field == "start":
            text = self.from_entry.get().strip()
        else:
            text = self.to_entry.get().strip()
        if not text:
            return
        new_date = self._parse_date(text)
        if new_date is None:
            self._update_display()
            return
        if field == "start":
            self._sel_start = new_date
            self.start_date = new_date
        else:
            self._sel_end = new_date
            self.end_date = new_date
        self._update_display()
        if self.on_change:
            self.on_change(self.start_date, self.end_date)

    def _update_display(self):
        self.from_entry.delete(0, "end")
        self.to_entry.delete(0, "end")
        if self.start_date:
            self.from_entry.insert(0, self.start_date.strftime("%d/%m/%y"))
        if self.end_date:
            self.to_entry.insert(0, self.end_date.strftime("%d/%m/%y"))

    def set_range(self, start, end):
        self.start_date = self.end_date = None
        self._sel_start = start
        self._sel_end = end
        self.start_date = start
        self.end_date = end
        self._update_display()

    def get_range_iso(self):
        if self.start_date and self.end_date:
            return self.start_date.strftime("%Y-%m-%d"), self.end_date.strftime("%Y-%m-%d")
        return None, None


class SortableTree:
    def __init__(self, tree):
        self.tree = tree
        self.sort_state = {}

    def attach(self):
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort(c))

    def sort(self, col):
        rows = [(self.tree.set(item, col), item) for item in self.tree.get_children("")]
        reverse = not self.sort_state.get(col, False)
        self.sort_state[col] = reverse

        def key(row):
            value = str(row[0]).replace("%", "").replace("km", "").replace(",", "").strip()
            try:
                return float(value)
            except ValueError:
                return value.lower()

        rows.sort(key=key, reverse=reverse)
        for index, (_, item) in enumerate(rows):
            self.tree.move(item, "", index)


class RiskAnalysisFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["page"])
        self.refresh_ms = 90000
        self.refresh_job = None
        self.chart_canvases = []
        self.raw_rows = {"fraud": [], "drivers": []}
        self.driver_threshold = 30
        self.table_page = {"fraud": 0, "drivers": 0}
        self.page_size = 8
        self.selected_reason = None
        self.loading = False

        self._init_vars()
        self._build_shell()
        self._load_filter_options()
        self.apply_filters()

    def destroy(self):
        if self.refresh_job:
            self.after_cancel(self.refresh_job)
        plt.close("all")
        super().destroy()

    def _init_vars(self):
        today = datetime.now()
        self.default_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.default_end = today.strftime("%Y-%m-%d")
        self.date_picker = None
        self.region_var = ctk.StringVar(value="All")
        self.service_var = ctk.StringVar(value="All")
        self.payment_var = ctk.StringVar(value="All")
        self.status_var = ctk.StringVar(value="All")
        self.peak_var = ctk.BooleanVar(value=False)
        self.top_fraud_var = ctk.StringVar(value="")
        self.top_driver_var = ctk.StringVar(value="")
        self.risk_fraud_var = ctk.StringVar(value="All Risk")
        self.risk_driver_var = ctk.StringVar(value="All Risk")
        self.cancel_driver_type_var = ctk.StringVar(value="All cancellations")

    def _build_shell(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Operational Analytics & Fraud Detection",
                     font=font(20, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(left, text="Live SQL-backed ride cancellation, VTAT, cash fraud, and driver risk monitoring",
                     font=font(11), text_color=COLORS["muted_light"]).pack(anchor="w", pady=(2, 0))

        self.status_label = ctk.CTkLabel(header, text="Ready", font=font(11),
                                         text_color=COLORS["muted"], fg_color=COLORS["surface"],
                                         corner_radius=20, padx=12, pady=4)
        self.status_label.pack(side="right", padx=(12, 0))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        self.filter_card = make_card(self.scroll)
        self.filter_card.pack(fill="x", pady=(0, 14))
        self._build_filters(self.filter_card)

        self.kpi_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.kpi_frame.pack(fill="x", pady=(0, 14))

        self.middle = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.middle.pack(fill="x", pady=(0, 14))
        self.middle.grid_columnconfigure((0, 1), weight=1, uniform="middle")

        self.cancel_card = make_card(self.middle)
        self.cancel_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.vtat_card = make_card(self.middle)
        self.vtat_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.vehicle_card = make_card(self.scroll)
        self.vehicle_card.pack(fill="x", pady=(0, 14))

        self.fraud_card = make_card(self.scroll)
        self.fraud_card.pack(fill="x", pady=(0, 14))

        self.driver_card = make_card(self.scroll)
        self.driver_card.pack(fill="x", pady=(0, 18))

    def _build_filters(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(top, text="Global Filters", font=font(14, "bold"),
                     text_color=COLORS["text"]).pack(side="left")
        self.loading_bar = ctk.CTkProgressBar(top, width=140, height=8,
                                              progress_color=COLORS["primary"],
                                              fg_color=COLORS["primary_light"])
        self.loading_bar.set(0)
        self.loading_bar.pack(side="right", padx=(10, 0))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 14))
        for i in range(8):
            grid.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(grid, text="DATE FROM", font=font(10, "bold"),
                     text_color=COLORS["muted_light"]).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 4))
        ctk.CTkLabel(grid, text="DATE TO", font=font(10, "bold"),
                     text_color=COLORS["muted_light"]).grid(row=0, column=1, sticky="w", padx=6, pady=(0, 4))
        self.date_picker = DateRangePicker(
            grid,
            default_start=datetime.strptime(self.default_start, "%Y-%m-%d").date(),
            default_end=datetime.strptime(self.default_end, "%Y-%m-%d").date(),
            on_change=lambda s, e: self.apply_filters()
        )
        self.date_picker.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6)
        self.region_box = self._field(grid, "Region / City", self.region_var, 2, "combo", ["All"])
        self.service_box = self._field(grid, "Service Type", self.service_var, 3, "combo", ["All"])
        self.payment_box = self._field(grid, "Payment", self.payment_var, 4, "combo", ["All"])
        self.status_box = self._field(grid, "Booking Status", self.status_var, 5, "combo", ["All"])

        peak = ctk.CTkCheckBox(grid, text="Peak hour", variable=self.peak_var,
                               font=font(12, "bold"), text_color=COLORS["text"],
                               fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"])
        peak.grid(row=1, column=6, sticky="w", padx=6, pady=(2, 0))

        actions = ctk.CTkFrame(grid, fg_color="transparent")
        actions.grid(row=0, column=7, rowspan=2, sticky="e", padx=(8, 0))
        ctk.CTkButton(actions, text="Apply", width=86, height=34,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
                      command=self.apply_filters).pack(side="left", padx=(0, 6))
        ctk.CTkButton(actions, text="Reset", width=82, height=34,
                      fg_color="#F3F4F6", hover_color="#E5E7EB",
                      text_color=COLORS["text"], command=self.reset_filters).pack(side="left")

    def _field(self, parent, label, var, col, kind, values=None):
        ctk.CTkLabel(parent, text=label.upper(), font=font(10, "bold"),
                     text_color=COLORS["muted_light"], wraplength=130).grid(row=0, column=col, sticky="w", padx=6, pady=(0, 4))
        if kind == "entry":
            widget = ctk.CTkEntry(parent, textvariable=var, height=38, fg_color="#F9FAFB",
                                  border_color=COLORS["border"], corner_radius=8)
        else:
            widget = ctk.CTkComboBox(parent, variable=var, values=values or ["All"], height=38,
                                     fg_color="#F9FAFB", border_color=COLORS["border"],
                                     button_color="#F3F4F6", button_hover_color="#E5E7EB",
                                     text_color=COLORS["text"], state="readonly")
        widget.grid(row=1, column=col, sticky="ew", padx=6)
        return widget

    def _load_filter_options(self):
        conn = get_db_connection()
        if not conn:
            self._set_status("Database unavailable", error=True)
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT MIN(`Date`), MAX(`Date`) FROM rides")
            min_date, max_date = cur.fetchone()
            if min_date and max_date:
                max_dt = datetime.strptime(str(max_date), "%Y-%m-%d")
                min_dt = datetime.strptime(str(min_date), "%Y-%m-%d")
                self.default_start = min_dt.strftime("%Y-%m-%d")
                self.default_end = max_dt.strftime("%Y-%m-%d")
                if self.date_picker:
                    self.date_picker.set_range(min_dt.date(), max_dt.date())
            cur.execute("""
                SELECT city FROM (
                    SELECT DISTINCT `Pickup Location` city FROM rides WHERE `Pickup Location` IS NOT NULL AND `Pickup Location`<>''
                    UNION
                    SELECT DISTINCT `Drop Location` city FROM rides WHERE `Drop Location` IS NOT NULL AND `Drop Location`<>''
                ) cities ORDER BY city
            """)
            self.region_box.configure(values=["All"] + [str(row[0]) for row in cur.fetchall()])
            for box, col in [
                (self.service_box, "Vehicle Type"),
                (self.payment_box, "Payment Method"),
                (self.status_box, "Booking Status"),
            ]:
                cur.execute(f"SELECT DISTINCT `{col}` FROM rides WHERE `{col}` IS NOT NULL AND `{col}`<>'' ORDER BY `{col}`")
                box.configure(values=["All"] + [str(row[0]) for row in cur.fetchall()])
        except Exception as exc:
            self._set_status(f"Filter load failed: {exc}", error=True)
        finally:
            conn.close()

    def reset_filters(self):
        if self.date_picker:
            sd = datetime.strptime(self.default_start, "%Y-%m-%d").date()
            ed = datetime.strptime(self.default_end, "%Y-%m-%d").date()
            self.date_picker.set_range(sd, ed)
        self.region_var.set("All")
        self.service_var.set("All")
        self.payment_var.set("All")
        self.status_var.set("All")
        self.peak_var.set(False)
        self.risk_fraud_var.set("All Risk")
        self.risk_driver_var.set("All Risk")
        self.cancel_driver_type_var.set("All cancellations")
        self.selected_reason = None
        self.apply_filters()

    def apply_filters(self):
        if self.loading:
            return
        self.loading = True
        snapshot = self._filter_snapshot()
        self._set_status("Refreshing SQL data...")
        self.loading_bar.set(0.25)
        for frame in [self.kpi_frame, self.cancel_card, self.vtat_card, self.vehicle_card, self.fraud_card, self.driver_card]:
            self._clear(frame)
        self._build_skeletons()
        thread = threading.Thread(target=lambda: self._load_dashboard_data(snapshot), daemon=True)
        thread.start()

    def _filter_snapshot(self):
        start_iso, end_iso = self.date_picker.get_range_iso() if self.date_picker else (None, None)
        return {
            "start": start_iso or self.default_start,
            "end": end_iso or self.default_end,
            "region": self.region_var.get(),
            "service": self.service_var.get(),
            "payment": self.payment_var.get(),
            "status": self.status_var.get(),
            "peak": self.peak_var.get(),
            "reason": self.selected_reason,
        }

    def _load_dashboard_data(self, snapshot):
        try:
            where, params = self._build_where(snapshot)
            prev_where, prev_params = self._build_previous_where(snapshot)
            data = {
                "kpi": self._query_kpis(where, params, prev_where, prev_params),
                "reasons": self._query_reasons(where, params),
                "vtat": self._query_vtat_analysis(where, params),
                "vehicles": self._query_vehicle_cancel_rates(where, params),
                "fraud": self._query_fraud(where, params),
                "drivers": self._query_driver_ranking(where, params),
            }
            self.after(0, lambda: self._render_dashboard(data))
        except Exception as exc:
            self.after(0, lambda: self._render_error(str(exc)))

    def _build_where(self, snapshot):
        clauses = ["1=1"]
        params = []
        if snapshot["start"] and snapshot["end"]:
            clauses.append("`Date` BETWEEN %s AND %s")
            params.extend([snapshot["start"], snapshot["end"]])
        if snapshot["region"] != "All":
            clauses.append("(`Pickup Location` = %s OR `Drop Location` = %s)")
            params.extend([snapshot["region"], snapshot["region"]])
        if snapshot["service"] != "All":
            clauses.append("`Vehicle Type` = %s")
            params.append(snapshot["service"])
        if snapshot["payment"] != "All":
            clauses.append("`Payment Method` = %s")
            params.append(snapshot["payment"])
        if snapshot["status"] != "All":
            clauses.append("`Booking Status` = %s")
            params.append(snapshot["status"])
        if snapshot["peak"]:
            clauses.append("HOUR(COALESCE(`Full_Timestamp`, CONCAT(`Date`, ' ', `Time`))) IN (7,8,9,17,18,19,20)")
        if snapshot["reason"]:
            clauses.append("(`Reason for cancelling by Customer` = %s OR `Driver Cancellation Reason` = %s)")
            params.extend([snapshot["reason"], snapshot["reason"]])
        return "WHERE " + " AND ".join(clauses), params

    def _build_previous_where(self, snapshot):
        try:
            start = datetime.strptime(snapshot["start"], "%Y-%m-%d")
            end = datetime.strptime(snapshot["end"], "%Y-%m-%d")
        except ValueError:
            return "WHERE 1=0", []
        days = max(1, (end - start).days + 1)
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        previous = dict(snapshot)
        previous["start"] = prev_start.strftime("%Y-%m-%d")
        previous["end"] = prev_end.strftime("%Y-%m-%d")
        where, params = self._build_where(previous)
        return where, params

    def _query_one(self, query, params=None):
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Cannot connect to the configured SQL database.")
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params or [])
            return cur.fetchone() or {}
        finally:
            conn.close()

    def _query_all(self, query, params=None):
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Cannot connect to the configured SQL database.")
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params or [])
            return cur.fetchall()
        finally:
            conn.close()

    def _query_kpis(self, where, params, prev_where, prev_params):
        expr = self._kpi_expr()
        current = self._query_one(f"SELECT {expr} FROM rides {where}", params)
        previous = self._query_one(f"SELECT {expr} FROM rides {prev_where}", prev_params)
        return current, previous

    def _kpi_expr(self):
        return f"""
            COUNT(*) total,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER)} OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END) customer_cancelled,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_DRIVER)} OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END) driver_cancelled,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_INCOMPLETE)} OR `Incomplete Rides` > 0 THEN 1 ELSE 0 END) incomplete,
            SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_COMPLETED)} THEN 1 ELSE 0 END) completed
        """

    def _query_reasons(self, where, params):
        query = f"""
            SELECT reason,
                   SUM(customer_cnt) customer_cnt,
                   SUM(driver_cnt) driver_cnt,
                   SUM(customer_cnt + driver_cnt) total_cnt
            FROM (
                SELECT `Reason for cancelling by Customer` reason, COUNT(*) customer_cnt, 0 driver_cnt
                FROM rides {where}
                  AND `Reason for cancelling by Customer` NOT IN ('', 'None', 'Not Applicable', '0')
                GROUP BY `Reason for cancelling by Customer`
                UNION ALL
                SELECT `Driver Cancellation Reason` reason, 0 customer_cnt, COUNT(*) driver_cnt
                FROM rides {where}
                  AND `Driver Cancellation Reason` NOT IN ('', 'None', 'Not Applicable', '0')
                GROUP BY `Driver Cancellation Reason`
            ) x
            GROUP BY reason
            ORDER BY total_cnt DESC
            LIMIT 30
        """
        return self._query_all(query, params + params)

    def _query_vtat_analysis(self, where, params):
        query = f"""
            SELECT
                   CASE
                       WHEN `Avg VTAT` < 3 THEN '0-3 min'
                       WHEN `Avg VTAT` < 6 THEN '3-6 min'
                       WHEN `Avg VTAT` < 9 THEN '6-9 min'
                       WHEN `Avg VTAT` < 12 THEN '9-12 min'
                       WHEN `Avg VTAT` < 15 THEN '12-15 min'
                       ELSE '15+ min'
                   END vtat_bucket,
                   CASE
                       WHEN `Avg VTAT` < 3 THEN 1
                       WHEN `Avg VTAT` < 6 THEN 2
                       WHEN `Avg VTAT` < 9 THEN 3
                       WHEN `Avg VTAT` < 12 THEN 4
                       WHEN `Avg VTAT` < 15 THEN 5
                       ELSE 6
                   END bucket_order,
                   COUNT(*) total,
                   SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                                OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END) cancelled,
                   AVG(`Avg VTAT`) avg_vtat,
                   AVG(`Avg CTAT`) avg_ctat,
                   ROUND(SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                                      OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) cancel_rate
            FROM rides {where}
              AND `Avg VTAT` IS NOT NULL AND `Avg VTAT` >= 0
            GROUP BY vtat_bucket, bucket_order
            ORDER BY bucket_order
        """
        return self._query_all(query, params)

    def _query_vehicle_cancel_rates(self, where, params):
        query = f"""
            SELECT `Vehicle Type` vehicle_type,
                   COUNT(*) total_rides,
                   SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER + STATUS_CANCEL_DRIVER)}
                                OR `Cancelled Rides by Customer` > 0
                                OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END) cancelled_rides,
                   ROUND(SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER + STATUS_CANCEL_DRIVER)}
                                      OR `Cancelled Rides by Customer` > 0
                                      OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) cancel_rate,
                   AVG(NULLIF(`Driver Ratings`, 0)) avg_driver_rating
            FROM rides {where}
              AND `Vehicle Type` IS NOT NULL
              AND `Vehicle Type` NOT IN ('', 'None', 'NaN', '0')
            GROUP BY `Vehicle Type`
            HAVING total_rides >= 50 AND cancelled_rides > 0
            ORDER BY cancel_rate DESC, cancelled_rides DESC
            LIMIT 12
        """
        return self._query_all(query, params)

    def _query_fraud(self, where, params):
        suspicious_statuses = ("Cancelled", "Cancelled by Driver", "Cancelled by Customer", "Incomplete", "No Completed", "No Complete")
        query = f"""
            SELECT r.`Booking ID`, r.`Driver ID`,
                   COALESCE(r.`Driver ID`, 'Unknown') driver_name,
                   r.`Ride Distance`, r.`Booking Status`, r.`Payment Method`,
                   COALESCE(r.`Full_Timestamp`, CONCAT(r.`Date`, ' ', r.`Time`)) event_time,
                   r.`Pickup Location` region,
                   driver_stats.suspicious_count,
                   (45
                    + CASE WHEN r.`Ride Distance` >= 12 THEN 25 WHEN r.`Ride Distance` >= 6 THEN 12 ELSE 5 END
                    + LEAST(driver_stats.suspicious_count * 6, 30)
                    + CASE WHEN r.`Booking Status` IN ('Cancelled by Driver', 'Cancelled') THEN 10 ELSE 0 END
                   ) risk_score
            FROM rides r
            JOIN (
                SELECT `Driver ID`, COUNT(*) suspicious_count
                FROM rides
                WHERE `Payment Method`='Cash'
                  AND `Booking Status` IN {sql_in(suspicious_statuses)}
                  AND `Ride Distance` > 1.0
                GROUP BY `Driver ID`
            ) driver_stats ON driver_stats.`Driver ID` = r.`Driver ID`
            {self._alias_where(where, 'r')}
              AND r.`Payment Method`='Cash'
              AND r.`Booking Status` IN {sql_in(suspicious_statuses)}
              AND r.`Ride Distance` > 1.0
            ORDER BY risk_score DESC, r.`Ride Distance` DESC
            LIMIT 5000
        """
        return self._query_all(query, list(suspicious_statuses) + params + list(suspicious_statuses))

    def _alias_where(self, where, alias):
        aliased = where
        for col in ["Date", "Pickup Location", "Drop Location", "Vehicle Type", "Payment Method", "Booking Status",
                    "Full_Timestamp", "Time", "Reason for cancelling by Customer", "Driver Cancellation Reason"]:
            aliased = aliased.replace(f"`{col}`", f"{alias}.`{col}`")
        return aliased

    def _query_driver_ranking(self, where, params):
        volume_row = self._query_one(f"""
            SELECT MAX(accepted_rides) max_rides
            FROM (
                SELECT COUNT(*) accepted_rides
                FROM rides {where}
                  AND `Driver ID` IS NOT NULL
                  AND `Driver ID` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')
                GROUP BY `Driver ID`
            ) volume
        """, params)
        max_rides = int(volume_row.get("max_rides") or 0)
        threshold = 30 if max_rides >= 30 else max(2, min(5, max_rides))
        if max_rides < 2:
            return {"rows": [], "threshold": 30}
        query = f"""
            SELECT `Driver ID`,
                   COUNT(*) accepted_rides,
                   SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_DRIVER)}
                               OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END) driver_cancelled,
                   SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                               OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END) customer_cancelled,
                   AVG(NULLIF(`Driver Ratings`, 0)) avg_rating,
                   ROUND(SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_DRIVER)}
                                     OR `Cancelled Rides by Driver` > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) cancel_rate,
                   ROUND(SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_CUSTOMER)}
                                     OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) customer_cancel_rate,
                   ROUND(SUM(CASE WHEN `Booking Status` IN {sql_literals(STATUS_CANCEL_DRIVER + STATUS_CANCEL_CUSTOMER)}
                                     OR `Cancelled Rides by Driver` > 0
                                     OR `Cancelled Rides by Customer` > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) total_cancel_rate,
                   COALESCE(NULLIF(SUBSTRING_INDEX(
                       GROUP_CONCAT(NULLIF(`Driver Cancellation Reason`, '') ORDER BY `Driver Cancellation Reason` SEPARATOR ','), ',', 1
                   ), ''), 'Not Available') common_reason
            FROM rides {where}
              AND `Driver ID` IS NOT NULL
              AND `Driver ID` NOT IN ('', 'None', 'NaN', '0', 'Unassigned')
            GROUP BY `Driver ID`
            HAVING accepted_rides >= %s AND (driver_cancelled > 0 OR customer_cancelled > 0)
            ORDER BY total_cancel_rate DESC, driver_cancelled DESC, customer_cancelled DESC
            LIMIT 2000
        """
        return {"rows": self._query_all(query, params + [threshold]), "threshold": threshold}

    def _render_dashboard(self, data):
        self.loading = False
        self.loading_bar.set(1)
        for frame in [self.kpi_frame, self.cancel_card, self.vtat_card, self.vehicle_card, self.fraud_card, self.driver_card]:
            self._clear(frame)
        plt.close("all")
        self.chart_canvases = []
        self.raw_rows["fraud"] = data["fraud"]
        self.raw_rows["drivers"] = data["drivers"]["rows"]
        self.driver_threshold = data["drivers"]["threshold"]
        self.table_page = {"fraud": 0, "drivers": 0}

        self._render_kpis(data["kpi"])
        self._render_cancel_reasons(data["reasons"])
        self._render_vtat_analysis(data["vtat"])
        self._render_vehicle_cancel_chart(data["vehicles"])
        self._render_fraud_table()
        self._render_driver_table()
        self._set_status("Live SQL refreshed " + datetime.now().strftime("%H:%M:%S"))
        self._schedule_refresh()

    def _render_error(self, error):
        self.loading = False
        self.loading_bar.set(0)
        for frame in [self.kpi_frame, self.cancel_card, self.vtat_card, self.vehicle_card, self.fraud_card, self.driver_card]:
            self._clear(frame)
        self._set_status("SQL refresh failed", error=True)
        ctk.CTkLabel(self.kpi_frame, text=error, font=font(13), text_color=COLORS["red"]).pack(anchor="w", pady=12)

    def _schedule_refresh(self):
        if self.refresh_job:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(self.refresh_ms, self.apply_filters)

    def _build_skeletons(self):
        for i in range(4):
            sk = make_card(self.kpi_frame, height=112, border_color="#EFEFEF")
            sk.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 7, 0 if i == 3 else 7))
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(sk, text="Loading SQL...", font=font(11), text_color=COLORS["muted_light"]).place(x=18, y=42)

    def _render_kpis(self, kpis):
        current, previous = kpis
        total = int(current.get("total") or 0)
        kpi_targets = [2000, 1000, 500, 95.0]
        cards = [
            ("Customer Cancelled Rides", current.get("customer_cancelled") or 0, previous.get("customer_cancelled") or 0,
             COLORS["yellow"], COLORS["yellow_bg"], "#D97706", COLORS["orange"], "ti-alert-triangle"),
            ("Driver Cancelled Rides", current.get("driver_cancelled") or 0, previous.get("driver_cancelled") or 0,
             "#FB923C", COLORS["orange_bg"], COLORS["orange"], COLORS["orange"], "ti-clock"),
            ("Incomplete / Unfinished Rides", current.get("incomplete") or 0, previous.get("incomplete") or 0,
             "#F87171", COLORS["red_bg"], COLORS["red"], COLORS["red"], "ti-shield-off"),
            ("Ride Completion Rate", (safe_float(current.get("completed")) / total * 100 if total else 0),
             (safe_float(previous.get("completed")) / safe_float(previous.get("total")) * 100 if previous.get("total") else 0),
             "#34D399", COLORS["green_bg"], COLORS["green"], COLORS["green"], "ti-circle-check"),
        ]
        for i, (card_data, target) in enumerate(zip(cards, kpi_targets)):
            raw_val = card_data[1]
            pct_val = min(100.0, (safe_float(raw_val) / target) * 100 if target > 0 else 0)
            self._kpi_card(i, card_data, total, pct_val)

    def _kpi_card(self, col, data, total, progress=0):
        title, value, old_value, border, icon_bg, icon_color, value_color, _ = data
        delta = pct_delta(value, old_value)
        warning = (title != "Ride Completion Rate" and delta > 15) or (title == "Ride Completion Rate" and delta < -3)
        status_color = COLORS["red"] if warning else (COLORS["orange"] if abs(delta) > 7 else COLORS["green"])
        card = make_card(self.kpi_frame, height=185, border_width=2, border_color=border)
        card.grid(row=0, column=col, sticky="ew", padx=7)
        card.grid_propagate(False)
        self.kpi_frame.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(card, text=title[:1], width=36, height=36, corner_radius=18,
                     fg_color=icon_bg, text_color=icon_color, font=font(18, "bold")).place(x=18, y=16)
        ctk.CTkLabel(card, text=f"{delta:+.1f}%", font=font(11, "bold"),
                     fg_color=COLORS["red_bg"] if warning else COLORS["green_bg"],
                     text_color=status_color, corner_radius=20, padx=9, pady=3).place(relx=0.95, y=17, anchor="ne")
        display = f"{value:.1f}%" if "Rate" in title else f"{int(value):,}"
        ctk.CTkLabel(card, text=display, font=font(25, "bold"),
                     text_color=value_color, wraplength=180).place(x=18, y=56)
        ctk.CTkLabel(card, text=title.upper(), font=font(10, "bold"),
                     text_color=COLORS["muted_light"], wraplength=190, justify="left").place(x=18, y=88)
        ctk.CTkLabel(card, text=f"vs previous period | total {total:,}", font=font(11),
                     text_color="#CCCCCC", wraplength=190, justify="left").place(x=18, y=120)

        ctk.CTkLabel(card, text=f"{progress:.1f}% toward target", font=font(9),
                     text_color=COLORS["muted"]).place(x=22, y=145)

        pb_bg = ctk.CTkFrame(card, fg_color="#E2E8F0", height=6, corner_radius=3)
        pb_bg.place(x=22, y=165, relwidth=0.74)
        pb_fill = ctk.CTkFrame(pb_bg, fg_color=value_color or border, height=6, corner_radius=3)
        pb_fill.place(x=0, y=0, relheight=1.0, relwidth=0)
        self._animate_relwidth(pb_fill, min(1.0, progress / 100.0))

    def _animate_relwidth(self, widget, target, steps=15, delay=12):
        def _tick(i=[0]):
            if i[0] >= steps:
                widget.place_configure(relwidth=target)
                return
            widget.place_configure(relwidth=target * (i[0] + 1) / steps)
            i[0] += 1
            widget.after(delay, _tick)

        _tick()

    def _render_cancel_reasons(self, rows):
        self._section_header(self.cancel_card, "Cancellation Reason Distribution",
                             "Grouped customer vs driver cancellation reasons; click a bar to drill down")
        if not rows:
            self._empty(self.cancel_card, "No cancellation reason rows returned for this filter.")
            return
        reasons = [r["reason"] for r in rows]
        cust = np.array([int(r["customer_cnt"] or 0) for r in rows])
        driv = np.array([int(r["driver_cnt"] or 0) for r in rows])
        totals = cust + driv
        y = np.arange(len(reasons))

        import textwrap
        fig, ax = self._figure(8.5, max(4.6, len(reasons) * 0.42))
        ax.barh(y - 0.18, cust, height=0.34, color=COLORS["red"], alpha=0.88, label="Customers", picker=True)
        ax.barh(y + 0.18, driv, height=0.34, color=COLORS["orange"], alpha=0.88, label="Drivers", picker=True)
        ax.set_yticks(y)
        _wrap = lambda s: "\n".join(textwrap.wrap(str(s), width=26)[:2])
        ax.set_yticklabels([_wrap(r) for r in reasons], fontsize=8.5)
        ax.spines["left"].set_visible(True)
        ax.spines["left"].set_color(COLORS["border"])
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(COLORS["border"])
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(axis="y", length=4, color=COLORS["border"], pad=8)
        ax.tick_params(axis="x", length=4, color=COLORS["border"])
        ax.invert_yaxis()
        ax.set_xlabel("Cancellation count", fontsize=8, color=COLORS["muted"])
        ax.legend(frameon=False, fontsize=8, loc="lower right")

        max_val = max(cust.max(), driv.max()) if len(cust) > 0 else 1
        ax.set_xlim(0, max_val * 1.4)

        for i, total in enumerate(totals):
            if total:
                pct = total / totals.sum() * 100
                longest_bar = max(cust[i], driv[i])
                ax.text(longest_bar + max_val * 0.05, i, f"{int(total)} ({pct:.1f}%)",
                        va="center", ha="left", fontsize=7.5, color=COLORS["text"])

        annot = ax.annotate("", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", ec=COLORS["border"]),
                            fontsize=8)
        annot.set_visible(False)

        def on_motion(event):
            if event.inaxes != ax or event.ydata is None:
                annot.set_visible(False)
                fig.canvas.draw_idle()
                return
            idx = int(round(event.ydata))
            if 0 <= idx < len(reasons):
                annot.xy = (event.xdata or 0, event.ydata)
                annot.set_text(f"{reasons[idx]}\nCustomer: {cust[idx]:,}\nDriver: {driv[idx]:,}")
                annot.set_visible(True)
                fig.canvas.draw_idle()

        def on_click(event):
            if event.inaxes != ax or event.ydata is None:
                return
            idx = int(round(event.ydata))
            if 0 <= idx < len(reasons):
                self.selected_reason = reasons[idx]
                self.apply_filters()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)
        fig.canvas.mpl_connect("button_press_event", on_click)
        fig.subplots_adjust(left=0.22, right=0.99, top=0.95, bottom=0.12)
        self._embed(self.cancel_card, fig, toolbar=True)

    def _render_vtat_analysis(self, rows):
        self._section_header(self.vtat_card, "VTAT Cancellation Pressure",
                             "Bucket chart: ride volume bars with customer cancellation-rate line")
        if not rows:
            self._empty(self.vtat_card, "No VTAT rows returned for this filter.")
            return

        labels = [str(row["vtat_bucket"]) for row in rows]
        totals = np.array([int(row["total"] or 0) for row in rows])
        cancelled = np.array([int(row["cancelled"] or 0) for row in rows])
        rates = np.array([safe_float(row["cancel_rate"]) for row in rows])
        avg_vtat = np.array([safe_float(row["avg_vtat"]) for row in rows])

        fig, ax = self._figure(6.2, 4.6)
        x = np.arange(len(labels))
        bar_colors = [
            COLORS["green"] if rate < 8 else COLORS["yellow"] if rate < 15 else COLORS["orange"] if rate < 22 else COLORS["red"]
            for rate in rates
        ]
        bars = ax.bar(x, totals, color=bar_colors, alpha=0.82, width=0.58,
                      edgecolor="white", linewidth=1.0, label="Ride volume")
        ax.set_ylabel("Ride volume", fontsize=8, color=COLORS["muted"])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8)

        ax2 = ax.twinx()
        ax2.plot(x, rates, color=COLORS["primary_dark"], linewidth=2.4,
                 marker="o", markersize=6, label="Customer cancellation rate")
        ax2.fill_between(x, rates, alpha=0.10, color=COLORS["primary_dark"])
        ax2.set_ylabel("Customer cancellation rate (%)", fontsize=8, color=COLORS["muted"])
        ax2.tick_params(colors=COLORS["muted"], labelsize=8)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color(COLORS["border"])
        ax.set_ylim(0, 45000)

        for i, (bar, rate) in enumerate(zip(bars, rates)):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(totals) * 0.02,
                    f"{totals[i]:,}", ha="center", fontsize=7.5, color=COLORS["text"])
            ax2.text(i, rate + max(rates.max(), 1) * 0.05, f"{rate:.1f}%",
                     ha="center", fontsize=7.5, color=COLORS["primary_dark"], fontweight="bold")

        handles1, labels1 = ax.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(handles1 + handles2, labels1 + labels2, fontsize=8, frameon=False, loc="upper left")

        annot = ax.annotate("", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", ec=COLORS["border"]),
                            fontsize=8)
        annot.set_visible(False)

        def on_motion(event):
            if event.inaxes not in (ax, ax2) or event.xdata is None:
                annot.set_visible(False)
                fig.canvas.draw_idle()
                return
            idx = int(round(event.xdata))
            if 0 <= idx < len(labels):
                annot.xy = (idx, totals[idx])
                annot.set_text(
                    f"{labels[idx]}\n"
                    f"Rides: {totals[idx]:,}\n"
                    f"Customer cancelled: {cancelled[idx]:,}\n"
                    f"Cancel rate: {rates[idx]:.2f}%\n"
                    f"Avg VTAT: {avg_vtat[idx]:.1f} min"
                )
                annot.set_visible(True)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)
        fig.tight_layout(pad=1.15)
        self._embed(self.vtat_card, fig, toolbar=True)

    def _render_vehicle_cancel_chart(self, rows):
        self._section_header(
            self.vehicle_card,
            "Vehicle Types With Highest Cancellation Rate",
            "Ranked by cancellation rate; each vehicle type uses its own color"
        )
        if not rows:
            self._empty(self.vehicle_card, "No vehicle cancellation data returned for this filter.")
            return

        labels = [str(row["vehicle_type"])[:18] for row in rows]
        rates = np.array([safe_float(row.get("cancel_rate")) for row in rows])
        totals = np.array([int(row.get("total_rides") or 0) for row in rows])
        cancelled = np.array([int(row.get("cancelled_rides") or 0) for row in rows])
        y = np.arange(len(labels))
        vehicle_palette = [
            "#EF4444", "#F97316", "#F59E0B", "#10B981", "#14B8A6", "#3B82F6",
            "#6366F1", "#8B5CF6", "#EC4899", "#64748B", "#84CC16", "#06B6D4",
        ]
        colors = [vehicle_palette[i % len(vehicle_palette)] for i in range(len(labels))]

        fig, ax = self._figure(9.5, max(3.8, len(labels) * 0.35))
        
        ax.set_axisbelow(True)
        ax.grid(axis='x', color="#94A3B8", linestyle='-', alpha=0.9, linewidth=1.5)
        
        bars = ax.barh(y, rates, color=colors, alpha=0.92, height=0.58, edgecolor="white", linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Cancellation rate (%)", fontsize=9, color=COLORS["muted"])
        for i, bar in enumerate(bars):
            ax.text(
                bar.get_width() + max(rates.max(), 1) * 0.012,
                bar.get_y() + bar.get_height() / 2,
                f"{rates[i]:.1f}%  |  {cancelled[i]:,}/{totals[i]:,}",
                va="center",
                fontsize=8,
                color=COLORS["text"],
                fontweight="bold" if i < 3 else "normal",
            )

        annot = ax.annotate("", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", ec=COLORS["border"]),
                            fontsize=8)
        annot.set_visible(False)

        def on_motion(event):
            if event.inaxes != ax or event.ydata is None:
                annot.set_visible(False)
                fig.canvas.draw_idle()
                return
            idx = int(round(event.ydata))
            if 0 <= idx < len(rows):
                annot.xy = (event.xdata or rates[idx], idx)
                annot.set_text(
                    f"{rows[idx]['vehicle_type']}\n"
                    f"Cancel rate: {rates[idx]:.2f}%\n"
                    f"Cancelled: {cancelled[idx]:,}\n"
                    f"Total rides: {totals[idx]:,}"
                )
                annot.set_visible(True)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)
        fig.tight_layout(pad=1.1)
        self._embed(self.vehicle_card, fig, toolbar=False)

    def _render_fraud_table(self):
        rows = self._filtered_rows("fraud", self.top_fraud_var.get())
        self._watchlist_header(
            self.fraud_card,
            "$",
            "Cash Fraud Watchlist",
            "Payment = Cash · Status: Cancelled / Incomplete · Distance > 1 km",
            self.top_fraud_var,
            self.risk_fraud_var,
            "fraud",
            lambda: self._export_rows("fraud"),
        )
        self._custom_table(
            self.fraud_card,
            kind="fraud",
            headers=("BOOKING\nID", "DRIVER", "DATE", "DISTANCE", "STATUS", "RISK"),
            rows=rows,
            widths=(1.2, 1.0, 1.2, 1.0, 1.25, 0.9),
        )
        self._pager(self.fraud_card, "fraud")

    def _fill_fraud_tree(self):
        rows = self._filtered_rows("fraud", self.top_fraud_var.get())
        start = self.table_page["fraud"] * self.page_size
        for row in rows[start:start + self.page_size]:
            risk = int(safe_float(row.get("risk_score")))
            tag, label = self._fraud_risk(row)
            self.fraud_tree.insert("", "end", tags=(tag,), values=(
                row.get("Booking ID"), row.get("Driver ID"), row.get("driver_name"),
                f"{safe_float(row.get('Ride Distance')):.1f} km", row.get("Booking Status"),
                row.get("Payment Method"), str(row.get("event_time")), row.get("region"), label, risk
            ))
        self._apply_risk_tags(self.fraud_tree)

    def _render_driver_table(self):
        rows = self._filtered_rows("drivers", self.top_driver_var.get())
        self._watchlist_header(
            self.driver_card,
            "!",
            "Driver Cancel Watchlist",
            f"Accepted rides >= {self.driver_threshold} · Sorted by cancellation rate · Repeated abnormal behavior",
            self.top_driver_var,
            self.risk_driver_var,
            "drivers",
            None,
            self.cancel_driver_type_var,
        )
        self._custom_table(
            self.driver_card,
            kind="drivers",
            headers=("RANK", "DRIVER", "ACCEPTED", "CANCELLED", "CANCEL RATE", "RISK"),
            rows=rows,
            widths=(0.7, 1.2, 1.0, 1.0, 1.15, 0.9),
        )
        self._pager(self.driver_card, "drivers")

    def _fill_driver_tree(self):
        rows = self._filtered_rows("drivers", self.top_driver_var.get())
        start = self.table_page["drivers"] * self.page_size
        for index, row in enumerate(rows[start:start + self.page_size], start + 1):
            rate = safe_float(row.get("cancel_rate"))
            rating = safe_float(row.get("avg_rating"))
            tag, label = self._driver_risk(row)
            self.driver_tree.insert("", "end", tags=(tag,), values=(
                index, row.get("Driver ID"), int(row.get("accepted_rides") or 0),
                int(row.get("driver_cancelled") or 0), f"{rate:.1f}%",
                f"{rating:.2f}" if rating else "N/A", label, row.get("common_reason")
            ))
        self._apply_risk_tags(self.driver_tree)

    def _watchlist_header(self, parent, icon, title, subtitle, top_var, risk_var, kind, export_cmd=None, cancel_type_var=None):
        rows_all = self.raw_rows[kind]
        risk_func = self._fraud_risk if kind == "fraud" else self._driver_risk
        high_count = sum(1 for row in rows_all if risk_func(row)[0] == "high")
        med_count = sum(1 for row in rows_all if risk_func(row)[0] == "medium")
        low_count = sum(1 for row in rows_all if risk_func(row)[0] == "low")

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 8))

        icon_box = ctk.CTkLabel(
            header,
            text=icon,
            width=32,
            height=32,
            corner_radius=10,
            fg_color=COLORS["red_bg"] if kind == "fraud" else COLORS["orange_bg"],
            text_color=COLORS["red"] if kind == "fraud" else COLORS["orange"],
            font=font(17, "bold"),
        )
        icon_box.pack(side="left", padx=(0, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_box, text=title, font=font(14, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_box, text=subtitle, font=font(10),
                     text_color="#8A94A6", wraplength=560, justify="left").pack(anchor="w", pady=(2, 0))

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")

        top_frame = ctk.CTkFrame(controls, fg_color="transparent")
        top_frame.pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(top_frame, text="Top", font=font(12, "bold"), text_color=COLORS["muted"]).pack(side="left", padx=(0, 4))

        entry = ctk.CTkEntry(
            top_frame,
            textvariable=top_var,
            placeholder_text="",
            width=48,
            height=28,
            fg_color="#F9FAFB",
            border_color=COLORS["border"],
            corner_radius=8,
            justify="center",
        )
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda *_: self._search_filter_changed(kind))

        risk_box = ctk.CTkComboBox(
            controls,
            variable=risk_var,
            values=["All Risk", "High Risk", "Medium Risk", "Low Risk"],
            width=108,
            height=28,
            fg_color="#FFFFFF",
            border_color="#FCA5A5" if high_count else COLORS["border"],
            button_color=COLORS["red_bg"] if high_count else COLORS["primary_light"],
            button_hover_color="#FECACA" if high_count else "#E0E7FF",
            text_color=COLORS["text"],
            state="readonly",
            command=lambda *_: self._risk_filter_changed(kind),
        )
        risk_box.pack(side="left", padx=(0, 8))

        if cancel_type_var is not None:
            cancel_box = ctk.CTkComboBox(
                controls,
                variable=cancel_type_var,
                values=["All cancellations", "Cancelled by Driver", "Cancelled by Customer"],
                width=140,
                height=28,
                fg_color="#FFFFFF",
                border_color=COLORS["border"],
                button_color=COLORS["orange_bg"],
                button_hover_color="#FED7AA",
                text_color=COLORS["text"],
                state="readonly",
                command=lambda *_: self._cancel_type_filter_changed(kind),
            )
            cancel_box.pack(side="left", padx=(0, 8))

        if export_cmd:
            ctk.CTkButton(
                controls,
                text="Export",
                width=74,
                height=28,
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_dark"],
                command=export_cmd,
            ).pack(side="left", padx=(0, 8))

        counts_frame = ctk.CTkFrame(controls, fg_color="transparent")
        counts_frame.pack(side="left")
        
        ctk.CTkLabel(
            counts_frame, text=f"{high_count} High", font=font(10, "bold"),
            fg_color="#FFF1F2", text_color="#DC2626", corner_radius=18, padx=8, pady=4
        ).pack(side="left", padx=(0, 4))
        
        ctk.CTkLabel(
            counts_frame, text=f"{med_count} Med", font=font(10, "bold"),
            fg_color="#FFF7ED", text_color="#D97706", corner_radius=18, padx=8, pady=4
        ).pack(side="left", padx=(0, 4))
        
        ctk.CTkLabel(
            counts_frame, text=f"{low_count} Low", font=font(10, "bold"),
            fg_color="#ECFDF5", text_color="#059669", corner_radius=18, padx=8, pady=4
        ).pack(side="left")

    def _custom_table(self, parent, kind, headers, rows, widths):
        start = self.table_page[kind] * self.page_size
        page_rows = rows[start:start + self.page_size]
        table = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0)
        table.pack(fill="x", padx=0, pady=(0, 6))

        head = ctk.CTkFrame(table, fg_color="#F8FAFC", corner_radius=0, height=36)
        head.pack(fill="x")
        head.pack_propagate(False)
        for index, width in enumerate(widths):
            head.grid_columnconfigure(index, weight=int(width * 100))
            ctk.CTkLabel(
                head,
                text=headers[index],
                font=font(9, "bold"),
                text_color="#475569",
                justify="left",
                anchor="w",
            ).grid(row=0, column=index, sticky="nsew", padx=10, pady=5)

        if not page_rows:
            ctk.CTkLabel(
                table,
                text="No rows match the current search/risk filter.",
                font=font(11),
                text_color=COLORS["muted"],
            ).pack(pady=24)
            return

        for row_offset, row in enumerate(page_rows, start=1):
            if kind == "fraud":
                display = self._fraud_display(row)
                risk_tag, risk_label = self._fraud_risk(row)
                row_bg = "#FFF7F7" if risk_tag == "high" else "#FFFCF5" if risk_tag == "medium" else "#F8FFFB"
                values = [
                    (display["booking"], "text", "bold"),
                    (display["driver"], "text", "normal"),
                    (display["date"], "text", "normal"),
                    (display["distance"], "distance", risk_tag),
                    (display["status"], "status", None),
                    (risk_label.title(), "risk", risk_tag),
                ]
            else:
                display = self._driver_display(row, start + row_offset)
                risk_tag, risk_label = self._driver_risk(row)
                row_bg = "#FFF7F7" if risk_tag == "high" else "#FFFCF5" if risk_tag == "medium" else "#F8FFFB"
                values = [
                    (display["rank"], "text", "bold"),
                    (display["driver"], "text", "bold"),
                    (display["accepted"], "text", "normal"),
                    (display["cancelled"], "distance", risk_tag),
                    (display["rate"], "distance", risk_tag),
                    (risk_label.title(), "risk", risk_tag),
                ]

            row_frame = ctk.CTkFrame(table, fg_color=row_bg, corner_radius=0, height=44)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)
            for index, width in enumerate(widths):
                row_frame.grid_columnconfigure(index, weight=int(width * 100))
                value, cell_type, weight = values[index]
                cell = ctk.CTkFrame(row_frame, fg_color="transparent")
                cell.grid(row=0, column=index, sticky="nsew", padx=6, pady=4)
                self._render_custom_cell(cell, value, cell_type, weight)
                for widget in [cell] + cell.winfo_children():
                    widget.bind("<Button-1>", lambda _event, r=row, k=kind: self._show_custom_detail(r, k))

            ctk.CTkFrame(table, fg_color="#F1F5F9", height=1).pack(fill="x")

    def _render_custom_cell(self, parent, value, cell_type, risk_tag):
        if cell_type == "status":
            bg, fg, border = self._status_colors(value)
            ctk.CTkLabel(parent, text=value, font=font(9, "bold"), fg_color=bg,
                         text_color=fg, corner_radius=14, padx=8, pady=2).pack(anchor="w", pady=5)
        elif cell_type == "risk":
            bg, fg, border = self._risk_colors(risk_tag)
            ctk.CTkLabel(parent, text=value, font=font(9, "bold"), fg_color=bg,
                         text_color=fg, corner_radius=14, padx=8, pady=2).pack(anchor="w", pady=5)
        elif cell_type == "distance":
            _, fg, _ = self._risk_colors(risk_tag)
            ctk.CTkLabel(parent, text=value, font=font(10, "bold"),
                         text_color=fg, wraplength=105, justify="left").pack(anchor="w", pady=5)
        else:
            ctk.CTkLabel(parent, text=value, font=font(10, "bold" if risk_tag == "bold" else "normal"),
                         text_color="#0F172A", wraplength=135, justify="left").pack(anchor="w", pady=4)

    def _fraud_display(self, row):
        return {
            "booking": str(row.get("Booking ID") or "N/A"),
            "driver": str(row.get("Driver ID") or "N/A"),
            "date": self._format_date(row.get("event_time")),
            "distance": f"{safe_float(row.get('Ride Distance')):.1f} km",
            "status": self._short_status(row.get("Booking Status")),
        }

    def _driver_display(self, row, rank):
        cancel_type = self.cancel_driver_type_var.get()
        if cancel_type == "Cancelled by Customer":
            cancelled = int(row.get("customer_cancelled") or 0)
            rate = safe_float(row.get("customer_cancel_rate"))
        elif cancel_type == "Cancelled by Driver":
            cancelled = int(row.get("driver_cancelled") or 0)
            rate = safe_float(row.get("cancel_rate"))
        else:
            cancelled = int(row.get("driver_cancelled") or 0) + int(row.get("customer_cancelled") or 0)
            rate = safe_float(row.get("total_cancel_rate"))
        return {
            "rank": f"#{rank}",
            "driver": str(row.get("Driver ID") or "N/A"),
            "accepted": f"{int(row.get('accepted_rides') or 0):,}",
            "cancelled": f"{cancelled:,}",
            "rate": f"{rate:.1f}%",
        }

    def _format_date(self, value):
        text = str(value or "")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(text[:19], fmt).strftime("%b %d, %Y")
            except ValueError:
                continue
        return text[:12] or "N/A"

    def _short_status(self, status):
        status = str(status or "N/A")
        if "Incomplete" in status:
            return "Incomplete"
        if "Cancel" in status:
            return "Cancelled"
        return status

    def _status_colors(self, status):
        if "Incomplete" in str(status):
            return "#FFF7ED", "#D97706", "#FCD34D"
        if "Cancel" in str(status):
            return "#FFF1F2", "#DC2626", "#FCA5A5"
        return "#ECFDF5", "#059669", "#6EE7B7"

    def _risk_colors(self, risk_tag):
        if risk_tag == "high":
            return "#FFF1F2", "#DC2626", "#FCA5A5"
        if risk_tag == "medium":
            return "#FFF7ED", "#D97706", "#FCD34D"
        return "#ECFDF5", "#059669", "#6EE7B7"

    def _show_custom_detail(self, row, kind):
        win = ctk.CTkToplevel(self)
        win.title("Fraud Ride Detail" if kind == "fraud" else "Driver Cancel Detail")
        win.geometry("680x600")
        box = make_card(win)
        box.pack(fill="both", expand=True, padx=18, pady=18)
        title = "Fraud Ride Detail" if kind == "fraud" else "Driver Cancel Detail"
        ctk.CTkLabel(box, text=title, font=font(18, "bold"),
                     text_color=COLORS["text"]).pack(anchor="w", padx=18, pady=(18, 10))
        for key, value in row.items():
            line = ctk.CTkFrame(box, fg_color="#F9FAFB", corner_radius=8)
            line.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(line, text=str(key), width=160, font=font(11, "bold"),
                         text_color=COLORS["muted"], anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(line, text=str(value), font=font(12), text_color=COLORS["text"],
                         wraplength=280, justify="left").pack(side="left", fill="x", expand=True, padx=10, pady=8)

    def _tree(self, parent, cols, style_name, height=10):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(style_name, background=COLORS["surface"], fieldbackground=COLORS["surface"],
                        foreground=COLORS["text"], borderwidth=0, rowheight=38, font=(FONT_FAMILY, 10))
        style.configure(f"{style_name}.Heading", background="#F9FAFB", foreground=COLORS["muted"],
                        borderwidth=0, font=(FONT_FAMILY, 10, "bold"))
        style.map(style_name, background=[("selected", COLORS["primary_light"])],
                  foreground=[("selected", COLORS["primary_dark"])])
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=14, pady=(0, 6))
        sb_y = ttk.Scrollbar(frame)
        sb_y.pack(side="right", fill="y")
        sb_x = ttk.Scrollbar(frame, orient="horizontal")
        sb_x.pack(side="bottom", fill="x")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=height,
                            yscrollcommand=sb_y.set, xscrollcommand=sb_x.set, style=style_name)
        sb_y.config(command=tree.yview)
        sb_x.config(command=tree.xview)
        for col in cols:
            width = 90
            if col in ("Timestamp", "Common Reason"):
                width = 210
            elif col in ("Booking ID", "Driver Name", "Status"):
                width = 140
            elif col in ("Region", "Payment"):
                width = 130
            elif col in ("Risk Score", "Cancel Rate", "Avg Rating", "Risk Level"):
                width = 110
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        tree.pack(fill="x", expand=True)
        SortableTree(tree).attach()
        return tree

    def _table_header(self, parent, title, subtitle, search_var, search_cmd, export_cmd, risk_var=None, kind=None):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 10))
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text=title, font=font(14, "bold"),
                     text_color=COLORS["text"], wraplength=520, justify="left").pack(anchor="w")
        ctk.CTkLabel(left, text=subtitle, font=font(11),
                     text_color=COLORS["muted_light"], wraplength=680, justify="left").pack(anchor="w")
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")
        entry = ctk.CTkEntry(right, textvariable=search_var, placeholder_text="Search...",
                             width=240, height=36, fg_color="#F9FAFB", border_color=COLORS["border"])
        entry.pack(side="left", padx=(0, 8))
        entry.bind("<KeyRelease>", search_cmd)
        if risk_var and kind:
            risk_box = ctk.CTkComboBox(
                right, variable=risk_var,
                values=["All Risk", "High Risk", "Medium Risk", "Low Risk"],
                width=132, height=36, fg_color="#F9FAFB", border_color=COLORS["border"],
                button_color=COLORS["primary_light"], button_hover_color="#E0E7FF",
                text_color=COLORS["text"], state="readonly",
                command=lambda *_: self._risk_filter_changed(kind)
            )
            risk_box.pack(side="left", padx=(0, 8))
        if export_cmd:
            ctk.CTkButton(right, text="Export", width=84, height=36, fg_color=COLORS["primary"],
                          hover_color=COLORS["primary_dark"], command=export_cmd).pack(side="left")

    def _pager(self, parent, kind):
        rows = self._filtered_rows(kind, self.top_fraud_var.get() if kind == "fraud" else self.top_driver_var.get())
        total_pages = max(1, math.ceil(len(rows) / self.page_size))
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(bar, text=f"Showing page {self.table_page[kind] + 1} of {total_pages} | {len(rows):,} rows",
                     font=font(11), text_color=COLORS["muted"]).pack(side="left")
        ctk.CTkButton(bar, text="Prev", width=62, height=28, fg_color="#F3F4F6", text_color=COLORS["text"],
                      hover_color="#E5E7EB", command=lambda: self._page(kind, -1)).pack(side="right", padx=(6, 0))
        ctk.CTkButton(bar, text="Next", width=62, height=28, fg_color="#F3F4F6", text_color=COLORS["text"],
                      hover_color="#E5E7EB", command=lambda: self._page(kind, 1)).pack(side="right")

    def _page(self, kind, delta):
        rows = self._filtered_rows(kind, self.top_fraud_var.get() if kind == "fraud" else self.top_driver_var.get())
        total_pages = max(1, math.ceil(len(rows) / self.page_size))
        self.table_page[kind] = min(max(0, self.table_page[kind] + delta), total_pages - 1)
        self._rerender_table(kind)

    def _risk_filter_changed(self, kind):
        self.table_page[kind] = 0
        self._rerender_table(kind)

    def _cancel_type_filter_changed(self, kind):
        self.table_page[kind] = 0
        self._rerender_table(kind)

    def _search_filter_changed(self, kind):
        self.table_page[kind] = 0
        self._rerender_table(kind)

    def _rerender_table(self, kind):
        if kind == "fraud":
            self._clear(self.fraud_card)
            self._render_fraud_table()
        else:
            self._clear(self.driver_card)
            self._render_driver_table()

    def _filtered_rows(self, kind, text):
        text = text.lower().strip()
        rows = self.raw_rows[kind]
        risk_value = self.risk_fraud_var.get() if kind == "fraud" else self.risk_driver_var.get()
        if risk_value != "All Risk":
            wanted = risk_value.split()[0].lower()
            risk_func = self._fraud_risk if kind == "fraud" else self._driver_risk
            rows = [row for row in rows if risk_func(row)[0] == wanted]
        if kind == "drivers":
            cancel_type = self.cancel_driver_type_var.get()
            if cancel_type == "Cancelled by Driver":
                rows = [row for row in rows if int(row.get("driver_cancelled") or 0) > 0]
            elif cancel_type == "Cancelled by Customer":
                rows = [row for row in rows if int(row.get("customer_cancelled") or 0) > 0]
        if text and text.isdigit():
            top_n = int(text)
            if top_n > 0:
                return rows[:top_n]

        return rows

    def _fraud_risk(self, row):
        score = int(safe_float(row.get("risk_score")))
        if score >= 80:
            return "high", "HIGH"
        if score >= 62:
            return "medium", "MEDIUM"
        return "low", "LOW"

    def _driver_risk(self, row):
        cancel_type = getattr(self, "cancel_driver_type_var", None)
        cancel_type = cancel_type.get() if cancel_type else "All cancellations"
        if cancel_type == "Cancelled by Customer":
            rate = safe_float(row.get("customer_cancel_rate"))
        elif cancel_type == "Cancelled by Driver":
            rate = safe_float(row.get("cancel_rate"))
        else:
            rate = safe_float(row.get("total_cancel_rate"))
        rating = safe_float(row.get("avg_rating"))
        if rate >= 40 or (rating and rating < 3.8):
            return "high", "HIGH"
        if rate >= 20 or (rating and rating < 4.2):
            return "medium", "MEDIUM"
        return "low", "LOW"

    def _apply_risk_tags(self, tree):
        tree.tag_configure("high", foreground="#991B1B", background="#FFF1F2")
        tree.tag_configure("medium", foreground="#9A3412", background="#FFF7ED")
        tree.tag_configure("low", foreground="#065F46", background="#ECFDF5")

    def _risk_summary_chips(self, parent, kind):
        rows = self.raw_rows[kind]
        risk_func = self._fraud_risk if kind == "fraud" else self._driver_risk
        counts = {"high": 0, "medium": 0, "low": 0}
        for row in rows:
            counts[risk_func(row)[0]] += 1

        chip_row = ctk.CTkFrame(parent, fg_color="transparent")
        chip_row.pack(fill="x", padx=16, pady=(0, 10))
        chips = [
            ("HIGH RISK", counts["high"], "#FEE2E2", "#991B1B", "#FCA5A5"),
            ("MEDIUM RISK", counts["medium"], "#FFF7ED", "#9A3412", "#FDBA74"),
            ("LOW RISK", counts["low"], "#ECFDF5", "#065F46", "#6EE7B7"),
        ]
        for label, count, bg, fg, border in chips:
            ctk.CTkLabel(
                chip_row,
                text=f"{label}: {count:,}",
                font=font(11, "bold"),
                fg_color=bg,
                text_color=fg,
                corner_radius=18,
                padx=12,
                pady=5,
            ).pack(side="left", padx=(0, 8))

    def _export_rows(self, kind):
        rows = self._filtered_rows(kind, self.top_fraud_var.get() if kind == "fraud" else self.top_driver_var.get())
        if not rows:
            messagebox.showinfo("Export", "No rows to export.")
            return
        path = f"{kind}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        headers = list(rows[0].keys())
        with open(path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in rows:
                f.write(",".join('"' + str(row.get(h, "")).replace('"', '""') + '"' for h in headers) + "\n")
        messagebox.showinfo("Export", f"Exported {len(rows):,} rows to {path}")

    def _show_row_detail(self, tree, title):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0], "values")
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("520x430")
        box = make_card(win)
        box.pack(fill="both", expand=True, padx=18, pady=18)
        ctk.CTkLabel(box, text=title, font=font(18, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=18, pady=(18, 10))
        for col, val in zip(tree["columns"], values):
            row = ctk.CTkFrame(box, fg_color="#F9FAFB", corner_radius=8)
            row.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(row, text=col, width=150, font=font(11, "bold"),
                         text_color=COLORS["muted"], anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=str(val), font=font(12), text_color=COLORS["text"],
                         wraplength=300, justify="left", anchor="w").pack(side="left", padx=10, pady=8, fill="x", expand=True)

    def _section_header(self, parent, title, subtitle):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 2))
        ctk.CTkLabel(header, text=title, font=font(14, "bold"),
                     text_color=COLORS["text"], wraplength=520, justify="left").pack(anchor="w")
        ctk.CTkLabel(header, text=subtitle, font=font(11),
                     text_color=COLORS["muted_light"], wraplength=620, justify="left").pack(anchor="w")

    def _figure(self, width, height):
        plt.rcParams["font.family"] = FONT_FAMILY
        fig, ax = plt.subplots(figsize=(width, height), dpi=96)
        fig.patch.set_facecolor(COLORS["surface"])
        ax.set_facecolor("#FFFFFF")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(COLORS["border"])
        ax.tick_params(colors=COLORS["muted"], labelsize=8)
        return fig, ax

    def _embed(self, parent, fig, toolbar=False):
        holder = ctk.CTkFrame(parent, fg_color="transparent")
        holder.pack(fill="both", expand=True, padx=10, pady=(2, 12))
        canvas = FigureCanvasTkAgg(fig, master=holder)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)
        if toolbar:
            toolbar_frame = ctk.CTkFrame(holder, fg_color="transparent", height=28)
            toolbar_frame.pack(fill="x")
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame, pack_toolbar=False)
            toolbar.update()
            toolbar.pack(side="left")
        self.chart_canvases.append(canvas)

    def _empty(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=font(12), text_color=COLORS["muted"]).pack(pady=28)

    def _clear(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()

    def _set_status(self, text, error=False):
        self.status_label.configure(text=text, text_color=COLORS["red"] if error else COLORS["muted"])


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RideHub - Operational Analytics & Fraud Detection")
        self.geometry("1450x900")
        self.minsize(1100, 720)
        self.configure(fg_color=COLORS["page"])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._sidebar()
        content = RiskAnalysisFrame(self)
        content.grid(row=0, column=1, sticky="nsew")

    def _sidebar(self):
        side = ctk.CTkFrame(self, width=220, fg_color=COLORS["surface"],
                            corner_radius=0, border_width=1, border_color=COLORS["border"])
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        logo = ctk.CTkFrame(side, fg_color="transparent")
        logo.pack(fill="x", padx=20, pady=(16, 20))
        ctk.CTkLabel(logo, text="R", width=28, height=28, corner_radius=8,
                     fg_color=COLORS["primary"], text_color="white", font=font(16, "bold")).pack(side="left")
        ctk.CTkLabel(logo, text="RideHub", font=font(16, "bold"),
                     text_color=COLORS["text"]).pack(side="left", padx=10)
        ctk.CTkLabel(side, text="OPERATIONS", font=font(10, "bold"),
                     text_color=COLORS["muted_light"]).pack(anchor="w", padx=20, pady=(6, 6))
        for text, active in [
            ("Dashboard", False),
            ("Ride Management", False),
            ("Driver Profiles", False),
            ("Cancel & Risk Analysis", True),
            ("Settings", False),
        ]:
            ctk.CTkButton(side, text=text, anchor="w", height=36, corner_radius=8,
                          fg_color=COLORS["primary_light"] if active else "transparent",
                          text_color=COLORS["primary_dark"] if active else "#555555",
                          hover_color=COLORS["primary_light"],
                          font=font(13, "bold" if active else "normal")).pack(fill="x", padx=12, pady=2)


if __name__ == "__main__":
    if auto_setup_database:
        auto_setup_database()
    app = App()
    app.mainloop()
