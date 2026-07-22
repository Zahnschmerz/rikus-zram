# Was sich geändert hat / Changelog

Alle Fassungen von Rikus Zram, neueste zuerst.
All releases of Rikus Zram, newest first.

---

## 1.17 — 22. Juli 2026

**🔴 🇩🇪 Wichtig: Eine Änderung der zram-Größe griff bisher erst nach einem Neustart des Rechners.**

- **Das Problem:** Ein zram-Gerät kann seine Größe **nicht ändern, solange es als Auslagerung aktiv ist**. Das Programm schrieb den neuen Wert korrekt in die Einstellungsdatei und startete den Dienst neu — aber der Schreibversuch auf das Gerät scheiterte still. Im Systemprotokoll stand: *„Schreibfehler: Das Gerät oder die Ressource ist belegt"*. Der Dienst meldete trotzdem Erfolg.
  **Folge:** Die Datei sagte 100 %, das Gerät blieb bei 51 %. Erst ein Neustart des ganzen Rechners hätte es in Ordnung gebracht. Gemessen auf einem Raspberry Pi.
- **Jetzt** wird das Gerät bei einer Größenänderung sauber abgeschaltet, zurückgesetzt und neu angelegt — die neue Größe gilt **sofort**.
- **Nur bei Größenänderungen.** Wird lediglich swappiness geändert, bleibt zram unangetastet — dann muss nichts zurück in den Arbeitsspeicher geschoben werden.
- Die **Nachmessung** hat den Widerspruch übrigens korrekt angezeigt (Datei 100 %, Gerät 51 %) — sie war die einzige Stelle, an der es überhaupt auffiel.

**🔴 🇬🇧 Important: a change to the zram size only took effect after a reboot.**

