import tkinter as tk
from tkinter import font as tkfont

class GreetingWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Приветствие")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Настройка цветов и шрифтов
        self.bg_color = "#2c3e50"
        self.fg_color = "#ecf0f1"
        self.btn_color = "#e74c3c"
        self.btn_hover_color = "#c0392b"
        
        self.root.configure(bg=self.bg_color)
        
        # Заголовок
        title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        label_font = tkfont.Font(family="Helvetica", size=14)
        btn_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        
        title_label = tk.Label(
            root, 
            text="Добро пожаловать!", 
            font=title_font, 
            bg=self.bg_color, 
            fg=self.fg_color
        )
        title_label.pack(pady=(60, 10))
        
        message_label = tk.Label(
            root, 
            text="Это красивое окно приветствия\nна Python с использованием Tkinter.", 
            font=label_font, 
            bg=self.bg_color, 
            fg=self.fg_color,
            justify="center"
        )
        message_label.pack(pady=10)
        
        # Кнопка закрытия
        self.close_button = tk.Button(
            root,
            text="Закрыть",
            font=btn_font,
            bg=self.btn_color,
            fg="white",
            border=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.close_window
        )
        self.close_button.pack(pady=30)
        
        # Эффекты при наведении
        self.close_button.bind("<Enter>", self.on_enter)
        self.close_button.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        self.close_button.configure(bg=self.btn_hover_color)
    
    def on_leave(self, event):
        self.close_button.configure(bg=self.btn_color)
    
    def close_window(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GreetingWindow(root)
    root.mainloop()
