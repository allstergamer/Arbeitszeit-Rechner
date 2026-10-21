"""Gemeinsame Daten- und Berechnungslogik für Arbeitszeitrechner (GUI und CLI)."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import json
import sys

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

DEFAULT_SETTINGS = {
    "fruehstueckspause": 20,
    "mittagspause": 30,
    "wochen_soll": 39 * 60,
    "tages_soll": {str(i): 468 for i in range(5)},
    "zeiten": {
        "0": {"flex": ["07:00", "17:00"], "kern": ["08:00", "15:00"], "regel": ["07:30", "16:15"]},
        "1": {"flex": ["07:00", "17:00"], "kern": ["08:00", "15:00"], "regel": ["07:30", "16:15"]},
        "2": {"flex": ["07:00", "17:00"], "kern": ["08:00", "15:00"], "regel": ["07:30", "16:15"]},
        "3": {"flex": ["07:00", "17:00"], "kern": ["08:00", "15:00"], "regel": ["07:30", "16:15"]},
        "4": {"flex": ["07:00", "15:15"], "kern": ["08:00", "12:00"], "regel": ["07:30", "14:30"]},
    },
    "appearance": "System",
}


def app_dir() -> Path:
    """Ordner neben Skript bzw. portablem EXE; CLI und GUI teilen dort ihre Daten."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("Datum bitte als TT.MM.JJJJ eingeben.")


def parse_time(value: str) -> int:
    try:
        h, m = value.strip().split(":", 1)
        h, m = int(h), int(m)
    except (ValueError, AttributeError):
        raise ValueError("Uhrzeit bitte im Format HH:MM eingeben.")
    if h < 0 or h > 23 or m < 0 or m > 59:
        raise ValueError("Ungültige Uhrzeit. Erlaubt ist 00:00 bis 23:59.")
    return h * 60 + m


def parse_duration(value: str) -> int:
    try:
        h, m = value.strip().split(":", 1)
        h, m = int(h), int(m)
    except (ValueError, AttributeError):
        raise ValueError("Dauer bitte im Format HH:MM eingeben.")
    if h < 0 or m < 0 or m > 59:
        raise ValueError("Ungültige Dauer. Beispiel: 07:48")
    return h * 60 + m


def fmt_minutes(minutes: int, signed: bool = False) -> str:
    sign = "-" if minutes < 0 else ("+" if signed and minutes > 0 else "")
    minutes = abs(int(minutes))
    return f"{sign}{minutes // 60:02d}:{minutes % 60:02d}"



def parse_diff(value: str) -> int:
    value = value.strip().replace("−", "-")
    sign = -1 if value.startswith("-") else 1
    value = value.lstrip("+-")
    if ":" in value:
        h, m = value.split(":", 1)
        return sign * (int(h) * 60 + int(m))
    return int(value) * sign


def clean_settings(data: dict) -> dict:
    """Fehlende Schlüssel älterer Einstellungsdateien mit Standards ergänzen."""
    result = json.loads(json.dumps(DEFAULT_SETTINGS))
    if isinstance(data, dict):
        for key in ("fruehstueckspause", "mittagspause", "wochen_soll", "appearance"):
            if key in data:
                result[key] = data[key]
        if isinstance(data.get("tages_soll"), dict):
            result["tages_soll"].update({str(k): int(v) for k, v in data["tages_soll"].items()})
        if isinstance(data.get("zeiten"), dict):
            for day, models in data["zeiten"].items():
                if day in result["zeiten"] and isinstance(models, dict):
                    for model in ("flex", "kern", "regel"):
                        if model in models and isinstance(models[model], list) and len(models[model]) == 2:
                            result["zeiten"][day][model] = models[model]
    return result


