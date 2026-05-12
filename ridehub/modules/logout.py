def perform_logout(app):
    """Destroy the current app and return to the login screen."""
    app.destroy()
    from modules.login import LoginWindow
    from main import launch_app
    login = LoginWindow(on_login_success=launch_app)
    login.mainloop()
