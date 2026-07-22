# Rikus Zram

**zram, swappiness und Swap-Dateien einstellen — mit Schiebereglern statt Terminal.**

![Rikus Zram](daten/icon.png)

Linux kann den Arbeitsspeicher besser nutzen, als die meisten Systeme es tun. **zram** presst selten gebrauchte Daten direkt im Arbeitsspeicher zusammen, statt sie auf die langsame Festplatte auszulagern — typisch 3- bis 4-fach. Der Rechner bleibt flüssig, auch wenn viel offen ist.

Der Haken: Einstellen lässt sich das bisher **nur über getippte Befehle und das Bearbeiten von Systemdateien**. Rikus Zram macht daraus ein Fenster.

---

## Was es kann

- **⭐ Einrichten, wo es noch kein zram gibt** — Paket installieren, einstellen, Dienst einschalten. Auch auf Systemen ohne systemd, wo `zram-tools` nur eine systemd-Einheit mitbringt und sonst gar nichts starten würde. **Das kann sonst kein Programm mit Fenster.**
- **Anzeigen** — wie viel Arbeitsspeicher belegt ist, ob zram läuft, wie stark es gerade komprimiert, welche Swap-Bereiche es gibt. Mit Ampel und Klartext-Urteil.
- **Empfehlen** — errechnet aus RAM-Größe, SSD oder Festplatte, Dateisystem und Ruhezustand, was für **diesen** Rechner passt. Mit Begründung in normaler Sprache.
- **Einstellen** — drei Schieberegler: zram-Größe, swappiness, Swap-Datei. Du schiebst selbst, die Empfehlung steht als Markierung daneben.
- **Übernehmen** — mit Vorschau, Sicherung jeder Datei, Passwortabfrage und **Nachmessung**, ob es wirklich gegriffen hat. Plus Rückgängig-Knopf.

**Zweisprachig:** Deutsch oder Englisch, automatisch nach Systemsprache.

---

## Installieren

**Ohne Terminal, in drei Schritten:**

1. **[Datei herunterladen](https://github.com/Zahnschmerz/rikus-zram/releases/latest)** — sie heißt **`rikus-zram_<fassung>_all.deb`** (die Zahl im Namen ist die Fassung) und landet in deinem Ordner **Downloads**.
2. Im Ordner **Downloads** die Datei **doppelt anklicken** → **„Paket installieren"** → Passwort eingeben.
3. Starten: Startmenü unter *System* → **Rikus Zram**.

<details>
<summary>Lieber im Terminal?</summary>

```
cd ~/Downloads
sudo apt install ./rikus-zram_1.20_all.deb
```

Den vollen Dateinamen nennen — **nicht** `rikus-zram*.deb` mit Stern: Liegen mehrere Fassungen im Ordner, sortiert `bash` alphabetisch und **1.9 steht hinter 1.19**; der Stern-Befehl installiert dann die ältere (am 22.07.2026 nachgemessen). Über den Knopf „neueste Fassung" heißt die Datei `rikus-zram-neueste.deb`. Bitte `apt install` nehmen, nicht `dpkg -i`.
</details>

**Läuft auf:** Debian, Ubuntu, Linux Mint, LMDE, MX Linux, antiX, Zorin, Pop!\_OS und Verwandten.
**Mit systemd und mit SysVinit** — das Programm erkennt selbst, welches dein System benutzt.

---

## Sicherheit

- Anschauen und Empfehlen läuft **ohne Passwort und ohne Schreibzugriff**
- Geändert wird **nur nach ausdrücklicher Bestätigung**, mit Vorschau vorher
- **Jede Datei wird gesichert**, bevor sie angefasst wird
- **Swap-Partitionen werden nie verändert** — nur Dateien
- Auf **btrfs** bekommt die Swap-Datei einen eigenen Bereich, damit **Timeshift weiterhin Sicherungspunkte anlegen kann**

---

## Ausführliche Anleitung

→ **[ANLEITUNG.md](ANLEITUNG.md)** — für Anfänger, Schritt für Schritt, mit Erklärung aller Fachbegriffe
→ **[CHANGELOG.md](CHANGELOG.md)** — was sich in jeder Fassung geändert hat

---

**Webseite:** [zram.rikus.info](https://zram.rikus.info)
**Herausgeber:** Gilbert Rikus · **Lizenz:** GPL-3.0
**Schwesterprogramm:** [Rikus Mintshot](https://snapshot.rikus.info) — bootfähiger Klon deines Linux-Mint-Systems mit einem Klick

*Englische Fassung: [README.md](README.md)*
