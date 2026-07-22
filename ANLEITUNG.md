# Rikus Zram — Anleitung (Deutsch)

**Arbeitsspeicher besser nutzen — ohne ein einziges getipptes Kommando.**
Von Gilbert Rikus · Freie Software (GPL-3.0)

---

## 1. Was ist das überhaupt?

Stell dir deinen Arbeitsspeicher (RAM) als **Schreibtisch** vor. Alles, woran der Rechner gerade arbeitet, liegt darauf. Wird der Tisch voll, muss etwas weichen.

Linux hat dafür zwei Möglichkeiten:

**Swap — die Ablage auf der Festplatte.**
Selten gebrauchte Sachen wandern von der Tischplatte in einen Aktenschrank. Der Tisch wird frei, aber jedes Zurückholen dauert — die Platte ist viel langsamer als der Arbeitsspeicher.

**zram — der Vakuumbeutel.**
Statt Sachen wegzuräumen, presst der Rechner sie **auf dem Tisch selbst** zusammen. Wie ein Vakuumbeutel für Winterkleidung: Es passt viel mehr hin, und nichts muss den Tisch verlassen. Deshalb ist es **um ein Vielfaches schneller** als der Aktenschrank.

Typisch werden Daten dabei **3- bis 4-fach** kleiner. Aus 4 GB Daten werden gut 1 GB belegter Speicher.

> ⚠️ **Wichtig zu verstehen: zram vergrößert deinen Arbeitsspeicher NICHT.**
> Es liegt **mitten darin**. Der Vakuumbeutel steht auf demselben Tisch — er nimmt selbst Platz weg, presst aber zusammen, was hineinkommt.
>
> **Ein Beispiel mit 16 GB Arbeitsspeicher:** In zram passen 16 GB Daten. Zusammengepresst belegen sie davon nur etwa 4,5 GB — **rund 11 GB bleiben also zusätzlich frei**. Der Rechner meldet weiterhin 16 GB Arbeitsspeicher, kommt damit aber deutlich weiter.
>
> Die **Swap-Datei auf der Festplatte** ist dagegen echter *zusätzlicher* Platz — dafür rund 160-mal langsamer.


**Und was macht dieses Programm?**
zram und Swap kann man unter Linux nur über getippte Befehle und das Bearbeiten von Systemdateien einstellen. Rikus Zram macht daraus ein Fenster mit Schiebereglern — mit Erklärung, was jeder Wert bedeutet, und einer Empfehlung für genau deinen Rechner.

---

## 2. Was du brauchst

- **Debian, Ubuntu, Linux Mint, LMDE, MX Linux, antiX, Zorin, Pop!\_OS** oder ein anderes System aus dieser Familie
- Dein normales Benutzerpasswort (nur beim Ändern, nicht beim Anschauen)
- Sonst nichts — alle benötigten Bausteine installiert das Paket mit

Das Programm läuft mit **systemd** und mit **SysVinit** (also auch auf MX Linux und antiX). Es merkt selbst, welches davon dein System benutzt.

---

## 3. Installieren

Dafür brauchst du **kein Terminal**.

**Schritt 1 — Herunterladen.**
Öffne die Download-Seite und klicke auf die Datei, die mit **`rikus-zram_`** anfängt und auf **`.deb`** endet (z. B. `rikus-zram_1.20_all.deb` — die Zahl ist die Fassung):

👉 **https://github.com/Zahnschmerz/rikus-zram/releases/latest**

Sie landet in deinem Ordner **Downloads**.

**Schritt 2 — Doppelklick.**
Öffne den Ordner **Downloads** und klicke die heruntergeladene Datei **doppelt** an. Das Installationsprogramm deines Systems geht auf, du klickst auf **„Paket installieren"** und gibst dein Passwort ein.

**Schritt 3 — Starten.**
**„Rikus Zram"** steht jetzt im Startmenü unter *System*.

### Lieber im Terminal?

Dieser eine Befehl genügt — er funktioniert aus **jedem** Ordner heraus:

```
cd ~/Downloads
sudo apt install ./rikus-zram_1.20_all.deb
```

