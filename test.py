import sys
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Проверка зависимостей
try:
    from easyocr import Reader
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class TipCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор чаевых с OCR")
        self.root.geometry("950x800")
        self.root.configure(bg='#f0f0f0')
        
        # Включение корректного масштабирования на Windows с высоким DPI
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        
        self.image_path = None
        self.reader = None
        
        self.create_widgets()
        
        if OCR_AVAILABLE:
            self.status_var.set("🔄 Загрузка OCR (первый раз может занять 10-30 сек)...")
            threading.Thread(target=self.init_ocr, daemon=True).start()
        else:
            self.status_var.set("❌ EasyOCR не установлен. Работает только ручной ввод.")
    
    def create_widgets(self):
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg='#f0f0f0')
        top_frame.pack(pady=10, fill=tk.X)
        
        self.load_btn = tk.Button(top_frame, text="📷 1. Загрузить чек", command=self.load_image,
                                  font=('Segoe UI', 11, 'bold'), bg='#4CAF50', fg='white', 
                                  padx=20, pady=5, cursor='hand2')
        self.load_btn.pack(side=tk.LEFT, padx=10)
        
        self.status_var = tk.StringVar(value="Готов")
        status_label = tk.Label(top_frame, textvariable=self.status_var, font=('Segoe UI', 9), 
                                fg='#555', bg='#f0f0f0')
        status_label.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)
        
        # Изображение
        img_frame = tk.LabelFrame(self.root, text=" Чек ", padx=5, pady=5, font=('Segoe UI', 10, 'bold'))
        img_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.image_label = tk.Label(img_frame, text="Загрузите фото чека", bg='#fafafa', 
                                    height=12, font=('Segoe UI', 10))
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Текст
        text_frame = tk.LabelFrame(self.root, text=" 2. Распознанный текст (можно редактировать) ", 
                                   padx=5, pady=5, font=('Segoe UI', 10, 'bold'))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_area = tk.Text(text_frame, height=6, wrap=tk.WORD, font=('Consolas', 10))
        scroll = tk.Scrollbar(text_frame, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scroll.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Параметры расчёта
        params_frame = tk.LabelFrame(self.root, text=" 3. Параметры расчёта ", 
                                     padx=10, pady=10, font=('Segoe UI', 10, 'bold'))
        params_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Сумма
        row1 = tk.Frame(params_frame, bg='#f0f0f0')
        row1.pack(fill=tk.X, pady=5)
        tk.Label(row1, text="💰 Сумма счета (руб):", width=20, anchor='w', 
                font=('Segoe UI', 11), bg='#f0f0f0').pack(side=tk.LEFT)
        self.total_sum = tk.StringVar(value="")
        self.sum_entry = tk.Entry(row1, textvariable=self.total_sum, width=18, 
                                  font=('Segoe UI', 11), bg='#ffffcc', relief=tk.SUNKEN)
        self.sum_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(row1, text="🔍 Найти сумму", command=self.extract_sum_from_text,
                 font=('Segoe UI', 9), bg='#2196F3', fg='white', padx=10, cursor='hand2'
                 ).pack(side=tk.LEFT, padx=10)
        
        # Чаевые
        row2 = tk.Frame(params_frame, bg='#f0f0f0')
        row2.pack(fill=tk.X, pady=5)
        tk.Label(row2, text="🍽️ Чаевые (%):", width=20, anchor='w',
                font=('Segoe UI', 11), bg='#f0f0f0').pack(side=tk.LEFT)
        self.tip_percent = tk.StringVar(value="10")
        tk.Spinbox(row2, from_=0, to=50, textvariable=self.tip_percent, width=16,
                  font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=5)
        
        # Люди
        row3 = tk.Frame(params_frame, bg='#f0f0f0')
        row3.pack(fill=tk.X, pady=5)
        tk.Label(row3, text="👥 Количество человек:", width=20, anchor='w',
                font=('Segoe UI', 11), bg='#f0f0f0').pack(side=tk.LEFT)
        self.people_count = tk.StringVar(value="1")
        tk.Spinbox(row3, from_=1, to=20, textvariable=self.people_count, width=16,
                  font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=5)
        
        # Кнопка расчёта
        self.calc_btn = tk.Button(params_frame, text="💵 4. РАССЧИТАТЬ", command=self.calculate,
                                  font=('Segoe UI', 13, 'bold'), bg='#FF9800', fg='white', 
                                  padx=30, pady=8, cursor='hand2')
        self.calc_btn.pack(pady=10)
        
        # Результат
        result_frame = tk.LabelFrame(self.root, text=" Результат ", padx=10, pady=10, 
                                     font=('Segoe UI', 10, 'bold'))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text_widget = tk.Text(result_frame, height=8, wrap=tk.NONE,
                                          font=('Courier New', 11), bg='#e8f5e9', 
                                          relief=tk.SUNKEN, padx=10, pady=10)
        self.result_text_widget.pack(fill=tk.BOTH, expand=True)
        
        result_scroll = tk.Scrollbar(result_frame, command=self.result_text_widget.yview)
        self.result_text_widget.configure(yscrollcommand=result_scroll.set)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def init_ocr(self):
        try:
            self.reader = Reader(['ru', 'en'], gpu=False, verbose=False)
            self.status_var.set("✅ OCR готов! Можно загружать чек.")
        except Exception as e:
            self.status_var.set(f"❌ Ошибка инициализации OCR: {str(e)[:80]}")
    
    def load_image(self):
        path = filedialog.askopenfilename(
            title="Выберите фото чека",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp"), ("Все файлы", "*.*")]
        )
        if not path: return
        
        self.image_path = path
        self.display_image(path)
        
        if OCR_AVAILABLE and self.reader:
            self.status_var.set("🔍 Распознавание текста... (подождите)")
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(1.0, "Распознавание... Пожалуйста, подождите.")
            threading.Thread(target=self.run_ocr, args=(path,), daemon=True).start()
        elif OCR_AVAILABLE and self.reader is None:
            self.status_var.set("⏳ OCR ещё загружается, подождите 10 секунд")
        else:
            self.status_var.set("ℹ️ OCR недоступен. Введите сумму вручную.")
    
    def display_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
        except Exception as e:
            self.image_label.config(text=f"Ошибка загрузки: {e}")
    
    def run_ocr(self, image_path):
        try:
            # paragraph удалён в новых версиях easyocr, используется только detail
            result = self.reader.readtext(image_path, detail=0)
            text = "\n".join(result)
            self.root.after(0, self.update_text_area, text)
            self.root.after(0, lambda: self.status_var.set("✅ Текст распознан! Нажмите 'Найти сумму'"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Ошибка OCR: {str(e)[:80]}"))
    
    def update_text_area(self, text):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, text)
    
    def extract_sum_from_text(self):
        text = self.text_area.get(1.0, tk.END)
        if not text or text.strip() == "":
            self.status_var.set("Нет текста. Сначала распознайте чек или введите вручную.")
            return
        
        self.status_var.set("🔍 Поиск суммы...")
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        patterns = [
            r'ИТОГО[:\s]*(\d+[\s.,]*\d+)',
            r'ВСЕГО[:\s]*(\d+[\s.,]*\d+)',
            r'СУММА[:\s]*(\d+[\s.,]*\d+)',
            r'TOTAL[:\s]*(\d+[\s.,]*\d+)',
            r'К ОПЛАТЕ[:\s]*(\d+[\s.,]*\d+)',
            r'(\d+[\s.,]?\d*)\s*руб',
            r'(\d+[\s.,]?\d*)\s*₽',
            r'\b(\d{1,3}(?:[\s]?\d{3})*[,.]\d{2})\b',
        ]
        
        found_sums = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                num_str = str(match).strip().replace(',', '.')
                if num_str.count('.') > 1:
                    parts = num_str.split('.')
                    num_str = parts[0] + '.' + parts[1]
                try:
                    value = float(num_str)
                    if 10 <= value <= 1000000:
                        found_sums.append(value)
                except:
                    continue
        
        found_sums = sorted(set(found_sums), reverse=True)
        
        if found_sums:
            best_sum = found_sums[0]
            self.total_sum.set(f"{best_sum:.2f}")
            self.status_var.set(f"✅ Найдена сумма: {best_sum:.2f} руб")
        else:
            self.status_var.set("❌ Сумма не найдена. Введите вручную.")
    
    def calculate(self):
        try:
            sum_str = self.total_sum.get().strip().replace(',', '.')
            if not sum_str:
                messagebox.showwarning("Ошибка", "Введите сумму счета")
                return
            
            total = float(sum_str)
            tip = float(self.tip_percent.get())
            people = int(self.people_count.get())
            
            if total <= 0:
                messagebox.showwarning("Ошибка", "Сумма должна быть больше 0")
                return
            if people <= 0:
                messagebox.showwarning("Ошибка", "Количество человек должно быть больше 0")
                return
            
            tip_amount = total * tip / 100
            total_with_tip = total + tip_amount
            per_person = total_with_tip / people
            
            result = f"""
{'='*55}
                    РЕЗУЛЬТАТ РАСЧЁТА
{'='*55}

  💰 Сумма счета:              {total:>10.2f}  руб
  🍽️ Чаевые ({tip}%):                {tip_amount:>10.2f}  руб
  💵 Всего к оплате:           {total_with_tip:>10.2f}  руб

{'='*55}
  👥 На {people} человек:            {per_person:>10.2f}  руб/чел
{'='*55}
"""
            self.result_text_widget.delete(1.0, tk.END)
            self.result_text_widget.insert(1.0, result)
            self.status_var.set("✅ Расчёт выполнен!")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность введённых чисел")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TipCalculatorApp(root)
    root.mainloop()
