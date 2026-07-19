# Was sich geändert hat / Changelog

Alle Fassungen von Rikus Zram, neueste zuerst.
All releases of Rikus Zram, newest first.

---

## 1.6 — 19. Juli 2026

**🔴 🇩🇪 Auf btrfs konnte die Swap-Datei verloren gehen, wenn `btrfs-progs` fehlte.**

- **Behoben: Datenverlust bei fehlendem `btrfs-progs`.** Beim Anlegen einer Swap-Datei auf btrfs löschte das Programm zuerst die alte Swap-Datei (abschalten, `fstab`-Eintrag entfernen, Datei löschen) und legte den btrfs-Bereich **erst danach** an. War das Paket `btrfs-progs` nicht installiert, brach es genau dazwischen ab — **der Rechner hatte hinterher weniger Swap als vorher, und der `fstab`-Eintrag war weg.** Jetzt wird **vorher** geprüft und mit einer klaren Meldung abgebrochen, **bevor irgendetwas angefasst wird**.
- **Behoben: Die RAID-Warnung schlug still nicht an.** Auf einem btrfs über mehrere Platten kann Linux keine Swap-Datei betreiben. Die Warnung dafür fragte `btrfs` ab — fehlte das Werkzeug, kam eine leere Antwort zurück, und die Warnung blieb aus. „Werkzeug fehlt" war nicht von „kein RAID" zu unterscheiden.
- **Abhängigkeiten vervollständigt:** `btrfs-progs` ist von *empfohlen* auf *erforderlich* hochgestuft, und **`mount` ist ergänzt** — daher kommen `swapon` und `swapoff`, und anders als `util-linux` ist es kein Grundbestandteil des Systems, muss also eingetragen sein.

> ⚠️ **Wer 1.5 oder älter auf einem btrfs-System benutzt hat:** Bitte mit `swapon --show` nachsehen, ob die Swap-Datei noch da ist. Betroffen war nur, wer eine Swap-Datei auf btrfs anlegen ließ **ohne** installiertes `btrfs-progs`.

**🔴 🇬🇧 On btrfs the swap file could be lost when `btrfs-progs` was missing.**

- **Fixed: data loss when `btrfs-progs` is absent.** When creating a swap file on btrfs, the program removed the old swap file first (swapoff, drop the `fstab` line, delete the file) and created the btrfs subvolume **afterwards**. Without `btrfs-progs` it aborted exactly in between — **the machine ended up with less swap than before, and the `fstab` entry was gone.** It now checks **first** and stops with a clear message **before touching anything**.
- **Fixed: the RAID warning silently never fired.** Linux cannot run a swap file on a btrfs spanning several disks. That warning queried `btrfs` — with the tool missing the answer was empty, so the warning never triggered. "Tool missing" was indistinguishable from "no RAID".
- **Dependencies completed:** `btrfs-progs` moved from *recommended* to *required*, and **`mount` added** — it provides `swapon` and `swapoff`, and unlike `util-linux` it is not an essential system component, so it has to be declared.

> ⚠️ **If you used 1.5 or older on a btrfs system:** please check with `swapon --show` whether your swap file is still there. Only affected: creating a swap file on btrfs **without** `btrfs-progs` installed.

---

## 1.5 — 19. Juli 2026

**🔴 🇩🇪 Wichtig: In den Fassungen 1.1 bis 1.4 funktionierten „Vorschau" und „Übernehmen" überhaupt nicht.**

- **Behoben: Das Programm stürzte beim Übernehmen ab.** Beim Einbau der Funktion „zram einrichten" in Fassung 1.1 wurde ein Wert abgefragt, der nie bereitgestellt wurde (`KeyError: 'zram'`). Folge: **Ein Druck auf „Vorschau" oder „Übernehmen …" brach still ab — das Programm konnte den Rechner nur noch anzeigen, aber nichts mehr ändern.** Betroffen sind alle Fassungen von 1.1 bis 1.4. Fassung 1.0 war nicht betroffen.
  **Wer 1.1 bis 1.4 benutzt hat: Es wurde nichts kaputtgemacht** — das Programm brach ab, *bevor* es irgendetwas geschrieben hat. Nur ändern ließ sich nichts.
