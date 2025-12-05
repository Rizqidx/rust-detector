# --- Import Library yang Dibutuhkan ---
import tkinter as tk  # Library utama untuk membuat GUI
from tkinter import ttk, filedialog, font, messagebox  # ttk untuk widget modern, filedialog untuk dialog file, font untuk mengatur font
from PIL import Image, ImageTk  # Pillow (PIL) untuk memanipulasi dan menampilkan gambar
import random  # Untuk menghasilkan data simulasi secara acak
import cv2  # OpenCV untuk memproses video dan feed kamera
import os  # Untuk berinteraksi dengan sistem operasi (misalnya, membuat direktori)
import sys 
import shutil  # Untuk operasi file tingkat tinggi (misalnya, menyalin file)
import threading  # Untuk menjalankan proses (seperti video) secara paralel agar UI tidak macet
import time  # Untuk memberikan jeda singkat dalam loop thread
import openpyxl  # Untuk membaca dan menulis file Excel (.xlsx)
from ultralytics import YOLO  # Yolo dari ultralytics
import numpy as np

def resource_path(relative_path):
    """ Mengambil path absolut ke sumber daya, berfungsi untuk dev dan PyInstaller """
    try:
        # PyInstaller membuat folder temp dan menyimpan path di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # os.path.dirname(__file__) akan selalu mendapatkan direktori skrip,
        # di mana pun Anda menjalankan perintahnya.
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)