Zuerst in den Ordner **Downloads** wechseln, dann die Datei **beim vollen Namen** nennen.

⚠️ **Warum nicht `rikus-zram*.deb` mit Stern?** Weil das schiefgehen kann. Liegen in deinem Downloads-Ordner mehrere Fassungen, sortiert die Standard-Kommandozeile (`bash`) sie *alphabetisch* — und dabei steht **1.9 hinter 1.19**. Gemessen am 22.07.2026 in einem frischen Debian 13: Der Stern-Befehl installierte die **alte 1.9** statt der neuen. Deshalb steht hier der volle Name.

Hast du über den Knopf **„neueste Fassung"** geladen, heißt deine Datei `rikus-zram-neueste.deb` — dann diesen Namen einsetzen.

⚠️ Bitte `apt install` benutzen, **nicht** `dpkg -i`: Nur `apt` holt fehlende Bausteine von selbst nach.

---

## 4. Die erste Seite: Was ist da?

Nach dem Start siehst du, wie es auf deinem Rechner gerade aussieht. **Hier wird nichts verändert — es wird nur geschaut.**

**Kurz gesagt** — eine Ampel mit Klartext-Urteil:
- 🟢 **Grün:** Alles in Ordnung
- 🟡 **Gelb:** Läuft, aber es gibt etwas anzuschauen
- 🔴 **Rot:** Weder zram noch Swap — bei vollem Speicher bricht ein Programm ab

Darunter stehen die Punkte, die dem Programm aufgefallen sind — im Klartext, nicht als Fehlernummer.

**Arbeitsspeicher** — wie viel belegt und wie viel frei ist.

**zram** — ob es läuft, wie groß es ist, welches Kompressionsverfahren (meist `zstd`) und **wie stark gerade zusammengepresst wird**. Steht dort „3 GB Daten belegen nur 0,8 GB", dann arbeitet zram gerade knapp vierfach.

**Swap** — ob es eine Auslagerungsdatei oder -partition gibt, wie groß, wie voll, und mit welcher **Priorität**.

**Einstellungen** — der Wert **swappiness** und was in der Konfigurationsdatei steht.

**Dieses System** — welche Distribution, welches Startsystem, ob SSD oder drehende Platte, welches Dateisystem.

Unten führt ein Knopf weiter zur zweiten Seite.

### ⭐ Wenn dein Rechner noch gar kein zram hat

Dann steht die Ampel auf **Rot** oder **Gelb**, und darunter liest du, dass zram bei dir noch nicht eingerichtet ist. **Das ist kein Problem — genau dafür ist dieses Programm da.**

Die zweite Seite bietet dir dann an, es **komplett einzurichten**:
1. das Paket `zram-tools` wird installiert (dafür brauchst du kurz Internet),
2. die Einstellungsdatei wird angelegt,
3. der Dienst wird eingeschaltet — **auch für jeden künftigen Start**, nicht nur für jetzt.

Du siehst vorher genau, was passieren wird, und musst es bestätigen.

**Warum das nicht selbstverständlich ist:** Das Paket `zram-tools` bringt nur eine Startdatei für **systemd** mit. Auf Systemen mit einem anderen Startverfahren — **MX Linux, antiX, Devuan** — würde nach der Installation schlicht *nichts* starten, ohne jede Fehlermeldung. Rikus Zram legt dort zusätzlich das passende Startskript an. Deshalb funktioniert es auch auf diesen Systemen.

---

### ⭐ Warum steht dort „GiB" und nicht „GB"?

Weil beides **nicht dasselbe** ist — und der Unterschied wächst mit der Größe:

| | rechnet mit | 16 Milliarden Bytes sind |
|---|---|---|
| **GB** (Gigabyte) | 1000 | 16,56 GB |
| **GiB** (Gibibyte) | 1024 | **15,43 GiB** |

**Linux rechnet mit 1024.** Deshalb zeigen `fastfetch`, `htop`, `free` und dieses Programm **GiB** — und deshalb steht auf einem Riegel „16 GB", während dein System 15,4 anzeigt. Es fehlt nichts, es wird nur anders gezählt.

