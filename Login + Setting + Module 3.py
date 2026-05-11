import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ================= 1. DATABASE CONFIG & INIT =================
DB_CONFIG = {"host": "localhost", "user": "root", "password": "Baolam080907*", "database": "qlud"}

def get_db_connection():
    try: return mysql.connector.connect(**DB_CONFIG)
    except: return None

def setup_database():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    
    # Bảng Admin Users
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
        users = [("admin", "admin123", "Admin", "Manager")]
        for i in range(1, 4): users.append((f"sup{i}", "123456", f"Supervisor {i}", "Supervisor"))
        for i in range(1, 11): users.append((f"head{i}", "123456", f"Department Head {i}", "Head"))
        cursor.executemany("INSERT INTO admin_users VALUES (%s, %s, %s, %s)", users)
    
    # Bảng Flag và Suspend cho Module 3
    cursor.execute("CREATE TABLE IF NOT EXISTS flagged_users (uid VARCHAR(100) PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS suspended_users (uid VARCHAR(100) PRIMARY KEY)")
    
    conn.commit()
    conn.close()

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

# ================= 3. SETTINGS MODULE =================
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color="transparent")
        self.current_user = current_user
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT: MY PROFILE ---
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

        # --- RIGHT: SYSTEM ACCESS MANAGEMENT ---
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


# ================= 4. MAIN APP ROUTING =================
class MainApp(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.title("RideHub SaaS - Admin Dashboard")
        self.geometry("1450x850")
        self.configure(fg_color="#F3F4F6")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=280, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#E5E7EB")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(25, 30), padx=20, sticky="w")
        ctk.CTkLabel(logo_frame, text="🚕", font=("Arial", 28)).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" RideHub", font=("Arial", 22, "bold"), text_color="#111827").pack(side="left", padx=5)

        self.nav_buttons = {}
        nav_items = [
            ("📊 Dashboard", "Dashboard", False), 
            ("🛣️ Ride Management", "Rides", False),
            ("👤 Driver & Customer Profiles", "Profiles", True), 
            ("📈 Analytics", "Analytics", False),
            ("⚙️ Settings", "Settings", True)
        ]

        for i, (text, key, is_active) in enumerate(nav_items, start=1):
            if is_active:
                btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", text_color="#6B7280", 
                                    font=("Arial", 14, "bold"), height=45, corner_radius=8, hover_color="#F9FAFB",
                                    command=lambda k=key: self.switch_frame(k))
            else:
                btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent", text_color="#9CA3AF", 
                                    font=("Arial", 14), height=45, corner_radius=8, hover=False)
            btn.grid(row=i, column=0, sticky="ew", padx=15, pady=5)
            self.nav_buttons[key] = btn

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

        self.frames = {
            "Profiles": UserProfileFrame(self.right_area), 
            "Settings": SettingsFrame(self.right_area, self.current_user)
        }
        self.current_frame = None
        self.user_menu = None
        self.switch_frame("Profiles")

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
        self.switch_frame("Settings")
        
    def logout(self):
        self.close_user_menu()
        self.destroy()
        app = LoginWindow()
        app.mainloop()

    def switch_frame(self, frame_name):
        for key, btn in self.nav_buttons.items():
            if key in ["Profiles", "Settings"]:
                if key == frame_name:
                    btn.configure(fg_color="#EEF2FF", text_color="#4F46E5")
                else:
                    btn.configure(fg_color="transparent", text_color="#6B7280")

        if self.current_frame:
            self.current_frame.grid_forget()
        self.current_frame = self.frames[frame_name]
        self.current_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=25)


# ================= 5. USER PROFILE FRAME =================
class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.current_limit = 30
        self.max_display_limit = 100

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

            if has_more_in_db:
                if self.current_limit < self.max_display_limit:
                    ctk.CTkButton(self.scroll_list, text="Show More", fg_color="#EEF2FF", text_color="#4F46E5", hover_color="#E0E7FF", corner_radius=8, command=self.load_more).pack(pady=10, fill="x")
                else:
                    ctk.CTkButton(self.scroll_list, text="Limit Reached (100)", fg_color="#FEE2E2", text_color="#EF4444", hover_color="#FECACA", corner_radius=8, command=lambda: messagebox.showinfo("Info", "Use filters to narrow down.")).pack(pady=10, fill="x")
            
            self.display_detail(display_rows[0]['uid'], user_type)

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

        ava_lbl = ctk.CTkLabel(header_card, text="👤", font=("Arial", 60), fg_color="transparent", width=90, height=90)
        ava_lbl.place(x=20, y=30)

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

        btn_flag = ctk.CTkButton(header_card, text="Unflag" if is_flagged else "📌 Flag", 
                                 fg_color="#FFFFFF", text_color="#F59E0B" if is_flagged else bg_color, 
                                 hover_color="#F3F4F6", font=("Arial", 12, "bold"), width=110,
                                 command=lambda u=uid: self.toggle_flag(u))
        btn_flag.place(relx=0.96, rely=0.3, anchor="e")

        if user_type == "Drivers":
            btn_suspend = ctk.CTkButton(header_card, text="Unsuspend" if is_suspended else "⛔ Suspend", 
                                     fg_color="#EF4444" if not is_suspended else "#FFFFFF", 
                                     text_color="#FFFFFF" if not is_suspended else "#EF4444",
                                     hover_color="#DC2626", font=("Arial", 12, "bold"), width=110,
                                     command=lambda u=uid: self.toggle_suspend(u))
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
        
        icon_lbl = ctk.CTkLabel(card, text=icon, font=("Arial", 22), fg_color=icon_bg, text_color=icon_fg, width=46, height=46, corner_radius=12)
        icon_lbl.place(relx=0.15, rely=0.5, anchor="w")
        
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.place(relx=0.45, rely=0.5, anchor="w")
        
        ctk.CTkLabel(text_frame, text=title, font=("Arial", 12), text_color="#6B7280").pack(anchor="w")
        val_color = "#EF4444" if is_danger else "#111827"
        ctk.CTkLabel(text_frame, text=val, font=("Arial", 22, "bold"), text_color=val_color).pack(anchor="w", pady=(2, 0))


if __name__ == "__main__":
    setup_database()
    app = LoginWindow()
    app.mainloop()