- **Behoben: Deutscher Text in der englischen Oberfläche.** Der Kasten „Dieses System" auf der ersten Seite war nicht übersetzt — englische Nutzer lasen dort „Startsystem" und „drehende Festplatte".

**Geprüft:** In einer frischen virtuellen Maschine **ohne jedes zram** eingerichtet und nachgemessen: zram läuft danach (zstd, 100 % des RAM, als Swap eingehängt), die Einstellungsdatei ist angelegt, der Dienst ist eingeschaltet — **und nach einem Neustart ist zram von allein wieder da**.

**🔴 🇬🇧 Important: in releases 1.1 through 1.4, "Preview" and "Apply" did not work at all.**

- **Fixed: the program crashed on applying.** When the "set up zram" feature was added in 1.1, a value was read that was never provided (`KeyError: 'zram'`). As a result, **pressing "Preview" or "Apply …" aborted silently — the program could only display your machine, never change it.** All releases from 1.1 to 1.4 are affected; 1.0 was not.
  **If you used 1.1–1.4: nothing was damaged** — the program aborted *before* writing anything. It simply could not apply.
- **Fixed: German text in the English interface.** The "This machine" box on the first page was left untranslated.

**Verified:** set up in a fresh virtual machine with **no zram at all** and measured afterwards: zram runs (zstd, 100 % of RAM, mounted as swap), the settings file is written, the service is enabled — **and after a reboot zram comes back on its own**.

---

## 1.4 — 19. Juli 2026

**🇩🇪 Auf älteren MX-Linux- und antiX-Fassungen ließ sich das Paket gar nicht installieren.**

- **Behoben: Abhängigkeit erfüllbar auf Debian 11.** Das Paket verlangte `polkitd` **und** `pkexec`. Diese beiden Pakete gibt es erst ab Debian 12 — auf Debian 11 (also **MX 21 und antiX 21**) steckt beides im Paket `policykit-1`. Dort brach `apt` mit „Abhängigkeit nicht erfüllbar" ab, obwohl das Programm ausdrücklich mit diesen Systemen wirbt. Jetzt steht dort eine Ausweichmöglichkeit (`polkitd | policykit-1`), sodass auf jedem System das passende Paket genommen wird.

*Am Programm selbst hat sich nichts geändert.*

**🇬🇧 On older MX Linux and antiX releases the package could not be installed at all.**

- **Fixed: dependencies now resolvable on Debian 11.** The package required `polkitd` **and** `pkexec`. Those packages only exist from Debian 12 onwards — on Debian 11 (**MX 21 and antiX 21**) both live inside `policykit-1`, so `apt` aborted with an unsatisfiable dependency, even though the program explicitly advertises those systems. An alternative (`polkitd | policykit-1`) now picks whichever package the system has.

*No change to the program itself.*

---

## 1.3 — 19. Juli 2026

**🇩🇪 Das Programm öffnete auf der falschen Seite.**

- **Behoben: Beim Start stand das Fenster auf „Empfehlung & Regler" statt auf der Übersicht.** Anleitung und Webseite versprechen beide, dass die erste Seite den Ist-Zustand zeigt und dort nichts verändert wird — der Nutzer landete aber sofort bei den Schiebereglern. Ursache: Das Fenster gibt beim Öffnen dem ersten bedienbaren Element den Fokus, das ist ein Schieberegler auf der zweiten Seite, und die Reiterleiste folgt dem Fokus. Der Fehler steckte seit Fassung 1.0 drin.
- Beim Knopf **„Neu messen"** bleibt man jetzt auf dem Reiter, auf dem man gerade ist.

**🇬🇧 The program opened on the wrong page.**

- **Fixed: on startup the window showed "Recommendation & sliders" instead of the overview.** Both the guide and the website promise that the first page shows your current state and changes nothing — but users landed straight on the sliders. Cause: on opening, the window gives focus to the first focusable widget, which is a slider on the second page, and the notebook follows the focus. Present since 1.0.
- The **"Measure again"** button now keeps you on the tab you are on.

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
