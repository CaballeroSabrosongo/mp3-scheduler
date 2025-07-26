
# mp3_scheduler_gui.py
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os, json, threading, time, datetime
import pygame

DAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
SCHEDULE_FILE = "schedule.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class MP3SchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cuñas MP3 Programadas")
        self.schedule = self.load_schedule()

        self.file_path = tk.StringVar()
        self.hour = tk.StringVar(value="10")
        self.minute = tk.StringVar(value="00")
        self.volume = tk.DoubleVar(value=1.0)

        self.selected_days = {day: tk.BooleanVar(value=False) for day in DAYS}
        self.used_tracks = set()

        pygame.mixer.init()
        self.build_ui()
        self.refresh_table()

        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        threading.Thread(target=self.check_schedule_loop, daemon=True).start()

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()

        ttk.Label(frm, text="Archivo MP3:").grid(column=0, row=0, sticky="w")
        ttk.Entry(frm, textvariable=self.file_path, width=40).grid(column=1, row=0)
        ttk.Button(frm, text="Seleccionar archivo", command=self.browse_file).grid(column=2, row=0)

        ttk.Label(frm, text="Usados previamente:").grid(column=0, row=1, sticky="nw")
        self.track_listbox = tk.Listbox(frm, height=5, width=40)
        self.track_listbox.grid(column=1, row=1, columnspan=2, sticky="w")
        self.track_listbox.bind("<<ListboxSelect>>", self.select_from_list)

        ttk.Label(frm, text="Días:").grid(column=0, row=2, sticky="nw")
        day_frame = ttk.Frame(frm)
        day_frame.grid(column=1, row=2, sticky="w")
        for i, day in enumerate(DAYS):
            cb = ttk.Checkbutton(day_frame, text=day, variable=self.selected_days[day])
            cb.grid(row=i//4, column=i%4, sticky="w")

        ttk.Label(frm, text="Hora:").grid(column=0, row=3, sticky="w")
        hour_spin = ttk.Spinbox(frm, from_=0, to=23, textvariable=self.hour, width=5, format="%02.0f")
        hour_spin.grid(column=1, row=3, sticky="w")

        ttk.Label(frm, text="Minuto:").grid(column=0, row=4, sticky="w")
        minute_spin = ttk.Spinbox(frm, from_=0, to=59, textvariable=self.minute, width=5, format="%02.0f")
        minute_spin.grid(column=1, row=4, sticky="w")

        ttk.Button(frm, text="Agregar a programación", command=self.add_schedule).grid(column=1, row=5, pady=5)
        ttk.Button(frm, text="▶ Reproducir ahora", command=self.play_now).grid(column=2, row=5, pady=5)

        self.tree = ttk.Treeview(frm, columns=("día", "hora", "archivo"), show="headings")
        self.tree.heading("día", text="Día")
        self.tree.heading("hora", text="Hora")
        self.tree.heading("archivo", text="Archivo MP3")
        self.tree.grid(column=0, row=6, columnspan=3, pady=10)

        ttk.Button(frm, text="🗑 Eliminar seleccionado", command=self.delete_selected).grid(column=1, row=7, pady=5)
        ttk.Button(frm, text="⏹ Detener", command=self.stop_playback).grid(column=2, row=7, pady=5)

        ttk.Label(frm, text="Volumen:").grid(column=0, row=8, sticky="w")
        vol_slider = ttk.Scale(frm, from_=0, to=1, variable=self.volume, orient='horizontal', command=self.set_volume)
        vol_slider.grid(column=1, row=8, columnspan=2, sticky="we")

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos MP3", "*.mp3")])
        if path:
            filename = os.path.basename(path)
            dest_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())
            self.file_path.set(filename)
            if filename not in self.used_tracks:
                self.used_tracks.add(filename)
                self.track_listbox.insert(tk.END, filename)

    def select_from_list(self, event):
        selection = self.track_listbox.curselection()
        if selection:
            self.file_path.set(self.track_listbox.get(selection[0]))

    def add_schedule(self):
        selected_days = [day for day, var in self.selected_days.items() if var.get()]
        if not selected_days:
            messagebox.showerror("Error", "Selecciona al menos un día")
            return

        time_str = f"{int(self.hour.get()):02}:{int(self.minute.get()):02}"
        filename = self.file_path.get()

        if not filename:
            messagebox.showerror("Error", "Debes seleccionar un archivo MP3")
            return

        for day in selected_days:
            self.schedule.setdefault(day, {})[time_str] = filename

        if filename not in self.used_tracks:
            self.used_tracks.add(filename)
            self.track_listbox.insert(tk.END, filename)

        self.save_schedule()
        self.refresh_table()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for day, entries in self.schedule.items():
            for time, file in entries.items():
                self.tree.insert('', 'end', values=(day, time, file))

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for item in selected:
            values = self.tree.item(item, 'values')
            day, time = values[0], values[1]
            if day in self.schedule and time in self.schedule[day]:
                del self.schedule[day][time]
                if not self.schedule[day]:
                    del self.schedule[day]
        self.save_schedule()
        self.refresh_table()

    def play_now(self):
        filename = self.file_path.get()
        if not filename:
            messagebox.showerror("Error", "Selecciona un archivo para reproducir")
            return
        full_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(full_path):
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(self.volume.get())
            pygame.mixer.music.play()

    def stop_playback(self):
        pygame.mixer.music.stop()

    def set_volume(self, val):
        pygame.mixer.music.set_volume(float(val))

    def load_schedule(self):
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE) as f:
                return json.load(f)
        return {}

    def save_schedule(self):
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(self.schedule, f, indent=2)

    def check_schedule_loop(self):
        while self.running:
            now = datetime.datetime.now()
            current_day = DAYS[now.weekday()]
            current_time = now.strftime("%H:%M")
            file_to_play = self.schedule.get(current_day, {}).get(current_time)
            if file_to_play:
                full_path = os.path.join(UPLOAD_FOLDER, file_to_play)
                if os.path.exists(full_path):
                    pygame.mixer.music.load(full_path)
                    pygame.mixer.music.set_volume(self.volume.get())
                    pygame.mixer.music.play()
                    time.sleep(60)
                    continue
            time.sleep(5)

    def on_close(self):
        self.running = False
        self.save_schedule()
        pygame.mixer.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MP3SchedulerApp(root)
    root.mainloop()
