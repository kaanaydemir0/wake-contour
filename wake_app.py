"""Small Turkish desktop UI for reusable wake-table contour plotting."""

from __future__ import annotations

import json
from pathlib import Path
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from wake_plot import draw_contour, parse_table, read_table, table_text
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

FIELDS = {"Hız oranı  Vx/Vs": "velocity", "İz katsayısı  w = 1 − Vx/Vs": "wake"}
GUIDE_PATH = Path(__file__).resolve().with_name("KULLANIM.md")
ICON_PATH = Path(__file__).resolve().parent / "assets" / "wake_contour.ico"


def read_help_sections() -> list[tuple[str, str]]:
    """Use the local guide as the single source for the in-app help tabs."""
    content = GUIDE_PATH.read_text(encoding="utf-8")
    parts = re.split(r"^## (.+)$", content, flags=re.MULTILINE)
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts), 2)]


class WakeApp:
    def __init__(self, root: tk.Tk, initial_path: Path | None = None):
        self.root = root
        root.title("Wake Contour · İz Alanı")
        if ICON_PATH.is_file():
            root.iconbitmap(default=str(ICON_PATH))
        width = min(1320, max(960, root.winfo_screenwidth() - 80))
        height = min(820, max(640, root.winfo_screenheight() - 100))
        root.geometry(f"{width}x{height}")
        root.minsize(960, 640)
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        self.field = tk.StringVar(value=next(iter(FIELDS)))
        self.mirror = tk.BooleanVar(value=False)
        self.show_points = tk.BooleanVar(value=True)
        self.bands = tk.StringVar(value="10")
        self.status = tk.StringVar(value="Hazır")
        self.last_plot = None
        self.saved_text = ""
        self.dirty = False
        self.help_window = None

        menu = tk.Menu(root)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="Kurulum ve kullanım kılavuzu", accelerator="F1", command=self.open_help)
        menu.add_cascade(label="Yardım", menu=help_menu)
        root.configure(menu=menu)
        self.menu = menu
        root.bind("<F1>", lambda _event: self.open_help())

        heading = ttk.Frame(root, padding=(18, 12))
        heading.pack(fill="x")
        ttk.Label(heading, text="Pervane düzleminde iz alanı", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(heading, text="Tabloyu yükle veya yapıştır → grafiği çiz → dışa aktar").pack(anchor="w", pady=(3, 0))
        ttk.Label(root, textvariable=self.status, relief="sunken", padding=(10, 6),
                  wraplength=1250).pack(side="bottom", fill="x", pady=(6, 0))
        panes = ttk.Panedwindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=14)
        left = ttk.Frame(panes, padding=(3, 5, 12, 5))
        right = ttk.Frame(panes)
        panes.add(left, weight=2)
        panes.add(right, weight=3)

        buttons = ttk.Frame(left)
        buttons.pack(fill="x")
        for label, command in (("CSV / TSV aç", self.open_file), ("CSV kaydet", self.save_table)):
            ttk.Button(buttons, text=label, command=command).pack(side="left", padx=(0, 5))
        ttk.Label(left, text="Girdi her zaman Vx/Vs hız oranıdır; açılar derecedir.",
                  wraplength=440).pack(anchor="w", pady=(12, 5))
        ttk.Label(left, text="İlk satır: angle_deg ve r/R değerleri. Sonraki satırlar: açı ve hız oranları.\n"
                  "Excel'den başlıklarla birlikte kopyalayıp Ctrl+V ile yapıştırabilirsiniz.",
                  wraplength=440).pack(anchor="w", pady=(0, 7))
        editor_frame = ttk.Frame(left)
        editor_frame.pack(fill="both", expand=True)
        self.editor = tk.Text(editor_frame, wrap="none", undo=True, width=50, height=10,
                              font=("Consolas", 10), background="#f8fafc", foreground="#172333")
        vertical = ttk.Scrollbar(editor_frame, orient="vertical", command=self.editor.yview)
        horizontal = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.editor.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        editor_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(0, weight=1)
        self.editor.bind("<<Modified>>", self.on_edit)
        self.editor.bind("<Control-a>", self.select_all)

        settings = ttk.LabelFrame(left, text="Grafik ayarları", padding=10)
        settings.pack(fill="x", pady=(12, 7))
        field_box = ttk.Combobox(settings, textvariable=self.field, values=list(FIELDS), state="readonly", width=32)
        field_box.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        field_box.bind("<<ComboboxSelected>>", lambda _event: self.mark_stale())
        ttk.Checkbutton(settings, text="Tam disk: 0–180° verisini simetriyle aynala",
                        variable=self.mirror, command=self.mark_stale).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(settings, text="Verilen / aynalanan noktaları göster", variable=self.show_points,
                        command=self.mark_stale).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Label(settings, text="Hedef renk bandı sayısı:").grid(row=3, column=0, sticky="w")
        band_box = ttk.Combobox(settings, textvariable=self.bands, values=[6, 8, 10, 12, 16, 20], width=6, state="readonly")
        band_box.grid(row=3, column=1, sticky="w")
        band_box.bind("<<ComboboxSelected>>", lambda _event: self.mark_stale())
        settings.columnconfigure(0, weight=1)
        actions = ttk.Frame(left)
        actions.pack(fill="x", pady=5)
        ttk.Button(actions, text="Grafiği çiz / güncelle", command=self.plot).pack(side="left", fill="x", expand=True)
        ttk.Button(actions, text="PNG / SVG kaydet", command=self.export_plot).pack(side="left", padx=(8, 0))
        ttk.Label(left, text="Veri dışına ekstrapolasyon yapılmaz. Simetri bir varsayımdır.\n"
                  "Kurulum ve kullanım: Yardım menüsü veya F1.", wraplength=440,
                  foreground="#475569").pack(anchor="w", pady=(8, 3))

        self.figure = Figure(figsize=(8.5, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=right)
        toolbar = NavigationToolbar2Tk(self.canvas, right, pack_toolbar=False)
        toolbar.pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)
        if initial_path is not None:
            self.replace_table(initial_path)
        else:
            self.show_empty_plot()

    def show_empty_plot(self):
        self.figure.clear()
        self.figure.set_facecolor("#ffffff")
        self.figure.text(0.5, 0.57, "Tablonuzu yükleyin veya yapıştırın", ha="center",
                         va="center", fontsize=17, fontweight="bold", color="#172333")
        self.figure.text(0.5, 0.48, "CSV / TSV aç → Grafik ayarları → Grafiği çiz", ha="center",
                         fontsize=11, color="#475569")
        self.figure.text(0.5, 0.39, "İlk kullanım için Yardım menüsünü açın veya F1'e basın.",
                         ha="center", fontsize=10, color="#64748b")
        self.canvas.draw()
        self.status.set("Başlamak için CSV / TSV açın veya tabloyu sol alana yapıştırın. Yardım: F1.")

    def open_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.deiconify()
            self.help_window.lift()
            self.help_window.focus_set()
            return
        try:
            sections = read_help_sections()
            if not sections:
                raise ValueError("Kılavuz içeriği boş.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Kılavuz açılamadı", f"KULLANIM.md dosyasını program klasöründe tutun.\n{exc}",
                                 parent=self.root)
            return
        window = tk.Toplevel(self.root)
        self.help_window = window
        window.title("Yardım · Kurulum ve kullanım")
        window.geometry(f"{min(900, self.root.winfo_screenwidth() - 100)}x"
                        f"{min(700, self.root.winfo_screenheight() - 120)}")
        window.minsize(640, 480)
        window.transient(self.root)
        ttk.Label(window, text="Kurulum ve kullanım kılavuzu", font=("Segoe UI", 16, "bold"),
                  padding=(16, 12)).pack(anchor="w")
        footer = ttk.Frame(window, padding=(14, 8))
        footer.pack(side="bottom", fill="x")
        ttk.Label(footer, text="Çevrimdışı kullanılabilir · Metin seçilip Ctrl+C ile kopyalanabilir.").pack(side="left")
        ttk.Button(footer, text="Kapat", command=window.destroy).pack(side="right")
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=14, pady=(0, 5))
        for title, body in sections:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=title)
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side="right", fill="y")
            text = tk.Text(frame, wrap="word", font=("Segoe UI", 11), padx=18, pady=14,
                           relief="flat", background="#ffffff", foreground="#172333",
                           yscrollcommand=scrollbar.set, spacing3=5)
            text.pack(fill="both", expand=True)
            scrollbar.configure(command=text.yview)
            text.tag_configure("heading", font=("Segoe UI", 12, "bold"), spacing1=10, spacing3=8)
            text.tag_configure("code", font=("Consolas", 10), background="#f1f5f9", spacing3=0)
            in_code = False
            for line in body.splitlines():
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if line.startswith("### ") and not in_code:
                    text.insert("end", line[4:] + "\n", "heading")
                else:
                    text.insert("end", line + "\n", "code" if in_code else ())
            text.configure(state="disabled")
        window.bind("<Escape>", lambda _event: window.destroy())

    def select_all(self, _event):
        self.editor.tag_add("sel", "1.0", "end-1c")
        return "break"

    def on_edit(self, _event=None):
        if self.editor.edit_modified():
            self.dirty = self.editor.get("1.0", "end-1c") != self.saved_text
            self.editor.edit_modified(False)
            self.mark_stale()

    def mark_stale(self):
        self.status.set("Girdi veya ayarlar değişti. Grafiği çiz / güncelle düğmesine basın.")

    def confirm_replace(self) -> bool:
        return not self.dirty or messagebox.askyesno(
            "Kaydedilmemiş tablo", "Tablodaki kaydedilmemiş değişiklikler silinsin mi?", parent=self.root
        )

    def replace_table(self, path: Path):
        try:
            table = read_table(path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Tablo okunamadı", str(exc), parent=self.root)
            return
        self.saved_text = table_text(table, delimiter="\t").rstrip("\n")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self.saved_text)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.dirty = False
        self.mirror.set(False)
        self.plot()

    def open_file(self):
        if not self.confirm_replace():
            return
        path = filedialog.askopenfilename(parent=self.root, filetypes=[
            ("Hız oranı tabloları", "*.csv *.tsv *.txt"), ("Tüm dosyalar", "*.*")
        ])
        if path:
            self.replace_table(Path(path))

    def get_table(self):
        return parse_table(self.editor.get("1.0", "end-1c"))

    def save_table(self):
        try:
            table = self.get_table()
        except ValueError as exc:
            messagebox.showerror("Geçersiz tablo", str(exc), parent=self.root)
            return
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv",
                                          initialfile="wake_table.csv", filetypes=[("CSV", "*.csv")])
        if path:
            try:
                Path(path).write_text(table_text(table), encoding="utf-8-sig")
            except OSError as exc:
                messagebox.showerror("Kaydetme hatası", str(exc), parent=self.root)
                return
            self.saved_text = self.editor.get("1.0", "end-1c")
            self.dirty = False
            self.status.set(f"Tablo kaydedildi: {path}")

    def plot(self) -> bool:
        try:
            table = self.get_table()
            options = dict(field=FIELDS[self.field.get()], mirror=self.mirror.get(),
                           show_points=self.show_points.get(), bands=int(self.bands.get()))
            draw_contour(self.figure, table, **options)
            self.canvas.draw()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Grafik çizilemedi", str(exc), parent=self.root)
            return False
        self.last_plot = (table, options)
        q = table.velocity_ratio
        note = " | Tam disk: simetri varsayımı" if options["mirror"] else ""
        self.status.set(f"{q.shape[0]} açı × {q.shape[1]} yarıçap = {q.size} girdi | "
                        f"Vx/Vs: {q.min():.3f} … {q.max():.3f} | "
                        f"r/R: {table.radii_ratio[0]:g} … {table.radii_ratio[-1]:g}" + note)
        return True

    def export_plot(self):
        # Always redraw from the current editor/settings to avoid stale exports.
        if not self.plot():
            return
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".png",
                                          initialfile="wake_contour.png", filetypes=[
                                              ("PNG · 300 dpi", "*.png"), ("SVG · vektörel", "*.svg")])
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() not in (".png", ".svg"):
            messagebox.showerror("Dosya türü", "PNG veya SVG uzantısı kullanın.", parent=self.root)
            return
        table, options = self.last_plot
        try:
            # Stable export dimensions independent of the window size.
            export_figure = Figure(figsize=(8.5, 8), dpi=100)
            draw_contour(export_figure, table, **options)
            export_figure.savefig(target, dpi=300, facecolor="white")
            metadata = {"input_quantity": "Vx/Vs", "angle_unit": "degree",
                        "angle_convention": "0 up, 90 right", "interpolation": "linear in r/R and angle",
                        **options}
            target.with_suffix(".settings.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            target.with_suffix(".input.csv").write_text(table_text(table), encoding="utf-8-sig")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Dışa aktarma hatası", str(exc), parent=self.root)
            return
        self.status.set(f"Grafik, girdi CSV'si ve ayarlar kaydedildi: {target}")

    def close(self):
        if self.confirm_replace():
            self.root.destroy()


def run(initial_path: Path | None = None):
    root = tk.Tk()
    WakeApp(root, initial_path)
    root.mainloop()


if __name__ == "__main__":
    run()

