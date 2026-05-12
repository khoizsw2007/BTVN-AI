from tkinter import messagebox

import customtkinter as ctk

from data.uber import get_db_connection


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, current_user=None):
        super().__init__(parent, fg_color="transparent")
        self.current_user = current_user or {}
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── LEFT: MY PROFILE ──
        left_col = ctk.CTkFrame(self, width=360, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_col.grid_propagate(False)

        ctk.CTkLabel(left_col, text="My Profile",
                     font=("Arial", 20, "bold"), text_color="#111827").pack(
            anchor="w", pady=(0, 15))

        profile_card = ctk.CTkFrame(left_col, fg_color="#FFFFFF", corner_radius=12,
                                    border_width=1, border_color="#E5E7EB")
        profile_card.pack(fill="both", expand=True)

        ctk.CTkLabel(profile_card, text="👨‍💼", font=("Arial", 60),
                     fg_color="#EEF2FF", corner_radius=16,
                     width=100, height=100).pack(pady=(30, 10))
        ctk.CTkLabel(profile_card,
                     text=self.current_user.get('full_name', 'Guest'),
                     font=("Arial", 18, "bold"), text_color="#111827").pack()

        role_color = ("#10B981" if self.current_user.get('role') == "Manager"
                      else "#F59E0B")
        ctk.CTkLabel(profile_card,
                     text=self.current_user.get('role', 'Guest'),
                     font=("Arial", 12, "bold"), text_color="#FFFFFF",
                     fg_color=role_color, corner_radius=10,
                     padx=10, pady=2).pack(pady=(5, 20))

        form_frame = ctk.CTkFrame(profile_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(form_frame, text="Username",
                     font=("Arial", 12, "bold"), text_color="#6B7280").pack(anchor="w")
        ctk.CTkEntry(form_frame,
                     textvariable=ctk.StringVar(
                         value=self.current_user.get('username', 'guest')),
                     state="readonly", height=40, fg_color="#F9FAFB",
                     border_color="#E5E7EB", text_color="#111827").pack(
            fill="x", pady=(5, 15))

        ctk.CTkLabel(form_frame, text="Email Address",
                     font=("Arial", 12, "bold"), text_color="#6B7280").pack(anchor="w")
        ctk.CTkEntry(form_frame,
                     textvariable=ctk.StringVar(
                         value=f"{self.current_user.get('username', 'guest')}@ridehub.com"),
                     state="readonly", height=40, fg_color="#F9FAFB",
                     border_color="#E5E7EB", text_color="#111827").pack(
            fill="x", pady=(5, 25))

        ctk.CTkButton(profile_card, text="🔑 Change Password",
                      fg_color="#F3F4F6", text_color="#4F46E5",
                      hover_color="#E0E7FF", font=("Arial", 12, "bold"),
                      height=40, command=self.change_password_popup).pack(
            fill="x", padx=30, pady=(0, 20))

        # ── RIGHT: SYSTEM ACCESS MANAGEMENT ──
        right_col = ctk.CTkFrame(self, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right_col, text="System Access Management",
                     font=("Arial", 20, "bold"), text_color="#111827").pack(
            anchor="w", pady=(0, 15))

        mg_card = ctk.CTkFrame(right_col, fg_color="#FFFFFF", corner_radius=12,
                               border_width=1, border_color="#E5E7EB")
        mg_card.pack(fill="both", expand=True)

        top_mg = ctk.CTkFrame(mg_card, fg_color="transparent")
        top_mg.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(top_mg, text="Authorized Personnel",
                     font=("Arial", 16, "bold"), text_color="#111827").pack(side="left")

        if self.current_user.get('role') == "Manager":
            ctk.CTkButton(top_mg, text="➕ Add New User",
                          font=("Arial", 12, "bold"), fg_color="#4F46E5",
                          hover_color="#4338CA",
                          command=self.add_user_popup).pack(side="right")
        else:
            ctk.CTkLabel(top_mg, text="👀 View Only Mode",
                         font=("Arial", 12, "italic", "bold"),
                         text_color="#9CA3AF").pack(side="right")

        header_tbl = ctk.CTkFrame(mg_card, fg_color="#F9FAFB", height=40, corner_radius=0)
        header_tbl.pack(fill="x", padx=20)
        header_tbl.pack_propagate(False)
        ctk.CTkLabel(header_tbl, text="Name & Role",
                     font=("Arial", 12, "bold"), text_color="#6B7280").place(x=60, y=10)
        ctk.CTkLabel(header_tbl, text="Username",
                     font=("Arial", 12, "bold"), text_color="#6B7280").place(x=350, y=10)
        ctk.CTkLabel(header_tbl, text="Action",
                     font=("Arial", 12, "bold"), text_color="#6B7280").place(
            relx=0.9, y=10)

        self.list_frame = ctk.CTkScrollableFrame(mg_card, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.load_users()

    def change_password_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Change Password")
        popup.geometry("380x420")
        popup.attributes("-topmost", True)

        ctk.CTkLabel(popup, text="Change Password",
                     font=("Arial", 18, "bold")).pack(pady=20)

        old_pw = ctk.StringVar()
        new_pw = ctk.StringVar()
        confirm_pw = ctk.StringVar()

        ctk.CTkLabel(popup, text="Current Password:",
                     font=("Arial", 11, "bold"), text_color="#4B5563").pack(
            anchor="w", padx=50)
        ctk.CTkEntry(popup, textvariable=old_pw, show="*", width=280).pack(pady=(5, 15))

        ctk.CTkLabel(popup, text="New Password:",
                     font=("Arial", 11, "bold"), text_color="#4B5563").pack(
            anchor="w", padx=50)
        ctk.CTkEntry(popup, textvariable=new_pw, show="*", width=280).pack(pady=(5, 15))

        ctk.CTkLabel(popup, text="Confirm New Password:",
                     font=("Arial", 11, "bold"), text_color="#4B5563").pack(
            anchor="w", padx=50)
        ctk.CTkEntry(popup, textvariable=confirm_pw, show="*", width=280).pack(
            pady=(5, 20))

        def save_pw():
            if old_pw.get() != self.current_user.get('password', ''):
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
            cursor.execute("UPDATE admin_users SET password=%s WHERE username=%s",
                           (new_pw.get(), self.current_user['username']))
            conn.commit()
            conn.close()

            self.current_user['password'] = new_pw.get()
            messagebox.showinfo("Success", "Password updated successfully!")
            popup.destroy()

        ctk.CTkButton(popup, text="Update Password", fg_color="#10B981",
                      hover_color="#059669", width=280, height=40,
                      font=("Arial", 12, "bold"), command=save_pw).pack()

    def load_users(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users ORDER BY role, full_name")
        for u in cursor.fetchall():
            row = ctk.CTkFrame(self.list_frame, fg_color="#FFFFFF",
                               border_color="#E5E7EB", border_width=1,
                               corner_radius=8, height=60)
            row.pack(fill="x", pady=4, padx=5)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text="👤", font=("Arial", 24)).place(x=15, y=15)
            ctk.CTkLabel(row, text=u['full_name'],
                         font=("Arial", 14, "bold"), text_color="#111827").place(
                x=60, y=10)

            r_color = ("#10B981" if u['role'] == "Manager"
                       else ("#3B82F6" if u['role'] == "Supervisor" else "#6B7280"))
            ctk.CTkLabel(row, text=u['role'],
                         font=("Arial", 10, "bold"), text_color=r_color).place(x=60, y=32)

            ctk.CTkLabel(row, text=u['username'],
                         font=("Arial", 13), text_color="#4B5563").place(x=350, y=20)

            if self.current_user.get('role') == "Manager":
                if u['username'] != self.current_user.get('username'):
                    ctk.CTkButton(row, text="Revoke ❌", width=80,
                                  fg_color="#FEE2E2", text_color="#EF4444",
                                  hover_color="#FECACA",
                                  command=lambda x=u['username']: self.delete_user(x)
                                  ).place(relx=0.88, y=15)
                else:
                    ctk.CTkLabel(row, text="Current User",
                                 font=("Arial", 12, "italic"),
                                 text_color="#9CA3AF").place(relx=0.88, y=20)
            else:
                if u['username'] == self.current_user.get('username'):
                    ctk.CTkLabel(row, text="You",
                                 font=("Arial", 13, "bold"),
                                 text_color="#4F46E5").place(relx=0.88, y=20)
                else:
                    ctk.CTkLabel(row, text="🔒 Restricted",
                                 font=("Arial", 12),
                                 text_color="#D1D5DB").place(relx=0.88, y=20)

        conn.close()

    def delete_user(self, username):
        if messagebox.askyesno("Confirm",
                               f"Are you sure you want to revoke access for '{username}'?"):
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

        ctk.CTkLabel(popup, text="Create Account",
                     font=("Arial", 18, "bold")).pack(pady=20)

        u_var = ctk.StringVar()
        p_var = ctk.StringVar()
        n_var = ctk.StringVar()
        r_var = ctk.StringVar(value="Supervisor")

        ctk.CTkLabel(popup, text="Username (Used for login, no spaces):",
                     font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkEntry(popup, textvariable=u_var, placeholder_text="e.g. johndoe",
                     width=280).pack(pady=(2, 15))

        ctk.CTkLabel(popup, text="Password (Minimum 6 characters):",
                     font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkEntry(popup, textvariable=p_var, placeholder_text="e.g. secret123",
                     width=280).pack(pady=(2, 15))

        ctk.CTkLabel(popup, text="Full Legal Name:",
                     font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkEntry(popup, textvariable=n_var, placeholder_text="e.g. John Doe",
                     width=280).pack(pady=(2, 15))

        ctk.CTkLabel(popup, text="System Role (Defines access level):",
                     font=("Arial", 11), text_color="#6B7280").pack(anchor="w", padx=60)
        ctk.CTkComboBox(popup, variable=r_var,
                        values=["Manager", "Supervisor", "Head"],
                        width=280).pack(pady=(2, 25))

        def save():
            if not u_var.get() or not p_var.get() or not n_var.get():
                messagebox.showwarning("Warning", "All fields are required!")
                return
            if len(p_var.get()) < 6:
                messagebox.showwarning("Warning",
                                       "Password must be at least 6 characters!")
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO admin_users VALUES (%s, %s, %s, %s)",
                               (u_var.get(), p_var.get(), n_var.get(), r_var.get()))
                conn.commit()
                self.load_users()
                messagebox.showinfo("Success", "User added successfully!")
                popup.destroy()
            except Exception:
                messagebox.showerror("Error", "Username already exists!")
            conn.close()

        ctk.CTkButton(popup, text="Save User", fg_color="#10B981",
                      hover_color="#059669", width=280, height=40,
                      font=("Arial", 12, "bold"), command=save).pack()
