#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import re
import socket
import webbrowser
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# --------------------- RUTAS ABSOLUTAS ---------------------
SYSTEM32 = os.path.join(os.environ['SystemRoot'], 'System32')
NETSH = os.path.join(SYSTEM32, 'netsh.exe')
DISM = os.path.join(SYSTEM32, 'dism.exe')
POWERSHELL = os.path.join(SYSTEM32, 'WindowsPowerShell', 'v1.0', 'powershell.exe')
POWERCFG = os.path.join(SYSTEM32, 'powercfg.exe')
REG = os.path.join(SYSTEM32, 'reg.exe')
ARP = os.path.join(SYSTEM32, 'arp.exe')
IPCONFIG = os.path.join(SYSTEM32, 'ipconfig.exe')
PING = os.path.join(SYSTEM32, 'ping.exe')
FINDSTR = os.path.join(SYSTEM32, 'findstr.exe')
CSCRIPT = os.path.join(SYSTEM32, 'cscript.exe')
SC = os.path.join(SYSTEM32, 'sc.exe')

# --------------------- ELEVACIÓN DE ADMINISTRADOR ---------------------
def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def run_as_admin():
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join(f'"{arg}"' for arg in sys.argv[1:])
        try:
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        except Exception:
            messagebox.showerror("Error", "No se pudo elevar a administrador.")
        sys.exit()

