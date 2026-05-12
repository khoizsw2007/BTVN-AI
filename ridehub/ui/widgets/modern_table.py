import customtkinter as ctk
from ui.theme import UI_FONT


class ModernTable(ctk.CTkFrame):
    ROW_H = 42
    HEAD_H = 38

    def __init__(self, parent, col_defs, data_rows, totals_row=None, max_scroll_rows=10, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._tip_win = None
        self._tip_timer = None
        n = len(col_defs)

        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color="#F9FAFB", height=self.HEAD_H, corner_radius=0,
                           border_width=1, border_color="#E5E7EB")
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        hdr.grid_columnconfigure(0, weight=1)
        for c, (txt, w, anc) in enumerate(col_defs):
            hdr.grid_columnconfigure(c + 1, weight=0)
            ctk.CTkLabel(hdr, text=txt, width=w, font=(UI_FONT, 10, "bold"),
                         text_color="#6B7280", anchor=anc).grid(row=0, column=c + 1, sticky="ew", padx=10)
        hdr.grid_columnconfigure(n + 1, weight=1)

        # ── Auto-switching frame (static vs scrollable) ──
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
                row_f.grid_columnconfigure(c + 1, weight=0)
            row_f.grid_columnconfigure(n + 1, weight=1)

            for c, (cell_txt, fg, fw) in enumerate(row_cells):
                _, w, anc = col_defs[c]
                lbl = ctk.CTkLabel(row_f, text=cell_txt, width=w, font=(UI_FONT, 11, fw),
                                   text_color=fg, anchor=anc)
                lbl.grid(row=0, column=c + 1, sticky="ew", padx=10)
                lbl.bind("<Enter>", lambda e, ri=r_idx, ci=c: self._schedule_tip(e, data_rows, ri, ci, col_defs))
                lbl.bind("<Leave>", self._cancel_tip)
            row_f.bind("<Enter>", lambda e, ri=r_idx: self._schedule_tip(e, data_rows, ri, None, col_defs))
            row_f.bind("<Leave>", self._cancel_tip)

        # ── Fixed TOTALS row ──
        if totals_row:
            sep = ctk.CTkFrame(self, fg_color="#E5E7EB", height=2)
            sep.pack(fill="x")
            tot_f = ctk.CTkFrame(self, fg_color="#F3F4F6", height=self.ROW_H, corner_radius=0,
                                 border_width=1, border_color="#E5E7EB")
            tot_f.pack(fill="x")
            tot_f.pack_propagate(False)

            tot_f.grid_columnconfigure(0, weight=1)
            for c, (col_txt, w, anc) in enumerate(col_defs):
                tot_f.grid_columnconfigure(c + 1, weight=0)
            tot_f.grid_columnconfigure(n + 1, weight=1)

            for c, (cell_txt, fg, fw) in enumerate(totals_row):
                _, w, anc = col_defs[c]
                ctk.CTkLabel(tot_f, text=cell_txt, width=w, font=(UI_FONT, 11, fw),
                             text_color=fg, anchor=anc).grid(row=0, column=c + 1, sticky="ew", padx=10)

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
        tw.geometry(f"+{x + 14}+{y + 14}")
        f = ctk.CTkFrame(tw, fg_color="#1F2937", corner_radius=8)
        f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text=tip_text, font=(UI_FONT, 11), text_color="#F9FAFB", justify="left").pack(padx=12, pady=8)
        self._tip_win = tw

    def _cancel_tip(self, event=None):
        if self._tip_timer:
            self.after_cancel(self._tip_timer)
            self._tip_timer = None
        self._hide_tip()

    def _hide_tip(self):
        if self._tip_win:
            try:
                self._tip_win.destroy()
            except Exception:
                pass
            self._tip_win = None