class ArbeitszeitDaten:
    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory else app_dir()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.dateipfad = self.directory / "arbeitszeitnachweis.md"
        self.einstellungen_pfad = self.directory / "arbeitszeit_einstellungen.json"
        self.einstellungen = self.einstellungen_laden()
        self.eintraege: dict[str, dict] = {}
        self.naechste_id = 1
        self.laden()

    def einstellungen_laden(self) -> dict:
        if self.einstellungen_pfad.exists():
            try:
                return clean_settings(json.loads(self.einstellungen_pfad.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return clean_settings({})

    def einstellungen_speichern(self) -> None:
        self.einstellungen_pfad.write_text(
            json.dumps(self.einstellungen, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def tages_soll(self, datum: date) -> int:
        if datum.weekday() > 4:
            return 0
        return int(self.einstellungen["tages_soll"].get(str(datum.weekday()), 468))

    def berechnen(self, datum_text: str, start_text: str, ende_text: str,
                  fruehstueck: int, mittag: int, notizen: str = "",
                  identifier: int | None = None, azv: bool = False) -> dict:
        datum = parse_date(datum_text)
        start = parse_time(start_text)
        ende = parse_time(ende_text)
        if ende <= start:
            ende += 24 * 60  # Ende am Folgetag / Nachtschicht
        brutto = ende - start
        if fruehstueck < 0 or mittag < 0 or fruehstueck + mittag >= brutto:
            raise ValueError("Pausen müssen mindestens 0 Minuten betragen und kürzer als die Anwesenheitszeit sein.")
        netto = brutto - fruehstueck - mittag
        soll = self.tages_soll(datum)
        return {
            "id": identifier or self.naechste_id,
            "date": datum.isoformat(),
            "day": WOCHENTAGE[datum.weekday()],
            "start": start_text.strip(),
            "end": ende_text.strip(),
            "breakfast": int(fruehstueck),
            "lunch": int(mittag),
            "worked": netto,
            "target": soll,
            # Bei AZV wird die tatsächliche Arbeitszeit behalten, aber keine Differenz gebucht.
            "diff": 0 if azv else netto - soll,
            "azv": bool(azv),
            "notes": notizen.strip(),
        }

    def speichern(self, eintrag: dict) -> None:
        datum = eintrag["date"]
        old = self.eintraege.get(datum)
        if old:
            eintrag["id"] = old["id"]
        else:
            eintrag["id"] = int(eintrag.get("id") or self.naechste_id)
            self.naechste_id = max(self.naechste_id, eintrag["id"] + 1)
        self.eintraege[datum] = eintrag
        self.exportieren()

    def loeschen(self, datum: str) -> bool:
        if datum not in self.eintraege:
            return False
        del self.eintraege[datum]
        self.exportieren()
        return True

    def sortiert(self, reverse: bool = True) -> list[dict]:
        return sorted(self.eintraege.values(), key=lambda x: x["date"], reverse=reverse)

    def laden(self) -> None:
        self.eintraege = {}
        if not self.dateipfad.exists():
            return
        try:
            lines = self.dateipfad.read_text(encoding="utf-8").splitlines()
        except OSError:
            return
        for line in lines:
            if "<!-- naechste_id:" in line:
                try:
                    self.naechste_id = max(self.naechste_id, int(line.split(":", 1)[1].split("-->")[0].strip()))
                except ValueError:
                    pass
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5 or cells[0].startswith("-") or cells[0].lower() == "id":
                continue
            try:
                if len(cells) >= 10:  # neues Format mit AZV und Notizen
                    ident, d, day, start, end, breakfast, lunch, diff, azv_text, notes = cells[:10]
                    azv = azv_text.lower() in ("ja", "true", "1", "x")
                    worked = None
                elif len(cells) >= 9:  # bisheriges Format inklusive Notizen
                    ident, d, day, start, end, breakfast, lunch, diff, notes = cells[:9]
                    azv, worked = False, None
                elif len(cells) >= 8:  # älteres Format
                    ident, d, day, start, end, breakfast, lunch, diff = cells[:8]
                    notes, azv, worked = "", False, None
                elif len(cells) == 6:  # ältere Version ohne Pausen
                    ident, d, day, start, end, diff = cells
                    breakfast, lunch, notes, azv, worked = 0, 0, "", False, None
                else:  # sehr altes Format ohne ID und Pausen
                    d, day, start, end, diff = cells[:5]
                    ident, breakfast, lunch, notes, azv, worked = self.naechste_id, 0, 0, "", False, None
                datum = parse_date(d).isoformat()
                dt = date.fromisoformat(datum)
                start_min = parse_time(start)
                end_min = parse_time(end)
                if end_min <= start_min:
                    end_min += 1440
                target = self.tages_soll(dt)
                netto = end_min - start_min - int(breakfast) - int(lunch)
                entry = {"id": int(ident), "date": datum, "day": day or WOCHENTAGE[dt.weekday()],
                         "start": start, "end": end, "breakfast": int(breakfast), "lunch": int(lunch),
                         "worked": netto, "target": target,
                         "diff": 0 if azv else parse_diff(diff), "azv": azv, "notes": notes}
                # Altdaten behalten ihre gespeicherte Differenz; neue Einträge werden normal berechnet.
                self.eintraege[datum] = entry
                self.naechste_id = max(self.naechste_id, int(ident) + 1)
            except (ValueError, IndexError, TypeError):
                continue

    def exportieren(self) -> None:
        rows = ["# Arbeitszeitnachweis", "", "| ID | Datum | Wochentag | Beginn | Ende | Frühstück (min) | Mittag (min) | Differenz | AZV | Notizen |",
                "|---:|---|---|---:|---:|---:|---:|---:|---:|---|"]
        total = 0
        for e in sorted(self.eintraege.values(), key=lambda x: x["date"]):
            total += int(e.get("diff", 0))
            notes = str(e.get("notes", "")).replace("|", "\\|").replace("\n", " ")
            azv_text = "Ja" if e.get("azv", False) else "Nein"
            rows.append(f"| {e['id']} | {e['date']} | {e['day']} | {e['start']} | {e['end']} | {e['breakfast']} | {e['lunch']} | {fmt_minutes(e['diff'], True)} | {azv_text} | {notes} |")
        rows += ["", f"**Gesamtdifferenz:** {fmt_minutes(total, True)}", "", f"<!-- naechste_id: {self.naechste_id} -->", ""]
        self.dateipfad.write_text("\n".join(rows), encoding="utf-8")

    def neu_berechnen(self, datum: str) -> None:
        """Sollzeit nach Settingsänderung für genau diesen Eintrag aktualisieren."""
        e = self.eintraege[datum]
        updated = self.berechnen(datetime.strptime(datum, "%Y-%m-%d").strftime("%d.%m.%Y"), e["start"], e["end"],
                                 e["breakfast"], e["lunch"], e.get("notes", ""), e["id"], e.get("azv", False))
        self.eintraege[datum] = updated