# --------------------- CLASE PRINCIPAL ---------------------
class WarclibSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("WARCLIB System Lab - Navaja Suiza de Diagnóstico Ultimate")
        self.root.geometry("880x650")
        self.root.minsize(800, 550)
        self.center_window()

        # Paleta de colores profesional
        self.bg_dark = "#1e1e2f"
        self.bg_medium = "#2a2a3b"
        self.bg_card = "#2d2d3f"
        self.fg_light = "#f0f0f0"
        self.accent_blue = "#3a86ff"
        self.accent_green = "#38b000"
        self.accent_orange = "#fb8500"
        self.accent_red = "#e63946"
        self.console_bg = "#0a0a0f"
        self.console_fg = "#0f0"

        self.setup_styles()

        # Frame principal con scroll
        self.main_frame = Frame(root, bg=self.bg_dark)
        self.main_frame.pack(fill=BOTH, expand=True)
        self.canvas = Canvas(self.main_frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = Scrollbar(self.main_frame, orient=VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg=self.bg_dark)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Título
        title_frame = Frame(self.scrollable_frame, bg=self.bg_dark)
        title_frame.pack(fill=X, pady=(20, 10))
        Label(title_frame, text="🛠️  WARCLIB System Lab  🛠️", font=("Segoe UI", 20, "bold"), fg=self.accent_blue, bg=self.bg_dark).pack()
        Label(title_frame, text="Suite Técnica Ultimate · Diagnóstico y recuperación", font=("Segoe UI", 10), fg=self.fg_light, bg=self.bg_dark).pack()

        # Botones (9 opciones, igual que el menú original)
        self.btn_frame = Frame(self.scrollable_frame, bg=self.bg_dark)
        self.btn_frame.pack(pady=20, padx=20, fill=BOTH, expand=True)

        buttons = [
            ("📡 1. Recuperar Contraseñas WiFi", self.wifi_passwords, self.accent_blue),
            ("🔑 2. Extractor de Licencias", self.extract_licenses, self.accent_blue),
            ("💻 3. Fichador de Hardware", self.hardware_info, self.accent_blue),
            ("🌐 4. Escáner Rápido de Red", self.network_scan, self.accent_blue),
            ("💾 5. Extractor de Controladores", self.backup_drivers, self.accent_green),
            ("🚀 6. Programas de Inicio", self.startup_apps, self.accent_orange),
            ("🛡️ 7. Inmunizador de Sistema", self.immunize_system, self.accent_red),
            ("🔋 8. Reporte de Batería", self.battery_report, self.accent_green),
            ("❌ 9. Salir", self.root.quit, "#888888")
        ]

        for i, (text, cmd, color) in enumerate(buttons):
            row = i // 3
            col = i % 3
            btn = Button(self.btn_frame, text=text, font=("Segoe UI", 11, "bold"),
                         bg=color, fg="white", activebackground=self.lighten_color(color),
                         activeforeground="white", bd=0, padx=12, pady=12,
                         cursor="hand2", command=cmd, relief=FLAT)
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.btn_frame.grid_columnconfigure(col, weight=1)
        for r in range(3):
            self.btn_frame.grid_rowconfigure(r, weight=1)

        # Área de log estilo consola
        log_frame = LabelFrame(self.scrollable_frame, text="📋  Registro de eventos  📋", font=("Segoe UI", 10, "bold"),
                               fg=self.accent_blue, bg=self.bg_card, bd=2, relief=GROOVE)
        log_frame.pack(fill=BOTH, expand=True, padx=20, pady=(10, 20))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, font=("Consolas", 9),
                                                  bg=self.console_bg, fg=self.console_fg,
                                                  insertbackground="white", wrap=WORD, bd=0)
        self.log_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Barra de progreso y estado
        self.progress = ttk.Progressbar(self.scrollable_frame, mode='indeterminate', style="TProgressbar")
        self.status_var = StringVar()
        self.status_var.set("✅ Listo")
        status_bar = Label(self.scrollable_frame, textvariable=self.status_var, font=("Segoe UI", 9),
                           bg=self.bg_medium, fg=self.fg_light, anchor=W, padx=5)
        status_bar.pack(fill=X, side=BOTTOM)

        self.log("🚀 WARCLIB System Lab iniciado correctamente (modo administrador)")
        self.log(f"🔧 Usando rutas de sistema: {SYSTEM32}")

    # --------------------- MÉTODOS AUXILIARES ---------------------
    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def lighten_color(self, hex_color, factor=0.3):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=12, troughcolor=self.bg_medium, background=self.accent_blue)
        style.configure("TLabel", background=self.bg_dark, foreground=self.fg_light)
        style.configure("TLabelframe", background=self.bg_card, foreground=self.accent_blue)
        style.configure("TLabelframe.Label", background=self.bg_card, foreground=self.accent_blue)

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{timestamp}] {msg}\n")
        self.log_text.see(END)
        self.root.update_idletasks()

    def start_progress(self, message):
        self.status_var.set(message)
        self.progress.pack(fill=X, padx=20, pady=(0,10))
        self.progress.start(10)
        self.root.update()

    def stop_progress(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("✅ Listo")
        self.root.update()

    def run_cmd(self, cmd, capture=True, shell=False):
        try:
            if capture:
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=shell, encoding='utf-8', errors='replace')
                return proc.stdout, proc.stderr, proc.returncode
            else:
                subprocess.run(cmd, shell=shell)
                return "", "", 0
        except Exception as e:
            return "", str(e), -1

    def open_notepad(self, filepath):
        if os.path.exists(filepath):
            os.startfile(filepath)
            self.log(f"📄 Abierto con notepad: {filepath}")
        else:
            self.log(f"❌ No se encontró el archivo: {filepath}")

    # --------------------- 1. RECUPERAR WIFI ---------------------
    def wifi_passwords(self):
        def task():
            self.start_progress("📡 Obteniendo redes WiFi guardadas...")
            cmd = f'"{NETSH}" wlan show profiles'
            out, err, rc = self.run_cmd(cmd)
            if rc != 0:
                self.log(f"❌ Error: {err}")
                self.stop_progress()
                return
            pattern = r'(?:Perfil de todos los usuarios|All User Profile)\s*:\s*(.+)'
            profiles = re.findall(pattern, out)
            if not profiles:
                self.log("⚠️ No se encontraron redes WiFi guardadas.")
                self.stop_progress()
                return

            top = Toplevel(self.root)
            top.title("Seleccionar red WiFi")
            top.geometry("450x350")
            top.configure(bg=self.bg_card)
            Label(top, text="📶 Redes disponibles:", font=("Segoe UI", 10, "bold"), bg=self.bg_card, fg=self.fg_light).pack(pady=10)
            listbox = Listbox(top, height=12, font=("Segoe UI", 9), bg=self.console_bg, fg=self.console_fg, selectbackground=self.accent_blue)
            for p in profiles:
                listbox.insert(END, p.strip())
            listbox.pack(fill=BOTH, expand=True, padx=20, pady=5)

            def show_key():
                sel = listbox.curselection()
                if not sel:
                    return
                ssid = listbox.get(sel[0])
                top.destroy()
                self.log(f"🔍 Procesando red: {ssid}")
                self.start_progress(f"Extrayendo clave de {ssid}...")
                filename = f"Clave_{ssid.replace(' ', '_')}.txt"
                cmd2 = f'"{NETSH}" wlan show profile name="{ssid}" key=clear'
                out2, err2, rc2 = self.run_cmd(cmd2)
                if rc2 != 0:
                    self.log(f"❌ Error: {err2}")
                    self.stop_progress()
                    return
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Reporte de Clave WiFi - WARCLIB System Lab\n\n")
                    f.write(out2)
                self.stop_progress()
                self.log(f"✅ Archivo '{filename}' generado.")
                self.open_notepad(filename)

            Button(top, text="Mostrar clave", command=show_key, bg=self.accent_green, fg="white",
                   font=("Segoe UI", 10, "bold"), padx=10, pady=5, relief=FLAT, cursor="hand2").pack(pady=15)
        threading.Thread(target=task, daemon=True).start()

    # --------------------- 2. EXTRACTOR DE LICENCIAS ---------------------
    def extract_licenses(self):
        def task():
            self.start_progress("🔑 Extrayendo licencias...")
            filename = "Product_Key_Reporte.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("REPORTE DE LICENCIAS - WARCLIB System Lab\n")
                f.write(f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                # Nombre del sistema
                cmd = f'"{REG}" query "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion" /v ProductName'
                out, _, _ = self.run_cmd(cmd)
                f.write(out + "\n")
                # Versión
                cmd = f'"{REG}" query "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion" /v DisplayVersion'
                out, _, _ = self.run_cmd(cmd)
                f.write(out + "\n")
                f.write("\n--- CLAVE EN BIOS/UEFI (OEM) ---\n")
                ps_cmd = f'"{POWERSHELL}" -NoProfile -Command "(Get-CimInstance Win32_SoftwareLicensingService).OA3xOriginalProductKey"'
                out, _, _ = self.run_cmd(ps_cmd)
                f.write(out + "\n")
                f.write("\n--- CLAVE DE RESPALDO EN REGISTRO ---\n")
                ps_cmd2 = f'"{POWERSHELL}" -NoProfile -Command "Get-ItemPropertyValue -Path \'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SoftwareProtectionPlatform\' -Name BackupProductKeyDefault"'
                out2, _, _ = self.run_cmd(ps_cmd2)
                f.write(out2 + "\n")
                f.write("\n--- INFO OFFICE ---\n")
                office_paths = [
                    os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Microsoft Office', 'Office16', 'ospp.vbs'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Microsoft Office', 'Office16', 'ospp.vbs')
                ]
                found = False
                for p in office_paths:
                    if os.path.exists(p):
                        cmd_off = f'"{CSCRIPT}" //nologo "{p}" /dstatus'
                        out_off, _, _ = self.run_cmd(cmd_off)
                        f.write(out_off)
                        found = True
                        break
                if not found:
                    f.write("No se detectó instalación clásica de Office.\n")
            self.stop_progress()
            self.log(f"✅ Archivo '{filename}' generado.")
            self.open_notepad(filename)
        threading.Thread(target=task, daemon=True).start()

    # --------------------- 3. FICHADOR DE HARDWARE (CORREGIDO) ---------------------
    def hardware_info(self):
        def task():
            self.start_progress("💻 Recopilando hardware avanzado...")
            filename = "Ficha_Hardware_Reporte.txt"
            
            # Script PowerShell corregido (comillas y sintaxis)
            ps_script = """
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor
$ram = Get-CimInstance Win32_PhysicalMemory
$disks = Get-CimInstance Win32_DiskDrive
$gpu = Get-CimInstance Win32_VideoController | Where-Object {($_.Name -notlike '*Remote*') -and ($_.Name -notlike '*Mirror*')} | Select-Object -First 1
$net = Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object {$_.IPEnabled -eq $true}
$bios = Get-CimInstance Win32_BIOS

Write-Output '=== SISTEMA OPERATIVO ==='
Write-Output "Nombre: $($os.Caption)"
Write-Output "Versión: $($os.Version)  Build: $($os.BuildNumber)"
Write-Output "Arquitectura: $($os.OSArchitecture)"
Write-Output "Instalación: $($os.InstallDate)"
Write-Output "Directorio: $($os.SystemDirectory)"
Write-Output ''

Write-Output '=== EQUIPO ==='
Write-Output "Fabricante: $($cs.Manufacturer)"
Write-Output "Modelo: $($cs.Model)"
Write-Output "Nombre de equipo: $($cs.Name)"
Write-Output "Usuario: $($cs.UserName)"
Write-Output ''

Write-Output '=== PROCESADOR ==='
Write-Output "Nombre: $($cpu.Name)"
Write-Output "Núcleos: $($cpu.NumberOfCores)"
Write-Output "Hilos lógicos: $($cpu.NumberOfLogicalProcessors)"
Write-Output "Velocidad máxima: $([math]::Round($cpu.MaxClockSpeed/1000, 2)) GHz"
Write-Output ''

Write-Output '=== MEMORIA RAM ==='
$totalRAM = [math]::Round(($ram | Measure-Object Capacity -Sum).Sum / 1GB, 2)
Write-Output "Total RAM: $totalRAM GB"
Write-Output "Módulos instalados: $($ram.Count)"
$i = 1
foreach ($modulo in $ram) {
    Write-Output "  Slot $i : $([math]::Round($modulo.Capacity/1GB, 0)) GB  -  Velocidad: $($modulo.Speed) MHz"
    $i++
}
Write-Output ''

Write-Output '=== DISCOS (físicos) ==='
foreach ($disk in $disks) {
    $sizeGB = [math]::Round($disk.Size / 1GB, 0)
    Write-Output "Modelo: $($disk.Model)"
    Write-Output "  Tamaño: $sizeGB GB"
    Write-Output "  Tipo: $($disk.MediaType)"
    Write-Output "  Interface: $($disk.InterfaceType)"
    Write-Output ''
}

Write-Output '=== TARJETA GRÁFICA ==='
if ($gpu) {
    Write-Output "Nombre: $($gpu.Name)"
    $memGB = [math]::Round($gpu.AdapterRAM/1GB, 0)
    Write-Output "Memoria dedicada: $memGB GB"
    Write-Output "Resolución: $($gpu.CurrentHorizontalResolution) x $($gpu.CurrentVerticalResolution)"
} else {
    Write-Output "No se detectó GPU dedicada (o es integrada)"
}
Write-Output ''

Write-Output '=== RED (adaptadores activos) ==='
foreach ($adapter in $net) {
    Write-Output "Adaptador: $($adapter.Description)"
    Write-Output "  Dirección MAC: $($adapter.MACAddress)"
    Write-Output "  IP: $($adapter.IPAddress -join ', ')"
    Write-Output "  Máscara: $($adapter.IPSubnet -join ', ')"
    Write-Output "  Gateway: $($adapter.DefaultIPGateway -join ', ')"
    Write-Output "  DNS: $($adapter.DNSServerSearchOrder -join ', ')"
    Write-Output ''
}

Write-Output '=== BIOS ==='
Write-Output "Fabricante: $($bios.Manufacturer)"
Write-Output "Versión: $($bios.SMBIOSBIOSVersion)"
Write-Output "Fecha: $($bios.ReleaseDate)"
"""
            cmd = f'"{POWERSHELL}" -NoProfile -Command "{ps_script}"'
            result, err, rc = self.run_cmd(cmd)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("FICHA TÉCNICA DE HARDWARE - WARCLIB System Lab\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write(result)
                if err and rc != 0:
                    f.write(f"\n[ERROR] {err}")
            
            self.stop_progress()
            self.log(f"✅ Archivo '{filename}' generado con información completa.")
            self.open_notepad(filename)
        threading.Thread(target=task, daemon=True).start()

    # --------------------- 4. ESCÁNER DE RED ---------------------
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith('127.'):
                return ip
        except:
            pass
        try:
            cmd = f'"{IPCONFIG}"'
            out, _, _ = self.run_cmd(cmd)
            patterns = [
                r'IPv4[^\d]*(\d+\.\d+\.\d+\.\d+)',
                r'Direcci[óo]n IPv4[^\d]*(\d+\.\d+\.\d+\.\d+)',
                r'IP Address[^\d]*(\d+\.\d+\.\d+\.\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, out, re.IGNORECASE)
                if match:
                    ip = match.group(1)
                    if not ip.startswith('127.'):
                        return ip
        except:
            pass
        return None

    def _ping_host(self, ip):
        subprocess.run(f'"{PING}" -n 1 -w 15 {ip}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def network_scan(self):
        def task():
            self.start_progress("🌐 Escaneando red (puede tardar ~30s)...")
            local_ip = self.get_local_ip()
            if not local_ip:
                self.log("❌ No se pudo determinar la IP local. Verifica tu conexión de red.")
                self.stop_progress()
                return
            prefix = '.'.join(local_ip.split('.')[:3])
            self.log(f"📡 Red detectada: {prefix}.0/24 - IP local: {local_ip}")

            for i in range(1, 255):
                threading.Thread(target=self._ping_host, args=(f"{prefix}.{i}",), daemon=True).start()

            self.root.after(10000, lambda: self._finish_scan(prefix))
        threading.Thread(target=task, daemon=True).start()

    def _finish_scan(self, prefix):
        self.stop_progress()
        cmd_arp = f'"{ARP}" -a'
        arp_out, _, _ = self.run_cmd(cmd_arp)
        lines = arp_out.splitlines()
        filtered = [line for line in lines if prefix in line]
        filename = "Dispositivos_Red_Reporte.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("DISPOSITIVOS EN RED - WARCLIB System Lab\n")
            f.write("\n".join(filtered))
        self.log(f"✅ Escaneo completado. Archivo '{filename}' generado.")
        self.open_notepad(filename)

    # --------------------- 5. RESPALDO DE CONTROLADORES ---------------------
    def backup_drivers(self):
        def task():
            dest = os.path.join(os.getcwd(), "Respaldo_Drivers")
            self.start_progress(f"💾 Exportando drivers a {dest}...")
            if not os.path.exists(dest):
                os.makedirs(dest)
            cmd = f'"{DISM}" /online /export-driver /destination:"{dest}"'
            self.run_cmd(cmd, capture=False)
            self.stop_progress()
            self.log(f"✅ Controladores respaldados en {dest}")
            messagebox.showinfo("Éxito", f"Drivers exportados a:\n{dest}")
        threading.Thread(target=task, daemon=True).start()

    # --------------------- 6. PROGRAMAS DE INICIO ---------------------
    def startup_apps(self):
        def task():
            self.start_progress("📂 Leyendo programas de inicio...")
            filename = "Programas_Inicio_Reporte.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("PROGRAMAS DE INICIO - WARCLIB System Lab\n\n")
                for hive in ["HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"]:
                    cmd = f'"{REG}" query "{hive}" /s'
                    out, _, _ = self.run_cmd(cmd)
                    f.write(f"--- {hive} ---\n{out}\n\n")
            self.stop_progress()
            self.log(f"✅ Archivo '{filename}' generado.")
            self.open_notepad(filename)
        threading.Thread(target=task, daemon=True).start()

    # --------------------- 7. INMUNIZADOR ---------------------
    def immunize_system(self):
        if messagebox.askyesno("Confirmar", "¿Deshabilitar Windows Update y telemetría básica?\nPodrás reactivar después manualmente."):
            self.start_progress("🛡️ Inmunizando sistema...")
            self.run_cmd(f'"{SC}" stop wuauserv', capture=False)
            self.run_cmd(f'"{SC}" config wuauserv start= disabled', capture=False)
            reg_cmd = f'"{REG}" add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" /v "NoAutoUpdate" /t REG_DWORD /d 1 /f'
            self.run_cmd(reg_cmd, capture=False)
            self.stop_progress()
            self.log("✅ Sistema inmunizado. Windows Update deshabilitado.")
            messagebox.showinfo("Éxito", "Windows Update ha sido deshabilitado.\nPara reactivar: 'sc config wuauserv start= auto' y 'net start wuauserv' como admin.")
        else:
            self.log("⏸️ Inmunización cancelada.")

    # --------------------- 8. REPORTE DE BATERÍA ---------------------
    def battery_report(self):
        def task():
            self.start_progress("🔋 Generando reporte de batería...")
            filename = "Bateria_Salud_Reporte.html"
            cmd = f'"{POWERCFG}" /batteryreport /output "{filename}"'
            self.run_cmd(cmd, capture=False)
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                self.stop_progress()
                self.log(f"✅ Reporte generado: {filename}")
                webbrowser.open(filename)
            else:
                self.stop_progress()
                self.log("❌ No se detectó batería o no se pudo generar el informe.")
        threading.Thread(target=task, daemon=True).start()

# --------------------- MAIN ---------------------
if __name__ == "__main__":
    run_as_admin()
    root = Tk()
    app = WarclibSuite(root)
    root.mainloop()
