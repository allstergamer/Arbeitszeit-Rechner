# Arbeitszeit-Rechner

Ein in Python entwickelter Arbeitszeit-Rechner zur Erfassung von Arbeitstagen und zur Berechnung von Arbeitszeitdifferenzen. Das Projekt bietet derzeit eine Anwendung für das Terminal. Eine grafische Benutzeroberfläche ist für die Zukunft geplant.

Die Terminal-Version (`rechner-cmd.py`) wird auch nach der Entwicklung der grafischen Anwendung separat verfügbar bleiben.

## Funktionen

- **Arbeitstage erfassen:** Wochentag, Datum, Arbeitsbeginn und Arbeitsende manuell eingeben.
- **Automatische Pausenberechnung:** Eine Frühstückspause von 20 Minuten und eine Mittagspause von 30 Minuten werden automatisch abgezogen.
- **Arbeitszeitdifferenz berechnen:** Anzeige der täglichen Differenz zur hinterlegten Regelarbeitszeit mit positivem oder negativem Vorzeichen.
- **Einträge verwalten:** Erfasste Arbeitstage anzeigen und einzelne Einträge über ihre eindeutige ID löschen.
- **Doppelte Einträge vermeiden:** Wird ein bereits erfasstes Datum erneut eingegeben, wird der vorhandene Eintrag aktualisiert.
- **Dauerhafte Speicherung:** Arbeitstage werden in einer Markdown-Datei gespeichert und beim nächsten Programmstart wieder geladen.
- **Übersichtliche Ausgabe:** Die erfassten Arbeitstage werden chronologisch sortiert angezeigt.
- **Flexible Datumseingabe:** Datumsangaben sind sowohl mit zweistelliger als auch mit vierstelliger Jahreszahl möglich.

## Arbeitszeitregelungen

Die folgenden Zeiten sind im aktuellen Programm hinterlegt:

| Regelung | Montag–Donnerstag | Freitag |
|---|---|---|
| Gleitzeit | 07:00–17:00 Uhr | 07:00–15:15 Uhr |
| Kernzeit | 08:00–15:00 Uhr | 08:00–12:00 Uhr |
| Regelarbeitszeit | 07:30–16:15 Uhr | 07:30–14:30 Uhr | 
| Frühstückspause | 20 Minuten | 20 Minuten |
| Mittagspause | 30 Minuten | 30 Minuten |

Die Pausen werden bei der Berechnung der täglichen Arbeitszeit und der Sollzeit berücksichtigt.
Die Zeiten von Freitag sind so noch nicht eindeutig und bedarf Rücksprache

**Hinweis:** Die aktuelle Berechnung vergleicht die erfasste Arbeitszeit mit der hinterlegten täglichen Regelarbeitszeit.

## Voraussetzungen

- Python 3
- Keine zusätzlichen Python-Pakete für die Terminal-Version erforderlich

## Installation und Start

1. Repository herunterladen oder klonen.
2. Ein Terminal im Projektverzeichnis öffnen.
3. Das Programm starten:

```bash
python rechner-cmd.py
```

Unter Windows kann alternativ der Python Launcher verwendet werden, sofern er installiert und verfügbar ist:

```powershell
py rechner-cmd.py
```

## Bedienung

Nach dem Start erscheint ein Menü mit folgenden Optionen:

1. **Arbeitstag erfassen** – einen neuen Arbeitstag eintragen oder einen bestehenden Eintrag aktualisieren.
2. **Liste anzeigen** – alle gespeicherten Einträge und die Gesamtdifferenz anzeigen.
3. **Markdown-Datei speichern** – den aktuellen Stand in die Datei schreiben.
4. **Eintrag löschen** – einen Eintrag anhand seiner ID auswählen und nach Bestätigung löschen.
5. **Beenden** – die Daten speichern und das Programm schließen.

### Datumseingabe

Datumsangaben können beispielsweise in folgenden Formaten eingegeben werden:

- `19.10.26`
- `19.10.2026`

## Datenspeicherung

Die Einträge werden in der Datei `arbeitszeitnachweis.md` gespeichert. Diese Datei wird im aktuellen Arbeitsverzeichnis des Programms angelegt.

Die gespeicherten Daten umfassen:

- ID des Eintrags
- Datum
- Wochentag
- Arbeitsbeginn
- Arbeitsende
- Arbeitszeitdifferenz

Die Markdown-Datei kann mit einem Texteditor geöffnet und gelesen werden. Sie lässt sich außerdem in vielen Markdown-Viewern übersichtlich darstellen.

**Wichtig:** Bewahre die Datei `arbeitszeitnachweis.md` auf, wenn du deine erfassten Arbeitszeiten behalten möchtest.

## Geplante Entwicklung

Das Projekt soll zukünftig um eine grafische Benutzeroberfläche erweitert werden.

Geplante Ziele:

- Grafische Eingabe von Datum und Arbeitszeiten
- Übersichtliche Darstellung der gespeicherten Arbeitstage
- Einträge über die Oberfläche hinzufügen, bearbeiten und löschen
- Anzeige der täglichen und gesamten Arbeitszeitdifferenz
- Weiterhin eine eigenständig nutzbare Terminal-Version anbieten

Die grafische Anwendung wird als zusätzliche Anwendung entwickelt. Die bestehende Datei `rechner-cmd.py` soll weiterhin separat verfügbar und ausführbar bleiben.

## Projekt

GitHub-Repository: [allstergamer/Arbeitszeit-Rechner](https://github.com/allstergamer/Arbeitszeit-Rechner)

Aktuelle Terminal-Version: [rechner-cmd.py](https://github.com/allstergamer/Arbeitszeit-Rechner/blob/main/rechner-cmd.py)