Rikus Zram schreibt bewusst **GiB**, damit die Zahlen zu dem passen, was der Rest deines Systems anzeigt.

---

### ⚠️ Wenn ein anderes Werkzeug zuständig ist

Für zram gibt es **drei** verbreitete Werkzeuge:

| | Einstellungsdatei | Dienst |
|---|---|---|
| **zram-tools** — das bedient dieses Programm | `/etc/default/zramswap` | `zramswap` |
| **systemd-zram-generator** | `/etc/systemd/zram-generator.conf` | `systemd-zram-setup@zram0` |
| **rpi-swap** (Raspberry Pi OS) | `/etc/rpi/swap.conf` | `dev-zram0.swap` |

Läuft auf deinem Rechner der **zweite**, sagt Rikus Zram das auf der ersten Seite und **sperrt die Änderungs-Knöpfe**. Anschauen und Messen geht weiterhin — nur Ändern nicht, denn sonst gäbe es zwei Einrichtungen, die sich gegenseitig ins Gehege kommen.

Wer dort etwas ändern möchte, bearbeitet die Datei von Hand und lädt sie neu:

```
sudo systemctl restart systemd-zram-setup@zram0
```

---

## 5. Die zweite Seite: Was wäre besser?

Hier siehst du **drei Schieberegler**. Sie stehen auf dem, **was bei dir gerade läuft**. Auf der Skala darunter ist markiert, was für deinen Rechner **empfohlen** wäre — dorthin schiebst du selbst, wenn du möchtest.

Unter jedem Regler erklärt eine Zeile, was der eingestellte Wert bedeutet — sie ändert sich mit, während du schiebst. Und in Farbe steht dabei, ob du gerade auf deinem jetzigen Stand bist, auf der Empfehlung, oder auf etwas Drittem.

### Regler 1 — zram-Größe

In Prozent vom Arbeitsspeicher. **100 % ist der bewährte Wert:** zram so groß wie der Arbeitsspeicher. Das klingt viel, ist es aber nicht — der Platz wird erst belegt, wenn er gebraucht wird, und die Daten darin sind ja zusammengepresst.

Bei sehr viel Arbeitsspeicher (ab 32 GB) genügt die Hälfte.

### Regler 2 — swappiness

Ein Wert zwischen 0 und 200. Er sagt, **wie bereitwillig** der Rechner selten gebrauchte Daten beiseiteschiebt.

| Wert | Bedeutung |
|---|---|
| 0–20 | nur im äußersten Notfall auslagern |
| 60 | der Standard ohne zram |
| **150** | **offensiv — passend, wenn zram läuft** |
| 200 | sehr offensiv |

**Warum darf er mit zram so hoch sein?** Weil das Auslagern dann in den schnellen Arbeitsspeicher geht und nicht auf die langsame Platte. Es kostet also kaum etwas.

### Regler 3 — Swap-Datei

Die Reserve auf der Festplatte, in Gigabyte. Sie bleibt im Alltag leer und greift nur, wenn Arbeitsspeicher **und** zram voll sind — ein Sicherheitsnetz.

**Wann brauchst du sie?**
- **Wenig Arbeitsspeicher (bis 4 GB):** ja, unbedingt
- **8 bis 16 GB:** eine kleine Reserve von 2 GB schadet nicht
- **Ab 32 GB mit laufendem zram:** eigentlich nicht
- **Wenn du den Ruhezustand (hibernate) nutzen willst:** dann muss sie **mindestens so groß wie dein Arbeitsspeicher** sein — denn dabei wird der gesamte Speicherinhalt auf die Platte geschrieben, und **das kann zram nicht leisten**

---

## 6. Änderung übernehmen — was dabei passiert

Wenn die Regler so stehen, wie du es willst:

**Schritt 1 — „Zeigen, was geändert würde"**
Ein Fenster listet im Klartext auf, was passieren würde, welche Dateien vorher gesichert werden und welcher Dienst neu gestartet wird. **Es passiert dabei garantiert nichts** — das ist nur die Vorschau.

