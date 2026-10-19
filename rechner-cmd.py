# code for a terminal based application to track work hours
# montag bis donnerstag:
# gleitzeit begin 7:00 untill 17:00
# kernzeit Begi 8:00 untill 15:00
# Regelarbeitszeit 7:30 untill 16:15
# freitags:
# gleitzeit begin 7:00 untill 15:15
# kernzeit Begi 8:00 untill 12:00
# Regelarbeitszeit 7:30 untill 14:30
# print rest time in minutes plus and negative 

# zeit wird manuell eingetragen, pausen werden automatisch abgezogen, wenn sie nicht angegeben werden. angabe in stunden und minuten einzeln

#zum convert fuer PDF:
# python -m pip install reportlab


from datetime import datetime
from pathlib import Path


class Arbeitszeit:
    FRUEHSTUECKSPAUSE = 20
    MITTAGSPAUSE = 30
    GESAMTPAUSE = FRUEHSTUECKSPAUSE + MITTAGSPAUSE

    DATEIPFAD = Path("arbeitszeitnachweis.md")

    ZEITEN = {
        "montag": {
            "gleitzeit": ("07:00", "17:00"),
            "kernzeit": ("08:00", "15:00"),
            "regel": ("07:30", "16:15"),
        },
        "dienstag": {
            "gleitzeit": ("07:00", "17:00"),
            "kernzeit": ("08:00", "15:00"),
            "regel": ("07:30", "16:15"),
        },
        "mittwoch": {
            "gleitzeit": ("07:00", "17:00"),
            "kernzeit": ("08:00", "15:00"),
            "regel": ("07:30", "16:15"),
        },
        "donnerstag": {
            "gleitzeit": ("07:00", "17:00"),
            "kernzeit": ("08:00", "15:00"),
            "regel": ("07:30", "16:15"),
        },
        "freitag": {
            "gleitzeit": ("07:00", "15:15"),
            "kernzeit": ("08:00", "12:00"),
            "regel": ("07:30", "14:30"),
        },
    }

    def __init__(self):
        self.eintraege = {}
        self.naechste_id = 1
        self.laden()

    @staticmethod
    def uhrzeit_eingeben(text):
        while True:
            eingabe = input(f"{text} (HH:MM): ").strip()

            try:
                zeit = datetime.strptime(eingabe, "%H:%M")
                return zeit.hour * 60 + zeit.minute
            except ValueError:
                print("Ungültige Uhrzeit. Beispiel: 07:30")

    @staticmethod
    def datum_eingeben():
        while True:
            eingabe = input(
                "Datum (TT.MM.JJ oder TT.MM.JJJJ): "
            ).strip()

            try:
                teile = eingabe.split(".")
                if len(teile) != 3:
                    raise ValueError

                tag, monat, jahr = teile

                if len(jahr) == 2:
                    jahr_zahl = int(jahr)
                    jahr = str(
                        2000 + jahr_zahl
                        if jahr_zahl <= 69
                        else 1900 + jahr_zahl
                    )
                elif len(jahr) != 4:
                    raise ValueError

                datum = f"{tag.zfill(2)}.{monat.zfill(2)}.{jahr}"
                datetime.strptime(datum, "%d.%m.%Y")
                return datum

            except ValueError:
                print("Ungültiges Datum. Beispiel: 19.10.26")

    @staticmethod
    def format_minuten(minuten):
        vorzeichen = "+" if minuten > 0 else ""
        stunden, rest = divmod(abs(minuten), 60)

        if minuten < 0:
            return f"-{stunden}:{rest:02d}"

        return f"{vorzeichen}{stunden}:{rest:02d}"

    @staticmethod
    def uhrzeit_text(minuten):
        return f"{minuten // 60:02d}:{minuten % 60:02d}"

    @staticmethod
    def uhrzeit_in_minuten(text):
        stunde, minute = map(int, text.split(":"))
        return stunde * 60 + minute

    @staticmethod
    def differenz_einlesen(text):
        text = text.strip()
        negativ = text.startswith("-")
        text = text.lstrip("+-")

        stunden_text, minuten_text = text.split(":")
        minuten = int(stunden_text) * 60 + int(minuten_text)

        return -minuten if negativ else minuten

    def tag_eingeben(self):
        while True:
            tag = input(
                "Wochentag (Montag bis Freitag): "
            ).strip().lower()

            if tag in self.ZEITEN:
                return tag

            print("Bitte einen gültigen Wochentag eingeben.")

    def tag_erfassen(self):
        tag = self.tag_eingeben()
        datum = self.datum_eingeben()

        start = self.uhrzeit_eingeben("Arbeitsbeginn")
        ende = self.uhrzeit_eingeben("Arbeitsende")

        if ende <= start:
            print("Arbeitsende muss nach Arbeitsbeginn liegen.")
            return

        arbeitszeit = ende - start - self.GESAMTPAUSE

        regel_start_text, regel_ende_text = (
            self.ZEITEN[tag]["regel"]
        )

        regel_start = self.uhrzeit_in_minuten(regel_start_text)
        regel_ende = self.uhrzeit_in_minuten(regel_ende_text)

        sollzeit = regel_ende - regel_start - self.GESAMTPAUSE
        differenz = arbeitszeit - sollzeit

        # Bei einem bestehenden Datum bleibt die ID erhalten.
        if datum in self.eintraege:
            eintrag_id = self.eintraege[datum]["id"]
            print("Vorhandener Eintrag wird ersetzt.")
        else:
            eintrag_id = self.naechste_id
            self.naechste_id += 1

        self.eintraege[datum] = {
            "id": eintrag_id,
            "datum": datum,
            "tag": tag.capitalize(),
            "beginn": self.uhrzeit_text(start),
            "ende": self.uhrzeit_text(ende),
            "differenz": differenz,
        }

        print(f"Eintrag mit ID {eintrag_id} gespeichert.")
        print(f"Tagesdifferenz: {self.format_minuten(differenz)}")

    def sortierte_eintraege(self):
        return sorted(
            self.eintraege.values(),
            key=lambda e: datetime.strptime(
                e["datum"], "%d.%m.%Y"
            ),
        )

    def liste_anzeigen(self):
        if not self.eintraege:
            print("Keine Arbeitstage erfasst.")
            return

        print("\n--- Arbeitszeitnachweis ---")
        print(
            f"{'ID':<5} {'Datum':<12} {'Wochentag':<14} "
            f"{'Beginn':<8} {'Ende':<8} {'Differenz':>12}"
        )
        print("-" * 67)

        for e in self.sortierte_eintraege():
            print(
                f"{e['id']:<5} "
                f"{e['datum']:<12} "
                f"{e['tag']:<14} "
                f"{e['beginn']:<8} "
                f"{e['ende']:<8} "
                f"{self.format_minuten(e['differenz']):>12}"
            )

        gesamt = sum(
            e["differenz"] for e in self.eintraege.values()
        )

        print("-" * 67)
        print(f"Gesamtdifferenz: {self.format_minuten(gesamt)}")

    def laden(self):
        if not self.DATEIPFAD.exists():
            return

        try:
            with self.DATEIPFAD.open(
                "r", encoding="utf-8"
            ) as datei:
                for zeile in datei:
                    zeile = zeile.strip()

                    # Nächste ID auch nach dem Löschen aller
                    # Einträge über Neustarts hinweg erhalten.
                    if zeile.startswith("<!-- naechste_id:"):
                        try:
                            wert = zeile.split(":", 1)[1]
                            wert = wert.split("-->", 1)[0].strip()
                            self.naechste_id = max(
                                self.naechste_id, int(wert)
                            )
                        except ValueError:
                            pass
                        continue

                    if not zeile.startswith("|"):
                        continue

                    teile = [
                        teil.strip()
                        for teil in zeile.strip("|").split("|")
                    ]

                    try:
                        # Neues Format: ID | Datum | Tag | Beginn | Ende | Differenz
                        if len(teile) == 6:
                            eintrag_id = int(teile[0])
                            datum, tag, beginn, ende, diff_text = teile[1:]

                        # Altes Format ohne ID:
                        # Datum | Tag | Beginn | Ende | Differenz
                        elif len(teile) == 5:
                            datum, tag, beginn, ende, diff_text = teile
                            eintrag_id = self.naechste_id
                            self.naechste_id += 1
                        else:
                            continue

                        datetime.strptime(datum, "%d.%m.%Y")
                        differenz = self.differenz_einlesen(diff_text)

                        eintrag = {
                            "id": eintrag_id,
                            "datum": datum,
                            "tag": tag,
                            "beginn": beginn,
                            "ende": ende,
                            "differenz": differenz,
                        }

                        self.eintraege[datum] = eintrag
                        self.naechste_id = max(
                            self.naechste_id, eintrag_id + 1
                        )

                    except (ValueError, IndexError):
                        # Kopfzeile und Markdown-Trennzeile ignorieren.
                        continue

            print(f"{len(self.eintraege)} Einträge geladen.")

        except OSError as fehler:
            print(f"Datei konnte nicht gelesen werden: {fehler}")

    def exportieren(self):
        gesamt = sum(
            e["differenz"] for e in self.eintraege.values()
        )

        try:
            with self.DATEIPFAD.open(
                "w", encoding="utf-8"
            ) as datei:
                datei.write("# Arbeitszeitnachweis\n\n")
                datei.write(f"<!-- naechste_id: {self.naechste_id} -->\n\n")
                datei.write(
                    "| ID | Datum | Wochentag | Beginn | Ende | Differenz |\n"
                )
                datei.write(
                    "|---:|-------|-----------|--------|------|----------:|\n"
                )

                for e in self.sortierte_eintraege():
                    datei.write(
                        f"| {e['id']} | {e['datum']} | {e['tag']} | "
                        f"{e['beginn']} | {e['ende']} | "
                        f"{self.format_minuten(e['differenz'])} |\n"
                    )

                datei.write(
                    "\n**Gesamtdifferenz: "
                    f"{self.format_minuten(gesamt)} Stunden**\n"
                )

            print(f"Datei gespeichert: {self.DATEIPFAD.resolve()}")

        except OSError as fehler:
            print(f"Fehler beim Speichern: {fehler}")

    def eintrag_loeschen(self):
        if not self.eintraege:
            print("Keine Einträge vorhanden.")
            return

        self.liste_anzeigen()
        eingabe = input("\nID des zu löschenden Eintrags: ").strip()

        try:
            eintrag_id = int(eingabe)
        except ValueError:
            print("Bitte eine gültige ID eingeben.")
            return

        for datum, eintrag in list(self.eintraege.items()):
            if eintrag["id"] == eintrag_id:
                bestaetigung = input(
                    f"Eintrag {eintrag_id} vom {datum} löschen? (j/n): "
                ).strip().lower()

                if bestaetigung == "j":
                    del self.eintraege[datum]
                    self.exportieren()
                    print(f"Eintrag mit ID {eintrag_id} gelöscht.")
                else:
                    print("Löschen abgebrochen.")
                return

        print(f"Kein Eintrag mit ID {eintrag_id} gefunden.")

    def starten(self):
        while True:
            print("\n--- Arbeitszeiterfassung ---")
            print("1. Arbeitstag erfassen")
            print("2. Liste anzeigen")
            print("3. Markdown-Datei speichern")
            print("4. Eintrag löschen")
            print("5. Beenden")

            auswahl = input("Auswahl: ").strip()

            if auswahl == "1":
                self.tag_erfassen()
            elif auswahl == "2":
                self.liste_anzeigen()
            elif auswahl == "3":
                self.exportieren()
            elif auswahl == "4":
                self.eintrag_loeschen()
            elif auswahl == "5":
                self.exportieren()
                break
            else:
                print("Ungültige Auswahl.")


if __name__ == "__main__":
    app = Arbeitszeit()
    app.starten()
