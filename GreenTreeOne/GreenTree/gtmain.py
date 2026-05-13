# MISSION: Create a file-type exploration tool.
# STATUS: Testing release.
# VERSION: 0.1.0
# NOTES: So far so good.
# DATE: 2026-05-12 17:26:52
# FILE: app.py
# AUTHOR: Randall Nagy
# MANUALLY UPDATED + RESTORED LOST FEATURES
#
import os, platform, subprocess, threading, json, webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
from collections import deque, Counter

class UltimateForestExplorer:
    def __init__(self, root):
        self.title = "GreenTree 9000"
        self.project_url = "https://www.soft9000.com"
        self.version = "2026/05/12"
        self.root = root
        self.root.title(self.title)
        self.root.geometry("1450x850")
        
        # Colors & Styles
        self.bg_color = "#228B22"  # Forest Green
        self.fg_color = "#FFFF00"  # Yellow
        self.alt_bg = "#1e7a1e"    # Darker Green for stripes
        self.root.configure(bg=self.bg_color)

        # Persistence Setup
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
        history = self.load_history()
        self.recent_dirs = deque(history.get("dirs", [os.getcwd()]), maxlen=5)
        self.recent_exts = deque(history.get("exts", [".txt", ".py"]), maxlen=5)
        self.current_path = self.recent_dirs[0] if self.recent_dirs else os.getcwd()
        
        self.master_file_list = [] 
        self.filter_after_id = None

        # --- THEME ENGINE ---
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background=self.bg_color, foreground=self.fg_color, 
                             fieldbackground=self.bg_color, rowheight=35, font=('Arial', 10))
        self.style.map("Treeview", background=[('selected', '#ffd700')], foreground=[('selected', 'black')])
        self.style.configure("Treeview.Heading", background="#004d00", foreground=self.fg_color, font=('Arial', 10, 'bold'))
        
        self.setup_menu()

        # --- 1. TOOLBAR ---
        self.toolbar = tk.Frame(root, bg="#004d00", bd=1, relief=tk.RAISED)
        self.toolbar.pack(side='top', fill='x', padx=5, pady=5)
        
        tk.Label(self.toolbar, text="Folders:", bg="#004d00", fg=self.fg_color).pack(side='left', padx=5)
        self.dir_combo = ttk.Combobox(self.toolbar, state="readonly", values=list(self.recent_dirs), width=35)
        self.dir_combo.pack(side='left', padx=5)
        self.dir_combo.set(self.current_path)
        self.dir_combo.bind("<<ComboboxSelected>>", self.on_lru_dir_select)
        tk.Button(self.toolbar, text="X", fg="red", bg="#004d00", command=self.remove_current_dir, bd=0).pack(side='left')

        tk.Label(self.toolbar, text=" | Types:", bg="#004d00", fg=self.fg_color).pack(side='left', padx=5)
        self.ext_combo = ttk.Combobox(self.toolbar, state="readonly", values=list(self.recent_exts), width=10)
        self.ext_combo.pack(side='left', padx=5)
        self.ext_combo.set(self.recent_exts[0] if self.recent_exts else "")
        self.ext_combo.bind("<<ComboboxSelected>>", self.on_lru_ext_select)
        tk.Button(self.toolbar, text="X", fg="red", bg="#004d00", command=self.remove_current_ext, bd=0).pack(side='left')

        tk.Button(self.toolbar, text="📊 Stat", command=self.show_file_stats, bg="#e1f5fe").pack(side='right', padx=10)

        tk.Button(self.toolbar, text="🔎 Hunt Dupes", command=self.hunt_duplicates, bg="#ffd700").pack(side='right', padx=5)

        # --- 2. SEARCH & FILTER ---
        self.ctrl_frame = tk.Frame(root, bg=self.bg_color)
        self.ctrl_frame.pack(pady=10, fill='x', padx=10)
        
        tk.Button(self.ctrl_frame, text="Folder...", command=self.change_directory).pack(side='left')
        self.entry = tk.Entry(self.ctrl_frame, width=10, bg="#004d00", fg=self.fg_color, insertbackground=self.fg_color)
        self.entry.pack(side='left', padx=10)
        self.entry.insert(0, self.ext_combo.get())
        
        self.btn_scan = tk.Button(self.ctrl_frame, text="START SCAN", bg="#ff4444", fg="white", 
                                  font=('Arial', 10, 'bold'), command=self.start_scan_thread, width=12)
        self.btn_scan.pack(side='left', padx=10)

        tk.Label(self.ctrl_frame, text="Subset:", bg=self.bg_color, fg=self.fg_color).pack(side='left', padx=10)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self.debounce_filter)
        self.filter_entry = tk.Entry(self.ctrl_frame, textvariable=self.filter_var, width=25, bg="#004d00", fg=self.fg_color, insertbackground=self.fg_color)
        self.filter_entry.pack(side='left', padx=5)

        self.progress = ttk.Progressbar(self.ctrl_frame, mode="indeterminate", length=150)
        self.progress.pack(side='right', padx=10)

        # --- 3. PANED VIEW & PREVIEW ---
        self.paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6, bg="#004d00")
        self.paned.pack(expand=True, fill='both', padx=10, pady=5)

        self.tree_frame = tk.Frame(self.paned)
        self.tree = ttk.Treeview(self.tree_frame, columns=("FileName", "Modified", "Path"), show='headings')
        self.tree.tag_configure('oddrow', background=self.alt_bg)
        self.tree.tag_configure('duplicate', background='#8b0000', foreground="white")
        for col in ("FileName", "Modified", "Path"):
            self.tree.heading(col, text=col, command=lambda _c=col: self.tree_sort_column(_c, False))
            self.tree.column(col, stretch=True)
        self.tree.pack(expand=True, fill='both')
        self.paned.add(self.tree_frame, width=900)

        self.preview_frame = tk.Frame(self.paned, bg=self.bg_color)
        tk.Button(self.preview_frame, text="Copy Path", command=self.copy_path, font=('Arial', 8)).pack(anchor='ne', pady=2)
        self.preview_text = tk.Text(self.preview_frame, bg="#002b00", fg=self.fg_color, font=('Consolas', 10), state='disabled', wrap='none')
        self.preview_text.pack(expand=True, fill='both')
        self.paned.add(self.preview_frame, width=500)

        # Bindings
        self.tree.bind("<<TreeviewSelect>>", self.update_preview)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Button-2>", self.show_context_menu)
        
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open File", command=self.on_double_click)
        self.context_menu.add_command(label="Open Folder", command=self.open_folder)
        self.context_menu.add_command(label="Rename", command=self.rename_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_file, foreground="red")

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor='w', bg="#004d00", fg=self.fg_color).pack(side='bottom', fill='x')


    def clear_all_history(self):
        if messagebox.askyesno("Clear", "Reset History?"):
            self.recent_dirs.clear(); self.recent_exts.clear()
            if os.path.exists(self.history_file): os.remove(self.history_file)
            self.update_lru_ui()

    # --- RESTORED STATS FEATURE ---
    def show_search_stats(self):
        ''' TODO: Unloved - Do we care? '''
        if not self.master_file_list:
            messagebox.showinfo("Stats", "No data to analyze. Run a scan first!")
            return
        
        win = tk.Toplevel(self.root); win.title("Full File.Stat Breakdown"); win.geometry("600x550"); win.configure(bg=self.bg_color)
        txt = tk.Text(win, bg="#002b00", fg=self.fg_color, font=('Consolas', 10), padx=15, pady=15)
        txt.pack(expand=True, fill='both')
        
        total_sz, exts, mtimes = 0, Counter(), []
        for n, mt_str, p in self.master_file_list:
            try:
                s = os.stat(p)
                total_sz += s.st_size
                mtimes.append(s.st_mtime)
                exts[os.path.splitext(n)[1].lower() or "none"] += 1
            except: continue

        def f_dt(ts): return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        
        res = [
            "--- AGGREGATE STATS ---",
            f"File Count:    {len(self.master_file_list)}",
            f"Total Size:    {total_sz/(1024*1024):.2f} MB",
            f"Average Size:  {(total_sz/len(self.master_file_list))/1024:.2f} KB",
            "\n--- TEMPORAL EXTREMES ---",
            f"Newest File:   {f_dt(max(mtimes)) if mtimes else 'N/A'}",
            f"Oldest File:   {f_dt(min(mtimes)) if mtimes else 'N/A'}",
            "\n--- EXTENSIONS ---"
        ]
        for e, c in exts.most_common(): res.append(f"{e:<12} : {c} files")
        
        txt.insert('1.0', "\n".join(res)); txt.config(state='disabled')


    # --- FILE STATS FEATURE ---
    def show_file_stats(self):
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024

        def get_date(zdate):
            return datetime.fromtimestamp(zdate).strftime('%Y-%m-%d %H:%M:%S')
            
        if not self.master_file_list:
            messagebox.showinfo("Stats", "No data to analyze. Run a scan first!")
            return

        isel = self.tree.selection()
        if not isel:
            messagebox.showinfo("Stats", "No file to analyze. Select 'ye a file?")
            return
        sel = self.tree.item(isel)
        
        win = tk.Toplevel(self.root); win.title("File Info."); win.geometry("600x400"); win.configure(bg=self.bg_color)
        txt = tk.Text(win, bg="#002b00", fg=self.fg_color, font=('Consolas', 18), padx=15, pady=15)
        txt.pack(expand=True, fill='both')
        
        total_sz, exts, mtimes = 0, Counter(), []
        try:
            zinfo = sel['values']
            zname = zinfo[0]
            zfile = zinfo[2]
            info = os.stat(zfile)
            res = [
                f"File: {zname}",
                f"Path: {zfile}",
                f"Size: {format_size(info.st_size)}",
                f"Permissions: {oct(info.st_mode)}",
                f"MTIME: {get_date(info.st_mtime)}",
                f"ATIME: {get_date(info.st_atime)}",
                f"CTIME: {get_date(info.st_ctime)}",
                f"Inode: {info.st_ino}",
                f"UID: {info.st_uid}",
                f"GID: {info.st_gid}",
                f"Hard Links: {info.st_nlink}"
            ]
            txt.insert('1.0', "\n".join(res)); txt.config(state='disabled')
        except Exception as ex:
            messagebox.showinfo("Yikes?", str(ex))
            return      


    # --- THE REST OF THE LOGIC ---
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f: return json.load(f)
            except: pass
        return {}

    def save_history(self, ext=None):
        if ext and ext.startswith('.') and len(ext) > 1:
            if ext in self.recent_exts: self.recent_exts.remove(ext)
            self.recent_exts.appendleft(ext)
        data = {"dirs": list(self.recent_dirs), "exts": list(self.recent_exts)}
        with open(self.history_file, 'w') as f: json.dump(data, f)
        self.dir_combo['values'] = list(self.recent_dirs); self.ext_combo['values'] = list(self.recent_exts)

    def hunt_duplicates(self):
        fingerprints, dups = {}, []
        for item in self.master_file_list:
            try:
                key = (item[0], os.path.getsize(item[2]))
                if key in fingerprints:
                    if fingerprints[key] not in dups: dups.append(fingerprints[key])
                    dups.append(item)
                else: fingerprints[key] = item
            except: continue
        self.tree.delete(*self.tree.get_children())
        for d in dups: self.tree.insert("", tk.END, values=d, tags=('duplicate',))
        self.status_var.set(f"Duplicates: Found {len(dups)} files.")

    def start_scan_thread(self):
        ext = self.entry.get().lower()
        if not ext: return
        self.save_history(ext)
        self.progress.start(10)
        self.btn_scan.config(text="SCANNING...", bg="#ffd700", fg="black", state="disabled")
        threading.Thread(target=self.perform_scan, args=(ext,), daemon=True).start()

    def perform_scan(self, ext):
        new_list = []
        try:
            for r, _, files in os.walk(self.current_path):
                for f in files:
                    if f.lower().endswith(ext):
                        fp = os.path.normpath(os.path.join(r, f))
                        mt = datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d %H:%M')
                        new_list.append((f, mt, fp))
            self.master_file_list = new_list
            self.root.after(0, self.apply_filter); self.root.after(0, self.scan_done_ui)
        except: self.root.after(0, self.reset_button)

    def scan_done_ui(self):
        self.progress.stop(); self.btn_scan.config(text="DONE!", bg="#00ff00", state="normal")
        self.root.after(2500, self.reset_button)

    def reset_button(self): self.btn_scan.config(text="START SCAN", bg="#ff4444", fg="white")

    def debounce_filter(self, *args):
        if self.filter_after_id: self.root.after_cancel(self.filter_after_id)
        self.filter_after_id = self.root.after(200, self.apply_filter)

    def apply_filter(self):
        zfilter = self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        count = 0
        for item in self.master_file_list:
            if not zfilter or any(zfilter in str(v).lower() for v in item):
                tag = 'oddrow' if count % 2 != 0 else 'evenrow'
                self.tree.insert("", tk.END, values=item, tags=(tag,))
                count += 1
        self.status_var.set(f"Set {count} of {len(self.master_file_list)} files")

    def update_preview(self, e):
        sel = self.tree.selection()
        if not sel: return
        p = self.tree.item(sel, "values")[2]
        self.preview_text.config(state='normal'); self.preview_text.delete('1.0', tk.END)
        try:
            with open(p, 'rb') as f: chunk = f.read(1024)
            if b'\x00' in chunk or any(b > 127 for b in chunk):
                dump = "\n".join([f"{i:08x}: {' '.join(f'{b:02x}' for b in chunk[i:i+16]):<48} |{''.join(chr(b) if 32<=b<=126 else '.' for b in chunk[i:i+16])}|" for i in range(0, len(chunk), 16)])
                self.preview_text.insert('1.0', dump)
            else: self.preview_text.insert('1.0', chunk.decode('utf-8', errors='ignore'))
        except: pass
        self.preview_text.config(state='disabled')

    def quit(self):
        import sys
        self.root.destroy()
        sys.exit()

    def setup_menu(self):
        m = tk.Menu(self.root)
        f_m = tk.Menu(m, tearoff=0)
        f_m.add_command(label="Clear History", command=self.clear_all_history)
        f_m.add_separator()
        f_m.add_command(label="Quit", command=self.quit)
        m.add_cascade(label="File", menu=f_m)
        h_m = tk.Menu(m, tearoff=0)
        h_m.add_command(label="Visit Project", command=lambda: webbrowser.open(self.project_url))
        h_m.add_command(label="About", command=lambda: messagebox.showinfo(self.title, f"Rev. {self.version}"))
        m.add_cascade(label="Help", menu=h_m)
        self.root.config(menu=m)

    def on_lru_dir_select(self, e): self.current_path = self.dir_combo.get(); self.start_scan_thread()
    def on_lru_ext_select(self, e): self.entry.delete(0, tk.END); self.entry.insert(0, self.ext_combo.get()); self.start_scan_thread()
    def remove_current_dir(self):
        if self.dir_combo.get() in self.recent_dirs: self.recent_dirs.remove(self.dir_combo.get()); self.save_history()
    def remove_current_ext(self):
        if self.ext_combo.get() in self.recent_exts: self.recent_exts.remove(self.ext_combo.get()); self.save_history()
    def change_directory(self):
        p = filedialog.askdirectory(initialdir=self.current_path)
        if p:
            if p in self.recent_dirs: self.recent_dirs.remove(p)
            self.recent_dirs.appendleft(p); self.current_path = p; self.save_history(); self.dir_combo.set(p)

    def rename_file(self):
        sel = self.tree.selection()
        if not sel: return
        n, mt, p = self.tree.item(sel, "values")
        nn = simpledialog.askstring("Rename", "New Name:", initialvalue=n)
        if nn: 
            np = os.path.join(os.path.dirname(p), nn)
            os.rename(p, np); self.tree.item(sel, values=(nn, mt, np))

    def delete_file(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Confirm", "Delete File?"):
            os.remove(self.tree.item(sel, "values")[2]); self.tree.delete(sel)

    def open_folder(self):
        sel = self.tree.selection()
        if sel:
            p = os.path.dirname(self.tree.item(sel, "values")[2])
            if platform.system() == 'Windows': subprocess.run(['explorer', p])
            else: subprocess.run(['open' if platform.system() == 'Darwin' else 'xdg-open', p])

    def on_double_click(self, e=None):
        sel = self.tree.selection()
        if sel:
            p = self.tree.item(sel, "values")[2]
            if platform.system() == 'Windows': os.startfile(p)
            else: subprocess.call(['open' if platform.system() == 'Darwin' else 'xdg-open', p])

    def show_context_menu(self, e):
        row = self.tree.identify_row(e.y)
        if row: self.tree.selection_set(row); self.context_menu.post(e.x_root, e.y_root)

    def copy_path(self):
        sel = self.tree.selection()
        if sel: self.root.clipboard_clear(); self.root.clipboard_append(self.tree.item(sel, "values")[2])

    def tree_sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)
        for i, (v, k) in enumerate(l):
            self.tree.move(k, '', i); self.tree.item(k, tags=('oddrow' if i % 2 != 0 else 'evenrow',))
        self.tree.heading(col, command=lambda: self.tree_sort_column(col, not reverse))


def main():
    root = tk.Tk()
    app = UltimateForestExplorer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    
