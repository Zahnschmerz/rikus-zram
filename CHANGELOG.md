# Was sich geändert hat / Changelog

Alle Fassungen von Rikus Zram, neueste zuerst.
All releases of Rikus Zram, newest first.

---

## 1.2 — 19. Juli 2026

**🇩🇪 Die Installationsanleitung war falsch. Das ist der Grund für diese Fassung.**

- **Behoben: Die Anleitungen nannten eine Datei, die es nicht mehr gab.** Nach der Veröffentlichung von 1.1 stand in allen vier Anleitungen weiter `rikus-zram_1.0_all.deb`. Wer den Befehl abtippte, bekam „Datei nicht gefunden".
- **Behoben: Der Terminal-Befehl scheiterte auch mit richtiger Versionsnummer.** Er begann mit `./` und setzte damit stillschweigend voraus, dass man im Ordner *Downloads* steht. Ein Terminal startet aber im persönlichen Ordner. Jetzt steht der vollständige Pfad im Befehl, und er funktioniert von überall.
- **Neu: Die Anleitungen sagen jetzt, WO man die Datei herunterlädt.** Vorher stand das nirgends.
- **Neu: Der Doppelklick ist überall der Hauptweg**, das Terminal nur noch die Alternative — passend zum Versprechen „ohne Terminal".
- **Der Installationsbefehl kann nicht mehr veralten:** Statt einer festen Versionsnummer steht dort jetzt ein Platzhalter.
- Aufgeräumt: eine vergessene Sicherungskopie aus dem Paket und eine aus dem Quellcode entfernt; die Lizenzdatei und dieses Änderungsprotokoll liegen jetzt bei.
- Das Paket meldet der Paketverwaltung jetzt seine Größe (vorher stand dort „0 Byte").

*Am Programm selbst hat sich nichts geändert — nur an Verpackung und Anleitung.*

**🇬🇧 The install instructions were wrong. That is why this release exists.**

- **Fixed: the guides named a file that no longer existed.** After 1.1 was published, all four guides still said `rikus-zram_1.0_all.deb`. Copying the command gave "file not found".
- **Fixed: the terminal command failed even with the right version number.** It started with `./`, silently assuming you were inside your *Downloads* folder — but a terminal starts in your home folder. The command now carries the full path and works from anywhere.
- **New: the guides now say WHERE to download the file.** That was missing entirely.
- **New: double-click is the primary route everywhere**, the terminal only an alternative — matching the "no terminal needed" promise.
- **The install command can no longer go stale:** a placeholder replaces the hard-coded version number.
- Cleanup: removed a forgotten backup file from the package and one from the source tree; the licence file and this changelog now ship with it.
- The package now reports its installed size (it previously showed "0 bytes").

*No change to the program itself — packaging and documentation only.*

---

## 1.1 — 18. Juli 2026

**🇩🇪 Richtet zram jetzt auch dort ein, wo noch gar keins vorhanden ist.** Das war von Anfang an der Sinn des Programms und fehlte in 1.0.

- **zram von Grund auf einrichten:** installiert `zram-tools`, schreibt die Einstellungen, schaltet den Dienst ein — und hält ihn auch über einen Neustart hinweg an.
- **Läuft auch auf Systemen ohne systemd:** `zram-tools` bringt *nur* eine systemd-Startdatei mit. Auf MX Linux, antiX und Devuan würde nach der Installation deshalb schlicht *nichts* starten, ohne jede Fehlermeldung. Rikus Zram legt dort das passende Startskript selbst an.
- **Ein fehlgeschlagener Dienststart wirft nicht mehr alles weg:** Vorher gingen dabei die Einstellungen für swappiness und Swap-Datei stillschweigend verloren.
- Längere Wartezeit, wenn ein Paket erst heruntergeladen werden muss, mit klarem Hinweis, dass dafür eine Internetverbindung nötig ist.

**🇬🇧 Now sets zram up on machines that have none yet.** That was the whole point of the program, and it was missing from 1.0.

- **Set up zram from scratch:** installs `zram-tools`, writes the settings, switches the service on — and keeps it on after a reboot.
- **Works on systems without systemd:** `zram-tools` ships *only* a systemd unit, so on MX Linux, antiX and Devuan nothing would start at all after installing it — silently. Rikus Zram writes the matching init script there.
- **A failing service start no longer aborts everything:** swappiness and swap-file changes used to be lost silently when zram could not start.
- Longer timeout when a package has to be downloaded, with a clear warning that an internet connection is needed.

---

## 1.0 — 18. Juli 2026

**🇩🇪 Erste Veröffentlichung.** zram, swappiness und Swap-Dateien mit Schiebereglern statt Terminal: Ist-Zustand mit Ampel und Klartext-Urteil, eine aus der Hardware errechnete Empfehlung, Vorschau vor jeder Änderung, Sicherung jeder angefassten Datei, Nachmessung und Rückgängig-Knopf. Deutsch und Englisch, systemd und SysVinit.

**🇬🇧 First release.** zram, swappiness and swap files with sliders instead of a terminal: current state with a traffic light and a plain-language verdict, a recommendation calculated from your hardware, a preview before every change, a backup of every file touched, verification afterwards and an undo button. German and English, systemd and SysVinit.
