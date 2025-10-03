import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
from datetime import datetime, time
import time as time_module
import subprocess
import sys

# Función para verificar e instalar dependencias
def check_and_install_dependencies():
    """Verifica e instala las dependencias necesarias"""
    dependencies = {
        'pygame': 'pygame'
    }
    
    missing_deps = []
    
    # Verificar qué dependencias faltan
    for module_name, package_name in dependencies.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_deps.append(package_name)
    
    # Si faltan dependencias, instalarlas
    if missing_deps:
        print("=" * 60)
        print("INSTALANDO DEPENDENCIAS NECESARIAS")
        print("=" * 60)
        print(f"\nSe necesitan instalar los siguientes paquetes: {', '.join(missing_deps)}\n")
        
        for package in missing_deps:
            print(f"Instalando {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} instalado correctamente\n")
            except subprocess.CalledProcessError as e:
                print(f"✗ Error al instalar {package}: {e}\n")
                return False
        
        print("=" * 60)
        print("TODAS LAS DEPENDENCIAS INSTALADAS CORRECTAMENTE")
        print("=" * 60)
        print("\n")
    
    return True

# Verificar e instalar dependencias antes de importar pygame
if not check_and_install_dependencies():
    print("Error: No se pudieron instalar todas las dependencias necesarias.")
    print("Por favor, instala manualmente con: pip install pygame")
    input("Presiona Enter para salir...")
    sys.exit(1)

# Ahora sí importar pygame
import pygame

class MusicScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("Programador de Música Automático")
        self.root.geometry("900x700")
        
        # Inicializar pygame mixer
        pygame.mixer.init()
        
        # Variables
        self.schedules = []
        self.running = False
        self.current_thread = None
        self.config_file = "music_schedules.json"
        
        # Crear interfaz PRIMERO
        self.create_widgets()
        
        # Cargar configuración DESPUÉS de crear la interfaz
        self.load_config()
        
        # NO iniciar automáticamente - esperar a que el usuario inicie
        self.running = False
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title = ttk.Label(main_frame, text="Programador de Música", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Frame para agregar horarios
        add_frame = ttk.LabelFrame(main_frame, text="Agregar Nuevo Horario", padding="10")
        add_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Archivo de audio
        ttk.Label(add_frame, text="Archivo de Audio:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(add_frame, textvariable=self.file_path, width=40)
        file_entry.grid(row=0, column=1, padx=5)
        
        file_buttons_frame = ttk.Frame(add_frame)
        file_buttons_frame.grid(row=0, column=2)
        ttk.Button(file_buttons_frame, text="Seleccionar Uno", command=self.select_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_buttons_frame, text="Seleccionar Varios", command=self.select_multiple_files).pack(side=tk.LEFT, padx=2)
        
        # Lista de archivos seleccionados
        ttk.Label(add_frame, text="Archivos seleccionados:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        files_list_frame = ttk.Frame(add_frame)
        files_list_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.selected_files_listbox = tk.Listbox(files_list_frame, height=4, width=50)
        self.selected_files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient=tk.VERTICAL, command=self.selected_files_listbox.yview)
        files_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.selected_files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        files_buttons = ttk.Frame(add_frame)
        files_buttons.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=2)
        ttk.Button(files_buttons, text="▶️ Probar", command=self.test_selected_file, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(files_buttons, text="⏹ Parar", command=self.stop_audio, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(files_buttons, text="❌ Quitar", command=self.remove_selected_file, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(files_buttons, text="🗑️ Limpiar Todo", command=self.clear_all_files, width=12).pack(side=tk.LEFT, padx=2)
        
        # Variable para almacenar los archivos
        self.selected_files = []
        
        # Hora de reproducción
        ttk.Label(add_frame, text="Hora (HH:MM):").grid(row=3, column=0, sticky=tk.W, pady=5)
        time_frame = ttk.Frame(add_frame)
        time_frame.grid(row=3, column=1, sticky=tk.W)
        
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f")
        hour_spin.grid(row=0, column=0)
        ttk.Label(time_frame, text=":").grid(row=0, column=1)
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f")
        minute_spin.grid(row=0, column=2)
        
        # Días de la semana
        ttk.Label(add_frame, text="Días:").grid(row=4, column=0, sticky=tk.W, pady=5)
        days_frame = ttk.Frame(add_frame)
        days_frame.grid(row=4, column=1, columnspan=2, sticky=tk.W)
        
        self.days_vars = {}
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # Botón "Todos los días"
        self.all_days_var = tk.BooleanVar()
        ttk.Checkbutton(days_frame, text="Todos los días", variable=self.all_days_var, 
                       command=self.toggle_all_days).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(0,5))
        
        for i, day in enumerate(days):
            var = tk.BooleanVar()
            self.days_vars[day] = var
            var.trace_add('write', lambda *args: self.check_all_days_state())
            ttk.Checkbutton(days_frame, text=day, variable=var).grid(row=(i//4)+1, column=i%4, sticky=tk.W, padx=5)
        
        # Volumen
        ttk.Label(add_frame, text="Volumen (0-100):").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        volume_frame = ttk.Frame(add_frame)
        volume_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        self.volume_var = tk.IntVar(value=70)
        volume_scale = ttk.Scale(volume_frame, from_=0, to=100, variable=self.volume_var, orient=tk.HORIZONTAL, length=150)
        volume_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        self.volume_label = ttk.Label(volume_frame, text="70%", width=5)
        self.volume_label.pack(side=tk.LEFT)
        
        self.volume_var.trace_add('write', self.update_volume_label)
        
        # Repetir
        self.repeat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(add_frame, text="Repetir audio", variable=self.repeat_var).grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Botón agregar
        ttk.Button(add_frame, text="Agregar Horario(s)", command=self.add_schedule, 
                  style='Accent.TButton').grid(row=7, column=0, columnspan=3, pady=10)
        
        # Lista de horarios programados
        list_frame = ttk.LabelFrame(main_frame, text="Horarios Programados", padding="10")
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Treeview para mostrar horarios
        columns = ('Hora', 'Días', 'Archivo', 'Volumen', 'Repetir')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=10)
        
        self.tree.heading('#0', text='ID')
        self.tree.column('#0', width=50)
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Archivo':
                self.tree.column(col, width=250)
            elif col == 'Días':
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=80)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Lista de horarios programados
        list_frame = ttk.LabelFrame(main_frame, text="Horarios Programados", padding="10")
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Treeview para mostrar horarios
        columns = ('Hora', 'Días', 'Archivo', 'Volumen', 'Repetir')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=10)
        
        self.tree.heading('#0', text='ID')
        self.tree.column('#0', width=50)
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Archivo':
                self.tree.column(col, width=250)
            elif col == 'Días':
                self.tree.column(col, width=200)
            else:
                self.tree.column(col, width=80)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Botones de control
        control_frame = ttk.Frame(list_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(control_frame, text="▶️ Probar Audio", command=self.test_audio, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏹ Detener Audio", command=self.stop_audio, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="❌ Eliminar Horario", command=self.delete_schedule, width=15).pack(side=tk.LEFT, padx=5)
        
        # Botones de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Frame para botones de configuración
        buttons_frame1 = ttk.Frame(config_frame)
        buttons_frame1.grid(row=0, column=0, pady=5, sticky=tk.W)
        
        ttk.Button(buttons_frame1, text="💾 Guardar Configuración", command=self.manual_save_config, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame1, text="📤 Exportar Configuración", command=self.export_config, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame1, text="📥 Importar Configuración", command=self.import_config, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame1, text="🔄 Actualizar Lista", command=self.update_tree, width=15).pack(side=tk.LEFT, padx=5)
        
        # Estado del sistema
        status_frame = ttk.LabelFrame(main_frame, text="Estado del Sistema y Control", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Frame superior con estado y botón
        top_status_frame = ttk.Frame(status_frame)
        top_status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(top_status_frame, text="● Sistema Detenido", foreground="red", font=('Arial', 12, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.start_stop_button = ttk.Button(top_status_frame, text="▶️ INICIAR SISTEMA", command=self.toggle_system, width=20)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_status_frame, text="🔄 Reiniciar", command=self.restart_system, width=12).pack(side=tk.LEFT, padx=5)
        
        # Separador visual
        ttk.Separator(status_frame, orient='horizontal').grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Botón adicional para limpiar log
        ttk.Button(status_frame, text="🗑️ Limpiar Registro", command=self.clear_log, width=15).grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        # Log de eventos
        ttk.Label(status_frame, text="Registro de Eventos:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(5, 2))
        
        log_frame = ttk.Frame(status_frame)
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.log_text = tk.Text(log_frame, height=6, width=80, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
    def update_volume_label(self, *args):
        self.volume_label.config(text=f"{self.volume_var.get()}%")
    
    def toggle_all_days(self):
        """Activa o desactiva todos los días de la semana"""
        state = self.all_days_var.get()
        for var in self.days_vars.values():
            var.set(state)
    
    def check_all_days_state(self):
        """Verifica si todos los días están seleccionados para actualizar el checkbox 'Todos los días'"""
        all_selected = all(var.get() for var in self.days_vars.values())
        if all_selected != self.all_days_var.get():
            # Temporalmente desconectar el trace para evitar bucle infinito
            self.all_days_var.set(all_selected)
        
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[("Archivos de Audio", "*.mp3 *.wav *.ogg *.flac"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            if filename not in self.selected_files:
                self.selected_files.append(filename)
                self.update_files_listbox()
    
    def select_multiple_files(self):
        filenames = filedialog.askopenfilenames(
            title="Seleccionar múltiples archivos de audio",
            filetypes=[("Archivos de Audio", "*.mp3 *.wav *.ogg *.flac"), ("Todos los archivos", "*.*")]
        )
        if filenames:
            added_count = 0
            for filename in filenames:
                if filename not in self.selected_files:
                    self.selected_files.append(filename)
                    added_count += 1
            
            self.update_files_listbox()
            
            if added_count > 0:
                self.log(f"✓ {added_count} archivo(s) añadido(s) a la lista")
                if self.selected_files:
                    self.file_path.set(f"{len(self.selected_files)} archivos seleccionados")
    
    def update_files_listbox(self):
        self.selected_files_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.selected_files_listbox.insert(tk.END, os.path.basename(file))
    
    def remove_selected_file(self):
        selection = self.selected_files_listbox.curselection()
        if selection:
            index = selection[0]
            removed_file = self.selected_files.pop(index)
            self.update_files_listbox()
            self.log(f"Archivo removido: {os.path.basename(removed_file)}")
            
            if self.selected_files:
                self.file_path.set(f"{len(self.selected_files)} archivos seleccionados")
            else:
                self.file_path.set("")
    
    def clear_all_files(self):
        if self.selected_files:
            count = len(self.selected_files)
            self.selected_files = []
            self.update_files_listbox()
            self.file_path.set("")
            self.log(f"🗑️ {count} archivo(s) limpiado(s) de la lista")
    
    def test_selected_file(self):
        """Prueba el archivo seleccionado de la lista de archivos por añadir"""
        selection = self.selected_files_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Debe seleccionar un archivo de la lista")
            return
        
        index = selection[0]
        file_path = self.selected_files[index]
        
        if not os.path.exists(file_path):
            self.log(f"⚠ ERROR: Archivo no encontrado: {os.path.basename(file_path)}")
            messagebox.showerror("Error", f"El archivo no existe:\n{os.path.basename(file_path)}")
            return
        
        try:
            pygame.mixer.music.load(file_path)
            volume = self.volume_var.get() / 100.0
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            
            self.log(f"♪ Probando: {os.path.basename(file_path)} (Vol: {self.volume_var.get()}%)")
            messagebox.showinfo("Reproduciendo", f"Reproduciendo:\n{os.path.basename(file_path)}\n\nPresiona 'Parar' para detener.")
            
        except Exception as e:
            self.log(f"⚠ ERROR al reproducir: {str(e)}")
            messagebox.showerror("Error", f"No se pudo reproducir el archivo:\n{str(e)}")
            
    def add_schedule(self):
        # Validaciones
        if not self.selected_files:
            messagebox.showerror("Error", "Debe seleccionar al menos un archivo de audio")
            return
            
        selected_days = [day for day, var in self.days_vars.items() if var.get()]
        if not selected_days:
            messagebox.showerror("Error", "Debe seleccionar al menos un día")
            return
        
        # Crear horario para cada archivo seleccionado
        added_count = 0
        for file_path in self.selected_files:
            if not os.path.exists(file_path):
                self.log(f"⚠ Archivo no encontrado: {os.path.basename(file_path)}")
                continue
            
            schedule = {
                'id': len(self.schedules) + 1,
                'file': file_path,
                'hour': int(self.hour_var.get()),
                'minute': int(self.minute_var.get()),
                'days': selected_days.copy(),
                'volume': self.volume_var.get(),
                'repeat': self.repeat_var.get(),
                'last_played': None
            }
            
            self.schedules.append(schedule)
            added_count += 1
        
        if added_count > 0:
            self.update_tree()
            self.save_config()
            self.log(f"✓ {added_count} horario(s) agregado(s): {int(self.hour_var.get()):02d}:{int(self.minute_var.get()):02d}")
            messagebox.showinfo("Éxito", f"Se agregaron {added_count} horario(s) correctamente")
            
            # Limpiar formulario
            self.selected_files = []
            self.update_files_listbox()
            self.file_path.set("")
            for var in self.days_vars.values():
                var.set(False)
            self.all_days_var.set(False)
        else:
            messagebox.showwarning("Advertencia", "No se pudo agregar ningún horario. Verifique que los archivos existan.")
            
    def update_tree(self):
        # Limpiar árbol
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ordenar horarios por hora y minuto
        sorted_schedules = sorted(self.schedules, key=lambda x: (x['hour'], x['minute']))
        
        # Agregar items
        for schedule in sorted_schedules:
            days_str = ", ".join([day[:3] for day in schedule['days']])
            file_name = os.path.basename(schedule['file'])
            repeat_str = "Sí" if schedule['repeat'] else "No"
            
            self.tree.insert('', tk.END, text=str(schedule['id']),
                           values=(f"{schedule['hour']:02d}:{schedule['minute']:02d}",
                                 days_str,
                                 file_name,
                                 f"{schedule['volume']}%",
                                 repeat_str))
        
        # Log con resumen
        if sorted_schedules:
            self.log(f"📋 Lista actualizada: {len(sorted_schedules)} horario(s) programado(s)")
    
    def delete_schedule(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Debe seleccionar un horario")
            return
            
        item = self.tree.item(selected[0])
        schedule_id = int(item['text'])
        
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self.update_tree()
        self.save_config()
        self.log(f"Horario eliminado: ID {schedule_id}")
        
    def test_audio(self):
        """Prueba el horario seleccionado de la tabla de horarios programados"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Debe seleccionar un horario de la tabla")
            return
            
        item = self.tree.item(selected[0])
        schedule_id = int(item['text'])
        schedule = next((s for s in self.schedules if s['id'] == schedule_id), None)
        
        if schedule:
            if not os.path.exists(schedule['file']):
                self.log(f"⚠ ERROR: Archivo no encontrado: {os.path.basename(schedule['file'])}")
                messagebox.showerror("Error", f"El archivo no existe:\n{os.path.basename(schedule['file'])}")
                return
            
            self.play_audio(schedule, test=True)
            messagebox.showinfo("Reproduciendo", f"Reproduciendo horario programado:\n{os.path.basename(schedule['file'])}\nHora: {schedule['hour']:02d}:{schedule['minute']:02d}\n\nPresiona 'Detener Audio' para parar.")
        else:
            messagebox.showerror("Error", "No se encontró el horario seleccionado")
            
    def stop_audio(self):
        """Detiene cualquier audio que se esté reproduciendo"""
        try:
            pygame.mixer.music.stop()
            self.log("⏹ Reproducción detenida")
        except Exception as e:
            self.log(f"⚠ Error al detener audio: {str(e)}")
    
    def manual_save_config(self):
        self.save_config()
        messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        self.log("✓ Configuración guardada manualmente")
    
    def export_config(self):
        filename = filedialog.asksaveasfilename(
            title="Exportar configuración",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Todos los archivos", "*.*")],
            initialfile="music_config_export.json"
        )
        
        if filename:
            try:
                config = {'schedules': []}
                
                for schedule in self.schedules:
                    schedule_copy = schedule.copy()
                    if 'last_played' in schedule_copy and schedule_copy['last_played']:
                        schedule_copy['last_played'] = schedule_copy['last_played'].isoformat()
                    config['schedules'].append(schedule_copy)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Éxito", f"Configuración exportada a:\n{filename}")
                self.log(f"✓ Configuración exportada a: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {str(e)}")
                self.log(f"⚠ ERROR al exportar configuración: {str(e)}")
    
    def import_config(self):
        filename = filedialog.askopenfilename(
            title="Importar configuración",
            filetypes=[("JSON files", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Preguntar si reemplazar o agregar
                response = messagebox.askyesnocancel(
                    "Importar Configuración",
                    "¿Desea reemplazar la configuración actual?\n\n"
                    "Sí: Reemplazar todo\n"
                    "No: Agregar a la configuración existente\n"
                    "Cancelar: No importar"
                )
                
                if response is None:  # Cancelar
                    return
                
                if response:  # Sí - Reemplazar
                    self.schedules = []
                
                # Importar horarios
                imported_count = 0
                for schedule in config.get('schedules', []):
                    # Verificar que el archivo existe
                    if not os.path.exists(schedule['file']):
                        self.log(f"⚠ Archivo no encontrado: {os.path.basename(schedule['file'])}")
                        continue
                    
                    # Asignar nuevo ID
                    schedule['id'] = len(self.schedules) + 1
                    
                    # Convertir fecha si existe
                    if 'last_played' in schedule and schedule['last_played']:
                        from datetime import date
                        schedule['last_played'] = date.fromisoformat(schedule['last_played'])
                    else:
                        schedule['last_played'] = None
                    
                    self.schedules.append(schedule)
                    imported_count += 1
                
                self.update_tree()
                self.save_config()
                
                messagebox.showinfo("Éxito", f"Se importaron {imported_count} horarios correctamente")
                self.log(f"✓ Configuración importada: {imported_count} horarios")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al importar: {str(e)}")
                self.log(f"⚠ ERROR al importar configuración: {str(e)}")
    
    def toggle_system(self):
        if self.running:
            # Pausar sistema
            self.running = False
            time_module.sleep(0.5)  # Esperar a que el thread termine
            self.start_stop_button.config(text="▶️ INICIAR SISTEMA")
            self.status_label.config(text="● Sistema Detenido", foreground="red")
            self.log("⏹ Sistema detenido - No se reproducirán horarios programados")
            messagebox.showinfo("Sistema Detenido", "El sistema ha sido detenido.\nNo se reproducirá música automáticamente.")
        else:
            # Iniciar sistema
            if not self.schedules:
                messagebox.showwarning("Sin Horarios", "No hay horarios programados.\nAgrega al menos un horario antes de iniciar el sistema.")
                return
            
            self.start_scheduler()
            self.start_stop_button.config(text="⏸️ PAUSAR SISTEMA")
            self.status_label.config(text="● Sistema Activo", foreground="green")
            self.log("▶️ Sistema iniciado - Monitoreando horarios programados")
            messagebox.showinfo("Sistema Iniciado", f"El sistema está activo.\nMonitoreando {len(self.schedules)} horario(s) programado(s).")
    
    def restart_system(self):
        """Reinicia el sistema de monitoreo completamente"""
        was_running = self.running
        
        if self.running:
            self.running = False
            self.log("🔄 Deteniendo sistema para reiniciar...")
            time_module.sleep(1.5)
        
        if was_running:
            if not self.schedules:
                messagebox.showwarning("Sin Horarios", "No hay horarios programados para monitorear.")
                return
                
            self.log("🔄 Reiniciando sistema de monitoreo...")
            self.start_scheduler()
            self.start_stop_button.config(text="⏸️ PAUSAR SISTEMA")
            self.status_label.config(text="● Sistema Activo", foreground="green")
            self.log("✓ Sistema reiniciado y monitoreando horarios")
            messagebox.showinfo("Sistema Reiniciado", "El sistema se ha reiniciado correctamente.\nMonitoreando horarios activamente.")
        else:
            self.log("ℹ️ El sistema estaba detenido - no se reinició")
            messagebox.showinfo("Sistema Detenido", "El sistema está detenido.\nPresiona 'INICIAR SISTEMA' para activarlo.")
    
    def clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.log("Log limpiado")
        
    def play_audio(self, schedule, test=False):
        try:
            if not os.path.exists(schedule['file']):
                self.log(f"⚠ ERROR: Archivo no encontrado: {os.path.basename(schedule['file'])}")
                return False
                
            pygame.mixer.music.load(schedule['file'])
            volume = schedule['volume'] / 100.0
            pygame.mixer.music.set_volume(volume)
            
            loops = -1 if schedule['repeat'] and not test else 0
            pygame.mixer.music.play(loops=loops)
            
            action = "Prueba" if test else "Reproduciendo"
            self.log(f"♪ {action}: {os.path.basename(schedule['file'])} (Vol: {schedule['volume']}%)")
            return True
            
        except Exception as e:
            self.log(f"⚠ ERROR al reproducir {os.path.basename(schedule['file'])}: {str(e)}")
            return False
            
    def start_scheduler(self):
        if self.current_thread and self.current_thread.is_alive():
            return  # Ya hay un thread corriendo
        
        self.running = True
        self.current_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.current_thread.start()
        self.log("🚀 Scheduler iniciado - monitoreando horarios...")
        
    def scheduler_loop(self):
        days_map = {
            'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Jueves': 3,
            'Viernes': 4, 'Sábado': 5, 'Domingo': 6
        }
        
        self.log("📅 Sistema de monitoreo ACTIVO - Revisando horarios cada 15 segundos")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                current_day = now.weekday()
                current_date = now.date()
                
                # Log de debug cada minuto
                if now.second == 0:
                    self.log(f"🔍 Verificando horarios... Hora actual: {now.strftime('%H:%M:%S')}")
                
                for schedule in self.schedules:
                    # Verificar si hoy está en los días programados
                    day_matches = any(days_map.get(day, -1) == current_day for day in schedule['days'])
                    
                    if not day_matches:
                        continue
                    
                    # Crear tiempo objetivo
                    target_hour = schedule['hour']
                    target_minute = schedule['minute']
                    
                    # Verificar si es la hora exacta (con ventana de 60 segundos)
                    current_hour = now.hour
                    current_minute = now.minute
                    
                    if current_hour == target_hour and current_minute == target_minute:
                        last_played = schedule.get('last_played')
                        
                        # Solo reproducir si no se ha reproducido hoy
                        if last_played != current_date:
                            self.log(f"⏰ ¡REPRODUCIENDO AHORA! Horario: {target_hour:02d}:{target_minute:02d}")
                            self.log(f"🎵 Archivo: {os.path.basename(schedule['file'])}")
                            
                            success = self.play_audio(schedule)
                            
                            if success:
                                schedule['last_played'] = current_date
                                self.save_config()
                                self.log(f"✓ Reproducción programada completada exitosamente")
                            else:
                                self.log(f"⚠ Error en reproducción - se intentará con el siguiente horario")
                
                # Verificar cada 15 segundos
                time_module.sleep(15)
                
            except Exception as e:
                self.log(f"⚠ ERROR CRÍTICO en el scheduler: {str(e)}")
                import traceback
                self.log(f"Detalles: {traceback.format_exc()}")
                time_module.sleep(60)
        
        self.log("⏹ Sistema de monitoreo DETENIDO")
                
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
    def save_config(self):
        try:
            config = {
                'schedules': []
            }
            
            for schedule in self.schedules:
                schedule_copy = schedule.copy()
                if 'last_played' in schedule_copy and schedule_copy['last_played']:
                    schedule_copy['last_played'] = schedule_copy['last_played'].isoformat()
                config['schedules'].append(schedule_copy)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.log(f"Error al guardar configuración: {str(e)}")
            
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                for schedule in config.get('schedules', []):
                    if 'last_played' in schedule and schedule['last_played']:
                        from datetime import date
                        schedule['last_played'] = date.fromisoformat(schedule['last_played'])
                    self.schedules.append(schedule)
                    
                self.update_tree()
                self.log(f"Configuración cargada: {len(self.schedules)} horarios")
                
        except Exception as e:
            self.log(f"Error al cargar configuración: {str(e)}")

def main():
    print("=" * 60)
    print("PROGRAMADOR DE MÚSICA AUTOMÁTICO")
    print("=" * 60)
    print("Iniciando aplicación...\n")
    
    root = tk.Tk()
    app = MusicScheduler(root)
    
    def on_closing():
        app.running = False
        pygame.mixer.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    print("✓ Aplicación iniciada correctamente")
    print("=" * 60)
    print("\n")
    
    root.mainloop()

if __name__ == "__main__":
    main()