- **The problem:** a zram device cannot change its size while it is active as swap. The program wrote the new value to the config file and restarted the service — but the write to the device failed silently (*„Device or resource busy"* in the journal), while the service still reported success. The file said 100 %, the device stayed at 51 %.
- **Now** the device is properly switched off, reset and recreated on a size change — the new size applies **immediately**.
- **Only on size changes.** For a swappiness-only change zram is left alone, so nothing has to be moved back into RAM.
- The **verification step** did flag the contradiction correctly — it was the only place where this surfaced at all.

---

## 1.16 — 22. Juli 2026

**🔴 🇩🇪 Drei Fehler in den Empfehlungen — sie hätten zu unnötigen Änderungen geführt.**

**1. SSDs wurden für drehende Festplatten gehalten.**
Der Kernel meldet über USB-Gehäuse und bei virtuellen Platten fast immer „rotierend", weil die Information unterwegs verlorengeht. Gemessen auf drei Rechnern — darunter eine **Samsung SSD 850 EVO**, bei der das Wort SSD sogar im Namen steht. Das Programm glaubte es und schrieb: *„Etwas zurückhaltender, weil sich deine Platte dreht."* Es empfahl dadurch swappiness 120 statt 150.
Jetzt wird gegengeprüft: Nennt sich das Gerät selbst SSD/NVMe, gilt es als SSD. Hängt es an **USB** oder läuft der ganze Rechner **virtuell**, gilt die Angabe als **unbekannt** — und unbekannt wird wie SSD behandelt, statt eine falsche Begründung zu erfinden.

**2. Vorhandene Swap-Partitionen wurden übersehen.**
Die Empfehlung zählte nur Swap-**Dateien**. Auf einem Server lagen **31,9 GiB als Partition** bereit — das Programm sah „0 GiB" und empfahl, **33 GB anzulegen**. Völlig überflüssig, und auf einem gemieteten Server teurer Platz.
Jetzt zählen Partitionen mit. Ist bereits genug da, lautet die Empfehlung **0** — mit Begründung: *„Du hast bereits eine Swap-Partition mit 31,9 GiB als Reserve."*
⚠️ **Das Programm ändert Partitionen weiterhin nie** — es rechnet sie nur mit.

**3. Der Ruhezustand führte zu einer riesigen Empfehlung, ohne zu prüfen, ob dafür schon gesorgt ist.**
Ist er eingerichtet und reicht eine vorhandene Partition dafür aus, wird das jetzt erkannt und **nichts Zusätzliches** empfohlen. Reicht sie nicht, wird nur noch die **Differenz** vorgeschlagen — und die vorhandene Größe genannt.

**Nachtrag zu Punkt 3 (noch am selben Tag gefunden):** Die Ruhezustands-Prüfung war auch nach der ersten Korrektur noch zu grob — sie schaute nur, *ob* die Datei Text enthält. Die enthält aber praktisch immer welchen, auch Kommentare und auch die ausdrückliche Abschaltung `RESUME=none`. Gemessen auf einem Server: Nach dem Abschalten meldete das Programm weiterhin „Ruhezustand eingerichtet". Jetzt zählt nur noch ein **echtes Ziel** (UUID oder Gerätepfad) — `none`, `auto` und Kommentarzeilen nicht.

*Am Verhalten des Programms ändert sich sonst nichts: Es fasst nach wie vor nur Swap-Dateien an, niemals Partitionen.*

**🔴 🇬🇧 Three faults in the recommendations — they would have caused needless changes.**

**1. SSDs were taken for spinning disks.** Over USB enclosures and on virtual disks the kernel almost always reports „rotational", because the information is lost on the way. Measured on three machines — one a **Samsung SSD 850 EVO**, with SSD in its very name. The program believed it and wrote *„slightly more cautious because your disk is a spinning one"*, recommending swappiness 120 instead of 150.
It now cross-checks: if the device calls itself SSD/NVMe, it counts as one. If it sits behind **USB** or the machine runs **virtualised**, the value counts as **unknown** — and unknown is treated as SSD rather than inventing a false reason.

**2. Existing swap partitions were ignored.** The recommendation counted only swap **files**. One server had **31.9 GiB as a partition** ready — the program saw „0 GiB" and suggested creating **33 GB**. Entirely redundant.
Partitions now count. When enough is present the recommendation is **0**, with the reason given.
⚠️ **The program still never touches partitions** — it merely counts them.

**3. Hibernation produced a huge recommendation without checking whether it was already provided for.** If a partition covers it, nothing extra is suggested; if not, only the **difference** is.

---

## 1.14 — 22. Juli 2026

**🔴 🇩🇪 Wichtig: Das Programm erkennt jetzt, wenn ein ANDERES Werkzeug das zram regelt — und hält sich heraus.**

- **Das Problem:** Für zram gibt es zwei verbreitete Werkzeuge. Dieses Programm bedient **`zram-tools`** (`/etc/default/zramswap`, Dienst `zramswap`). Daneben gibt es den **`systemd-zram-generator`** (`/etc/systemd/zram-generator.conf`, Dienst `systemd-zram-setup@zram0`) — er ist verbreiteter, als lange angenommen: **auf drei von sechs geprüften Servern** war er im Einsatz, alle unter Debian 13.
- **Bis Fassung 1.13 hat das Programm ihn nicht bemerkt.** Es hätte dort eine eigene Konfiguration angelegt und einen zweiten Dienst gestartet — **zwei Werkzeuge für dieselbe Sache auf demselben Rechner**. Auf einem Server mit laufenden Diensten ein unnötiges Risiko.
- **Jetzt:** Das Programm erkennt den Fall, zeigt die dort geltenden Einstellungen (Größe, Verfahren, Priorität), **sperrt die Änderungs-Knöpfe** und sagt in Klartext, warum. **Anschauen und Messen funktioniert weiterhin.** Wer dort etwas ändern will, bekommt den passenden Weg genannt.
- **Doppelt abgesichert:** Neben den grauen Knöpfen prüft auch das Übernehmen selbst noch einmal — selbst wenn die Sperre je umgangen würde, wird nichts geändert.
- **Keine Auswirkung auf Rechner mit `zram-tools`:** Dort verhält sich alles wie bisher (gegengeprüft).

**🔴 🇬🇧 Important: the program now detects when ANOTHER tool manages zram — and stays out of the way.**

- **The problem:** Two common tools configure zram. This program operates **`zram-tools`** (`/etc/default/zramswap`, service `zramswap`). Alongside it there is **`systemd-zram-generator`** (`/etc/systemd/zram-generator.conf`, service `systemd-zram-setup@zram0`) — far more widespread than assumed: **three out of six servers checked** used it, all on Debian 13.
- **Up to release 1.13 the program did not notice.** It would have written its own configuration and started a second service — **two tools doing the same job on one machine**. On a server running live services, an unnecessary risk.
- **Now:** the program detects it, shows the settings in force there (size, algorithm, priority), **disables the apply buttons** and explains why in plain words. **Viewing and measuring still work.** Anyone wanting to change something is told the right way to do it.
- **Belt and braces:** besides the greyed-out buttons, the apply routine checks again — even if the lock were bypassed, nothing gets changed.
- **No effect on machines using `zram-tools`:** everything behaves as before (verified).

---

## 1.13 — 22. Juli 2026

**🔴 🇩🇪 Ein Rechenfehler beim zram-Regler — die genannte Datenmenge war um das 3,5-fache zu hoch.**

- **Behoben:** Beim zram-Regler stand *„zram-Größe 15,4 GiB. Bei etwa 3,5-facher Kompression entspricht das rund **54,0 GiB** an Daten, die hineinpassen."*
  Das war falsch. Die zram-Größe **ist bereits die Datenmenge**, die hineinpasst — das System rechnet sie schon unkomprimiert (`zramctl` nennt sie `DISKSIZE`). Das Programm hat eine Zahl, die schon multipliziert war, ein zweites Mal multipliziert.
  Jetzt steht dort: *„zram-Größe **15,4 GiB**. So viele Daten passen hinein — sie belegen dabei nur rund **4,4 GiB** echten Arbeitsspeicher. Es bleiben also rund **11,0 GiB** mehr für deine Programme übrig."*
- **Der Gewinn liegt nicht darin, dass mehr hineinpasst, sondern dass das Hineingelegte weniger Platz braucht.** Das ist derselbe Vorteil — nur richtig herum beschrieben.
- **Neu in beiden Anleitungen:** ein Kasten, der klarstellt, dass **zram den Arbeitsspeicher NICHT vergrößert**. Es liegt mitten darin — der Vakuumbeutel steht auf demselben Tisch. Mit einem Rechenbeispiel für 16 GB und der Abgrenzung zur Swap-Datei, die tatsächlich *zusätzlichen* Platz schafft (dafür rund 160-mal langsamer).

**🔴 🇬🇧 A miscalculation on the zram slider — the amount of data stated was 3.5× too high.**

- **Fixed:** the slider used to say *"zram size 15.4 GiB. At roughly 3.5× compression that holds about **54.0 GiB** of data."*
  Wrong: the zram size **already is** the amount of data that fits — the kernel counts it uncompressed (`zramctl` calls it `DISKSIZE`). The program multiplied a figure that was already multiplied.
  It now reads: *"zram size **15.4 GiB**. That much data fits in — occupying only about **4.4 GiB** of real RAM. That leaves around **11.0 GiB** more for your programs."*
- **The gain is not that more fits in, but that what goes in takes less room.** Same benefit — described the right way round.
- **New in both guides:** a box making clear that **zram does not make your RAM bigger**. It sits inside it. With a worked example for 16 GB and the distinction from a swap file, which genuinely adds space (but is around 160 times slower).

---

## 1.12 — 22. Juli 2026

**🔴 🇩🇪 Fünf Fehler — gefunden, weil das Programm zum ersten Mal auf einem fremden Rechner lief (Raspberry Pi 5, 15,8 GiB Arbeitsspeicher).**

**1. Wichtig: Die Ampel meldete „alles in Ordnung", obwohl zram nur halb so groß war wie möglich.**
Sie prüfte nur, *ob* zram läuft — nicht, *ob es groß genug ist*. Die Empfehlung wurde zwar berechnet, stand aber auf der zweiten Seite und wusste nichts von der Ampel. Auf dem Pi war zram auf 8 GiB eingestellt statt der empfohlenen 15,8 — die Ampel sagte trotzdem **grün**. Wer das liest, schaut nicht weiter und verschenkt dauerhaft die Hälfte.
Jetzt vergleicht die Ampel die eingestellte Größe mit der Empfehlung und wird **gelb**, wenn sie deutlich darunter liegt.
⚠️ **Kein Fehlalarm bei bewusst kleineren Werten:** Bei viel Arbeitsspeicher lautet die Empfehlung ohnehin 50 % — wer dort 50 % eingestellt hat, bleibt grün. Gewarnt wird erst unterhalb von drei Vierteln der Empfehlung.

**2. Die erste Seite sagte nicht, wie viel eingestellt ist und was fehlt.**
Im zram-Kasten stand nur die Größe — ob das viel oder wenig ist, nirgends. Wer „8,0 GiB" liest, kann nicht wissen, dass 15,8 möglich wären. Jetzt steht direkt darunter:
*„Das sind 51 % deines Arbeitsspeichers (15,8 GiB). Empfohlen wären 15,8 GiB (100 %) — es fehlen 7,8 GiB."*
Dasselbe beim Swap-Kasten: *„Empfohlen wären 2,0 GiB als Reserve — es fehlen 1,8 GiB."* Passt die Einstellung, steht dort schlicht *„Das entspricht der Empfehlung."*

**3. Die Ampel war auf manchen Systemen ein leeres Kästchen.**
Sie bestand aus einem farbigen Emoji (🟢🟡🔴), das nur wenige Schriften kennen — auf dem Testrechner **keine einzige**. Betroffen waren auch die Zeichen für Update-Hinweis, Ruhezustand und btrfs-Warnung. Jetzt steht dort ein schlichter Punkt **●**, den praktisch jede Schrift kann; die Farbe setzt das Programm ohnehin selbst.

**4. Eine irreführende Kompressionsangabe bei fast leerem zram.**
Standen nur wenige Kilobyte darin, erschien z. B. *„16,0 KiB Daten belegen nur 48,0 KiB — das ist 0,3-fach"*. Das liest sich wie miserable Kompression, ist aber nur der Verwaltungsaufwand von zram, der bei leerem Speicher naturgemäß größer ist als die Daten. Die Rate erscheint jetzt erst ab 10 MiB.

**5. Auf großen Bildschirmen war das Fenster unnötig abgeschnitten.**
Es war fest auf 800 Pixel Höhe eingestellt; die Kästen *Einstellungen*, *Dieses System* und *Und weiter?* lagen darunter. Man konnte rollen, aber nichts wies darauf hin. Die Fensterhöhe richtet sich jetzt nach dem Bildschirm.

**🔴 🇬🇧 Five fixes — found the first time the program ran on someone else's machine (Raspberry Pi 5, 15.8 GiB of RAM).**

**1. Important: the traffic light reported "all good" while zram was only half the size it could be.**
It only checked *whether* zram was running, not *whether it is large enough*. The recommendation was computed but lived on the second page, unknown to the light. On the Pi, zram was set to 8 GiB instead of the recommended 15.8 — and the light still said **green**. Anyone reading that stops looking and permanently gives away half.
The light now compares the configured size against the recommendation and turns **amber** when it falls well below.
⚠️ **No false alarms for deliberately smaller values:** with plenty of RAM the recommendation is 50 % anyway, so 50 % stays green. The warning starts below three quarters of the recommendation.

**2. The first page never said how much is configured and what is missing.**
The zram panel showed only the size — never whether that is a lot or a little. It now reads: *"That is 51 % of your RAM (15.8 GiB). The recommendation would be 15.8 GiB (100 %) — 7.8 GiB short."* The same for the swap panel. When the setting fits, it simply says *"That matches the recommendation."*

**3. On some systems the traffic light was an empty box.**
It used a coloured emoji (🟢🟡🔴) that few fonts carry — **none at all** on the test machine. The same applied to the update hint, hibernation and btrfs symbols. They are now a plain **●**, which virtually every font has; the colour comes from the program itself anyway.

**4. A misleading compression figure when zram is nearly empty.**
With only a few kilobytes inside it read e.g. *"16.0 KiB of data occupy 48.0 KiB — that is 0.3×"*, which looks like terrible compression but is merely zram's own overhead. The ratio now appears from 10 MiB upwards.

**5. On large screens the window was cut off for no reason.**
Its height was fixed at 800 pixels, leaving *Settings*, *This machine* and *What next?* below the edge. You could scroll, but nothing indicated it. The height now follows the screen.

---

## 1.11 — 22. Juli 2026

**🇩🇪 Die Zahlen passen jetzt zu dem, was andere Programme anzeigen.**

- **Behoben: Das Programm schrieb „GB", rechnete aber in GiB.** An 34 Stellen stand die Einheit falsch — bei 15,43 GiB Arbeitsspeicher hieß es „15,4 GB". Die Zahl stimmte, die Einheit nicht: 15,4 GB wären 14,3 GiB, also fast ein Gigabyte weniger. Jetzt steht überall **GiB**, so wie Linux tatsächlich rechnet und wie es auch `fastfetch`, `htop` und `free` anzeigen.
- **Neu: Die Gesamtsumme der Auslagerung steht jetzt da.** Bisher zeigte das Programm zram und Swap-Datei nur einzeln — die Summe, die jedes andere Werkzeug anzeigt, nirgends. Wer 2 GiB Swap-Datei sah und in fastfetch 17,4 GiB, musste schließen, dass eine der beiden Zahlen falsch ist.
  Jetzt steht unter „Swap": **„Zusammen 17,4 GiB Auslagerung — davon 15,4 GiB zram (im Arbeitsspeicher) und 2,0 GiB auf der Platte"**, mit dem Hinweis, dass andere Programme nur diese Summe zeigen, weil Linux zram ebenfalls als Auslagerung führt.
- **Warum das wichtig war:** Beide Darstellungen waren technisch richtig — aber wer sie nebeneinander sah, musste das Programm für falsch halten. Ein Programm, das den Nutzer an sich zweifeln lässt, hat seine Aufgabe verfehlt.

**🇬🇧 The numbers now match what other tools show.**

- **Fixed: the program said "GB" but calculated in GiB.** The unit was wrong in 34 places — 15.43 GiB of RAM was labelled "15.4 GB". The figure was right, the unit was not: 15.4 GB would be 14.3 GiB, almost a gigabyte less. It now says **GiB** throughout, matching how Linux actually counts and what `fastfetch`, `htop` and `free` display.
- **New: the swap total is now shown.** The program listed zram and the swap file separately, but never the total that every other tool reports. Seeing 2 GiB of swap file here and 17.4 GiB in fastfetch, you could only conclude that one of them was lying.
  Under "Swap" it now reads **"17.4 GiB of swap in total — of that 15.4 GiB zram (inside RAM) and 2.0 GiB on disk"**, explaining that other tools show only this total because Linux treats zram as swap too.
- **Why this mattered:** both views were technically correct — but seeing them side by side, you had to conclude the program was wrong. A program that makes its user doubt it has failed at its job.

---

## 1.10 — 21. Juli 2026

**🇩🇪 Das Programm sagt jetzt Bescheid, wenn es eine neuere Fassung gibt.**

- **Neu: Update-Hinweis.** Beim Start schaut das Programm einmal nach, ob auf GitHub eine neuere Fassung liegt. Wenn ja, erscheint unter dem Titel eine kleine grüne Zeile: „🔔 Version X ist verfügbar — ansehen", mit Link zur Download-Seite. **Es wird nichts heruntergeladen und nichts installiert** — nur der Hinweis.
- **Warum das nötig war:** Das Programm kommt als `.deb` über GitHub und ist damit *keine* apt-Quelle. `apt update` erfährt also nie von einer neuen Fassung — man bliebe auf einer alten sitzen, ohne es zu merken.
- **Diese Fassung ist gleich die Nagelprobe:** Von 1.9 auf **1.10** ist genau der Sprung, bei dem eine schlampige Prüfung versagt — als Text gelesen ist „1.10" *kleiner* als „1.9", der Hinweis bliebe ab jetzt für immer aus. Hier werden Versionen in Zahlen zerlegt und als Zahlen verglichen; der Fall ist eigens geprüft.
- **Was der Hinweis NICHT tut:** Er hält das Fenster nicht auf (eigener Hintergrund-Vorgang mit 4-Sekunden-Grenze). Er stürzt nicht ab (schlägt etwas fehl, bleibt die Zeile einfach weg). Er braucht **kein zusätzliches Paket**. Und er übersteht den Neuaufbau des Fensters nach einer Änderung — eigens nachgemessen.
- **Abschaltbar:** `touch ~/.config/rikus-zram/kein-update-hinweis` — dann fragt das Programm gar nicht mehr nach. Steht in beiden Anleitungen.

**🇬🇧 The program now tells you when a newer version is out.**

- **New: update hint.** At startup the program checks once whether a newer release exists on GitHub. If so, a small green line appears below the title: „🔔 Version X is available — view", linking to the download page. **Nothing is downloaded and nothing is installed.**
- **Why:** The program ships as a `.deb` via GitHub and is therefore *not* an apt source, so `apt update` never learns about newer versions.
- **This release is the acid test:** Going from 1.9 to **1.10** is exactly the step where a sloppy check fails — read as text, „1.10" is *smaller* than „1.9". Here versions are split into numbers and compared as numbers; that case is explicitly tested.
- **What it does not do:** It never blocks the window (background check, 4-second limit), never crashes (on failure the line simply stays hidden), needs **no extra package**, and survives the window rebuild after a change — verified.
- **Can be switched off:** `touch ~/.config/rikus-zram/kein-update-hinweis`. Documented in both guides.

---

## 1.9 — 21. Juli 2026

**🇩🇪 Der Ruhezustand wird jetzt erklärt, statt nur genannt.**

- **Auf der ersten Seite** stand bisher nur „Dein Rechner könnte den Ruhezustand (hibernate), er ist aber nicht eingerichtet". Wer den Begriff nicht kennt, weiß damit nichts anzufangen — und er wird oft mit der Bereitschaft verwechselt, in die ein Laptop beim Zuklappen geht. Jetzt steht dort, **was** dabei passiert (der ganze Arbeitsspeicher wandert auf die Platte, der Rechner geht komplett aus), **worin der Unterschied zur Bereitschaft** liegt, und **welche zwei Dinge** nötig wären.
- **Die entscheidende Zahl fehlte.** Es hieß „eine Swap-Datei wäre nötig", aber nicht wie groß. Jetzt wird die konkrete Größe für **diesen** Rechner genannt — bei 16 GB Arbeitsspeicher also mindestens 16 GB — zusammen mit der aktuell vorhandenen Größe.
- **Der zweite nötige Schritt wurde verschwiegen.** Selbst mit ausreichend großer Datei funktioniert der Ruhezustand nicht ohne den `resume=`-Eintrag in der Startkonfiguration. **Dieses Programm setzt ihn bewusst nicht** — es fasst den Startvorgang nicht an. Wer nur den Regler hochschob, stand danach ratlos da. Jetzt steht es klar dabei.
- **Beim Swap-Regler** erscheint zusätzlich die Marke „ab X GB wäre der Ruhezustand möglich" — mit demselben Vorbehalt.
- **Beide Anleitungen** haben statt drei Zeilen jetzt einen vollständigen Abschnitt mit einer Tabelle Herunterfahren / Bereitschaft / Ruhezustand und dem Selbst-Prüfbefehl `cat /sys/power/state`.

*Am Programm selbst hat sich nichts geändert — nur an dem, was es erklärt.*

**🇬🇧 Hibernation is now explained rather than merely named.**

- **The first page** used to say only "This machine could hibernate, but it is not set up". Anyone unfamiliar with the term learns nothing from that — and it is easily confused with the standby a laptop enters when you close the lid. It now says **what** happens (the whole of RAM goes to disk, the machine switches off completely), **how it differs from standby**, and **which two things** would be required.
- **The decisive number was missing.** It said "would need a swap file", but not how large. The concrete size for **this** machine is now given — with 16 GB of RAM, at least 16 GB — alongside the size currently present.
- **The second required step was left out.** Even with a large enough file, hibernation does not work without the `resume=` entry in the boot configuration. **This program deliberately does not set it** — it does not touch the boot process. Anyone who merely raised the slider was left puzzled. That is now stated plainly.
- **The swap slider** additionally shows "from X GB up, hibernation would be possible" — with the same caveat.
- **Both guides** now have a full section with a shutdown / standby / hibernation table and the self-check command `cat /sys/power/state`, instead of three lines.

*No change to the program itself — only to what it explains.*

---

## 1.8 — 21. Juli 2026

**🔴 🇩🇪 Wichtig: Bis Fassung 1.7 konnte beim Ändern der Swap-Datei eine ZWEITE angelegt werden, statt die vorhandene zu ersetzen.**

- **Behoben: Das Programm suchte die vorhandene Swap-Datei am falschen Ort.** Es nahm an, sie liege unter `/swap/swapfile` — dort, wo es selbst eine anlegen würde. Auf Linux Mint (und den meisten anderen Systemen) liegt sie aber unter **`/swapfile`**. Folge: Abschalten, Eintrag entfernen und Löschen liefen ins Leere, und danach wurde eine **zusätzliche** Datei angelegt. Wer 2 GB hatte und 4 GB einstellte, bekam **2 GB + 4 GB gleichzeitig** — und beim nächsten Öffnen rechnete das Programm mit der Summe weiter.
  Jetzt wird die Datei genommen, die das Programm **tatsächlich gemessen** hat (aus `/proc/swaps`). Auch mehrere vorhandene Dateien werden alle sauber entfernt.
- **Neu abgesichert: Swap-Partitionen werden nachweislich nie angefasst.** Das Programm versprach das schon immer, prüfte es aber nicht. Jetzt werden ausschließlich Einträge vom Typ *file* entfernt; eine Swap-**Partition** bleibt unberührt, und die Vorschau sagt das ausdrücklich.
- Die Vorschau nennt jetzt den **echten Pfad** der Datei, die entfernt wird — nicht mehr einen angenommenen.

> ⚠️ **Wer 1.7 oder älter benutzt und die Swap-Datei geändert hat:** Bitte mit `swapon --show` nachsehen. Stehen dort **zwei** Dateien, ist die überflüssige gefahrlos zu entfernen — abschalten, Zeile aus `/etc/fstab` nehmen, Datei löschen.

**🔴 🇬🇧 Important: up to release 1.7, changing the swap file could create a SECOND one instead of replacing the existing one.**

- **Fixed: the program looked for the existing swap file in the wrong place.** It assumed `/swap/swapfile` — where it would create one itself. On Linux Mint (and most other systems) it lives at **`/swapfile`**. So switching off, removing the fstab line and deleting all ran into nothing, and an **additional** file was created. Someone with 2 GB who set 4 GB ended up with **2 GB + 4 GB at once** — and on the next start the program carried on from the sum.
  It now uses the file it has **actually measured** (from `/proc/swaps`). Several existing files are all removed properly.
- **Newly guaranteed: swap partitions are provably never touched.** The program always promised this but never checked. Only entries of type *file* are removed now; a swap **partition** is left alone, and the preview says so explicitly.
- The preview now names the **real path** of the file being removed, not an assumed one.

> ⚠️ **If you use 1.7 or older and changed the swap file:** please check with `swapon --show`. If **two** files are listed, the surplus one can safely be removed — switch it off, drop its line from `/etc/fstab`, delete the file.

---

## 1.7 — 19. Juli 2026

**🔴 🇩🇪 Der Terminal-Befehl aus der Anleitung fand die heruntergeladene Datei nicht.**

- **Behoben: Ein Zeichen im Befehl war falsch.** Zum Herunterladen werden zwei Dateien angeboten — `rikus-zram_1.6_all.deb` (mit **Unterstrich**) und `rikus-zram-neueste.deb` (mit **Bindestrich**). Der Befehl in der Anleitung lautete `rikus-zram_*.deb` und passte damit **nur auf die erste**. Wer die zweite geladen hatte, bekam „keine Treffer" und konnte nicht installieren.
  Jetzt heißt es `rikus-zram*.deb` — das passt auf **beide**.
- **Behoben: Die Anleitung sagte „die Datei, die auf `.deb` endet".** Davon gibt es zwei. Jetzt wird die Datei **beim Namen genannt** (`rikus-zram-neueste.deb`), und der Download-Verweis führt **direkt auf diese Datei** statt auf die Liste aller Anhänge.

*Am Programm selbst hat sich nichts geändert.*

**🔴 🇬🇧 The terminal command from the guide did not find the downloaded file.**

- **Fixed: one character in the command was wrong.** Two files are offered for download — `rikus-zram_1.6_all.deb` (with an **underscore**) and `rikus-zram-neueste.deb` (with a **hyphen**). The guide said `rikus-zram_*.deb`, which matches **only the first one**. Anyone who downloaded the second got "no matches" and could not install.
  It now reads `rikus-zram*.deb`, which matches **both**.
- **Fixed: the guide said "the file ending in `.deb`".** There are two of those. The file is now **named explicitly** (`rikus-zram-neueste.deb`), and the download link points **directly at that file** instead of at the list of assets.

*No change to the program itself.*

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
