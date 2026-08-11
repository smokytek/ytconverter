from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config import AppConfig, ConfigStore
from downloader import AudioDownloader, DownloadEvent, DownloadResult, QUALITY_BITRATES
from ffmpeg_manager import find_ffmpeg


class YTConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ytconverter")
        self.geometry("720x590")
        self.minsize(640, 520)
        self.store = ConfigStore()
        self.config_data = self.store.load()
        self.events: queue.Queue[DownloadEvent] = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None
        self._build_style()
        self._build_ui()
        self.after(80, self._drain_events)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 20))
        style.configure("Muted.TLabel", foreground="#5f6368")
        style.configure("Primary.TButton", font=("Segoe UI Semibold", 10), padding=(16, 8))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ytconverter", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Scarica e converti una traccia audio in MP3.", style="Muted.TLabel").pack(anchor="w", pady=(2, 20))

        ttk.Label(outer, text="Indirizzo del video").pack(anchor="w")
        url_row = ttk.Frame(outer)
        url_row.pack(fill="x", pady=(5, 14))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_row, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(url_row, text="Incolla", command=self._paste).pack(side="left", padx=(8, 0))

        ttk.Label(outer, text="Cartella di destinazione").pack(anchor="w")
        folder_row = ttk.Frame(outer)
        folder_row.pack(fill="x", pady=(5, 14))
        self.folder_var = tk.StringVar(value=self.config_data.output_folder)
        ttk.Entry(folder_row, textvariable=self.folder_var).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Sfoglia…", command=self._browse).pack(side="left", padx=(8, 0))

        settings = ttk.Frame(outer)
        settings.pack(fill="x")
        ttk.Label(settings, text="Qualità").grid(row=0, column=0, sticky="w")
        self.quality_var = tk.StringVar(value=self.config_data.quality)
        ttk.Combobox(settings, textvariable=self.quality_var, values=list(QUALITY_BITRATES), state="readonly", width=23).grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.zip_var = tk.BooleanVar(value=self.config_data.create_zip)
        self.alt_var = tk.BooleanVar(value=self.config_data.allow_alternatives)
        ttk.Checkbutton(settings, text="Crea uno ZIP al termine", variable=self.zip_var).grid(row=1, column=1, sticky="w", padx=(28, 0))
        ttk.Checkbutton(settings, text="Prova un’alternativa se necessario", variable=self.alt_var).grid(row=2, column=1, sticky="w", padx=(28, 0), pady=(6, 0))

        ttk.Separator(outer).pack(fill="x", pady=20)
        self.status_var = tk.StringVar(value="Pronto")
        self.detail_var = tk.StringVar(value="Incolla un indirizzo per iniziare.")
        ttk.Label(outer, textvariable=self.status_var, font=("Segoe UI Semibold", 11)).pack(anchor="w")
        ttk.Label(outer, textvariable=self.detail_var, style="Muted.TLabel").pack(anchor="w", pady=(3, 8))
        self.progress = ttk.Progressbar(outer, maximum=100)
        self.progress.pack(fill="x")

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=14)
        self.start_button = ttk.Button(buttons, text="Scarica MP3", style="Primary.TButton", command=self._start)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(buttons, text="Annulla", state="disabled", command=self._cancel)
        self.cancel_button.pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Apri cartella", command=self._open_folder).pack(side="right")

        self.details_button = ttk.Button(outer, text="Mostra dettagli", command=self._toggle_details)
        self.details_button.pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(outer, height=8, font=("Consolas", 9), state="disabled")
        self.url_entry.focus_set()

    def _paste(self) -> None:
        try:
            self.url_var.set(self.clipboard_get().strip())
        except tk.TclError:
            pass

    def _browse(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.folder_var.get() or str(Path.home()))
        if selected:
            self.folder_var.set(selected)

    def _toggle_details(self) -> None:
        if self.log_area.winfo_manager():
            self.log_area.pack_forget()
            self.details_button.configure(text="Mostra dettagli")
        else:
            self.log_area.pack(fill="both", expand=True, pady=(8, 0))
            self.details_button.configure(text="Nascondi dettagli")

    def _append_log(self, message: str) -> None:
        self.log_area.configure(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _start(self) -> None:
        source = self.url_var.get().strip()
        folder_text = self.folder_var.get().strip()
        if not source:
            messagebox.showwarning("Indirizzo mancante", "Incolla l’indirizzo di un video.")
            return
        if not folder_text:
            messagebox.showwarning("Cartella mancante", "Scegli una cartella di destinazione.")
            return
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            messagebox.showerror("FFmpeg non trovato", "Inserisci ffmpeg.exe nella cartella dependencies accanto all’applicazione.")
            return

        destination = Path(folder_text).expanduser()
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Cartella non disponibile", str(exc))
            return

        self.config_data = AppConfig(self.zip_var.get(), self.alt_var.get(), self.quality_var.get(), str(destination))
        try:
            self.store.save(self.config_data)
        except OSError as exc:
            self._append_log(f"Impossibile salvare le preferenze: {exc}")

        self.cancel_event.clear()
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)
        self.status_var.set("Avvio in corso…")
        self.detail_var.set("")
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.worker = threading.Thread(
            target=self._run_download,
            args=(source, destination, ffmpeg, self.config_data),
            daemon=True,
        )
        self.worker.start()

    def _run_download(
        self, source: str, destination: Path, ffmpeg: Path, config: AppConfig
    ) -> None:
        before = set(destination.iterdir())
        downloader = AudioDownloader(ffmpeg, self.events.put)
        result = downloader.download(
            source,
            destination,
            config.quality,
            self.cancel_event,
            config.allow_alternatives,
        )
        created = set(destination.iterdir()) - before
        if result is DownloadResult.SUCCESS and config.create_zip and created:
            self.events.put(DownloadEvent("phase", "Creazione archivio ZIP…"))
            try:
                import zipfile
                archive = destination / "ytconverter_downloads.zip"
                with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
                    for path in created:
                        if path.is_file():
                            handle.write(path, path.name)
                self.events.put(DownloadEvent("log", f"Archivio creato: {archive.name}"))
            except OSError as exc:
                self.events.put(DownloadEvent("log", f"Impossibile creare lo ZIP: {exc}"))
        self.events.put(DownloadEvent("done", result.name))

    def _drain_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event.kind == "progress":
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    if event.percent is not None:
                        self.progress["value"] = event.percent
                    self.status_var.set(event.title or "Download in corso…")
                    bits = [part for part in (event.speed, f"ETA {event.eta}" if event.eta else "") if part]
                    self.detail_var.set(" · ".join(bits))
                elif event.kind == "phase":
                    self.status_var.set(event.message)
                    self.detail_var.set(event.title)
                    self.progress.configure(mode="indeterminate")
                    self.progress.start(12)
                elif event.kind == "log":
                    self._append_log(event.message)
                elif event.kind == "done":
                    self._finish(DownloadResult[event.message])
        except queue.Empty:
            pass
        self.after(80, self._drain_events)

    def _finish(self, result: DownloadResult) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        if result is DownloadResult.SUCCESS:
            self.progress["value"] = 100
            self.status_var.set("Download completato")
            self.detail_var.set("Il file MP3 è pronto nella cartella scelta.")
        elif result is DownloadResult.CANCELLED:
            self.progress["value"] = 0
            self.status_var.set("Download annullato")
            self.detail_var.set("Puoi avviare un nuovo download.")
        else:
            self.progress["value"] = 0
            self.status_var.set("Download non riuscito")
            self.detail_var.set("Apri i dettagli per maggiori informazioni.")
            messagebox.showerror("Download non riuscito", "Non è stato possibile completare il download.")

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.status_var.set("Annullamento in corso…")

    def _open_folder(self) -> None:
        folder = Path(self.folder_var.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(folder)
        except OSError as exc:
            messagebox.showerror("Cartella non disponibile", str(exc))

    def _close(self) -> None:
        self.cancel_event.set()
        self.destroy()


if __name__ == "__main__":
    YTConverterApp().mainloop()
