from collections import Counter
from tkinter import messagebox

import customtkinter as ctk

from data.uber import get_db_connection


class _AnalyticsMixin:
    """F5 – Bulk Pattern Detection popup."""

    def f5_find_patterns(self):
        selected = [
            item for item in self.table.get_children()
            if self.table.item(item)['values'][0] == '☑'
        ]
        total_selected = len(selected)

        if total_selected == 0:
            messagebox.showwarning(
                "Selection Required",
                "Please select at least 1 ride to analyze!"
            )
            return

        ids = [
            str(self.table.item(item)['values'][1]).replace("#", "")
            for item in selected
        ]

        conn = get_db_connection()
        rows = []
        if conn:
            cursor = conn.cursor(dictionary=True)
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(
                f"SELECT * FROM rides WHERE `Booking ID` IN ({format_strings})",
                tuple(ids)
            )
            rows = cursor.fetchall()
            conn.close()

        if not rows:
            return

        status_counts = {'Completed': 0, 'Cancelled': 0, 'Incomplete': 0}
        interruption_reasons = Counter()
        hours_dist = {
            'Morning (06-12)': 0, 'Afternoon (12-17)': 0,
            'Evening (17-21)': 0, 'Night (21-06)': 0
        }
        pickup_zones = Counter()
        vehicles = Counter()
        payments = Counter()

        ignore_words = ["none", "nan", "null", ""]

        for row in rows:
            status = str(row.get('Booking Status', ''))
            if 'Completed' in status:
                status_counts['Completed'] += 1
            elif 'Cancel' in status:
                status_counts['Cancelled'] += 1
            else:
                status_counts['Incomplete'] += 1

            if 'Cancel' in status:
                c_reason = str(row.get('Reason for cancelling by Customer', '')).strip()
                d_reason = str(row.get('Driver Cancellation Reason', '')).strip()
                if c_reason and c_reason.lower() not in ignore_words:
                    interruption_reasons[f"[C] {c_reason}"] += 1
                if d_reason and d_reason.lower() not in ignore_words:
                    interruption_reasons[f"[D] {d_reason}"] += 1
            elif 'Completed' not in status:
                i_reason = str(row.get('Incomplete Rides Reason', '')).strip()
                if i_reason and i_reason.lower() not in ignore_words:
                    interruption_reasons[f"[I] {i_reason}"] += 1

            time_str = str(row.get('Time', '00:00'))
            try:
                hour = int(time_str.split(":")[0])
                if 6 <= hour < 12:
                    hours_dist['Morning (06-12)'] += 1
                elif 12 <= hour < 17:
                    hours_dist['Afternoon (12-17)'] += 1
                elif 17 <= hour < 21:
                    hours_dist['Evening (17-21)'] += 1
                else:
                    hours_dist['Night (21-06)'] += 1
            except Exception:
                pass

            pickup = str(row.get('Pickup Location', 'Unknown'))
            if pickup and pickup.lower() not in ignore_words:
                pickup_zones[pickup] += 1

            vehicle = str(row.get('Vehicle Type', 'Unknown'))
            if vehicle and vehicle.lower() not in ignore_words:
                vehicles[vehicle] += 1

            payment = str(row.get('Payment Method', 'Unknown'))
            if payment and payment.lower() not in ignore_words:
                payments[payment] += 1

        # Build window
        win = ctk.CTkToplevel(self)
        win.title("Common Pattern Analysis")
        win.geometry("550x750")
        win.configure(fg_color="#ffffff")
        win.attributes('-topmost', True)

        scroll_f = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll_f.pack(fill="both", expand=True, padx=5, pady=5)

        # Header
        header_f = ctk.CTkFrame(scroll_f, fg_color="transparent")
        header_f.pack(fill="x", padx=15, pady=(5, 10))
        ctk.CTkLabel(
            header_f, text=" Common Pattern Analysis",
            font=("Arial", 18, "bold"), text_color="#0f172a"
        ).pack(anchor="w")
        ctk.CTkLabel(
            header_f, text=f"{total_selected} ride(s) selected for analysis",
            font=("Arial", 12), text_color="#64748b"
        ).pack(anchor="w")
        ctk.CTkFrame(header_f, height=1, width=480, fg_color="#e2e8f0").pack(
            anchor="w", pady=(10, 0)
        )

        # 3 status boxes
        status_f = ctk.CTkFrame(scroll_f, fg_color="transparent")
        status_f.pack(fill="x", padx=15, pady=(0, 15))

        boxes = [
            ("Completed", status_counts['Completed'],
             "#ecfdf5", "#a7f3d0", "#059669"),
            ("Cancelled", status_counts['Cancelled'],
             "#fef2f2", "#fecaca", "#dc2626"),
            ("Incomplete", status_counts['Incomplete'],
             "#fffbeb", "#fde68a", "#d97706"),
        ]

        for i, (title, count, bg, border, text_col) in enumerate(boxes):
            status_f.columnconfigure(i, weight=1)
            box = ctk.CTkFrame(
                status_f, fg_color=bg, border_width=1,
                border_color=border, corner_radius=10
            )
            box.grid(row=0, column=i, padx=4, sticky="ew")
            ctk.CTkLabel(
                box, text=str(count),
                font=("Arial", 22, "bold"), text_color=text_col
            ).pack(pady=(15, 0))
            ctk.CTkLabel(
                box, text=title, font=("Arial", 11), text_color="#64748b"
            ).pack(pady=(0, 15))

        # Bar chart helper
        def draw_bar_section(parent, title, icon, color, data_dict, is_counter=True):
            sec_f = ctk.CTkFrame(parent, fg_color="transparent")
            sec_f.pack(fill="x", padx=15, pady=(5, 10))

            title_f = ctk.CTkFrame(sec_f, fg_color="transparent")
            title_f.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(
                title_f, text=f"{icon} {title.upper()}",
                font=("Arial", 11, "bold"), text_color=color
            ).pack(side="left")

            items = data_dict.most_common() if is_counter else list(data_dict.items())
            if not items:
                ctk.CTkLabel(
                    sec_f, text="No data available.",
                    font=("Arial", 11, "italic"), text_color="#94a3b8"
                ).pack(anchor="w", padx=10)
                return

            for key, val in items:
                pct = int((val / total_selected) * 100) if total_selected > 0 else 0

                row_f = ctk.CTkFrame(sec_f, fg_color="transparent")
                row_f.pack(fill="x", pady=0)

                ctk.CTkLabel(
                    row_f, text=str(key),
                    font=("Arial", 11), text_color="#334155"
                ).pack(side="left", padx=(5, 0))
                ctk.CTkLabel(
                    row_f, text=f"{val} rides ({pct}%)",
                    font=("Arial", 11, "bold"), text_color=color
                ).pack(side="right")

                bar_bg = ctk.CTkFrame(
                    sec_f, height=6, fg_color="#f1f5f9", corner_radius=3
                )
                bar_bg.pack(fill="x", padx=(5, 0), pady=(1, 5))

                if pct > 0:
                    bar_fill = ctk.CTkFrame(
                        bar_bg, height=6, fg_color=color, corner_radius=3
                    )
                    bar_fill.place(
                        relx=0, rely=0, relwidth=pct / 100, relheight=1
                    )

        # Draw all bar sections
        if interruption_reasons:
            draw_bar_section(
                scroll_f, "Interruption Reasons (Cancel/Incomplete)",
                "", "#dc2626", interruption_reasons
            )

        draw_bar_section(
            scroll_f, "Peak Hours Distribution",
            "", "#eab308", hours_dist, is_counter=False
        )
        draw_bar_section(
            scroll_f, "Common Pickup Zones",
            "", "#10b981", pickup_zones
        )
        draw_bar_section(
            scroll_f, "Vehicle Type Distribution",
            "", "#3b82f6", vehicles
        )
        draw_bar_section(
            scroll_f, "Payment Method",
            "", "#8b5cf6", payments
        )

        # System conclusion
        conclusion_f = ctk.CTkFrame(
            scroll_f, fg_color="#f4f8ff", corner_radius=12,
            border_width=1, border_color="#dbeafe"
        )
        conclusion_f.pack(side="top", fill="x", padx=15, pady=(5, 15), ipady=5)

        ctk.CTkLabel(
            conclusion_f, text=" SYSTEM CONCLUSION",
            font=("Arial", 11, "bold"), text_color="#2563eb"
        ).pack(anchor="w", padx=20, pady=(10, 2))

        cancel_rate = (
            int(((status_counts['Cancelled'] + status_counts['Incomplete']) /
                 total_selected) * 100) if total_selected > 0 else 0
        )
        top_zone = pickup_zones.most_common(1)[0][0] if pickup_zones else "Unknown"
        top_vehicle = vehicles.most_common(1)[0][0] if vehicles else "Unknown"
        top_hour = (
            max(hours_dist, key=hours_dist.get)
            if any(hours_dist.values()) else "Unknown"
        )
        top_payment = payments.most_common(1)[0][0] if payments else "Unknown"

        conclusion_text = (
            f"Analysis of {total_selected} selected ride(s): "
            f"Failure rate (Cancel/Incomplete) is at {cancel_rate}%. "
        )

        if interruption_reasons:
            top_reason = interruption_reasons.most_common(1)[0][0]
            conclusion_text += f"Primary anomaly pattern detected: '{top_reason}'. "

        conclusion_text += (
            f"Peak demand window is {top_hour}. "
            f"Most frequent pickup zone: {top_zone}. "
            f"Dominant vehicle type: {top_vehicle}. "
            f"Preferred payment method: {top_payment}. "
            "Action: Review operational metrics and allocation in "
            "high-demand zones to optimize performance."
        )

        ctk.CTkLabel(
            conclusion_f, text=conclusion_text,
            font=("Arial", 12), text_color="#475569",
            wraplength=450, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))