# --- Kelas Utama Aplikasi ---
class GUIDetectorApp:
    """
    Kelas utama untuk aplikasi GUI Detector.
    Mengelola semua elemen UI, fungsionalitas, dan state aplikasi.
    """
    # --- Palet Warna dan Font (Konfigurasi Desain) ---
    COLOR_BACKGROUND = "#1E1E1E"
    COLOR_FRAME = "#2D2D2D"
    COLOR_TEXT = "#F0F0F0"
    COLOR_ACCENT = "#4A90E2"
    COLOR_ACCENT_DARK = "#357ABD"
    COLOR_SUCCESS = "#1EAE8F"
    COLOR_DANGER = "#E35050"
    COLOR_DISABLED_TEXT = "#888888"
    FONT_BOLD = ("Segoe UI", 12, "bold")
    FONT_NORMAL = ("Segoe UI", 11)
    FONT_SMALL = ("Segoe UI", 9)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    MODEL_DIR = os.path.join(base_dir, "models")  # Nama direktori untuk menyimpan model YOLO

    # --- Metode Inisialisasi (`__init__`) ---
    def __init__(self, root):
        """
        Fungsinya untuk menginisialisasi jendela utama dan semua state awal.
        """
        self.root = root  # Menyimpan referensi ke jendela utama
        self.root.title("GUI YOLO Detector")

        # self.root.iconbitmap(resource_path("deep-learning.ico"))

        self.root.after_idle(lambda: self.root.iconbitmap(resource_path(r"assets\deep-learning.ico")))

        self.root.geometry("1200x800")  # Mengatur ukuran awal jendela
        self.root.minsize(1000, 700)  # Mengatur ukuran minimum jendela
        self.root.configure(bg=self.COLOR_BACKGROUND)  # Mengatur warna latar belakang utama

        # --- Variabel Statis ---
        self.video_capture = None       # menyimpan objek video dari OpenCV
        self.image_tk = None            # menyimpan gambar yang siap ditampilkan di Tkinter
        self.is_predicting = False      # Status apakah prediksi sedang berjalan (True/False)
        self.current_media_type = None  # Menyimpan tipe media saat ini ('image', 'video', 'camera')
        self.original_pil_image = None  # menyimpan gambar asli
        self.model = None               # menyimpan objek model YOLO
        
        # --- Variabel untuk Logging ---
        # List ini akan menyimpan semua riwayat aktivitas aplikasi.
        self.log_messages = []
        
        # --- Variabel untuk Threading ---
        self.video_thread = None  # Akan menyimpan objek thread video
        self.stop_thread = threading.Event()  # Objek untuk memberi sinyal kapan thread harus berhenti

        # --- Setup Awal ---
        self._setup_model_directory()  # Memastikan direktori model ada
        self._configure_styles()  # Mengatur gaya visual untuk widget ttk

        # --- Konfigurasi Grid Layout Utama ---
        self.root.columnconfigure(0, weight=0, minsize=280)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0, minsize=320)
        self.root.rowconfigure(0, weight=1)

        # --- Membuat Panel-Panel Utama ---
        self._create_left_panel()
        self._create_center_panel()
        self._create_right_panel()
        
        # --- Inisialisasi Akhir ---
        self._load_existing_models()  # Memuat model yang sudah tersimpan
        self._reset_ui_state()  # Mengatur state awal tombol-tombol

        # Menangani event penutupan jendela untuk cleanup yang aman
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Menambahkan log pertama saat aplikasi dimulai ---
        self._add_log("Aplikasi berhasil dimulai.")

    def _setup_model_directory(self):
        """Memeriksa dan membuat direktori 'models' jika belum ada"""
        if not os.path.exists(self.MODEL_DIR):
            os.makedirs(self.MODEL_DIR)

    def _configure_styles(self):
        """Mengkonfigurasi style ttk untuk semua widget agar memiliki tampilan modern"""
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TFrame', background=self.COLOR_FRAME)
        style.configure('TLabel', background=self.COLOR_FRAME, foreground=self.COLOR_TEXT, font=self.FONT_NORMAL)
        style.configure('Header.TLabel', font=self.FONT_BOLD, foreground=self.COLOR_TEXT)
        style.configure('TButton', font=self.FONT_BOLD, padding=12, borderwidth=0, relief="flat", foreground=self.COLOR_TEXT)
        style.map('TButton', background=[('!active', self.COLOR_FRAME), ('active', self.COLOR_ACCENT_DARK)], foreground=[('disabled', self.COLOR_DISABLED_TEXT)])
        style.configure('Accent.TButton', background=self.COLOR_ACCENT, foreground=self.COLOR_TEXT)
        style.map('Accent.TButton', background=[('active', self.COLOR_ACCENT_DARK)], foreground=[('disabled', self.COLOR_DISABLED_TEXT)])
        style.configure('Success.TButton', background=self.COLOR_SUCCESS, foreground=self.COLOR_TEXT)
        style.map('Success.TButton', background=[('active', '#3dbba1')], foreground=[('disabled', self.COLOR_DISABLED_TEXT)])
        style.configure('Danger.TButton', background=self.COLOR_DANGER, foreground=self.COLOR_TEXT)
        style.map('Danger.TButton', background=[('active', '#c94242')], foreground=[('disabled', self.COLOR_DISABLED_TEXT)])
        self.root.option_add('*TCombobox*Listbox.background', self.COLOR_FRAME)
        self.root.option_add('*TCombobox*Listbox.foreground', self.COLOR_TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.COLOR_ACCENT)
        style.configure('TCombobox', font=self.FONT_NORMAL, padding=8)
        style.map('TCombobox',
                  fieldbackground=[('readonly', self.COLOR_FRAME)],
                  selectbackground=[('readonly', self.COLOR_FRAME)],
                  selectforeground=[('readonly', self.COLOR_TEXT)],
                  foreground=[('readonly', self.COLOR_TEXT)])
        style.configure("Treeview", background=self.COLOR_FRAME, foreground=self.COLOR_TEXT, 
                        fieldbackground=self.COLOR_FRAME, rowheight=30, font=self.FONT_NORMAL)
        style.configure("Treeview.Heading", background=self.COLOR_FRAME, font=self.FONT_BOLD, 
                        foreground=self.COLOR_ACCENT, borderwidth=0, padding=5)
        style.map("Treeview", background=[('selected', self.COLOR_ACCENT_DARK)])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def _create_left_panel(self):
        """Membuat dan menata semua widget di panel kontrol sebelah kiri."""
        left_frame = ttk.Frame(self.root, padding="20 25")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        ttk.Label(left_frame, text="KONTROL PREDIKSI", style='Header.TLabel').pack(pady=(0, 15), anchor="w")
        self.start_predict_button = ttk.Button(left_frame, text="▶  Start Predict", command=self._start_prediction, style='Success.TButton')
        self.start_predict_button.pack(fill="x", pady=5, ipady=5)
        self.stop_predict_button = ttk.Button(left_frame, text="■  Stop Predict", command=self._stop_prediction, style='Danger.TButton')
        self.stop_predict_button.pack(fill="x", pady=5, ipady=5)

        ttk.Label(left_frame, text="SUMBER MEDIA", style='Header.TLabel').pack(pady=(30, 15), anchor="w")
        ttk.Button(left_frame, text="🎬  Unggah Gambar", command=self._select_image).pack(fill="x", pady=5)
        ttk.Button(left_frame, text="📹  Unggah Video", command=self._select_video).pack(fill="x", pady=5)
        self.camera_button = ttk.Button(left_frame, text="📷  Buka Kamera", command=self._open_camera)
        self.camera_button.pack(fill="x", pady=5)
        self.close_camera_button = ttk.Button(left_frame, text="📷  Tutup Kamera", command=self._close_camera)
        self.close_camera_button.pack(fill="x", pady=5)
        ttk.Button(left_frame, text="❌  Clear Media", command=self._clear_media).pack(fill="x", pady=(15,5))

        ttk.Label(left_frame, text="MODEL ANALISIS", style='Header.TLabel').pack(pady=(30, 15), anchor="w")
        self.model_combobox = ttk.Combobox(left_frame, state="readonly")
        self.model_combobox.pack(fill="x", pady=5)

        # --- Frame untuk menampung tombol Unggah dan Pengaturan Model ---
        model_button_frame = ttk.Frame(left_frame)
        model_button_frame.pack(fill="x", pady=5)
        model_button_frame.columnconfigure(0, weight=1)  # Kolom untuk tombol unggah agar bisa melebar
        model_button_frame.columnconfigure(1, weight=0)  # Kolom untuk tombol settings

        # Tombol Unggah Model
        upload_button = ttk.Button(model_button_frame, text="↑  Unggah Model...", command=self._upload_model, style='Accent.TButton')
        upload_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # --- Tombol Pengaturan Model ---
        # Tombol ini akan membuka jendela baru untuk mengelola (menghapus) model.
        settings_button = ttk.Button(model_button_frame, text="⚙️", command=self._open_manage_models_window, width=3)
        settings_button.grid(row=0, column=1, sticky="e")

    def _create_center_panel(self):
        """Membuat panel tengah untuk menampilkan gambar atau video."""
        center_frame = ttk.Frame(self.root, padding=0)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        center_frame.rowconfigure(0, weight=1)
        center_frame.columnconfigure(0, weight=1)
        
        self.frame_sketch = tk.Canvas(center_frame, bg=self.COLOR_BACKGROUND, highlightthickness=0)
        self.frame_sketch.grid(row=0, column=0, sticky="nsew")
        
        self.frame_sketch_text = self.frame_sketch.create_text(
            10, 10, text="Pilih sumber media untuk memulai analisis", 
            font=("Segoe UI", 16, "italic"), fill="#555")
        self.frame_sketch.bind("<Configure>", self._center_frame_sketch_content)

    def _create_right_panel(self):
        """Membuat panel kanan untuk menampilkan hasil deteksi dan tombol tambahan."""
        right_frame = ttk.Frame(self.root, padding=(20, 25, 15, 25))
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.grid_propagate(False)

        ttk.Label(right_frame, text="HASIL DETEKSI OBJEK", style='Header.TLabel').grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        cols = ('objek', 'jumlah')
        self.results_table = ttk.Treeview(right_frame, columns=cols, show='headings', selectmode='none')
        self.results_table.heading('objek', text='Objek Terdeteksi', anchor='w')
        self.results_table.heading('jumlah', text='Jumlah', anchor='center')
        self.results_table.column('objek', anchor='w')
        self.results_table.column('jumlah', width=80, anchor='center')
        self.results_table.grid(row=1, column=0, sticky="nsew")

        ttk.Button(right_frame, text="Simpan Hasil", command=self._save_results).grid(row=2, column=0, sticky="ew", pady=(20, 10), ipady=5)

        # --- Frame untuk tombol bawah (About & Log) ---
        bottom_button_frame = ttk.Frame(right_frame)
        bottom_button_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        bottom_button_frame.columnconfigure(0, weight=1) # Kolom untuk tombol About
        bottom_button_frame.columnconfigure(1, weight=1) # Kolom untuk tombol Log

        # Tombol About, membuka jendela informasi aplikasi
        about_button = ttk.Button(bottom_button_frame, text="About", command=self._open_about_window)
        about_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Tombol Log, membuka jendela riwayat aktivitas
        log_button = ttk.Button(bottom_button_frame, text="Log", command=self._open_log_window)
        log_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _center_frame_sketch_content(self, event=None):
        """Menengahkan konten (teks atau gambar) di dalam frame_sketch."""
        frame_sketch_width = self.frame_sketch.winfo_width()
        frame_sketch_height = self.frame_sketch.winfo_height()
        if self.image_tk:
            self.frame_sketch.coords("image", frame_sketch_width / 2, frame_sketch_height / 2)
        else:
            self.frame_sketch.coords(self.frame_sketch_text, frame_sketch_width / 2, frame_sketch_height / 2)

    def _stop_current_feed(self):
        """Memberi sinyal thread untuk berhenti dan melepaskan sumber video."""
        self.stop_thread.set()
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=0.5)
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        self.is_camera_on = False

    def _reset_ui_state(self):
        """Mengatur ulang state semua tombol dan tabel ke kondisi awal."""
        self.is_predicting = False
        self.start_predict_button.config(state="disabled" if not self.current_media_type else "normal")
        self.stop_predict_button.config(state="disabled")
        self.camera_button.config(state="normal")
        self.close_camera_button.config(state="disabled")
        for i in self.results_table.get_children():
            self.results_table.delete(i)

    def _clear_media(self):
        """Membersihkan media (gambar/video) tanpa memengaruhi kamera."""
        if self.current_media_type in ['image', 'video']:
            self._add_log(f"Media '{self.current_media_type}' dibersihkan.")
            self._stop_current_feed()
            self.current_media_type = None
            self.frame_sketch.delete("all")
            self.image_tk = None
            self.frame_sketch_text = self.frame_sketch.create_text(
                self.frame_sketch.winfo_width()/2, self.frame_sketch.winfo_height()/2, 
                text="Pilih sumber media untuk memulai analisis", 
                font=("Segoe UI", 16, "italic"), fill="#555")
            self._reset_ui_state()

    def _select_image(self):
        """Membuka dialog untuk memilih gambar dan menampilkannya."""
        file_path = filedialog.askopenfilename(filetypes=[("File Gambar", "*.jpg *.jpeg *.png")])
        if not file_path:
            self._add_log("Pemilihan gambar dibatalkan.")
            return
        self._add_log(f"Gambar dipilih: {os.path.basename(file_path)}")
        self._stop_current_feed()
        self.current_media_type = 'image'
        self.start_predict_button.config(text="▶  Start Predict")
        self._reset_ui_state()
        img = Image.open(file_path)
        self.original_pil_image = img.copy()
        self._display_image(img)

    def _start_video_stream(self, source):
        """Memulai stream video (dari file atau kamera) di thread terpisah."""
        self._stop_current_feed()
        self.video_capture = cv2.VideoCapture(source)
        if not self.video_capture.isOpened():
            print(f"Error: Tidak dapat membuka sumber video: {source}")
            self._close_camera()
            return
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.frame_delay_sec = 1 / fps if fps > 0 else 1 / 30
        self.stop_thread.clear()
        self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
        self.video_thread.start()

    def _select_video(self):
        """Membuka dialog untuk memilih video."""
        file_path = filedialog.askopenfilename(filetypes=[("File Video", "*.mp4 *.avi *.mov")])
        if not file_path:
            self._add_log("Pemilihan video dibatalkan.")
            return
        self._add_log(f"Video dipilih: {os.path.basename(file_path)}")
        self.current_media_type = 'video'
        self.start_predict_button.config(text="▶  Start Continue Predict")
        self._reset_ui_state()
        self._start_video_stream(file_path)

    def _open_camera(self):
        """Fungsi khusus untuk membuka kamera."""
        self._add_log("Kamera dibuka.")
        self.is_camera_on = True
        self.camera_button.config(state="disabled")
        self.close_camera_button.config(state="normal")
        self.current_media_type = 'camera'
        self.start_predict_button.config(text="▶  Start Continue Predict")
        self._reset_ui_state()
        self.camera_button.config(state="disabled")
        self.close_camera_button.config(state="normal")
        self._start_video_stream(0)

    def _close_camera(self):
        """Fungsi khusus untuk menutup kamera dan membersihkan frame_sketch."""
        self._add_log("Kamera ditutup.")
        self._stop_current_feed()
        self.current_media_type = None
        self.frame_sketch.delete("all")
        self.image_tk = None
        self.frame_sketch_text = self.frame_sketch.create_text(
            self.frame_sketch.winfo_width()/2, self.frame_sketch.winfo_height()/2, 
            text="Pilih sumber media untuk memulai analisis", 
            font=("Segoe UI", 16, "italic"), fill="#555")
        self._reset_ui_state()

    def _video_loop(self):
        """Loop yang berjalan di thread terpisah untuk terus memproses frame video."""
        while not self.stop_thread.is_set():
            if self.video_capture and self.video_capture.isOpened():
                ret, frame = self.video_capture.read()
                if ret:
                    display_frame = frame
                    if self.is_predicting and self.model:
                        results = self.model(frame, verbose=False)[0]
                        display_frame = results.plot()
                        object_counts = {}
                        for box in results.boxes:
                            class_name = self.model.names[int(box.cls[0])]
                            object_counts[class_name] = object_counts.get(class_name, 0) + 1
                        self.root.after(0, self._update_results_table, object_counts)
                    frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    self.root.after(0, self._display_image, img)
                else:
                    self.root.after(0, self._close_camera if self.is_camera_on else self._clear_media)
                    break
            time.sleep(self.frame_delay_sec)

    def _load_yolo_model(self):
        """Memuat model YOLO yang dipilih dari combobox."""
        selected_model_file = self.model_combobox.get()
        if "Default" in selected_model_file or "Error" in selected_model_file or not selected_model_file or "Belum Ditemukan" in selected_model_file:
            messagebox.showwarning("Model Belum Dipilih", "Silakan pilih model analisis yang valid dari daftar.")
            return False
        model_path = os.path.join(self.MODEL_DIR, selected_model_file)
        if not os.path.exists(model_path):
            messagebox.showerror("File Tidak Ditemukan", f"File model tidak ditemukan di:\n{model_path}")
            return False
        try:
            self._add_log(f"Memuat model: {selected_model_file}...")
            self.root.config(cursor="watch")
            self.root.update()
            self.model = YOLO(model_path)
            self._add_log("Model berhasil dimuat.")
            return True
        except Exception as e:
            self._add_log(f"Gagal memuat model: {e}")
            messagebox.showerror("Gagal Memuat Model", f"Terjadi kesalahan saat memuat model:\n{e}")
            self.model = None
            return False
        finally:
            self.root.config(cursor="")
            self.root.update()

    def _run_yolo_on_image(self):
        """Menjalankan deteksi pada gambar statis dan menampilkan hasilnya."""
        if not self.model or not self.original_pil_image:
            self._stop_prediction()
            return
        results = self.model(self.original_pil_image, verbose=False)[0]
        processed_image_bgr = results.plot()
        object_counts = {}
        for box in results.boxes:
            class_name = self.model.names[int(box.cls[0])]
            object_counts[class_name] = object_counts.get(class_name, 0) + 1
        self._update_results_table(object_counts)
        processed_image_rgb = cv2.cvtColor(processed_image_bgr, cv2.COLOR_BGR2RGB)
        final_image = Image.fromarray(processed_image_rgb)
        self._display_image(final_image)
        self.root.after(100, self._stop_prediction)
    
    def _start_prediction(self):
        """Memulai proses prediksi menggunakan model YOLO."""
        if not self.current_media_type: return
        self._add_log(f"Memulai prediksi untuk '{self.current_media_type}'.")
        if not self._load_yolo_model():
            self._add_log("Prediksi dibatalkan karena model gagal dimuat.")
            return
        self.is_predicting = True
        self.start_predict_button.config(state="disabled")
        self.stop_predict_button.config(state="normal")
        if self.current_media_type == 'image':
            self._run_yolo_on_image()

    def _stop_prediction(self):
        """Menghentikan proses prediksi."""
        if self.is_predicting:
            self._add_log("Prediksi dihentikan.")
        self.is_predicting = False
        self.start_predict_button.config(state="normal")
        self.stop_predict_button.config(state="disabled")

    def _display_image(self, img):
        """Mengubah ukuran gambar dan menampilkannya di frame_sketch."""
        if not self.current_media_type: return
        frame_sketch_width = self.frame_sketch.winfo_width()
        frame_sketch_height = self.frame_sketch.winfo_height()
        if frame_sketch_width <= 1 or frame_sketch_height <= 1: return
        img_ratio = img.width / img.height
        frame_sketch_ratio = frame_sketch_width / frame_sketch_height
        if frame_sketch_ratio > img_ratio:
            new_height = frame_sketch_height
            new_width = int(new_height * img_ratio)
        else:
            new_width = frame_sketch_width
            new_height = int(new_width / img_ratio)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(resized_img)
        self.frame_sketch.delete("all")
        self.frame_sketch.create_image(frame_sketch_width / 2, frame_sketch_height / 2, image=self.image_tk, anchor="center", tags="image")

    def _load_existing_models(self):
        """Memuat daftar model dari direktori 'models'."""
        try:
            model_files = [f for f in os.listdir(self.MODEL_DIR) if f.endswith(('.pt', '.weights'))]
            if not model_files:
                self.model_combobox['values'] = ["Model Belum Ditemukan"]
                self.model_combobox.set("Model Belum Ditemukan")
            else:
                self.model_combobox['values'] = sorted(model_files)
                self.model_combobox.current(0)
        except Exception as e:
            self.model_combobox['values'] = ["Error Memuat Model"]
            self.model_combobox.set("Error Memuat Model")

    def _upload_model(self):
        """Mengunggah file model baru ke direktori 'models'."""
        file_path = filedialog.askopenfilename(title="Pilih File Model YOLO", filetypes=[("Model YOLO", "*.pt *.weights"), ("Semua File", "*.*")])
        if not file_path:
            self._add_log("Pemilihan file model untuk diunggah dibatalkan.")
            return
        try:
            filename = os.path.basename(file_path)
            destination_path = os.path.join(self.MODEL_DIR, filename)
            if os.path.exists(destination_path):
                 if not messagebox.askyesno("Konfirmasi Timpa", f"Model dengan nama '{filename}' sudah ada. Apakah Anda ingin menimpanya?"):
                     self._add_log(f"Penimpaan model '{filename}' dibatalkan.")
                     return
            shutil.copy(file_path, destination_path)
            self._add_log(f"Model '{filename}' berhasil diunggah.")
            self._load_existing_models()
        except Exception as e:
            self._add_log(f"Gagal mengunggah model: {e}")
            messagebox.showerror("Gagal Unggah", f"Gagal mengunggah model: {e}")
    
    def _center_window(self, window):
        """Memusatkan jendela (Toplevel) di tengah layar tanpa glitch sekilas."""
        window.withdraw()  # Sembunyikan dulu agar tidak muncul sekilas di pojok
        window.update_idletasks()

        w = window.winfo_width()
        h = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (w // 2)
        y = (window.winfo_screenheight() // 2) - (h // 2)
        window.geometry(f"{w}x{h}+{x}+{y}")

        window.deiconify()  # Tampilkan kembali setelah posisi benar

    # --- Fungsi-fungsi untuk Manajemen Model ---
    def _open_manage_models_window(self):
        """Membuka jendela baru untuk mengelola (menghapus) model."""
        self._add_log("Jendela 'Kelola Model' dibuka.")
        self.manage_window = tk.Toplevel(self.root)
        self.manage_window.title("Kelola Model")
        self.manage_window.geometry("400x450")
        self.manage_window.minsize(350, 400)
        self.manage_window.configure(bg=self.COLOR_BACKGROUND)
        self.manage_window.transient(self.root)
        self.manage_window.grab_set()

        self._center_window(self.manage_window)

        self.manage_window.after_idle(lambda: self.manage_window.iconbitmap(resource_path("deep-learning.ico")))

        main_frame = ttk.Frame(self.manage_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        ttk.Label(main_frame, text="DAFTAR MODEL TERSEDIA", style='Header.TLabel').grid(row=0, column=0, sticky="w", pady=(0, 15))
        self.models_list_treeview = ttk.Treeview(main_frame, columns=('model',), show='headings', selectmode='browse')
        self.models_list_treeview.heading('model', text='Nama File Model', anchor='w')
        self.models_list_treeview.column('model', anchor='w')
        self.models_list_treeview.grid(row=1, column=0, sticky="nsew")
        delete_button = ttk.Button(main_frame, text="Hapus Model Terpilih", command=self._delete_selected_model, style='Danger.TButton')
        delete_button.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        self._populate_models_list()

    def _populate_models_list(self):
        """Mengisi Treeview di jendela kelola model dengan daftar file model."""
        for item in self.models_list_treeview.get_children():
            self.models_list_treeview.delete(item)
        try:
            model_files = [f for f in os.listdir(self.MODEL_DIR) if f.endswith(('.pt', '.weights'))]
            if model_files:
                for model_file in sorted(model_files):
                    self.models_list_treeview.insert('', 'end', values=(model_file,))
            else:
                self.models_list_treeview.insert('', 'end', values=("(Tidak ada model di direktori)",), tags=('disabled_item',))
                self.models_list_treeview.tag_configure('disabled_item', foreground=self.COLOR_DISABLED_TEXT)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca direktori model: {e}", parent=self.manage_window)

    def _delete_selected_model(self):
        """Menghapus model yang dipilih dari Treeview dan dari disk."""
        selected_item = self.models_list_treeview.focus()
        if not selected_item:
            messagebox.showwarning("Tidak Ada Pilihan", "Silakan pilih model yang ingin dihapus.", parent=self.manage_window)
            return
        item_values = self.models_list_treeview.item(selected_item)['values']
        if not item_values or "(Tidak ada model" in item_values[0]:
             messagebox.showwarning("Pilihan Tidak Valid", "Item ini tidak dapat dihapus.", parent=self.manage_window)
             return
        selected_model_filename = item_values[0]
        if messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus model '{selected_model_filename}' secara permanen?", parent=self.manage_window, icon='warning'):
            try:
                model_path = os.path.join(self.MODEL_DIR, selected_model_filename)
                os.remove(model_path)
                self._add_log(f"Model '{selected_model_filename}' berhasil dihapus.")
                self._populate_models_list()
                self._load_existing_models()
                messagebox.showinfo("Berhasil", f"Model '{selected_model_filename}' telah dihapus.", parent=self.manage_window)
            except Exception as e:
                self._add_log(f"Gagal menghapus model: {e}")
                messagebox.showerror("Error", f"Terjadi kesalahan saat menghapus model: {e}", parent=self.manage_window)

    def _update_results_table(self, object_counts):
        """Memperbarui tabel hasil dengan data deteksi baru."""
        for i in self.results_table.get_children():
            self.results_table.delete(i)
        for obj, count in sorted(object_counts.items()):
            self.results_table.insert('', 'end', values=(obj, count))

    def _run_analysis_simulation(self):
        """Menjalankan simulasi deteksi dan memperbarui tabel hasil."""
        possible_objects = ["Karat Parah", "Karat Sedang", "Karat Ringan", "Baut Berkarat", "Pipa Korosi"]
        detected_objects = random.choices(possible_objects, k=random.randint(1, 10))
        object_counts = {}
        for obj in detected_objects:
            object_counts[obj] = object_counts.get(obj, 0) + 1
        self._update_results_table(object_counts)

    # --- Fungsi-fungsi untuk Jendela Log dan About ---
    def _add_log(self, message):
        """Menambahkan pesan ke log history dengan timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        # Jika jendela log sudah terbuka, langsung perbarui isinya
        if hasattr(self, 'log_window') and self.log_window.winfo_exists():
            self._populate_log_viewer()

    def _open_about_window(self):
        """Membuka jendela 'About' yang berisi informasi aplikasi."""
        self._add_log("Jendela 'About' dibuka.")
        about_window = tk.Toplevel(self.root)
        about_window.title("About GUI Detector")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        about_window.configure(bg=self.COLOR_BACKGROUND)
        about_window.transient(self.root)
        about_window.grab_set()

        self._center_window(about_window)

        about_window.after_idle(lambda: about_window.iconbitmap(resource_path("deep-learning.ico")))

        about_frame = ttk.Frame(about_window, padding=25)
        about_frame.pack(expand=True, fill="both")
        ttk.Label(about_frame, text="GUI Detector", font=("Segoe UI", 16, "bold"), foreground=self.COLOR_ACCENT).pack(pady=(0, 10))
        ttk.Label(about_frame, text="Versi 1.0", font=self.FONT_NORMAL).pack(pady=2)
        ttk.Label(about_frame, text="Aplikasi untuk deteksi objek menggunakan YOLO ", font=self.FONT_SMALL).pack(pady=(0, 20))
        ttk.Label(about_frame, text="Pembuat Oleh YONO", font=self.FONT_SMALL, foreground=self.COLOR_DISABLED_TEXT).pack(pady=10)
        ttk.Label(about_frame, text="Dibuat Menggunakan Python, Tkinter, dan OpenCV.", font=self.FONT_SMALL, foreground=self.COLOR_DISABLED_TEXT).pack(pady=5)
        close_button = ttk.Button(about_frame, text="Tutup", command=about_window.destroy, style="Accent.TButton")
        close_button.pack(pady=(20, 0))

    def _open_log_window(self):
        """Membuka jendela baru untuk menampilkan log aktivitas."""
        # Jika jendela belum ada atau sudah ditutup, buat yang baru
        if not hasattr(self, 'log_window') or not self.log_window.winfo_exists():
            self._add_log("Jendela 'Log' dibuka.")
            self.log_window = tk.Toplevel(self.root)
            self.log_window.title("Log Aktivitas")
            self.log_window.geometry("700x500")
            self.log_window.configure(bg=self.COLOR_BACKGROUND)
            self.log_window.transient(self.root)

            self._center_window(self.log_window)

            self.log_window.after_idle(lambda: self.log_window.iconbitmap(resource_path("deep-learning.ico")))

            log_frame = ttk.Frame(self.log_window, padding=15)
            log_frame.pack(fill="both", expand=True)
            log_frame.rowconfigure(0, weight=1)
            log_frame.columnconfigure(0, weight=1)
            self.log_text_widget = tk.Text(log_frame, bg=self.COLOR_BACKGROUND, fg=self.COLOR_TEXT, 
                                           font=("Consolas", 10), wrap="word", borderwidth=0,
                                           highlightthickness=1, highlightbackground=self.COLOR_FRAME)
            self.log_text_widget.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(log_frame, command=self.log_text_widget.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.log_text_widget['yscrollcommand'] = scrollbar.set
            button_frame = ttk.Frame(log_frame)
            button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            clear_button = ttk.Button(button_frame, text="Bersihkan Log", command=self._clear_log_history, style="Danger.TButton")
            clear_button.pack(side="left")
        
        self.log_window.lift() # Selalu bawa jendela log ke depan jika sudah ada
        self._populate_log_viewer()

    def _populate_log_viewer(self):
        """Mengisi text widget di jendela log dengan history."""
        if not hasattr(self, 'log_text_widget') or not self.log_text_widget.winfo_exists(): return
        self.log_text_widget.config(state="normal")
        self.log_text_widget.delete('1.0', tk.END)
        for msg in self.log_messages:
            self.log_text_widget.insert(tk.END, msg + "\n")
        self.log_text_widget.see(tk.END) # Auto-scroll ke bawah
        self.log_text_widget.config(state="disabled")

    def _clear_log_history(self):
        """Membersihkan log history dan tampilan di jendela log."""
        if messagebox.askyesno("Konfirmasi", "Anda yakin ingin membersihkan seluruh history log?", parent=self.log_window):
            self.log_messages.clear()
            self._add_log("Log history dibersihkan.")
            self._populate_log_viewer()

    def _save_results(self):
        """Menyimpan data dari tabel hasil ke file Excel."""
        items = self.results_table.get_children()
        if not items:
            messagebox.showwarning("Tidak Ada Data", "Tidak ada data deteksi untuk disimpan.")
            self._add_log("Penyimpanan hasil gagal: tidak ada data.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Simpan Hasil Deteksi"
        )
        if not file_path:
            self._add_log("Penyimpanan hasil dibatalkan oleh pengguna.")
            return
        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Hasil Deteksi"
            sheet.append(['Objek Terdeteksi', 'Jumlah'])
            sheet.column_dimensions['A'].width = 30
            sheet.column_dimensions['B'].width = 15
            for item in items:
                data = self.results_table.item(item)['values']
                sheet.append(data)
            workbook.save(filename=file_path)
            self._add_log(f"Hasil deteksi disimpan ke: {os.path.basename(file_path)}")
            messagebox.showinfo("Berhasil", f"Hasil berhasil disimpan di:\n{file_path}")
        except Exception as e:
            self._add_log(f"Gagal menyimpan file hasil: {e}")
            messagebox.showerror("Gagal Menyimpan", f"Gagal menyimpan file: {e}")

    def _on_closing(self):
        """Fungsi cleanup yang aman saat aplikasi ditutup."""
        self._add_log("Aplikasi ditutup.")
        print("Menutup aplikasi...")
        self._stop_current_feed()
        self.root.destroy()

class SplashScreen:
    """
    Kelas untuk membuat dan menampilkan jendela loading (splash screen).
    """
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True) # Menghilangkan border, title bar, dll.

        # Ukuran splash screen
        width = 400
        height = 350

        # Mengambil ukuran layar untuk menempatkan splash screen di tengah
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Mengatur tampilan splash screen
        self.splash_frame = ttk.Frame(self.window, style="TFrame")
        self.splash_frame.pack(fill="both", expand=True)

        try:
            # Muat gambar loading (pastikan ada file 'loading.png' di direktori)
            self.img = Image.open(resource_path(r"assets\loading.jpg")) # Ganti dengan path gambar Anda
            self.img = self.img.resize((200, 150), Image.Resampling.LANCZOS)
            self.photo_img = ImageTk.PhotoImage(self.img)
            ttk.Label(self.splash_frame, image=self.photo_img, background=GUIDetectorApp.COLOR_FRAME).pack(pady=(30,10))
        except FileNotFoundError:
            ttk.Label(self.splash_frame, text="🖼️", font=("Segoe UI", 40), background=GUIDetectorApp.COLOR_FRAME).pack(pady=(30,10))
            print("Peringatan: File 'loading.png' tidak ditemukan. Menampilkan teks pengganti.")

        ttk.Label(self.splash_frame, text="GUI Detector", font=GUIDetectorApp.FONT_BOLD, background=GUIDetectorApp.COLOR_FRAME, foreground=GUIDetectorApp.COLOR_ACCENT).pack(pady=5)
        self.status_label = ttk.Label(self.splash_frame, text="Mohon Menunggu...", font=GUIDetectorApp.FONT_SMALL, background=GUIDetectorApp.COLOR_FRAME, foreground=GUIDetectorApp.COLOR_TEXT)
        self.status_label.pack(pady=(15, 20))

        # Progress bar untuk memberikan feedback visual
        self.progress = ttk.Progressbar(self.splash_frame, orient="horizontal", length=300, mode='determinate')
        self.progress.pack(pady=10)
        self.progress.start(10) # Memulai animasi progress bar

    def close(self):
        """Menutup splash screen."""
        self.progress.stop()
        self.window.destroy()

# --- Titik Masuk Program ---
if __name__ == "__main__":
    """
    Blok ini hanya akan dieksekusi jika file ini dijalankan secara langsung.
    """
    app_root = tk.Tk()
    app_root.withdraw() # Sembunyikan jendela utama pada awalnya

    # Tampilkan splash screen
    splash = SplashScreen(app_root)
    
    # Inisialisasi aplikasi utama di "background"
    main_app = GUIDetectorApp(app_root)

    def main_app_ready():
        """Fungsi untuk menutup splash dan menampilkan aplikasi utama."""
        splash.close()
        app_root.deiconify() # Tampilkan kembali jendela utama

    # Atur jeda agar splash screen sempat terlihat sebelum aplikasi utama muncul.
    # 3000ms = 3 detik. Anda bisa sesuaikan nilainya.
    app_root.after(3000, main_app_ready)

    app_root.mainloop()