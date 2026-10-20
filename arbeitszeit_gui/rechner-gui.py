"""Tkinter-GUI für den Arbeitszeitrechner
benötigt nur Python-Standardbibliothek."""
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
from arbeitszeit_core import ArbeitszeitDaten, WOCHENTAGE, fmt_minutes, parse_date, parse_duration

APP_TITLE = "Arbeitszeitrechner"

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

    # Legt Farben, Schriftarten und das Aussehen der Tabellen fest.
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista" if "vista" in style.theme_names() else "clam")
        except tk.TclError:
            pass
        appearance = self.daten.einstellungen.get("appearance", "System")
        if appearance == "Dunkel":
            bg, panel, fg, accent = "#2b3038", "#2b3038", "#edf0f5", "#5b9cff"
        else:
            bg, panel, fg, accent = "#f3f5f7", "#f3f5f7", "#202632", "#1769d2"
        self.colors = {"bg": bg, "panel": panel, "fg": fg, "muted": "#7b8493", "accent": accent, "line": "#dce1e8"}

        # Die Hintergrundfarbe des Fensters und der Panels, Schriftarten und Farben für Labels, Buttons und Tabellen.
        self.configure(bg=bg)
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), background=bg, foreground=fg)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), background=bg, foreground=self.colors["muted"])
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10), background=panel, foreground=self.colors["muted"])
        style.configure("CardValue.TLabel", font=("Segoe UI", 20, "bold"), background=panel, foreground=fg)
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Accent.TButton", background=accent, foreground="gray", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", accent)])
        style.configure("Treeview", rowheight=29, font=("Segoe UI", 10), background=panel, fieldbackground=panel, foreground=fg)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=7)

    # Erstellt die feste Seitenleiste und den Bereich für die Seiten.
    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg="#202a38", width=205)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Die Navigation mit Überschrift, Trennlinie, Buttons und Fußzeile.
        tk.Label(self.sidebar, text="◷  Arbeitszeit", bg="#202a38", fg="white", font=("Segoe UI", 16, "bold"), anchor="w", padx=18, pady=25).pack(fill="x")
        tk.Frame(self.sidebar, bg="#3b4656", height=1).pack(fill="x", padx=15, pady=(0, 12))
        for label, glyph in [("Dashboard", "⌂"), ("Eintrag erfassen", "+"), ("Einträge", "☷"), ("Auswertungen", "▥"), ("Einstellungen", "⚙")]:
            b = tk.Button(self.sidebar, text=f"{glyph}   {label}", anchor="w", padx=18, pady=12, bd=0,
                          bg="#202a38", fg="#e7edf5", activebackground="#33465f", activeforeground="white",
                          font=("Segoe UI", 10), command=lambda page=label: self.show_page(page), cursor="hand2")
            b.pack(fill="x", padx=8, pady=2)
        tk.Label(self.sidebar, text="Lokale Daten\nMarkdown + JSON", bg="#202a38", fg="#aab6c6", font=("Segoe UI", 9), justify="left", padx=18).pack(side="bottom", anchor="w", pady=20)
        self.main = tk.Frame(self, bg=self.colors["bg"])
        self.main.pack(side="left", fill="both", expand=True)

    # Entfernt die alte Seite, bevor eine neue angezeigt wird.
    def _clear(self):
        for w in self.main.winfo_children(): w.destroy()

    # Zeigt oben auf jeder Seite eine Überschrift an.
    def _header(self, title, subtitle=""):
        head = ttk.Frame(self.main)
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
            tk.Label(
                frame, text=note, bg=self.colors["panel"],
                fg=self.colors["muted"], font=("Segoe UI", 9), anchor="w"
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

    # Übersicht mit den wichtigsten Zeiten und Schnellzugriffen.
    def page_dashboard(self):
        today = date.today()
        today_entry = self.daten.eintraege.get(today.isoformat())
        week = self._week_entries(today)
        month = self._month_entries(today)
        self._header("Dashboard", today.strftime("%A, %d. %B %Y"))
        cards = ttk.Frame(self.main)
        cards.pack(fill="x", padx=28)
        # Die vier Kennzahlen-Karten: Heute, Diese Woche, Zeitkonto, Dieser Monat.
        vals = [("Heute", fmt_minutes(today_entry["worked"]) if today_entry else "—", "Nettoarbeitszeit"),
                ("Diese Woche", fmt_minutes(sum(e["worked"] for e in week)), f"Soll {fmt_minutes(self.daten.einstellungen['wochen_soll'])}"),
                ("Zeitkonto", fmt_minutes(sum(e["diff"] for e in self.daten.eintraege.values()), True), "Gesamte Differenz"),
                ("Dieser Monat", fmt_minutes(sum(e["worked"] for e in month)), f"{len(month)} Einträge")]
        # Die Karten nebeneinander anordnen, gleichmäßig verteilen und die Spaltenbreite anpassen.
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
        tree = ttk.Treeview(left, columns=("date", "hours", "diff"), show="headings", height=9)
        for col, text, width in [("date", "Datum", 120), ("hours", "Arbeitszeit", 120), ("diff", "Differenz", 120)]:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True, pady=(12, 0))
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
                     "notes": tk.StringVar(value=initial.get("notes", ""))}
        labels = [("Datum (TT.MM.JJJJ)", "date"), ("Beginn (HH:MM)", "start"), ("Ende (HH:MM)", "end"), ("Frühstückspause (Min.)", "breakfast"), ("Mittagspause (Min.)", "lunch")]
        for i, (label, key) in enumerate(labels):
            r, c = divmod(i, 2)
            block = ttk.Frame(fields, style="Panel.TFrame")
            block.grid(row=r, column=c, sticky="ew", padx=(0, 18 if c == 0 else 0), pady=9)
            ttk.Label(block, text=label).pack(anchor="w", pady=(0, 5))
            ent = ttk.Entry(block, textvariable=variables[key], width=28)
            ent.pack(fill="x")
            if i == 0: ent.focus_set()
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=1)
        block = ttk.Frame(panel, style="Panel.TFrame")
        block.pack(fill="x", pady=(8, 4))
        ttk.Label(block, text="Notizen (optional)").pack(anchor="w", pady=(0, 5))
        ttk.Entry(block, textvariable=variables["notes"]).pack(fill="x")
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
                target = self.daten.tages_soll(dt)
                calc.configure(text=f"Nettoarbeitszeit: {fmt_minutes(worked)}     Soll: {fmt_minutes(target)}     Differenz: {fmt_minutes(worked-target, True)}")
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
                                         int(variables["breakfast"].get()), int(variables["lunch"].get()), variables["notes"].get(), ident)
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
        panel = self._panel(self.main, 10)
        panel.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        cols = ("id", "date", "day", "start", "end", "worked", "break", "diff", "notes")
        tree = ttk.Treeview(panel, columns=cols, show="headings", selectmode="browse")
        headings = {"id":"ID", "date":"Datum", "day":"Wochentag", "start":"Beginn", "end":"Ende", "worked":"Netto", "break":"Pausen", "diff":"Differenz", "notes":"Notizen"}
        widths = {"id":45,"date":100,"day":105,"start":70,"end":70,"worked":80,"break":75,"diff":90,"notes":220}
        for col in cols:
            tree.heading(col, text=headings[col], command=lambda c=col: self.sort_tree(c, tree))
            tree.column(col, width=widths[col], minwidth=40, anchor="w")
        yscroll = ttk.Scrollbar(panel, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(panel, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
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
                tree.insert("", "end", values=(e["id"],e["date"],e["day"],e["start"],e["end"],fmt_minutes(e["worked"]),f"{e['breakfast']+e['lunch']} min",fmt_minutes(e["diff"],True),e.get("notes", "")))
        self._fill_entries = fill
        self.filter_var.trace_add("write", fill)
        fill()
        tree.bind("<Double-1>", lambda _: self.edit_selected(selected()))

    # Ändert die Sortierung, wenn eine Spaltenüberschrift angeklickt wird.
    def sort_tree(self, column, tree):
        keymap = {"id":"id", "date":"date", "day":"day", "start":"start", "end":"end", "worked":"worked", "break":"breakfast", "diff":"diff", "notes":"notes"}
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

    # Fasst die gespeicherten Tageswerte nach Woche und Monat zusammen.
    def page_reports(self):
        self._header("Auswertungen", "Wochen- und Monatsübersicht aus den gespeicherten Einträgen.")
        tabs = ttk.Notebook(self.main)
        tabs.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        weekly = ttk.Frame(tabs, padding=16)
        monthly = ttk.Frame(tabs, padding=16)
        tabs.add(weekly, text="Wochenübersicht")
        tabs.add(monthly, text="Monatsübersicht")
        cols = ("period", "count", "worked", "target", "diff")
        for parent, title in ((weekly,"Kalenderwochen"),(monthly,"Monate")):
            ttk.Label(parent, text=title, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))
            tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
            for col, text, width in [("period","Zeitraum",220),("count","Einträge",100),("worked","Nettozeit",130),("target","Sollzeit",130),("diff","Differenz",130)]:
                tree.heading(col, text=text)
                tree.column(col, width=width, anchor="w")
            tree.pack(fill="both", expand=True)
            groups = {}
            for e in self.daten.eintraege.values():
                d = date.fromisoformat(e["date"])
                if parent is weekly:
                    iso = d.isocalendar()
                    key = f"{iso.year}-KW{iso.week:02d}"
                else: key = d.strftime("%Y-%m")
                g = groups.setdefault(key, {"count":0,"worked":0,"target":0,"diff":0})
                for k in ("count",): g[k] += 1
                for k in ("worked","target","diff"): g[k] += int(e.get(k,0))
            for key, g in sorted(groups.items(), reverse=True):
                tree.insert("", "end", values=(key,g["count"],fmt_minutes(g["worked"]),fmt_minutes(g["target"]),fmt_minutes(g["diff"],True)))
        ttk.Label(self.main, text="Hinweis: Auswertungen summieren die gespeicherten Tageswerte. Änderungen am Soll ändern bestehende Einträge nicht automatisch.", style="Subtitle.TLabel").pack(anchor="w", padx=30, pady=(0, 14))

    # Formular für Sollzeiten, Pausen, Zeitmodelle und Darstellung.
    def page_settings(self):
        self._header("Einstellungen", "Änderungen gelten für neue bzw. erneut gespeicherte Einträge.")
        panel = self._panel(self.main, 20)
        panel.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        s = self.daten.einstellungen
        vars = {"week": tk.StringVar(value=fmt_minutes(s["wochen_soll"])), "breakfast": tk.StringVar(value=str(s["fruehstueckspause"])),
                "lunch": tk.StringVar(value=str(s["mittagspause"])), "appearance": tk.StringVar(value=s.get("appearance", "System"))}
        ttk.Label(panel, text="Sollzeiten und Pausen", font=("Segoe UI", 13, "bold")).grid(row=0,column=0,columnspan=4,sticky="w",pady=(0,12))
        settings_fields = [("Wochen-Soll (HH:MM)","week"),("Frühstückspause (Minuten)","breakfast"),("Mittagspause (Minuten)","lunch")]
        for i,(label,key) in enumerate(settings_fields, start=1):
            ttk.Label(panel,text=label).grid(row=i,column=0,sticky="w",pady=7,padx=(0,15))
            ttk.Entry(panel,textvariable=vars[key],width=18).grid(row=i,column=1,sticky="w",pady=7)
        ttk.Label(panel,text="Tages-Sollzeiten",font=("Segoe UI",13,"bold")).grid(row=4,column=0,columnspan=4,sticky="w",pady=(20,8))
        day_vars = {}
        for i,day in enumerate(WOCHENTAGE[:5]):
            var = tk.StringVar(value=fmt_minutes(int(s["tages_soll"].get(str(i),468))))
            day_vars[str(i)] = var
            ttk.Label(panel,text=day).grid(row=5+i,column=0,sticky="w",pady=5)
            ttk.Entry(panel,textvariable=var,width=18).grid(row=5+i,column=1,sticky="w",pady=5)
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
                ttk.Entry(inner,textvariable=a,width=7).pack(side="left")
                ttk.Label(inner,text="–").pack(side="left",padx=3)
                ttk.Entry(inner,textvariable=b,width=7).pack(side="left")
        ttk.Label(panel,text="Darstellung").grid(row=16,column=0,sticky="w",pady=(18,6))
        ttk.Combobox(panel,textvariable=vars["appearance"],values=("System","Hell","Dunkel"),state="readonly",width=15).grid(row=16,column=1,sticky="w",pady=(18,6))
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
                messagebox.showinfo("Gespeichert","Einstellungen gespeichert. Die Darstellung wird aktualisiert.")
                self._setup_style()
                self.show_page("Einstellungen")
            except (ValueError, OSError) as exc: messagebox.showerror("Einstellungen prüfen",str(exc))
        ttk.Button(buttons,text="Standardeinstellungen laden",command=lambda:self.reset_settings()).pack(side="left")
        ttk.Button(buttons,text="Speichern",style="Accent.TButton",command=save).pack(side="right")

    # Setzt die Einstellungen nach Rückfrage auf Standardwerte zurück.
    def reset_settings(self):
        from arbeitszeit_core import DEFAULT_SETTINGS, clean_settings
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
