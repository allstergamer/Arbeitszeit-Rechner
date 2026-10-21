"""Tkinter-GUI für den Arbeitszeitrechner
benötigt nur Python-Standardbibliothek."""
from datetime import date, datetime, timedelta
import calendar
from logging import root
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from turtle import save
from arbeitszeit_core import ArbeitszeitDaten, WOCHENTAGE, fmt_minutes, parse_date, parse_duration, parse_time
import os
import sys
import subprocess

APP_TITLE = "Arbeitszeitrechner"

# Alle möglichen Uhrzeiten in 5-Minuten-Schritten.
UHRZEITEN = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 5)]
# Sollzeiten können bis zu 24 Stunden lang sein.
DAUERWERTE = [f"{h:02d}:{m:02d}" for h in range(25) for m in range(0, 60, 5) if h < 24 or m == 0]
PAUSENWERTE = [str(minuten) for minuten in range(0, 181, 5)]
MONATSNAMEN = ["Januar", "Februar", "März", "April", "Mai", "Juni",
               "Juli", "August", "September", "Oktober", "November", "Dezember"]


def resource_path(relative_path):
    """Findet Dateien sowohl im Python-Code als auch in der PyInstaller-EXE."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class KalenderPopup(tk.Toplevel):
    # Kleiner Kalender ohne zusätzliche Bibliotheken.
    def __init__(self, parent, startwert, callback):
        super().__init__(parent)
        self.callback = callback
        try:
            self.aktuelles_datum = parse_date(startwert)
        except ValueError:
            self.aktuelles_datum = date.today()
        self.jahr = self.aktuelles_datum.year
        self.monat = self.aktuelles_datum.month
        self.title("Datum auswählen")
        self.farben = parent.colors
        self.configure(bg=self.farben["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.anzeigen()

    def anzeigen(self):
        # Alte Kalenderbuttons entfernen und den Monat neu aufbauen.
        for widget in self.winfo_children():
            widget.destroy()
        kopf = ttk.Frame(self, padding=8)
        kopf.pack(fill="x")
        ttk.Button(kopf, text="‹", width=3, command=self.vorheriger_monat).pack(side="left")
        ttk.Label(kopf, text=f"{MONATSNAMEN[self.monat - 1]} {self.jahr}", width=18, anchor="center").pack(side="left", padx=5)
        ttk.Button(kopf, text="›", width=3, command=self.naechster_monat).pack(side="left")
        tage = ttk.Frame(self, padding=(8, 0, 8, 8))
        tage.pack()
        for spalte, name in enumerate(("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")):
            ttk.Label(tage, text=name, width=4, anchor="center").grid(row=0, column=spalte, pady=4)
        for woche_nr, woche in enumerate(calendar.monthcalendar(self.jahr, self.monat), start=1):
            for spalte, tag in enumerate(woche):
                if tag == 0:
                    continue
                ttk.Button(tage, text=str(tag), width=3,
                           command=lambda t=tag: self.datum_waehlen(t)).grid(
                               row=woche_nr, column=spalte, padx=1, pady=1)
        ttk.Button(self, text="Heute", command=lambda: self.datum_waehlen(date.today().day, heute=True)).pack(pady=(0, 8))

    def vorheriger_monat(self):
        if self.monat == 1:
            self.monat, self.jahr = 12, self.jahr - 1
        else:
            self.monat -= 1
        self.anzeigen()

    def naechster_monat(self):
        if self.monat == 12:
            self.monat, self.jahr = 1, self.jahr + 1
        else:
            self.monat += 1
        self.anzeigen()

    def datum_waehlen(self, tag, heute=False):
        ausgewaehlt = date.today() if heute else date(self.jahr, self.monat, tag)
        self.callback(ausgewaehlt.strftime("%d.%m.%Y"))
        self.destroy()

class ArbeitszeitGUI(tk.Tk):
    # Startet das Fenster und baut die Navigation auf.
    
    def __init__(self):
        super().__init__()
        self.daten = ArbeitszeitDaten()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(940, 620)
        self.configure(bg="#f3f5f7")
        self.current_page = "Dashboard"
        self.edit_date = None
        self.sort_column = "date"
        self.sort_reverse = True
        self._setup_style()
        self._build_shell()
        self.show_page("Dashboard")
        self.iconphoto(True, tk.PhotoImage(file=resource_path("icon.png")))
    # Legt Farben, Schriftarten und das Aussehen der Tabellen fest.

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        appearance = self.daten.einstellungen.get("appearance", "Dunkel")
        if appearance == "Dunkel":
            bg, panel, fg, accent = "#2b3038", "#2b3038", "#edf0f5", "#5b9cff"
        else:
            bg, panel, fg, accent = "#f3f5f7", "#f3f5f7", "#202632", "#1769d2"

        self.colors = {
            "bg": bg,
            "panel": panel,
            "fg": fg,
            "muted": "#7b8493",
            "accent": accent,
            "line": "#7b8493",
        }

        self.configure(bg=bg)

        # Frames und Labels
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("TableBorder.TFrame", background="#7b8493")
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), background=bg, foreground=fg)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), background=bg, foreground=self.colors["muted"])
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10), background=panel, foreground=self.colors["muted"])
        style.configure("CardValue.TLabel", font=("Segoe UI", 20, "bold"), background=panel, foreground=fg)


        # Normale Buttons
        style.configure("TButton", background=panel, foreground=fg, font=("Segoe UI", 10), padding=(14, 9), borderwidth=1, relief="flat", bordercolor="#7b8493", focusthickness=0)
        style.map("TButton", background=[("pressed", accent), ("active", "#e1e9f5" if appearance != "Dunkel" else "#3a4658")], foreground=[("disabled", self.colors["muted"])], bordercolor=[("focus", accent), ("active", accent)])

        # Primäre Aktionsbuttons, z. B. Speichern und Neuer Eintrag
        style.configure("Accent.TButton", background=accent, foreground="#ffffff", font=("Segoe UI", 10, "bold"), padding=(15, 9), borderwidth=0, relief="flat", focusthickness=0)
        style.map("Accent.TButton", background=[("pressed", "#1554a8" if appearance != "Dunkel" else "#397bd4"), ("active", "#347fe0" if appearance != "Dunkel" else "#76adff"), ("disabled", panel)], foreground=[("disabled", self.colors["muted"])])

        # Dropdowns
        style.configure("TCombobox", fieldbackground=panel, background=panel, foreground=fg, arrowcolor=fg, padding=(9, 8), borderwidth=1, relief="flat", bordercolor="#7b8493")
        style.map("TCombobox", fieldbackground=[("readonly", panel), ("disabled", bg)], foreground=[("readonly", fg), ("disabled", self.colors["muted"])], bordercolor=[("focus", accent), ("active", accent)], arrowcolor=[("disabled", self.colors["muted"])])

        # Eingabefelder
        style.configure("TEntry", fieldbackground=panel, foreground=fg, insertcolor=fg, padding=(9, 8), borderwidth=1, relief="flat", bordercolor="#7b8493")
        style.map("TEntry", bordercolor=[("focus", accent)], fieldbackground=[("disabled", bg)], foreground=[("disabled", self.colors["muted"])])
        style.configure("Custom.TCheckbutton", background=panel, foreground=fg, font=("Segoe UI", 10), padding=(2, 4))
        style.map("Custom.TCheckbutton", background=[("active", panel)], foreground=[("disabled", self.colors["muted"])])


        # Tabellen: Außenrahmen im Dashboard entfernen
        style.configure("Dashboard.Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=24, borderwidth=0, relief="flat")

        # Das Clam-Theme zeichnet den Rahmen über Treeview.field.
        # Durch dieses Layout wird das rahmenzeichnende Element umgangen.
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.map("Dashboard.Treeview", background=[("selected", accent)], foreground=[("selected", "#ffffff")])

        # Tabellen
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=24, borderwidth=0, relief="flat")
        style.configure("Treeview.Heading", background=panel, foreground=fg, relief="raised", borderwidth=1)
        style.map("Treeview", background=[("selected", accent)], foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", panel), ("pressed", panel)], foreground=[("active", fg), ("pressed", fg)])




    # Erstellt die feste Seitenleiste und den Bereich für die Seiten.
    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg="#202a38", width=205)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="◷  Arbeitszeit", bg="#202a38", fg="white", font=("Segoe UI", 16, "bold"), anchor="w", padx=18, pady=25).pack(fill="x")
        tk.Frame(self.sidebar, bg="#3b4656", height=1).pack(fill="x", padx=15, pady=(0, 12))
        for label, glyph in [("Dashboard", "⌂"), ("Eintrag erfassen", "+"), ("Einträge", "☷"), ("Auswertungen", "▥"), ("Einstellungen", "⚙")]:
            b = tk.Button(self.sidebar, text=f"{glyph}   {label}", anchor="w", padx=18, pady=12, bd=0,
                          bg="#202a38", fg="#e7edf5", activebackground="#33465f", activeforeground="white",
                          font=("Segoe UI", 10), command=lambda page=label: self.show_page(page), cursor="hand2")
            b.pack(fill="x", padx=8, pady=2)
        tk.Label(self.sidebar, text="Copyright © 2026 \nAllster / Lisa", bg="#202a38", fg="#aab6c6", font=("Segoe UI", 9), justify="left", padx=18).pack(side="bottom", anchor="w", pady=20)
        # Die rechte Inhaltsfläche ist scrollbar, damit auch kleine Fenster reichen.
        self.inhaltsbereich = tk.Frame(self, bg=self.colors["bg"])
        self.inhaltsbereich.pack(side="left", fill="both", expand=True)

        # Fester Bereich für die Seitenüberschrift
        self.header_container = tk.Frame(
            self.inhaltsbereich, bg=self.colors["bg"]
        )
        self.header_container.pack(side="top", fill="x")

        # Nur der eigentliche Seiteninhalt ist scrollbar
        self.scrollbereich = tk.Frame(
            self.inhaltsbereich, bg=self.colors["bg"]
        )
        self.scrollbereich.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.scrollbereich,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.scrollbereich,
            orient="vertical",
            command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.main = tk.Frame(self.canvas, bg=self.colors["bg"])
        self.main_fenster = self.canvas.create_window(
            (0, 0), window=self.main, anchor="nw"
        )

        self.main.bind("<Configure>", self._scrollbereich_aktualisieren)
        self.canvas.bind("<Configure>", self._inhaltsbreite_anpassen)
        self.canvas.bind_all("<MouseWheel>", self._mausrad_scrollen)


    def _scrollbereich_aktualisieren(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.after_idle(self._scrollposition_pruefen)


    def _scrollposition_pruefen(self):
        bbox = self.canvas.bbox(self.main_fenster)
        if not bbox:
            return

        inhaltshoehe = bbox[3] - bbox[1]
        sichtbare_hoehe = self.canvas.winfo_height()

        if inhaltshoehe <= sichtbare_hoehe:
            # Inhalt passt vollständig ins Fenster: kein Scrollen nötig.
            self.canvas.yview_moveto(0)
        else:
            # Scrollposition innerhalb der gültigen Grenzen halten.
            self.canvas.yview()


    def _inhaltsbreite_anpassen(self, event):
        # Der Inhalt bleibt so breit wie der sichtbare Bereich.
        self.canvas.itemconfigure(self.main_fenster, width=event.width)

    
   
    def _mausrad_scrollen(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)

        if widget is None:
            return

        # Prüfen, ob sich der Mauszeiger über einem Eingabefeld befindet.
        aktuelles_widget = widget
        while aktuelles_widget is not None:
            if isinstance(aktuelles_widget, (tk.Entry, ttk.Entry, tk.Spinbox, ttk.Spinbox)):
                # Das Mausrad-Ereignis dem Eingabefeld überlassen.
                # Der Seiteninhalt darf dabei nicht mitscrollen.
                return

            parent_name = aktuelles_widget.winfo_parent()
            if not parent_name:
                break

            try:
                aktuelles_widget = aktuelles_widget.nametowidget(parent_name)
            except KeyError:
                break

        # Nur innerhalb des scrollbaren Inhalts scrollen.
        if not str(widget).startswith(str(self.main)):
            return

        bbox = self.canvas.bbox(self.main_fenster)
        if not bbox:
            return

        inhaltshoehe = bbox[3] - bbox[1]
        sichtbare_hoehe = self.canvas.winfo_height()

        if inhaltshoehe > sichtbare_hoehe:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")


    # Entfernt die alte Seite, bevor eine neue angezeigt wird.
    def _clear(self):
        for widget in self.main.winfo_children():
            widget.destroy()

        for widget in self.header_container.winfo_children():
            widget.destroy()

    # Zeigt oben auf jeder Seite eine Überschrift an.
    def _header(self, title, subtitle=""):
        for widget in self.header_container.winfo_children():
            widget.destroy()

        head = ttk.Frame(self.header_container)
        head.pack(fill="x", padx=28, pady=(24, 18))

        ttk.Label(head, text=title, style="Title.TLabel").pack(anchor="w")

        if subtitle:
            ttk.Label(head, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

    # Erstellt einen einheitlich gestalteten Inhaltsbereich.
    def _panel(self, parent, padding=16):
        return ttk.Frame(parent, style="Panel.TFrame", padding=padding)

    # Erstellt eine kleine Kennzahlen-Karte für das Dashboard.
    def _card(self, parent, label, value, note=""):
        frame = self._panel(parent, 16)
        ttk.Label(frame, text=label, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(frame, text=value, style="CardValue.TLabel").pack(anchor="w", pady=(7, 2))
        if note:
            tk.Label(frame, text=note, bg=self.colors["panel"], fg=self.colors["muted"], font=("Segoe UI", 9), anchor="w"
            ).pack(anchor="w")
        return frame

    # Liefert alle Einträge aus der Kalenderwoche eines Datums.
    def _week_entries(self, today=None):
        today = today or date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return [e for e in self.daten.eintraege.values() if monday.isoformat() <= e["date"] <= sunday.isoformat()]

    # Liefert alle Einträge aus dem Monat eines Datums.
    def _month_entries(self, today=None):
        today = today or date.today()
        prefix = today.strftime("%Y-%m-")
        return [e for e in self.daten.eintraege.values() if e["date"].startswith(prefix)]

    # Wechselt zwischen Dashboard, Formular, Liste, Berichten und Einstellungen.
    def show_page(self, page):
        self.current_page = page
        self._clear()
        {"Dashboard": self.page_dashboard, "Eintrag erfassen": self.page_form, "Einträge": self.page_entries,
        "Auswertungen": self.page_reports, "Einstellungen": self.page_settings}[page]()

        # Beim Wechsel der Seite immer ganz nach oben scrollen.
        self.after_idle(lambda: self.canvas.yview_moveto(0))

    # Übersicht mit den wichtigsten Zeiten und Schnellzugriffen.
    def page_dashboard(self):
        today = date.today()
        today_entry = self.daten.eintraege.get(today.isoformat())
        week = self._week_entries(today)
        month = self._month_entries(today)
        self._header("Dashboard", today.strftime("%A, %d. %B %Y"))
        cards = ttk.Frame(self.main)
        cards.pack(fill="x", padx=28)
        vals = [("Heute", fmt_minutes(today_entry["worked"]) if today_entry else "—", "Nettoarbeitszeit"),
                ("Diese Woche", fmt_minutes(sum(e["worked"] for e in week)), f"Soll {fmt_minutes(self.daten.einstellungen['wochen_soll'])}"),
                ("Zeitkonto", fmt_minutes(sum(e["diff"] for e in self.daten.eintraege.values()), True), "Gesamte Differenz"),
                ("Dieser Monat", fmt_minutes(sum(e["worked"] for e in month)), f"{len(month)} Einträge")]
        for i, (label, value, note) in enumerate(vals):
            c = self._card(cards, label, value, note)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0), pady=0)
            cards.columnconfigure(i, weight=1, uniform="cards")
        row = ttk.Frame(self.main)
        row.pack(fill="both", expand=True, padx=28, pady=22)
        left = self._panel(row, 16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        top = ttk.Frame(left, style="Panel.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Zuletzt erfasst", font=("Segoe UI", 13, "bold"), background=self.colors["panel"], foreground=self.colors["fg"]).pack(side="left")
        ttk.Button(top, text="Alle Einträge", command=lambda: self.show_page("Einträge")).pack(side="right")
        table_frame = ttk.Frame(left, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True, pady=(12, 0))
        tree = ttk.Treeview(table_frame, columns=("date", "hours", "diff"), show="headings", height=9, style="Dashboard.Treeview")
        for col, text, width in [
            ("date", "Datum", 120),
            ("hours", "Arbeitszeit", 120),
            ("diff", "Differenz", 120)
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="center")

        tree.pack(fill="both", expand=True, padx=0, pady=0)
        for e in self.daten.sortiert()[:8]: tree.insert("", "end", values=(datetime.strptime(e["date"], "%Y-%m-%d").strftime("%d.%m.%Y"), fmt_minutes(e["worked"]), fmt_minutes(e["diff"], True)))
        right = self._panel(row, 16)
        right.pack(side="left", fill="y", padx=(10, 0))
        ttk.Label(right, text="Schnellzugriff", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))
        ttk.Button(right, text="＋  Arbeitszeit eintragen", style="Accent.TButton", command=lambda: self.show_page("Eintrag erfassen")).pack(fill="x", pady=4)
        ttk.Button(right, text="Einträge verwalten", command=lambda: self.show_page("Einträge")).pack(fill="x", pady=4)
        ttk.Button(right, text="Wochen-/Monatsbericht", command=lambda: self.show_page("Auswertungen")).pack(fill="x", pady=4)
        ttk.Label(right, text="Daten-Dateien", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(22, 5))
        tk.Label(right, text=str(self.daten.directory), bg=self.colors["panel"], fg=self.colors["muted"], wraplength=200, justify="left").pack(anchor="w")

    # Formular zum Anlegen oder Ändern eines Arbeitstages.
    def page_form(self, initial=None):
        initial = initial or {}
        self._header("Eintrag bearbeiten" if initial else "Eintrag erfassen", "Trage Beginn, Ende und Pausen ein. Ein Ende vor oder gleich dem Beginn wird als Folgetag gewertet.")
        panel = self._panel(self.main, 20)
        panel.pack(fill="x", padx=28, pady=(0, 20), anchor="n")
        fields = ttk.Frame(panel, style="Panel.TFrame")
        fields.pack(fill="x")
        today = date.today().strftime("%d.%m.%Y")
        variables = {"date": tk.StringVar(value=datetime.strptime(initial["date"], "%Y-%m-%d").strftime("%d.%m.%Y") if initial else today),
                     "start": tk.StringVar(value=initial.get("start", "07:30")), "end": tk.StringVar(value=initial.get("end", "16:15")),
                     "breakfast": tk.StringVar(value=str(initial.get("breakfast", self.daten.einstellungen["fruehstueckspause"]))),
                     "lunch": tk.StringVar(value=str(initial.get("lunch", self.daten.einstellungen["mittagspause"]))),
                     "notes": tk.StringVar(value=initial.get("notes", "")),
                     "azv": tk.BooleanVar(value=bool(initial.get("azv", False)))}
        labels = [("Datum (TT.MM.JJJJ)", "date"), ("Beginn (HH:MM)", "start"), ("Ende (HH:MM)", "end"), ("Frühstückspause (Min.)", "breakfast"), ("Mittagspause (Min.)", "lunch")]
        for i, (label, key) in enumerate(labels):
            r, c = divmod(i, 2)
            block = ttk.Frame(fields, style="Panel.TFrame")
            block.grid(row=r, column=c, sticky="ew", padx=(0, 18 if c == 0 else 0), pady=9)
            ttk.Label(block, text=label).pack(anchor="w", pady=(0, 5))
            if key == "date":
                datumzeile = ttk.Frame(block, style="Panel.TFrame")
                datumzeile.pack(fill="x")
                ent = ttk.Entry(datumzeile, textvariable=variables[key], width=20)
                ent.pack(side="left", fill="x", expand=True)
                ttk.Button(datumzeile, text="Kalender", command=lambda: KalenderPopup(
                    self, variables["date"].get(), variables["date"].set)).pack(side="left", padx=(6, 0))
            elif key in ("start", "end"):
                ent = ttk.Combobox(block, textvariable=variables[key], values=UHRZEITEN, state="readonly", width=25)
                ent.pack(fill="x")
            else:
                ent = ttk.Combobox(block, textvariable=variables[key], values=PAUSENWERTE, state="readonly", width=25)
                ent.pack(fill="x")
            if i == 0:
                ent.focus_set()
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        block = ttk.Frame(panel, style="Panel.TFrame")
        block.pack(fill="x", pady=(8, 4))
        ttk.Label(block, text="Notizen (optional)").pack(anchor="w", pady=(0, 5))
        ttk.Entry(block, textvariable=variables["notes"]).pack(fill="x")
        ttk.Checkbutton(panel, text="AZV – Arbeitszeitkonto ausgleichen (keine Plus- oder Minusstunden)", variable=variables["azv"], style="Custom.TCheckbutton").pack(anchor="w", pady=(12, 0))
        calc = ttk.Label(panel, text="Nettoarbeitszeit: —     Differenz: —", font=("Segoe UI", 11, "bold"))
        calc.pack(anchor="w", pady=(18, 0))
        def preview(*_):
            try:
                dt = parse_date(variables["date"].get())
                start = variables["start"].get().strip()
                end = variables["end"].get().strip()
                from arbeitszeit_core import parse_time
                a, b = parse_time(start), parse_time(end)
                if b <= a: b += 1440
                fr, mi = int(variables["breakfast"].get()), int(variables["lunch"].get())
                worked = b - a - fr - mi
                if worked <= 0:
                    raise ValueError("Pausen sind zu lang")
                target = self.daten.tages_soll(dt)
                diff = 0 if variables["azv"].get() else worked - target
                zusatz = " (AZV)" if variables["azv"].get() else ""
                calc.configure(text=f"Nettoarbeitszeit: {fmt_minutes(worked)}     Soll: {fmt_minutes(target)}     Differenz: {fmt_minutes(diff, True)}{zusatz}")
            except (ValueError, TypeError): calc.configure(text="Nettoarbeitszeit: —     Differenz: —")
        for var in variables.values(): var.trace_add("write", preview)
        preview()
        buttons = ttk.Frame(panel, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(20, 0))
        ttk.Button(buttons, text="Abbrechen", command=lambda: self.show_page("Einträge" if initial else "Dashboard")).pack(side="right", padx=(8, 0))
        
        
        
        def save():
            try:
                dt = parse_date(variables["date"].get())
                old = self.daten.eintraege.get(dt.isoformat())
                ident = initial.get("id") if initial else (old["id"] if old else None)
                e = self.daten.berechnen(variables["date"].get(), variables["start"].get(), variables["end"].get(),
                                         int(variables["breakfast"].get()), int(variables["lunch"].get()),
                                         variables["notes"].get(), ident, variables["azv"].get())
                if initial and initial["date"] != e["date"]:
                    if e["date"] in self.daten.eintraege and not messagebox.askyesno("Datum bereits vorhanden", "Für dieses Datum existiert bereits ein Eintrag. Diesen ersetzen?"):
                        return
                    self.daten.loeschen(initial["date"])
                self.daten.speichern(e)
                messagebox.showinfo("Gespeichert", f"Eintrag für {dt.strftime('%d.%m.%Y')} wurde gespeichert.")
                self.show_page("Einträge")
            except (ValueError, OSError) as exc: messagebox.showerror("Eingabe prüfen", str(exc))
        ttk.Button(buttons, text="Speichern", style="Accent.TButton", command=save).pack(side="right")

        



    # Zeigt die Einträge mit Suche, Sortierung, Bearbeiten und Löschen.
    def page_entries(self):
        self._header("Einträge", "Alle erfassten Arbeitstage verwalten. Spaltenüberschriften sortieren die Liste.")
        toolbar = ttk.Frame(self.main)
        toolbar.pack(fill="x", padx=28, pady=(0, 12))
        self.filter_var = tk.StringVar()
        ttk.Label(toolbar, text="Suche").pack(side="left", padx=(0, 8))
        search = ttk.Entry(toolbar, textvariable=self.filter_var, width=32)
        search.pack(side="left")
        ttk.Button(toolbar, text="＋ Neuer Eintrag", style="Accent.TButton", command=lambda: self.show_page("Eintrag erfassen")).pack(side="right")

        panel = ttk.Frame(self.main, padding=0)
        panel.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        cols = ("id", "date", "day", "start", "end", "worked", "break", "diff", "azv", "notes")
        table_frame = ttk.Frame(panel, padding=0)
        table_frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        headings = {"id":"ID", "date":"Datum", "day":"Wochentag", "start":"Beginn", "end":"Ende", "worked":"Netto", "break":"Pausen", "diff":"Differenz", "azv":"AZV", "notes":"Notizen"}
        widths = {"id":45,"date":100,"day":105,"start":70,"end":70,"worked":80,"break":75,"diff":90,"azv":55,"notes":220}
        for col in cols:
            tree.heading(col, text=headings[col], command=lambda c=col: self.sort_tree(c, tree))
            tree.column(col, width=widths[col], minwidth=40, anchor="w")
            yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            tree.grid(row=0, column=0, sticky="nsew")
            yscroll.grid(row=0, column=1, sticky="ns")
            xscroll.grid(row=1, column=0, sticky="ew")
            table_frame.rowconfigure(0, weight=1)
            table_frame.columnconfigure(0, weight=1)
        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        def selected():
            item = tree.focus()
            if not item: messagebox.showwarning("Auswahl fehlt", "Bitte zuerst einen Eintrag auswählen."); return None
            vals = tree.item(item, "values")
            return self.daten.eintraege.get(vals[1])
        ttk.Button(actions, text="Bearbeiten", command=lambda: self.edit_selected(selected())).pack(side="left")
        ttk.Button(actions, text="Löschen", command=lambda: self.delete_selected(selected())).pack(side="left", padx=8)
        ttk.Label(actions, text=f"Datei: {self.daten.dateipfad}").pack(side="right")
        def fill(*_):
            tree.delete(*tree.get_children())
            q = self.filter_var.get().lower().strip()
            entries = sorted(self.daten.eintraege.values(), key=lambda e: e.get(self.sort_column, e["date"]), reverse=self.sort_reverse)
            for e in entries:
                line = " ".join(str(e.get(k, "")) for k in ("id","date","day","start","end","notes")).lower()
                if q and q not in line: continue
                tree.insert("", "end", values=(e["id"], e["date"], e["day"], e["start"], e["end"],
                           fmt_minutes(e["worked"]), f"{e['breakfast'] + e['lunch']} min",
                           fmt_minutes(e["diff"], True), "Ja" if e.get("azv", False) else "Nein",
                           e.get("notes", "")))
        self._fill_entries = fill
        self.filter_var.trace_add("write", fill)
        fill()
        tree.bind("<Double-1>", lambda _: self.edit_selected(selected()))

    # Ändert die Sortierung, wenn eine Spaltenüberschrift angeklickt wird.
    def sort_tree(self, column, tree):
        keymap = {"id":"id", "date":"date", "day":"day", "start":"start", "end":"end", "worked":"worked", "break":"breakfast", "diff":"diff", "azv":"azv", "notes":"notes"}
        if self.sort_column == keymap[column]: self.sort_reverse = not self.sort_reverse
        else: self.sort_column, self.sort_reverse = keymap[column], False
        self._fill_entries()

    # Öffnet das Formular mit den Daten des ausgewählten Eintrags.
    def edit_selected(self, entry):
        if entry: self.page_form(dict(entry))

    # Löscht einen Eintrag erst nach einer Sicherheitsabfrage.
    def delete_selected(self, entry):
        if entry and messagebox.askyesno("Eintrag löschen", f"Eintrag vom {entry['date']} wirklich löschen?"):
            self.daten.loeschen(entry["date"])
            self.show_page("Einträge")

    # Zeigt einen Dropdown zur Auswahl der Woche bzw. des Monats.
    def _export_zeitraum_waehlen(self, mode):
        heute = date.today()
        fenster = tk.Toplevel(self)
        fenster.title("Zeitraum auswählen")
        fenster.transient(self)
        fenster.grab_set()
        fenster.resizable(False, False)
        rahmen = ttk.Frame(fenster, padding=18)
        rahmen.pack(fill="both", expand=True)

        if mode == "week":
            montag_aktuell = heute - timedelta(days=heute.weekday())
            start = montag_aktuell - timedelta(weeks=52)
            optionen = []
            cursor = start
            for _ in range(105):
                freitag = cursor + timedelta(days=4)
                iso = cursor.isocalendar()
                label = f"KW {iso.week:02d}/{iso.year}  ({cursor.strftime('%d.%m.%Y')}–{freitag.strftime('%d.%m.%Y')})"
                optionen.append((label, cursor))
                cursor += timedelta(days=7)
            aktuell = next((label for label, d in optionen if d == montag_aktuell), optionen[-1][0])
            ttk.Label(rahmen, text="Welche Kalenderwoche möchtest du exportieren?").pack(anchor="w", pady=(0, 8))
            auswahl = tk.StringVar(value=aktuell)
            ttk.Combobox(rahmen, textvariable=auswahl, values=[x[0] for x in optionen], state="readonly", width=42).pack(fill="x")
            auswahl_typ = "week"
        else:
            optionen = []
            for offset in range(-36, 37):
                monat_index = heute.year * 12 + (heute.month - 1) + offset
                jahr, monat0 = divmod(monat_index, 12)
                monat = monat0 + 1
                label = f"{MONATSNAMEN[monat - 1]} {jahr}"
                optionen.append((label, jahr, monat))
            aktuell = f"{MONATSNAMEN[heute.month - 1]} {heute.year}"
            ttk.Label(rahmen, text="Welchen Monat möchtest du exportieren?").pack(anchor="w", pady=(0, 8))
            auswahl = tk.StringVar(value=aktuell)
            ttk.Combobox(rahmen, textvariable=auswahl, values=[x[0] for x in optionen], state="readonly", width=32).pack(fill="x")
            auswahl_typ = "month"

        buttons = ttk.Frame(rahmen)
        buttons.pack(fill="x", pady=(16, 0))
        result = {"value": None}

        def bestaetigen():
            wert = auswahl.get()
            if auswahl_typ == "week":
                result["value"] = next((d for label, d in optionen if label == wert), None)
            else:
                result["value"] = next(((jahr, monat) for label, jahr, monat in optionen if label == wert), None)
            fenster.destroy()

        ttk.Button(buttons, text="Abbrechen", command=fenster.destroy).pack(side="right")
        ttk.Button(buttons, text="Weiter", command=bestaetigen).pack(side="right", padx=(0, 8))
        fenster.bind("<Return>", lambda _e: bestaetigen())
        fenster.bind("<Escape>", lambda _e: fenster.destroy())
        fenster.update_idletasks()
        fenster.geometry(f"+{self.winfo_rootx() + 100}+{self.winfo_rooty() + 100}")
        self.wait_window(fenster)
        return result["value"]

    # Speichert den Nachweis direkt als PDF, damit man nicht erst im Browser drucken muss.
    def export_print_sheet(self, mode):
        auswahl = self._export_zeitraum_waehlen(mode)
        if not auswahl:
            return

        if mode == "week":
            montag = auswahl
            tage = [montag + timedelta(days=i) for i in range(5)]
            titel = f"Wochenarbeitszeitnachweis – {tage[0].strftime('%d.%m.%Y')} bis {tage[-1].strftime('%d.%m.%Y')}"
            standardname = f"Arbeitszeit_Woche_{montag.isoformat()}.pdf"
            wochen = [(montag, tage)]
        else:
            jahr, monat = auswahl
            anzahl = calendar.monthrange(jahr, monat)[1]
            alle_tage = [date(jahr, monat, tag) for tag in range(1, anzahl + 1)
                         if date(jahr, monat, tag).weekday() < 5]
            titel = f"Monatsarbeitszeitnachweis – {MONATSNAMEN[monat - 1]} {jahr}"
            standardname = f"Arbeitszeit_Monat_{jahr}-{monat:02d}.pdf"
            # Jede Kalenderwoche bekommt eine eigene Tabelle; Samstag und Sonntag kommen nicht rein.
            gruppiert = {}
            for tag in alle_tage:
                montag = tag - timedelta(days=tag.weekday())
                gruppiert.setdefault(montag, []).append(tag)
            wochen = sorted(gruppiert.items())

        ziel = filedialog.asksaveasfilename(
            parent=self, title="PDF-Nachweis speichern", initialfile=standardname,
            defaultextension=".pdf", filetypes=[("PDF-Datei", "*.pdf")]
        )
        if not ziel:
            return

        # Kumulativ wird mit dem letzten gespeicherten Stand vor dem Exportzeitraum gestartet.
        eintraege = self.daten.eintraege
        differenzen = {datum: int(e.get("diff", 0)) for datum, e in eintraege.items()}
        erster_tag = wochen[0][1][0]
        kumulativ = sum(diff for datum, diff in differenzen.items()
                        if date.fromisoformat(datum) < erster_tag)
        tabellen = []
        for wochenstart, tage_der_woche in wochen:
            zeilen = []
            for tag in tage_der_woche:
                eintrag = eintraege.get(tag.isoformat())
                if eintrag:
                    differenz = int(eintrag.get("diff", 0))
                    kumulativ += differenz
                    beginn = str(eintrag.get("start", ""))
                    ende = str(eintrag.get("end", ""))
                    differenz_text = fmt_minutes(differenz, True)
                else:
                    beginn = ende = differenz_text = ""
                zeilen.append((beginn, "", ende, "", differenz_text, fmt_minutes(kumulativ, True),
                               f"{WOCHENTAGE[tag.weekday()]}, {tag.strftime('%d.%m.%Y')}"))
            iso = wochenstart.isocalendar()
            tabellen.append((f"KW {iso.week:02d}/{iso.year}", zeilen))

        # Ein kleiner PDF-Schreiber mit Python-Bordmitteln; dadurch braucht die App kein Zusatzpaket.
        # A4 quer ist breit genug für alle Spalten und die Monatsübersicht wird auf Vorder-/Rückseite verteilt.
        seiten = [tabellen[i:i + 3] for i in range(0, len(tabellen), 3)]
        if mode == "week":
            seiten = [tabellen]
        breite, hoehe = 842, 595  # A4 quer in PDF-Punkten
        objekte = []
        seitenobjekte = []
        schrift_obj = 3

        def pdf_text(zeichenfolge, x, y, groesse=9, fett=False):
            # Hex-Text mit Windows-1252 sorgt dafür, dass Umlaute und Gedankenstriche passen.
            font = "/F2" if fett else "/F1"
            daten = str(zeichenfolge).encode("cp1252", errors="replace").hex().upper()
            return f"BT {font} {groesse} Tf 1 0 0 1 {x:.1f} {y:.1f} Tm <{daten}> Tj ET\n"

        def linie(x1, y1, x2, y2):
            return f"{x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S\n"

        for seiten_index, tabellen_der_seite in enumerate(seiten):
            inhalt = "0.15 0.15 0.15 RG 0.15 0.15 0.15 rg 0.7 w\n"
            inhalt += pdf_text(titel, 42, 555, 16, True)
            inhalt += pdf_text("Name: ______________________________________________", 42, 528, 11, True)
            y = 493
            spalten = [42, 112, 196, 266, 350, 438, 526, 800]
            kopf = ["Beginn", "Signum", "Ende", "Signum", "Differenz", "Kumulativ", "Wochentag + Datum"]
            for wochenname, zeilen in tabellen_der_seite:
                inhalt += pdf_text(wochenname, 42, y, 10, True)
                y -= 8
                kopf_oben = y
                kopf_unten = y - 23
                # Kopfzeile grau hinterlegen, damit die Spalten beim Ausfüllen gut zu erkennen sind.
                inhalt += f"0.92 0.92 0.92 rg 42 {kopf_unten} 758 23 re f 0 0 0 rg 0 0 0 RG\n"
                inhalt += linie(42, kopf_oben, 800, kopf_oben)
                inhalt += linie(42, kopf_unten, 800, kopf_unten)
                for x in spalten:
                    inhalt += linie(x, kopf_oben, x, kopf_unten - len(zeilen) * 19)
                for i, text in enumerate(kopf):
                    mitte = (spalten[i] + spalten[i + 1]) / 2
                    inhalt += pdf_text(text, mitte - min(len(text) * 2.3, 60), kopf_unten + 8, 8, True)
                y_zeile = kopf_unten
                for zeile in zeilen:
                    naechstes_y = y_zeile - 19
                    inhalt += linie(42, naechstes_y, 800, naechstes_y)
                    for i, wert in enumerate(zeile):
                        if i == 6:
                            x_text = spalten[i] + 5
                            groesse = 8
                        else:
                            x_text = (spalten[i] + spalten[i + 1]) / 2 - min(len(str(wert)) * 2.2, 35)
                            groesse = 9
                        inhalt += pdf_text(wert, x_text, y_zeile - 13, groesse)
                    y_zeile = naechstes_y
                y = y_zeile - 14
            inhalt += pdf_text("Signum-Felder bitte handschriftlich ausfüllen.", 42, 25, 8)
            inhalt += pdf_text(f"Seite {seiten_index + 1} von {len(seiten)}", 735, 25, 8)
            seitenobjekte.append(inhalt.encode("latin-1"))

        # PDF-Objekte zusammenbauen und die Byte-Offsets für die Datei-Index-Tabelle merken.
        objekte = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
                   b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
        content_ids = []
        page_ids = []
        for inhalt in seitenobjekte:
            content_id = len(objekte) + 1
            objekte.append(b"<< /Length " + str(len(inhalt)).encode() + b" >>\nstream\n" + inhalt + b"endstream")
            page_id = len(objekte) + 1
            objekte.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {breite} {hoehe}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>".encode())
            content_ids.append(content_id)
            page_ids.append(page_id)
        objekte[1] = (f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] /Count {len(page_ids)} >>").encode()
        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for nummer, objekt in enumerate(objekte, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{nummer} 0 obj\n".encode())
            pdf.extend(objekt)
            pdf.extend(b"\nendobj\n")
        xref = len(pdf)
        pdf.extend(f"xref\n0 {len(objekte) + 1}\n".encode())
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(f"trailer\n<< /Size {len(objekte) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())

        try:
            with open(ziel, "wb") as datei:
                datei.write(pdf)
            messagebox.showinfo( "PDF erstellt", f"Der Nachweis wurde direkt als PDF gespeichert.\n\nDatei: {ziel}\nFormat: A4 quer\nSeiten: {len(seiten)}", parent=self)
        except OSError as exc:
            messagebox.showerror("Export fehlgeschlagen", str(exc), parent=self)

    # Fasst die gespeicherten Tageswerte zusammen und schaltet per Regler zwischen Woche und Monat um.
    def page_reports(self):
        self._header("Auswertungen", "Wochen- und Monatsübersicht aus den gespeicherten Einträgen.")
        exportzeile = ttk.Frame(self.main)
        exportzeile.pack(fill="x", padx=28, pady=(0, 10))
        ttk.Button(exportzeile, text="Wochenzettel als PDF", command=lambda: self.export_print_sheet("week")).pack(side="left", padx=(0, 8))
        ttk.Button(exportzeile, text="Monatszettel als PDF", command=lambda: self.export_print_sheet("month")).pack(side="left")

        # Android-10-artiger Switch: eine flache, abgerundete Schiene mit
        # einem farbigen Schieber. Die Texte stehen links und rechts daneben.
        schalterzeile = ttk.Frame(self.main)
        schalterzeile.pack(anchor="center", pady=(0, 12))
        ttk.Label(schalterzeile, text="Wochenübersicht", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        schalter = tk.Canvas(schalterzeile, width=52, height=30, highlightthickness=0, bd=0, bg=self.colors["bg"], cursor="hand2")
        schalter.pack(side="left")
        ttk.Label(schalterzeile, text="Monatsübersicht", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))

        inhalt = ttk.Frame(self.main)
        inhalt.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        wochen_frame = ttk.Frame(inhalt, padding=16)
        monate_frame = ttk.Frame(inhalt, padding=16)
        # Es wird immer nur eine Übersicht eingepackt. So liegen die Tabellen
        # nicht übereinander und bleiben auch nach dem Umschalten sichtbar.

        def tabelle_bauen(parent, titel, nach_woche):
            ttk.Label(parent, text=titel, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))
            spalten = ("period", "count", "worked", "target", "diff")
            tree = ttk.Treeview(parent, columns=spalten, show="headings", height=16)
            for spalte, text, breite in [("period", "Zeitraum", 220), ("count", "Einträge", 100),("worked", "Nettozeit", 130), ("target", "Sollzeit", 130),("diff", "Differenz", 130)]:
                tree.heading(spalte, text=text)
                tree.column(spalte, width=breite, anchor="center")
            tree.pack(fill="both", expand=True)
            gruppen = {}
            for eintrag in self.daten.eintraege.values():
                datum = date.fromisoformat(eintrag["date"])
                if nach_woche:
                    iso = datum.isocalendar()
                    schluessel = f"{iso.year}-KW{iso.week:02d}"
                else:
                    schluessel = datum.strftime("%Y-%m")
                gruppe = gruppen.setdefault(schluessel, {"count": 0, "worked": 0, "target": 0, "diff": 0})
                gruppe["count"] += 1
                for feld in ("worked", "target", "diff"):
                    gruppe[feld] += int(eintrag.get(feld, 0))
            for schluessel, gruppe in sorted(gruppen.items(), reverse=True):
                tree.insert("", "end", values=(schluessel, gruppe["count"], fmt_minutes(gruppe["worked"]),
                                                 fmt_minutes(gruppe["target"]), fmt_minutes(gruppe["diff"], True)))

        tabelle_bauen(wochen_frame, "Kalenderwochen", True)
        tabelle_bauen(monate_frame, "Monate", False)
        auswahl_monat = tk.BooleanVar(value=False)

        def schalter_zeichnen():
            # Alles neu zeichnen, damit der Schalter bei jedem Wechsel sauber bleibt.
            schalter.delete("all")

            ist_monat = auswahl_monat.get()

            # Farben passend zum aktuellen hellen oder dunklen Design.
            # Farben passend zum vorhandenen GUI-Design auswählen.
            if self.colors["bg"].lower() == "#2b3038":
                # Dunkles Design: dezente, gut sichtbare Grautöne.
                track_farbe = "#666c76" if ist_monat else "#454a53"
                knopf_farbe = "#e6e8ec"
                schatten_farbe = "#171a20"
            else:
                # Helles Design: heller Knopf und neutraler Schienenton.
                track_farbe = "#858b95" if ist_monat else "#d5d9df"
                knopf_farbe = "#ffffff"
                schatten_farbe = "#b6bbc3"

            # Der Canvas hat etwas mehr Platz, damit nichts abgeschnitten wird.
            # Die Schiene ist bewusst etwas breiter und dezenter gehalten.
            schalter.create_line(13, 15, 39, 15, fill=track_farbe, width=12, capstyle="round", smooth=True)

            # Knopf links für Woche, rechts für Monat.
            x = 15 if not ist_monat else 37

            # Dezenter Schatten unter dem Knopf für etwas mehr Tiefe.
            schalter.create_oval(
                x - 10, 4, x + 10, 24, fill=schatten_farbe, outline="", width=0)

            # Der Knopf selbst mit dünnem Rand.
            schalter.create_oval(x - 9, 4, x + 9, 22, fill=knopf_farbe, outline="#a5aab2", width=0)

            schalter.create_arc(x - 7, 5, x + 7, 19, start=45, extent=180, style="arc", outline="#ffffff", width=1)

        def umschalten(_event=None):
            # Erst die alte Tabelle ausblenden, dann die gewünschte Übersicht zeigen.
            auswahl_monat.set(not auswahl_monat.get())
            if auswahl_monat.get():
                wochen_frame.pack_forget()
                monate_frame.pack(fill="both", expand=True)
            else:
                monate_frame.pack_forget()
                wochen_frame.pack(fill="both", expand=True)
            schalter_zeichnen()

        schalter.bind("<Button-1>", umschalten)
        # Beim Öffnen ist die Wochenübersicht sichtbar, wie bei der bisherigen Registeransicht.
        wochen_frame.pack(fill="both", expand=True)
        schalter_zeichnen()
        ttk.Label(self.main, text="Hinweis: Auswertungen summieren die gespeicherten Tageswerte. Änderungen am Soll ändern bestehende Einträge nicht automatisch.", style="Subtitle.TLabel").pack(anchor="w", padx=30, pady=(0, 14))

    # Formular für Sollzeiten, Pausen, Zeitmodelle und Darstellung.
    def page_settings(self):
        self._header("Einstellungen", "Änderungen gelten für neue bzw. erneut gespeicherte Einträge.")
        panel = self._panel(self.main, 20)
        panel.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        s = self.daten.einstellungen
        vars = {"week": tk.StringVar(value=fmt_minutes(s["wochen_soll"])), "breakfast": tk.StringVar(value=str(s["fruehstueckspause"])),
                "lunch": tk.StringVar(value=str(s["mittagspause"])), "appearance": tk.StringVar(value=s.get("appearance", "Dunkel"))}
        ttk.Label(panel, text="Sollzeiten und Pausen", font=("Segoe UI", 13, "bold")).grid(row=0,column=0,columnspan=4,sticky="w",pady=(0,12))
        settings_fields = [("Wochen-Soll (HH:MM)","week"),("Frühstückspause (Minuten)","breakfast"),("Mittagspause (Minuten)","lunch")]
        for i,(label,key) in enumerate(settings_fields, start=1):
            ttk.Label(panel,text=label).grid(row=i,column=0,sticky="w",pady=7,padx=(0,15))
            if key == "week":
                # Das Wochen-Soll bleibt frei eingebbar, damit auch 39:00 möglich ist.
                ttk.Entry(panel, textvariable=vars[key], width=18).grid(row=i,column=1,sticky="w",pady=7)
            else:
                ttk.Combobox(panel, textvariable=vars[key], values=PAUSENWERTE, state="readonly", width=15).grid(row=i,column=1,sticky="w",pady=7)
        ttk.Label(panel,text="Tages-Sollzeiten",font=("Segoe UI",13,"bold")).grid(row=4,column=0,columnspan=4,sticky="w",pady=(20,8))
        day_vars = {}
        for i,day in enumerate(WOCHENTAGE[:5]):
            var = tk.StringVar(value=fmt_minutes(int(s["tages_soll"].get(str(i),468))))
            day_vars[str(i)] = var
            ttk.Label(panel,text=day).grid(row=5+i,column=0,sticky="w",pady=5)
            # Tages-Soll bleibt frei eingebbar, z. B. 07:48 bei 39 Stunden pro Woche.
            ttk.Entry(panel, textvariable=var, width=18).grid(row=5+i,column=1,sticky="w",pady=5)
        ttk.Label(panel,text="Zeitmodelle (HH:MM)",font=("Segoe UI",13,"bold")).grid(row=10,column=0,columnspan=4,sticky="w",pady=(20,8))
        model_vars = {}
        for r, (i, day) in enumerate(enumerate(WOCHENTAGE[:5]), start=11):
            ttk.Label(panel,text=day).grid(row=r,column=0,sticky="w",pady=4)
            for c,(model,label) in enumerate((("flex","Flex von/bis"),("kern","Kernzeit von/bis"),("regel","Regelzeit von/bis"))):
                pair = s["zeiten"][str(i)] [model]
                a = tk.StringVar(value=pair[0])
                b = tk.StringVar(value=pair[1])
                model_vars[(str(i),model)] = (a,b)
                box = ttk.Frame(panel,style="Panel.TFrame")
                box.grid(row=r,column=c+1,sticky="w",padx=(0,8),pady=4)
                ttk.Label(box,text=label if r==11 else "").pack(anchor="w")
                inner=ttk.Frame(box,style="Panel.TFrame")
                inner.pack()
                ttk.Combobox(inner, textvariable=a, values=UHRZEITEN, state="readonly", width=7).pack(side="left")
                ttk.Label(inner,text="–").pack(side="left",padx=3)
                ttk.Combobox(inner, textvariable=b, values=UHRZEITEN, state="readonly", width=7).pack(side="left")
        ttk.Label(panel,text="Darstellung").grid(row=16,column=0,sticky="w",pady=(18,6))
        ttk.Combobox(panel,textvariable=vars["appearance"],values=("Hell","Dunkel"),state="readonly",width=15).grid(row=16,column=1,sticky="w",pady=(18,6))
        ttk.Label(panel,text="Datenordner",style="Subtitle.TLabel").grid(row=17,column=0,sticky="w",pady=(12,0))
        ttk.Label(panel,text=str(self.daten.directory),style="Subtitle.TLabel").grid(row=17,column=1,columnspan=3,sticky="w",pady=(12,0))
        buttons=ttk.Frame(panel,style="Panel.TFrame")
        buttons.grid(row=18,column=0,columnspan=4,sticky="ew",pady=(20,0))
        def save():
            try:
                s["wochen_soll"] = parse_duration(vars["week"].get())
                s["fruehstueckspause"] = int(vars["breakfast"].get())
                s["mittagspause"] = int(vars["lunch"].get())
                if s["fruehstueckspause"] < 0 or s["mittagspause"] < 0: raise ValueError("Pausen dürfen nicht negativ sein.")
                for k,v in day_vars.items(): s["tages_soll"][k] = parse_duration(v.get())
                from arbeitszeit_core import parse_time
                for (day,model),(a,b) in model_vars.items(): parse_time(a.get()); parse_time(b.get()); s["zeiten"][day][model] = [a.get().strip(),b.get().strip()]
                s["appearance"] = vars["appearance"].get()
                self.daten.einstellungen_speichern()
                messagebox.showinfo("Gespeichert","Einstellungen gespeichert. Die Darstellung wird aktualisiert. Die Anwendung startet neu.")
                self._setup_style()
                self.show_page("Einstellungen")
            except (ValueError, OSError) as exc: messagebox.showerror("Einstellungen prüfen",str(exc))

        def save_settings_and_restart():
            save()
            subprocess.Popen([sys.executable] + sys.argv)
            self.destroy()
        ttk.Button(buttons,text="Standardeinstellungen laden",command=lambda:self.reset_settings()).pack(side="left")
        ttk.Button(buttons,text="Speichern",style="Accent.TButton",command=save_settings_and_restart).pack(side="right")

    # Setzt die Einstellungen nach Rückfrage auf Standardwerte zurück.
    def reset_settings(self):
        from arbeitszeit_core import clean_settings
        if messagebox.askyesno("Zurücksetzen","Alle Einstellungen auf Standardwerte zurücksetzen?"):
            self.daten.einstellungen = clean_settings({})
            self.daten.einstellungen_speichern()
            self._setup_style()
            self.show_page("Einstellungen")

if __name__ == "__main__":
    try:
        app = ArbeitszeitGUI()
        app.mainloop()
    except Exception as exc:
        messagebox.showerror("Arbeitszeitrechner", f"Die Anwendung konnte nicht gestartet werden:\n{exc}")
        raise