**Schritt 2 — „Übernehmen …"**
Dieselbe Liste, aber mit der Frage „Jetzt wirklich ändern?". Erst nach deinem Klick kommt die **Passwortabfrage**.

**Schritt 3 — die Nachmessung**
Danach misst das Programm **selbst nach**, ob die Änderung wirklich gegriffen hat, und zeigt dir das mit ✔ oder ✖ pro Punkt. Kein „müsste jetzt passen" — es wird nachgeschaut.

### Was das Programm dabei für dich absichert

- **Jede Datei wird vorher gesichert** (`<datei>.bak-rikuszram-<datum>`)
- **Es prüft vorher, ob genug Platz da ist** — und bricht mit Begründung ab, wenn nicht
- **Es warnt, wenn gerade Daten ausgelagert sind**, die beim Abschalten zurück in den Arbeitsspeicher müssten
- **Es fasst keine Swap-Partitionen an**, nur Dateien — Partitionen zu verändern könnte Daten zerstören
- **Es räumt keine fremden Ordner weg**

---

## 7. Rückgängig machen

Gibt es Sicherungen, erscheint auf der zweiten Seite ein Knopf **„Rückgängig"**. Ein Klick stellt den Zustand von vor der Änderung wieder her.

Von Hand geht es auch:

```
sudo cp /etc/default/zramswap.bak-rikuszram-<datum> /etc/default/zramswap
sudo service zramswap restart      # bei systemd: systemctl restart zramswap
```

---

## 8. Sonderfall btrfs — bitte lesen, wenn du btrfs benutzt

Liegt dein System auf **btrfs** (das prüft das Programm selbst und sagt es dir), gilt eine Besonderheit:

**Ein Bereich mit einer aktiven Swap-Datei kann nicht mehr gesichert werden.** Läge die Datei einfach in `/`, könnte **Timeshift keine Sicherungspunkte mehr anlegen** — und zwar lautlos, ohne Fehlermeldung. Du würdest es erst merken, wenn du eine Sicherung brauchst.

**Deshalb legt Rikus Zram die Datei in einen eigenen, abgetrennten Bereich** (`/swap`) und erzeugt sie mit dem btrfs-eigenen Befehl, der alles Nötige richtig einstellt. Nach dem Anlegen prüft das Programm nach, ob Timeshift weiterhin arbeiten kann, und zeigt dir das Ergebnis.

Du musst dafür nichts tun — es passiert von selbst. Der Hinweis steht hier, damit du weißt, **warum** es diesen zusätzlichen Bereich gibt.

---

## 9. Häufige Fragen

**Ist das gefährlich?**
Anschauen und Empfehlen läuft ganz ohne Passwort und ohne Schreibzugriff. Geändert wird nur, was du ausdrücklich bestätigst — mit Vorschau, Sicherung und Rückgängig-Knopf.

**Brauche ich zram überhaupt?**
Wenn dein Rechner bei vielen offenen Programmen zäh wird: ja. zram verschafft dir spürbar mehr Luft, ohne dass etwas auf die langsame Platte muss. Auf modernen Systemen ist es weit verbreitet.

**Warum zeigt mir ein anderes Programm andere Zahlen?**
Eine 2-GB-Swap-Datei meldet sich dem System als 1,999996 GB — die ersten Kilobyte sind ein interner Kopf und nicht nutzbar. Manche Programme schneiden das auf „1 GB" ab. Rikus Zram rundet auf **2 GB**, weil das die Größe ist, die du eingestellt hast.

**Was ist der Ruhezustand überhaupt — und brauche ich ihn?**

Es gibt drei Arten, den Rechner „auszumachen":

| | Was passiert | Wieder da in | Strom |
|---|---|---|---|
| **Herunterfahren** | alles wird geschlossen | 30–60 s (alles neu öffnen) | keiner |
| **Bereitschaft** (Standby) | alles bleibt offen im Arbeitsspeicher | 1–2 Sekunden | ein wenig — **bei leerem Akku ist alles weg** |
| **Ruhezustand** (Hibernate) | der Arbeitsspeicher wird auf die Platte geschrieben | 15–30 Sekunden | **gar keiner** — alles bleibt erhalten |

