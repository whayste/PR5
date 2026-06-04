from database import init_db
from windows.login_window import LoginWindow
from windows.main_window import MainWindow


def on_login_success(user):
    app = MainWindow(user)
    app.mainloop()


if __name__ == "__main__":
    init_db()
    LoginWindow(on_login_success).mainloop()