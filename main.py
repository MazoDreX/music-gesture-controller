import ttkbootstrap as ttk
from camera_selector_gui import CameraSelectorApp

if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = CameraSelectorApp(root)
    root.mainloop()