Wenn du deinen Laptop zuklappst, geht er normalerweise in **Bereitschaft**. Der **Ruhezustand** ist etwas anderes: Er speichert ein vollständiges Abbild deines Arbeitsspeichers auf die Festplatte und schaltet den Rechner **ganz** aus. Beim nächsten Einschalten ist alles wieder offen wie vorher — dieselben Programme, dieselbe Stelle im Text.

**Dafür brauchst du zwei Dinge:**

1. **Eine Swap-Datei mindestens so groß wie dein Arbeitsspeicher.** Bei 16 GB RAM also mindestens 16 GB. Ist sie kleiner, lehnt Linux den Ruhezustand von vornherein ab. Die Größe stellst du mit Regler 3 ein — das Programm zeigt dir an, ab welchem Wert es reichen würde.
2. **Einen Eintrag in der Startkonfiguration** (`resume=`), damit der Rechner beim Einschalten weiß, wo das Abbild liegt. **Diesen Schritt macht Rikus Zram nicht** — er greift in den Startvorgang ein, und das ist bewusst außerhalb dessen, was dieses Programm anfasst.

**zram hilft hier nicht.** Es liegt selbst im Arbeitsspeicher und ist beim Ausschalten mit weg — man kann das Abbild nicht in dem Raum lagern, den man gerade abbildet.

**Brauchst du ihn?** Für den Alltag reicht die Bereitschaft völlig und ist zehnmal schneller. Der Ruhezustand lohnt sich, wenn du den Rechner tagelang liegen lässt und trotzdem alles offen behalten willst, oder wenn du oft mit leerem Akku dastehst.

**Ob dein Rechner ihn kann**, steht auf der ersten Seite unter „Dieses System". Prüfen kannst du es auch selbst:
```
cat /sys/power/state
```
Steht dort `disk`, ist der Ruhezustand technisch möglich.

**Kann ich es wieder loswerden?**
`sudo apt remove rikus-zram`. Deine Einstellungen und eine angelegte Swap-Datei bleiben erhalten — das Programm räumt dir nichts weg, was du eingerichtet hast.

**Was, wenn etwas schiefgeht?**
Die Sicherungen liegen neben den Originaldateien (`*.bak-rikuszram-*`). Der Rückgängig-Knopf stellt sie wieder her. Und Änderungen an zram und swappiness wirken sich nie auf deine Daten aus — es geht nur um Speicherverwaltung.

---

## 10. Der Update-Hinweis

Ab Fassung 1.10 schaut das Programm beim Start einmal nach, ob es eine neuere Fassung
gibt. Wenn ja, erscheint unter dem Titel eine kleine grüne Zeile mit einem Link zur
Download-Seite. **Mehr passiert nicht** — es wird nichts heruntergeladen und nichts
installiert. Ohne Internet erscheint die Zeile einfach nicht; das Fenster geht wie
gewohnt sofort auf.

**Warum es das gibt:** Das Programm kommt als `.deb` von GitHub und ist damit *keine*
apt-Quelle. `apt update` erfährt also nie davon, dass es etwas Neueres gibt — man
bliebe ohne Hinweis auf einer alten Fassung sitzen, ohne es zu merken.

**Abschalten** — eine einzige Zeile im Terminal:

```
touch ~/.config/rikus-zram/kein-update-hinweis
```

Danach fragt das Programm gar nicht mehr nach. Wieder einschalten:

```
rm ~/.config/rikus-zram/kein-update-hinweis
```


**Webseite:** [zram.rikus.info](https://zram.rikus.info)
**Quelltext und Fehlermeldungen:** [github.com/Zahnschmerz/rikus-zram](https://github.com/Zahnschmerz/rikus-zram)

Fehler gefunden oder eine Idee? Melde sie gern — das Programm lebt von Rückmeldungen.

**Rikus Zram** — von Gilbert Rikus · GPL-3.0
Schwesterprogramm: **Rikus Mintshot** ([snapshot.rikus.info](https://snapshot.rikus.info)) — baut mit einem Klick einen bootfähigen Klon deines Linux-Mint-Systems.

## Hilfe und Rückmeldungen
