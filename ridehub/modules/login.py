"""
Login Window: authenticates admin users before granting access to the main app.
Uses a callback pattern — on success, calls on_login_success(user).
"""
from tkinter import messagebox

import customtkinter as ctk

from data.uber import get_db_connection


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success=None):
        """
        on_login_success: callable(user_dict) — called after successful login.
                          The callback receives the user row (dict) from admin_users.
        """
        super().__init__()
        self.on_login_success = on_login_success
        self.title("RideHub - Login")
        self.configure(fg_color="#F3F4F6")
        self.geometry(self._center_window(450, 550))

        card = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=16,
                            border_width=1, border_color="#E5E7EB")
        card.pack(expand=True, padx=40, pady=40, fill="both")

        ctk.CTkLabel(card, text="🚕", font=("Arial", 40)).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="Welcome to RideHub",
                     font=("Arial", 22, "bold"), text_color="#111827").pack()
        ctk.CTkLabel(card, text="Please sign in to your account",
                     font=("Arial", 13), text_color="#6B7280").pack(pady=(0, 20))

        self.txt_user = ctk.CTkEntry(card, placeholder_text="Username", height=45,
                                     corner_radius=8, fg_color="#F9FAFB",
                                     border_color="#D1D5DB", text_color="#111827")
        self.txt_user.pack(fill="x", padx=30, pady=10)

        self.txt_pwd = ctk.CTkEntry(card, placeholder_text="Password", height=45,
                                    corner_radius=8, fg_color="#F9FAFB",
                                    border_color="#D1D5DB", text_color="#111827",
                                    show="*")
        self.txt_pwd.pack(fill="x", padx=30, pady=10)

        btn_login = ctk.CTkButton(card, text="Sign In", font=("Arial", 14, "bold"),
                                  height=45, corner_radius=8, fg_color="#4F46E5",
                                  hover_color="#4338CA", command=self.check_login)
        btn_login.pack(fill="x", padx=30, pady=(20, 10))

        self.bind('<Return>', lambda e: self.check_login())

    @staticmethod
    def _center_window(w, h):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            root.destroy()
        except Exception:
            screen_w, screen_h = 1920, 1080
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        return f"{w}x{h}+{x}+{y}"

    def check_login(self):
        u, p = self.txt_user.get(), self.txt_pwd.get()
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "Database connection failed!")
            return
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM admin_users WHERE username=%s AND password=%s", (u, p))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.destroy()
            if self.on_login_success:
                self.on_login_success(user)
        else:
            messagebox.showerror("Error", "Invalid username or password!")
