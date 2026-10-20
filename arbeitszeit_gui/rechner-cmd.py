# Terminalversion des Arbeitszeitrechners. Daten werden mit der GUI geteilt.
from datetime import datetime
from arbeitszeit_core import ArbeitszeitDaten, parse_date, parse_duration, fmt_minutes, WOCHENTAGE

class Arbeitszeit:
    def __init__(self):
        self.daten = ArbeitszeitDaten()
        self.eintraege = self.daten.eintraege

    def tag_erfassen(self):
        try:
            datum_text = input("Datum (TT.MM.JJJJ): ").strip()
            datum = parse_date(datum_text)
            start = input("Beginn (HH:MM): ").strip()
            ende = input("Ende (HH:MM): ").strip()
            standard = input(f"Standardpausen verwenden? (J/n) [Frühstück {self.daten.einstellungen['fruehstueckspause']} min, Mittag {self.daten.einstellungen['mittagspause']} min]: ").strip().lower()
            if standard in ("n", "nein"):
                fr = parse_duration(input("Frühstückspause (HH:MM): "))
                mi = parse_duration(input("Mittagspause (HH:MM): "))
            else:
                fr = int(self.daten.einstellungen["fruehstueckspause"])
                mi = int(self.daten.einstellungen["mittagspause"])
            notes = input("Notizen (optional): ").strip()
            old = self.daten.eintraege.get(datum.isoformat())
            e = self.daten.berechnen(datum.strftime("%d.%m.%Y"), start, ende, fr, mi, notes, old["id"] if old else None)
            self.daten.speichern(e)
            print(f"Gespeichert: {e['day']} – Netto {fmt_minutes(e['worked'])}, Differenz {fmt_minutes(e['diff'], True)}")
        except (ValueError, OSError) as exc:
            print(f"Fehler: {exc}")

    def liste_anzeigen(self):
        total = 0
        for e in self.daten.sortiert(reverse=False):
            total += e["diff"]
            print(f"{e['id']:>3} | {e['date']} | {e['day']:<10} | {e['start']}–{e['end']} | Pause {e['breakfast']+e['lunch']} min | {fmt_minutes(e['diff'], True)} | {e.get('notes','')}")
        print(f"Gesamtdifferenz: {fmt_minutes(total, True)}")

    def eintrag_loeschen(self):
        ident = input("ID des Eintrags: ").strip()
        found = next((e for e in self.daten.eintraege.values() if str(e["id"]) == ident), None)
        if not found:
            print("ID nicht gefunden.")
        elif input(f"Eintrag {found['date']} wirklich löschen? (j/N): ").lower() == "j":
            self.daten.loeschen(found["date"])
            self.eintraege = self.daten.eintraege
            print("Gelöscht.")

    def arbeitszeit_einstellungen(self):
        s = self.daten.einstellungen
        while True:
            print("\nEinstellungen: 1 Wochen-Soll, 2 Tages-Soll, 3 Pausen, 4 Arbeitszeitmodelle anzeigen, 5 zurück")
            auswahl = input("> ").strip()
            try:
                if auswahl == "1":
                    s["wochen_soll"] = parse_duration(input("Wochen-Soll (HH:MM): "))
                    print("Wochen-Soll gespeichert. Tages-Sollwerte werden nicht automatisch verändert.")
                elif auswahl == "2":
                    for i, day in enumerate(WOCHENTAGE[:5]):
                        value = input(f"{day} Soll (HH:MM, leer = unverändert): ").strip()
                        if value:
                            s["tages_soll"][str(i)] = parse_duration(value)
                elif auswahl == "3":
                    s["fruehstueckspause"] = parse_duration(input("Frühstückspause (HH:MM): "))
                    s["mittagspause"] = parse_duration(input("Mittagspause (HH:MM): "))
                elif auswahl == "4":
                    for i, day in enumerate(WOCHENTAGE[:5]):
                        print(day, s["zeiten"][str(i)])
                elif auswahl == "5":
                    self.daten.einstellungen_speichern()
                    return
                else:
                    print("Bitte eine gültige Auswahl eingeben.")
            except ValueError as exc:
                print(f"Fehler: {exc}")

    def starten(self):
        while True:
            print("\n=== Arbeitszeitrechner ===\n1 Eintrag erfassen\n2 Einträge anzeigen\n3 Markdown exportieren\n4 Eintrag löschen\n5 Einstellungen\n6 Beenden")
            wahl = input("> ").strip()
            if wahl == "1": self.tag_erfassen()
            elif wahl == "2": self.liste_anzeigen()
            elif wahl == "3":
                self.daten.exportieren(); print(f"Export gespeichert: {self.daten.dateipfad}")
            elif wahl == "4": self.eintrag_loeschen()
            elif wahl == "5": self.arbeitszeit_einstellungen()
            elif wahl == "6":
                self.daten.einstellungen_speichern(); self.daten.exportieren(); print("Gespeichert. Tschüss!"); break
            else: print("Ungültige Auswahl.")

if __name__ == "__main__":
    Arbeitszeit().starten()
