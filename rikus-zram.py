#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rikus Zram — Speicher-Verwaltung per Klick
von Gilbert Rikus · GPL-3.0

ETAPPE 4: ANZEIGEN + EMPFEHLEN + UEBERNEHMEN (alle drei Regler).

SICHERHEITSGRUNDSAETZE (nicht aufweichen!):
 - Ohne ausdrueckliche Bestaetigung wird NICHTS geschrieben. Messen und
   Empfehlen laeuft komplett ohne Root-Rechte.
 - Vor jeder Aenderung wird die betroffene Datei gesichert
   (<datei>.bak-rikuszram-<datum>) — dafuer gibt es einen Rueckgaengig-Knopf.
 - Es gibt einen Trockenlauf ("Zeigen, was geaendert wuerde"), der NUR anzeigt.
 - Nach dem Anwenden wird NACHGEMESSEN, ob es wirklich gegriffen hat —
   nicht "muesste jetzt passen".
 - Alles Root-Pflichtige laeuft in EINEM Skript ueber pkexec/sudo, nicht in
   vielen Einzelaufrufen.

WICHTIG (teuer gelernt am 18.07.2026):
Alle Systembefehle werden mit VOLLEM PFAD aufgerufen. Aus dem Startmenue
heraus enthaelt der Suchpfad kein /sbin und kein /usr/sbin — ein blosses
"zramctl" liefe dann ins Leere und das Programm wuerde faelschlich
"kein zram vorhanden" melden. Genau dieser Fehler ist beim Bau passiert.
"""

import os
import re
import glob
import json
import threading
import subprocess

import gi
gi.require_version('Gtk', '3.0')
# Gdk wird fuer die Bildschirmhoehe gebraucht (siehe _fensterhoehe).
# ⚠️ Fehlt der Import, faellt die Fensterhoehe STILL auf den alten festen
# Wert zurueck — ohne Fehlermeldung, weil dort ein try/except steht.
from gi.repository import Gtk, Pango, GLib, Gdk

VERSION = '1.14'


# ---------------------------------------------------------------------------
# UPDATE-HINWEIS
#
# Das Programm wird als .deb ueber GitHub verteilt und hat KEINE apt-Quelle.
# "apt update" erfaehrt also nie davon, dass es eine neuere Fassung gibt — der
# Nutzer bleibt auf seiner sitzen, ohne es zu merken.
#
# Deshalb: eine unaufdringliche Zeile im Fenster. KEIN Popup beim Start, KEINE
# automatische Installation — nur ein Hinweis mit Link.
#
# Grundregeln, die hier nicht verhandelbar sind:
#   * Das Fenster darf NIE warten          -> eigener Faden + hartes Zeitlimit
#   * Es darf NIE abstuerzen               -> schlaegt etwas fehl, bleibt die Zeile weg
#   * KEINE neue Abhaengigkeit             -> urllib steckt in python3
#   * Abschaltbar                          -> Datei KEIN_UPDATE_DATEI anlegen
# ---------------------------------------------------------------------------

UPDATE_API = 'https://api.github.com/repos/Zahnschmerz/rikus-zram/releases/latest'
UPDATE_SEITE = 'https://github.com/Zahnschmerz/rikus-zram/releases/latest'
KONFIG_ORDNER = os.path.expanduser('~/.config/rikus-zram')
KEIN_UPDATE_DATEI = os.path.join(KONFIG_ORDNER, 'kein-update-hinweis')
UPDATE_ZEITLIMIT = 4          # Sekunden; danach still aufgeben


def version_tupel(text):
    """'v1.10' -> (1, 10). Fuer den VERGLEICH von Versionen.

    ⚠️ Versionen NIEMALS als Text vergleichen: '1.10' < '1.9' ist als Text WAHR,
    der Hinweis bliebe ab 1.10 fuer immer aus. Zahlen vergleichen, nicht Buchstaben.
    """
    return tuple(int(t) for t in re.findall(r'\d+', text or '')) or (0,)


def neuere_version():
    """Fragt GitHub nach der neuesten Fassung. Rueckgabe: '1.10' oder None.

    None heisst schlicht 'keinen Hinweis anzeigen' — egal ob es nichts Neues gibt,
    das Netz fehlt, GitHub bockt oder der Nutzer es abgeschaltet hat. Kein Internet
    ist der NORMALFALL, kein Fehler.
    """
    if os.path.exists(KEIN_UPDATE_DATEI):
        return None
    try:
        import urllib.request
        with urllib.request.urlopen(UPDATE_API, timeout=UPDATE_ZEITLIMIT) as antwort:
            tag = json.loads(antwort.read().decode('utf-8')).get('tag_name', '')
        if version_tupel(tag) > version_tupel(VERSION):
            return tag.lstrip('vV') or tag
    except Exception:
        pass                  # bewusst ALLES abfangen: ein Hinweis darf nie stoeren
    return None


# ---------------------------------------------------------------------------
# SPRACHE — deutsch oder englisch, automatisch nach Systemeinstellung
# (gleiches Verfahren wie in Rikus Mintshot)
# ---------------------------------------------------------------------------

def _systemsprache():
    lang = (os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES')
            or os.environ.get('LANG') or 'en')
    return 'de' if lang.lower().startswith('de') else 'en'


SPRACHE = _systemsprache()


def t(de, en):
    """Gibt den Text in der Systemsprache zurueck.

    Bewusst eine FUNKTION statt eines Woerterbuchs wie bei Mintshot: Fast jeder
    Text hier enthaelt Messwerte (f-Strings). So steht die Uebersetzung direkt
    neben dem Original und kann beim Aendern nicht vergessen werden.
    """
    return de if SPRACHE == 'de' else en

# ---------------------------------------------------------------------------
# Systembefehle IMMER mit vollem Pfad (siehe Kopfkommentar)
# ---------------------------------------------------------------------------
PFADE = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']


def _werkzeug(name):
    """Vollen Pfad zu einem Systemwerkzeug finden — nie auf $PATH verlassen."""
    for p in PFADE:
        voll = os.path.join(p, name)
        if os.access(voll, os.X_OK):
            return voll
    return None


def _lauf(name, *args):
    """Werkzeug ausfuehren und Ausgabe zurueckgeben. Nie eine Ausnahme werfen."""
    voll = _werkzeug(name)
    if not voll:
        return ''
    try:
        e = subprocess.run([voll] + list(args), capture_output=True,
                           text=True, timeout=10)
        return e.stdout.strip()
    except Exception:
        return ''


def _lies(pfad):
    try:
        with open(pfad, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        return ''


def gb_gerundet(bytes_):
    """Bytes in ganze GiB — GERUNDET, niemals abgeschnitten.

    Wichtig, sonst wird die Anzeige irrefuehrend: Eine 2-GiB-Auslagerungsdatei
    ist auf der Platte exakt 2.147.483.648 Bytes gross, meldet sich in
    /proc/swaps aber mit 2.147.479.552 Bytes — die ersten 4 KB sind der Kopf
    der Datei und nicht nutzbar. Das sind 1,999996 GiB. Mit int() wird daraus 1.
    Folge: Die Anzeige spraenge nach dem Uebernehmen von 2 auf 1 zurueck, und
    das Programm hielte die Reserve faelschlich fuer zu klein.
    """
    return round(bytes_ / 1024**3)


def sicher(wert):
    """Werte aus dem System fuer die Textauszeichnung entschaerfen.

    🔴 BEWIESEN am 18.07.2026: Enthaelt ein Systemwert ein `&` oder `<`
    (z. B. ein Distributionsname „Foo & Bar Linux", ein Geraetename, ein
    Pfad), dann zeigt GTK die GANZE Zeile LEER an — ohne Absturz und ohne
    sichtbare Fehlermeldung. Der Nutzer sieht nur einen leeren Kasten.

    Auf dem eigenen Rechner faellt das NIE auf, weil „Debian GNU/Linux 13"
    harmlos ist. Es trifft ausschliesslich fremde Nutzer — dieselbe Falle
    wie bei den Paket-Abhaengigkeiten.

    Deshalb: JEDER Wert, der aus dem System kommt und in einen formatierten
    Text geht, laeuft durch diese Funktion.
    """
    return GLib.markup_escape_text(str(wert))


def zahl(wert, stellen=1):
    """Zahl in der Schreibweise der jeweiligen Sprache.

    Deutsch schreibt 6,0 — Englisch 6.0. Ohne diese Unterscheidung stand im
    englischen Fenster „6,0 GiB", was dort schlicht falsch aussieht.
    Bewusst EINE Stelle dafuer, damit derselbe Fehler nicht an drei Orten
    getrennt lauert (dieselbe Lehre wie bei gb_gerundet).
    """
    s = f'{wert:.{stellen}f}'
    return s.replace('.', ',') if SPRACHE == 'de' else s


def groesse(bytes_):
    """Bytes in etwas Lesbares. Bewusst mit KiB/MiB/GiB (durch 1024)."""
    b = float(bytes_)
    for einheit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if b < 1024 or einheit == 'TiB':
            return f'{zahl(b)} {einheit}'
        b /= 1024
    return f'{zahl(b)} TiB'


# ---------------------------------------------------------------------------
# MESSEN — alles nur lesend
# ---------------------------------------------------------------------------

def ram_messen():
    werte = {}
    for zeile in _lies('/proc/meminfo').splitlines():
        teile = zeile.split(':')
        if len(teile) == 2:
            m = re.match(r'\s*(\d+)', teile[1])
            if m:
                werte[teile[0]] = int(m.group(1)) * 1024
    gesamt = werte.get('MemTotal', 0)
    frei = werte.get('MemAvailable', werte.get('MemFree', 0))
    return {'gesamt': gesamt, 'verfuegbar': frei, 'belegt': gesamt - frei}


def zram_messen():
    ausgabe = _lauf('zramctl', '--noheadings', '--bytes',
                    '-o', 'NAME,ALGORITHM,DISKSIZE,DATA,TOTAL,MOUNTPOINT')
    geraete = []
    for zeile in ausgabe.splitlines():
        felder = zeile.split()
        if len(felder) >= 5:
            geraete.append({
                'name': felder[0], 'verfahren': felder[1],
                'groesse': int(felder[2]) if felder[2].isdigit() else 0,
                'daten': int(felder[3]) if felder[3].isdigit() else 0,
                'belegt_echt': int(felder[4]) if felder[4].isdigit() else 0,
                'zweck': felder[5] if len(felder) > 5 else '',
            })
    return geraete


def swap_messen():
    bereiche = []
    for zeile in _lies('/proc/swaps').splitlines()[1:]:
        felder = zeile.split()
        if len(felder) >= 5:
            bereiche.append({
                'name': felder[0], 'art': felder[1],
                'groesse': int(felder[2]) * 1024, 'benutzt': int(felder[3]) * 1024,
                'prio': int(felder[4]), 'ist_zram': 'zram' in felder[0],
            })
    return bereiche


def swappiness_messen():
    laufend = _lies('/proc/sys/vm/swappiness').strip()
    laufend = int(laufend) if laufend.isdigit() else None
    dateien = []
    for pfad in sorted(glob.glob('/etc/sysctl.d/*.conf')) + ['/etc/sysctl.conf']:
        for zeile in _lies(pfad).splitlines():
            zeile = zeile.strip()
            if zeile.startswith('#') or '=' not in zeile:
                continue
            s, w = zeile.split('=', 1)
            if s.strip() == 'vm.swappiness':
                dateien.append({'datei': pfad, 'wert': w.strip()})
    return {'laufend': laufend, 'dateien': dateien}


def einstellung_messen():
    pfad = '/etc/default/zramswap'
    if not os.path.exists(pfad):
        return {'vorhanden': False, 'werte': {}, 'pfad': pfad}
    werte = {}
    for zeile in _lies(pfad).splitlines():
        zeile = zeile.strip()
        if zeile.startswith('#') or '=' not in zeile:
            continue
        s, w = zeile.split('=', 1)
        werte[s.strip()] = w.strip().strip('"').strip("'")
    return {'vorhanden': True, 'werte': werte, 'pfad': pfad}


GENERATOR_PFADE = ['/etc/systemd/zram-generator.conf',
                   '/usr/lib/systemd/zram-generator.conf',
                   '/etc/systemd/zram-generator.conf.d']


def generator_messen():
    """Regelt auf diesem Rechner ein ANDERES Werkzeug das zram?

    🔴🔴 Gefunden am 22.07.2026 beim Ausrollen auf Gilberts Server: **drei von
    sechs** (debian, rk-pr01, pi4) benutzen nicht `zram-tools`, sondern den
    **systemd-zram-generator** — ein voellig anderes Werkzeug fuer dieselbe
    Aufgabe:

        zram-tools:            /etc/default/zramswap        · Dienst zramswap
        systemd-zram-generator: /etc/systemd/zram-generator.conf
                               · Dienst systemd-zram-setup@zram0

    Dieses Programm kann nur den ersten. Waere es dort blind gelaufen, haette
    es `/etc/default/zramswap` angelegt und den Dienst `zramswap` gestartet —
    **zwei zram-Systeme parallel auf demselben Rechner**, auf einem
    Produktivserver (Nextcloud, Immich, Paperless) ein unnoetiges Risiko.

    ➡️ Deshalb wird der Fall ERKANNT und das Programm haelt sich heraus,
    statt Schaden anzurichten. Anschauen bleibt erlaubt — nur Aendern nicht.
    """
    pfade = [p for p in GENERATOR_PFADE if os.path.exists(p)]
    if not pfade:
        return {'aktiv': False, 'pfad': None, 'werte': {}}
    werte = {}
    for p in pfade:
        if os.path.isdir(p):
            continue
        for zeile in _lies(p).splitlines():
            zeile = zeile.split('#')[0].strip()
            if '=' not in zeile or zeile.startswith('['):
                continue
            s, w = zeile.split('=', 1)
            werte[s.strip()] = w.strip()
    return {'aktiv': True, 'pfad': pfade[0], 'werte': werte}


def system_messen():
    name = 'Linux'
    for zeile in _lies('/etc/os-release').splitlines():
        if zeile.startswith('PRETTY_NAME='):
            name = zeile.split('=', 1)[1].strip().strip('"')
    pid1 = _lies('/proc/1/comm').strip() or '?'
    return {'name': name, 'ist_systemd': pid1 == 'systemd',
            'start': 'systemd' if pid1 == 'systemd' else f'SysVinit ({pid1})'}


def platte_messen():
    """Wo liegt / , ist es eine SSD, welches Dateisystem?
    Wichtig: btrfs braucht bei Auslagerungsdateien eine Sonderbehandlung."""
    zeile = _lauf('findmnt', '-no', 'SOURCE,FSTYPE,AVAIL', '/')
    felder = zeile.split()
    quelle = felder[0] if felder else ''
    dateisystem = felder[1] if len(felder) > 1 else '?'
    frei_text = felder[2] if len(felder) > 2 else '?'

    # Dreht sich die Platte? (0 = SSD)
    ssd = None
    geraet = re.sub(r'\[.*\]$', '', quelle)
    geraet = os.path.basename(geraet)
    geraet = re.sub(r'p?\d+$', '', geraet)
    rota = _lies(f'/sys/block/{geraet}/queue/rotational').strip()
    if rota in ('0', '1'):
        ssd = (rota == '0')

    return {'quelle': quelle, 'dateisystem': dateisystem, 'ssd': ssd,
            'frei_text': frei_text}


def ruhezustand_messen():
    """Kann der Rechner Winterschlaf, und ist er eingerichtet?"""
    kann = 'disk' in _lies('/sys/power/state')
    eingerichtet = bool(
        _lies('/etc/initramfs-tools/conf.d/resume').strip()
        or re.search(r'resume=', _lies('/etc/default/grub')))
    return {'kann': kann, 'eingerichtet': eingerichtet}


# ---------------------------------------------------------------------------
# EMPFEHLEN — rechnen und begruenden
# ---------------------------------------------------------------------------

def empfehlung_rechnen(ram, zram, swap, swp, platte, ruhe):
    """Gibt fuer jeden Regler den Soll-Wert samt Begruendung in Klartext."""
    gb = ram['gesamt'] / 1024**3
    ssd = platte['ssd'] is not False   # unbekannt wie SSD behandeln
    e = {}

    # --- Turbo-Groesse (Prozent vom RAM) -----------------------------------
    if gb >= 32:
        e['zram_prozent'] = 50
        e['zram_warum'] = t(
            f'Du hast mit {gb:.0f} GiB reichlich Arbeitsspeicher. Die Hälfte '
            'als zram genügt — mehr würde selten gebraucht.',
            f'With {gb:.0f} GiB you have plenty of RAM. Half of it as zram is '
            'enough — more would rarely be used.')
    else:
        e['zram_prozent'] = 100
        e['zram_warum'] = t(
            'zram in Größe des Arbeitsspeichers hat sich bewährt. Weil '
            'die Daten etwa 3- bis 4-fach zusammengepresst werden, gewinnst '
            'du dadurch ein Vielfaches an nutzbarem Platz.',
            'zram the size of your RAM is a proven setting. Because data is '
            'compressed roughly 3–4×, you gain a multiple of that in usable '
            'space.')

    # --- swappiness ----------------------------------
    hat_zram = len(zram) > 0
    if hat_zram and ssd:
        e['swappiness'] = 150
        e['swappiness_warum'] = t(
            'Mit zram darf der Rechner beherzt auslagern — es geht ja '
            'in den schnellen Arbeitsspeicher, nicht auf die Platte. '
            '150 ist der Wert, der sich in der Praxis am besten bewährt hat.',
            'With zram the system may swap freely — it goes into fast RAM, '
            'not onto the disk. 150 is the value that works best in practice.')
    elif hat_zram:
        e['swappiness'] = 120
        e['swappiness_warum'] = t(
            'Mit zram darf ausgelagert werden. Etwas zurückhaltender, weil '
            'sich deine Platte dreht.',
            'With zram swapping is fine. Slightly more cautious here because '
            'your disk is a spinning one.')
    elif ssd:
        e['swappiness'] = 60
        e['swappiness_warum'] = t(
            'Ohne zram landet Ausgelagertes auf der Platte. 60 ist der '
            'übliche Mittelweg.',
            'Without zram, swapped data lands on the disk. 60 is the usual '
            'middle ground.')
    else:
        e['swappiness'] = 20
        e['swappiness_warum'] = t(
            'Ohne zram und mit drehender Platte ist Auslagern langsam — '
            'lieber selten.',
            'Without zram and on a spinning disk, swapping is slow — better '
            'keep it rare.')

    # --- Reserve auf der Platte (Swap-Datei) -------------------------------
    if ruhe['eingerichtet']:
        e['swap_gb'] = max(int(gb) + 2, 4)
        e['swap_warum'] = t(
            f'Dein Ruhezustand ist eingerichtet. Dafür muss der ganze '
            f'Arbeitsspeicher auf die Platte passen — also mindestens '
            f'{int(gb)} GiB. zram kann das nicht leisten.',
            f'Hibernation is set up. It needs the entire RAM to fit on disk — '
            f'so at least {int(gb)} GiB. zram cannot do that.')
    elif gb <= 4:
        e['swap_gb'] = 4
        e['swap_warum'] = t(
            'Bei wenig Arbeitsspeicher ist eine Reserve auf der Platte '
            'sinnvoll — sonst bricht bei Speichermangel ein Programm ab.',
            'With little RAM a reserve on disk makes sense — otherwise a '
            'program gets killed when memory runs out.')
    elif gb <= 16:
        e['swap_gb'] = 2
        e['swap_warum'] = t(
            'Eine kleine Reserve als Sicherheitsnetz. Im Alltag bleibt sie '
            'leer — sie greift nur, wenn Arbeitsspeicher UND zram voll sind.',
            'A small safety net. It stays empty in daily use — it only kicks '
            'in when both RAM and zram are full.')
    else:
        e['swap_gb'] = 0
        e['swap_warum'] = t(
            f'Mit {gb:.0f} GiB und laufendem zram brauchst du keine Swap-Datei '
            'auf der Platte — außer du möchtest den Ruhezustand nutzen.',
            f'With {gb:.0f} GiB and zram running you do not need a swap file — '
            'unless you want to use hibernation.')

    # --- Sonderfall btrfs ---------------------------------------------------
    e['warnung'] = ''
    if platte['dateisystem'] == 'btrfs' and e['swap_gb'] > 0:
        e['warnung'] = t(
            '⚠️ Dein Dateisystem ist btrfs. Eine Auslagerungsdatei muss dort '
            'besonders angelegt werden (ohne Kopier-Schutz und außerhalb der '
            'Sicherungspunkte) — sonst nimmt das Dateisystem Schaden. Das '
            'Programm macht das selbst richtig.',
            '⚠️ Your filesystem is btrfs. A swap file must be created in a '
            'special way there (no copy-on-write, outside of snapshots) — '
            'otherwise the filesystem takes damage. This program handles it '
            'correctly by itself.')
    return e


# ---------------------------------------------------------------------------
# AENDERN — alles, was Root braucht, in EINEM Skript (Muster von Rikus Mintshot)
# ---------------------------------------------------------------------------

STEMPEL = 'rikuszram'


def root_praefix():
    """Passwortloses sudo, wenn vorhanden — sonst pkexec-Passwortdialog."""
    try:
        if subprocess.run(['/usr/bin/sudo', '-n', 'true'],
                          capture_output=True, timeout=5).returncode == 0:
            return ['/usr/bin/sudo', '-n']
    except Exception:
        pass
    return ['/usr/bin/pkexec']


def dienst_befehl(sys_):
    """Der RICHTIGE Neustart-Befehl.
    ⚠️ Nicht danach fragen, OB es systemctl gibt — auf MX ist es installiert,
    obwohl SysVinit laeuft. Entscheidend ist, was als Prozess 1 laeuft."""
    if sys_['ist_systemd']:
        return 'systemctl restart zramswap'
    return 'service zramswap restart'


INIT_SKRIPT = '/etc/init.d/zramswap'

# Ein vollwertiges LSB-Startskript. Es ruft nur das auf, was auch die
# systemd-Fassung des Pakets aufruft (»zramswap start« bzw. »stop«).
INIT_SKRIPT_INHALT = '''#!/bin/sh
### BEGIN INIT INFO
# Provides:          zramswap
# Required-Start:    $local_fs
# Required-Stop:     $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: zram-based swap
# Description:       Compressed swap in RAM (set up by Rikus Zram)
### END INIT INFO
# Von Rikus Zram angelegt, weil das Paket zram-tools nur eine
# systemd-Einheit mitbringt und auf Systemen ohne systemd sonst
# nichts starten wuerde.
PATH=/sbin:/usr/sbin:/bin:/usr/bin
DAEMON=/usr/sbin/zramswap
[ -x "$DAEMON" ] || exit 0

case "$1" in
  start)   "$DAEMON" start ;;
  stop)    "$DAEMON" stop ;;
  restart|force-reload) "$DAEMON" stop 2>/dev/null || true; "$DAEMON" start ;;
  status)  /sbin/zramctl 2>/dev/null | grep -q zram && echo "zram laeuft" \\
             || { echo "zram laeuft nicht"; exit 3; } ;;
  *) echo "Aufruf: $0 {start|stop|restart|status}" >&2; exit 2 ;;
esac
exit 0
'''


def dienst_start_befehle(sys_):
    """Dienst dauerhaft einschalten UND jetzt starten.

    Zwei Dinge, nicht eines: »start« gilt nur bis zum Neustart, das
    Eintragen sorgt dafuer, dass zram nach dem naechsten Hochfahren wieder
    da ist. Wer nur startet, wundert sich am naechsten Tag.

    ⚠️⚠️ HART ERARBEITET (19.07.2026, echter Test in einem ausgepackten
    antiX 26): **Das Paket zram-tools liefert NUR eine systemd-Einheit** —
    `/usr/lib/systemd/system/zramswap.service` — und KEIN Init-Skript.
    Auf yoga (MX) faellt das nicht auf, weil MX ein eigenes Zusatzpaket
    `zramswap-sysvinit-compat` mitliefert. Das gibt es in antiX NICHT
    (`apt-cache policy` dort: kein Kandidat).
    Folge: Ein blindes `update-rc.d zramswap defaults` scheitert auf antiX
    mit »initscript does not exist« — genau auf dem System, fuer das dieses
    Programm als einziges taugt.
    ➡️ Deshalb legen wir das Startskript selbst an, wenn keines da ist.
    antiX/runit fuehrt `/etc/rcS.d/S*` aus, `update-rc.d` wirkt also."""
    # ⚠️⚠️ ZWEITER TEUER ERKAUFTER PUNKT (19.07., derselbe antiX-Test):
    # Der Start MUSS fehlschlagen duerfen, ohne alles andere mitzureissen.
    # Das Skript laeuft mit »set -e« — als der zram-Start einmal scheiterte
    # (Kernel ohne zram-Modul), brach es sofort ab, und **swappiness wurde
    # nie gesetzt**. Der Nutzer haette „nicht durchgelaufen" gesehen und
    # NICHTS von seinen Einstellungen bekommen, obwohl zwei davon problemlos
    # moeglich waren. Ob zram wirklich laeuft, zeigt ohnehin die Nachmessung.
    if sys_['ist_systemd']:
        return ['systemctl enable zramswap || true',
                'systemctl restart zramswap || true']

    # ⚠️ Die Existenzpruefung steht IM Skript, nicht hier: Zwischen Planen und
    # Ausfuehren wird womoeglich erst das Paket installiert. Was hier gilt,
    # muss dort nicht mehr gelten.
    return [
        f'if [ ! -f "{INIT_SKRIPT}" ]; then',
        f'  cat > "{INIT_SKRIPT}" <<\'RIKUSZRAM_INIT_EOF\'',
        INIT_SKRIPT_INHALT.rstrip('\n'),
        'RIKUSZRAM_INIT_EOF',
        f'  chmod 755 "{INIT_SKRIPT}"',
        'fi',
        'update-rc.d zramswap defaults >/dev/null 2>&1 || true',
        # Direkt das Programm aufrufen statt »service«: das funktioniert
        # auch dort, wo »service« den Dienst (noch) nicht kennt.
        '/usr/sbin/zramswap start || true',
    ]


def zram_lage(einst, zram, sys_):
    """Was fehlt diesem Rechner, damit zram ueberhaupt laufen kann?

    Drei Dinge muessen zusammenkommen, und sie fehlen unabhaengig voneinander:
      1. das Paket zram-tools (liefert Dienst + Konfigdatei)
      2. die Konfigdatei /etc/default/zramswap
      3. der laufende Dienst

    ⚠️ Diese Unterscheidung ist der Grund, warum das Programm ueberhaupt
    existiert: Auf einem Rechner OHNE zram half die alte Fassung gar nicht
    weiter — sie konnte nur aendern, was schon da war."""
    paket_da = bool(_werkzeug('zramswap')) or os.path.exists(
        '/usr/sbin/zramswap') or os.path.exists('/usr/bin/zramswap')
    # Zweiter Weg: das Init-Skript bzw. die Unit. Auf SysVinit liegt es in
    # /etc/init.d, unter systemd als Unit — eines von beidem reicht als Beweis.
    if not paket_da:
        paket_da = (os.path.exists('/etc/init.d/zramswap') or
                    os.path.exists('/lib/systemd/system/zramswap.service') or
                    os.path.exists('/usr/lib/systemd/system/zramswap.service'))
    return {
        'paket_da': paket_da,
        'konfig_da': einst['vorhanden'],
        'laeuft': len(zram) > 0,
        # Nur wenn alles drei fehlt, ist es ein echtes „von Null einrichten".
        'muss_eingerichtet_werden': not (paket_da and einst['vorhanden']
                                         and len(zram) > 0),
    }


def swappiness_zieldatei(swp):
    """In WELCHE Datei schreiben wir?
    Gibt es schon eine, aendern wir DIESE — sonst haetten wir zwei Dateien,
    die dasselbe einstellen (genau davor warnt das Programm selbst)."""
    if swp['dateien']:
        return swp['dateien'][-1]['datei'], False
    return f'/etc/sysctl.d/99-{STEMPEL}.conf', True


def aenderungen_sammeln(sys_, swp, einst, ziel_prozent, ziel_swappiness,
                        ziel_swap_gb=None, swap=None, platte=None, zram=None):
    """Was soll geaendert werden? Liefert eine Liste in KLARTEXT (fuer den
    Trockenlauf) und die noetigen Shell-Zeilen."""
    schritte = []      # (klartext, shell-zeilen)
    datum = subprocess.run(['/usr/bin/date', '+%Y%m%d-%H%M%S'],
                           capture_output=True, text=True).stdout.strip()
    lage = zram_lage(einst, zram or [], sys_)

    # --- 0. zram ERST EINRICHTEN, wenn es noch keins gibt --------------------
    # ⚠️ Das ist der Kern des Programms und der Grund, warum es gebaut wurde:
    # Alles darunter kann nur AENDERN, was schon da ist. Auf einem Rechner ohne
    # zram passierte frueher gar nichts — der Regler liess sich schieben, das
    # Uebernehmen meldete „nichts zu tun". Genau das ist es, was sonst kein
    # Programm mit Fenster kann.
    if lage['muss_eingerichtet_werden']:
        text = []
        zeilen = []

        if not lage['paket_da']:
            text.append(t('das Paket zram-tools installieren '
                          '(es bringt den zram-Dienst mit)',
                          'install the package zram-tools '
                          '(it provides the zram service)'))
            # -y, weil niemand im Passwort-Fenster eine Rueckfrage beantworten
            # kann; DEBIAN_FRONTEND, damit keine Dialogmaske aufgeht.
            zeilen += [
                'export DEBIAN_FRONTEND=noninteractive',
                'apt-get update -qq || true',
                'apt-get install -y -qq zram-tools',
            ]

        if not lage['konfig_da']:
            d = einst['pfad']
            text.append(t(f'die Einstellungsdatei {d} anlegen',
                          f'create the settings file {d}'))
            # Kein cp-Backup: die Datei gibt es ja noch nicht. Falls das Paket
            # sie gerade selbst mitgebracht hat, wird sie hier ueberschrieben —
            # deshalb VORHER sichern, wenn sie dann doch existiert.
            zeilen += [
                f'[ -f "{d}" ] && cp -a "{d}" "{d}.bak-{STEMPEL}-{datum}" || true',
                f'cat > "{d}" <<\'RIKUSZRAM_EOF\'',
                '# von Rikus Zram angelegt',
                'ALGO=zstd',
                f'PERCENT={ziel_prozent}',
                'PRIORITY=100',
                'RIKUSZRAM_EOF',
            ]
        elif str(einst['werte'].get('PERCENT')) != str(ziel_prozent):
            # Konfig ist da, aber der Wert stimmt nicht — mitnehmen, sonst
            # richten wir zram mit der falschen Groesse ein.
            d = einst['pfad']
            text.append(t(f'die zram-Größe auf {ziel_prozent} % setzen',
                          f'set the zram size to {ziel_prozent} %'))
            zeilen += [
                f'cp -a "{d}" "{d}.bak-{STEMPEL}-{datum}"',
                f'sed -i "s/^[[:space:]]*PERCENT=.*/PERCENT={ziel_prozent}/" "{d}"',
                f'grep -q "^PERCENT=" "{d}" || echo "PERCENT={ziel_prozent}" >> "{d}"',
            ]

        text.append(t('den zram-Dienst einschalten und starten '
                      '(auch nach jedem Neustart)',
                      'switch the zram service on and start it '
                      '(also after every reboot)'))
        zeilen += dienst_start_befehle(sys_)

        schritte.append((t('zram einrichten: ', 'set up zram: ') +
                         ', '.join(text),
                         zeilen,
                         einst['pfad'] if lage['konfig_da'] else ''))

        # Die Groessen-Aenderung unten wuerde dasselbe nochmal tun.
        einst = dict(einst, vorhanden=True,
                     werte=dict(einst['werte'], PERCENT=str(ziel_prozent)))

    # --- 1. Turbo-Groesse ---------------------------------------------------
    ist_prozent = einst['werte'].get('PERCENT')
    hat_size = bool(einst['werte'].get('SIZE'))
    if einst['vorhanden'] and (str(ist_prozent) != str(ziel_prozent) or hat_size):
        text = []
        if str(ist_prozent) != str(ziel_prozent):
            text.append(t(f'zram-Größe von {ist_prozent} % auf '
                          f'{ziel_prozent} % ändern',
                          f'change zram size from {ist_prozent} % to '
                          f'{ziel_prozent} %'))
        if hat_size:
            text.append(t(f'die Zeile SIZE={einst["werte"]["SIZE"]} stilllegen '
                          '(sie würde die Prozent-Angabe überstimmen)',
                          f'comment out the line SIZE={einst["werte"]["SIZE"]} '
                          '(it would override the percentage)'))
        d = einst['pfad']
        zeilen = [
            f'cp -a "{d}" "{d}.bak-{STEMPEL}-{datum}"',
            f'sed -i "s/^[[:space:]]*PERCENT=.*/PERCENT={ziel_prozent}/" "{d}"',
            f'grep -q "^PERCENT=" "{d}" || echo "PERCENT={ziel_prozent}" >> "{d}"',
        ]
        if hat_size:
            zeilen.append(
                f'sed -i "s/^[[:space:]]*SIZE=/# von Rikus Zram stillgelegt: '
                f'SIZE=/" "{d}"')
        schritte.append((' und '.join(text), zeilen, d))

    # --- 2. swappiness --------------------------------------------
    if swp['laufend'] != ziel_swappiness:
        ziel, ist_neu = swappiness_zieldatei(swp)
        text = t(f'swappiness von {swp["laufend"]} auf {ziel_swappiness} ändern',
                 f'change swappiness from {swp["laufend"]} to {ziel_swappiness}')
        text += (t(f' (neue Datei {ziel})', f' (new file {ziel})') if ist_neu
                 else t(f' (in {os.path.basename(ziel)})',
                        f' (in {os.path.basename(ziel)})'))
        zeilen = []
        if not ist_neu:
            zeilen.append(f'cp -a "{ziel}" "{ziel}.bak-{STEMPEL}-{datum}"')
            zeilen.append(
                f'sed -i "s/^[[:space:]]*vm.swappiness[[:space:]]*=.*/'
                f'vm.swappiness={ziel_swappiness}/" "{ziel}"')
        else:
            zeilen.append(
                f'printf "%s\\n" "# von Rikus Zram angelegt" '
                f'"vm.swappiness={ziel_swappiness}" > "{ziel}"')
        zeilen.append('sysctl --system >/dev/null 2>&1')
        schritte.append((text, zeilen, ziel if not ist_neu else None))

    # --- 3. Reserve auf der Platte (Regler 3) ------------------------------
    if ziel_swap_gb is not None and swap is not None and platte is not None:
        schritte += swap_aenderung(ziel_swap_gb, swap, platte, datum)

    return schritte, datum


SWAP_ORT = '/swap'                 # eigener Bereich, damit Timeshift weiter sichern kann
SWAP_DATEI = '/swap/swapfile'


def swap_aenderung(ziel_gb, swap, platte, datum):
    """Schritte fuer die Auslagerungsdatei (Regler 3).

    ⚠️ btrfs-BESONDERHEIT (btrfs-Doku + Arch-Wiki, geprueft 18.07.2026):
    Ein Subvolume mit AKTIVER Auslagerungsdatei kann NICHT MEHR gesnapshottet
    werden. Laege die Datei direkt in `/`, koennte Timeshift keine
    Sicherungspunkte mehr anlegen — lautlos. Deshalb bekommt sie ein EIGENES
    Subvolume /swap, das Timeshift nicht anfasst.
    Ausserdem MUSS die Datei NOCOW sein; `btrfs filesystem mkswapfile`
    erledigt das von selbst (btrfs-progs >= 6.1).
    """
    ist_bytes = sum(x['groesse'] for x in swap if not x['ist_zram'])
    ist_gb = gb_gerundet(ist_bytes)
    benutzt = sum(x['benutzt'] for x in swap if not x['ist_zram'])
    if ziel_gb == ist_gb:
        return []

    ist_btrfs = platte['dateisystem'] == 'btrfs'
    schritte = []

    # ⚠️ Die vorhandenen Swap-DATEIEN kommen aus der MESSUNG (/proc/swaps),
    # NICHT aus der Annahme, sie laegen unter SWAP_DATEI.
    # Gilbert 21.07.2026: Auf Linux Mint liegt die Datei standardmaessig unter
    # /swapfile. Der frueher fest verdrahtete Pfad /swap/swapfile traf sie nicht
    # — swapoff/sed/rm liefen ins Leere, danach wurde eine ZWEITE Datei
    # angelegt. Ergebnis bei ihm: /swapfile 2 GiB + /swap/swapfile 15 GiB
    # gleichzeitig, und beim naechsten Lauf rechnete das Programm mit der
    # Summe weiter. Der Fehler war unsichtbar, solange man nur auf Systemen
    # OHNE vorhandene Swap-Datei testet.
    # 🛑 'partition' wird bewusst NIE angefasst — dort liegen Daten, und das
    # Programm verspricht das ausdruecklich in der Anleitung.
    vorhandene = [x for x in swap
                  if not x['ist_zram'] and x.get('art') == 'file' and x.get('name')]
    partitionen = [x for x in swap
                   if not x['ist_zram'] and x.get('art') != 'file']

    # --- vorhandene Reserve abschalten und entfernen ---
    if vorhandene:
        weg = [f'cp -a /etc/fstab "/etc/fstab.bak-{STEMPEL}-{datum}"']
        for eintrag in vorhandene:
            pfad = eintrag['name']
            weg += [
                f'swapoff {pfad} 2>/dev/null || true',
                f'sed -i "\\|^{pfad}[[:space:]]|d" /etc/fstab',
                f'rm -f {pfad}',
            ]
        namen = ', '.join(x['name'] for x in vorhandene)
        text = t(f'die vorhandene Swap-Datei {namen} ({ist_gb} GiB) abschalten '
                 f'und entfernen',
                 f'switch off and remove the existing swap file {namen} '
                 f'({ist_gb} GiB)')
        if partitionen:
            text += t(' — deine Swap-Partition bleibt unangetastet',
                      ' — your swap partition is left untouched')
        if benutzt > 0:
            text += t(f' — ⚠️ ACHTUNG: davon sind gerade {groesse(benutzt)} in '
                      'Benutzung, die müssen zurück in den Arbeitsspeicher',
                      f' — ⚠️ CAUTION: {groesse(benutzt)} of it is in use and '
                      'must move back into RAM')
        schritte.append((text, weg, '/etc/fstab'))

    # --- neue Reserve anlegen ---
    if ziel_gb > 0:
        neu = []
        if ist_btrfs:
            neu += [
                # ⚠️ /swap kann schon als GEWOEHNLICHES Verzeichnis existieren
                # (auf yoga seit 17.06.2026, leer, Herkunft unbekannt).
                # `btrfs subvolume create` scheitert dann — mit `set -e` waere
                # das Skript mittendrin abgebrochen. Also vorher wegraeumen;
                # rmdir schlaegt absichtlich fehl, wenn etwas drin liegt.
                f'if [ -d {SWAP_ORT} ] && [ "$(stat -c %i {SWAP_ORT})" != "256" ]; '
                f'then rmdir {SWAP_ORT}; fi',
                f'btrfs subvolume show {SWAP_ORT} >/dev/null 2>&1 || '
                f'btrfs subvolume create {SWAP_ORT}',
                f'btrfs filesystem mkswapfile --size {ziel_gb}g {SWAP_DATEI}',
            ]
        else:
            neu += [
                f'mkdir -p {SWAP_ORT}',
                f'fallocate -l {ziel_gb}G {SWAP_DATEI} || '
                f'dd if=/dev/zero of={SWAP_DATEI} bs=1M count={ziel_gb * 1024}',
                f'chmod 600 {SWAP_DATEI}',
                f'mkswap {SWAP_DATEI}',
            ]
        neu += [
            f'grep -q "^{SWAP_DATEI}" /etc/fstab || '
            f'printf "%s\\n" "{SWAP_DATEI} none swap defaults,pri=10 0 0" '
            f'>> /etc/fstab',
            f'swapon --priority 10 {SWAP_DATEI}',
        ]
        # Sicherung nur, wenn sie nicht schon im Aufraeum-Schritt lief.
        # ⚠️ Nicht an `ist_gb == 0` haengen: Wer eine Swap-PARTITION hat, hat
        # ist_gb > 0, aber es gibt keinen Aufraeum-Schritt (Partitionen werden
        # nie angefasst) — dann fehlte die Sicherung.
        if not vorhandene:
            neu.insert(0, f'cp -a /etc/fstab "/etc/fstab.bak-{STEMPEL}-{datum}"')
        text = t(f'eine Swap-Datei von {ziel_gb} GiB anlegen unter {SWAP_DATEI}, '
                 f'dauerhaft eintragen und einschalten (Priorität 10 — zram '
                 f'behält mit 100 den Vortritt)',
                 f'create a {ziel_gb} GiB swap file at {SWAP_DATEI}, add it '
                 f'permanently and switch it on (priority 10 — zram keeps '
                 f'precedence with 100)')
        if ist_btrfs:
            text += t('; dafür wird ein eigener Bereich „/swap" angelegt, damit '
                      'Timeshift weiter Sicherungspunkte machen kann',
                      '; a separate subvolume "/swap" is created so Timeshift '
                      'can still make snapshots')
        schritte.append((text, neu, '/etc/fstab'))

    return schritte


def timeshift_pruefen():
    """Kann Timeshift noch Sicherungspunkte anlegen?

    Kritisch ist NUR: Liegt die Auslagerungsdatei in einem EIGENEN Subvolume?
    Ein Subvolume mit aktiver Auslagerungsdatei kann nicht gesnapshottet
    werden — laege sie direkt in `/`, waere Timeshift lautlos lahmgelegt.

    Trick ohne Root-Rechte: Das Wurzelverzeichnis eines btrfs-Subvolumes hat
    IMMER die Inode-Nummer 256. Damit laesst sich das pruefen, ohne etwas
    anzufassen oder testweise einen Snapshot anzulegen.
    """
    if not os.path.exists(SWAP_DATEI):
        return True, t('ja (keine Swap-Datei vorhanden)',
                       'yes (no swap file present)')
    try:
        if os.stat(SWAP_ORT).st_ino == 256:
            return True, t(f'ja — Datei liegt im eigenen Bereich {SWAP_ORT}',
                           f'yes — file sits in its own subvolume {SWAP_ORT}')
    except Exception:
        pass
    return False, t(f'NEIN — {SWAP_ORT} ist kein eigener Bereich, Timeshift '
                    'wäre blockiert!',
                    f'NO — {SWAP_ORT} is not its own subvolume, Timeshift '
                    'would be blocked!')


def swap_pruefen(ziel_gb, swap, platte):
    """Sicherheitspruefungen VOR dem Anlegen. Gibt einen Hinderungsgrund
    zurueck (Klartext) oder None, wenn alles in Ordnung ist."""
    ist_bytes = sum(x['groesse'] for x in swap if not x['ist_zram'])
    ist_gb = gb_gerundet(ist_bytes)
    if ziel_gb == ist_gb:
        return None

    # 0) Auf btrfs wird das Werkzeug `btrfs` gebraucht. FEHLT es, darf hier
    #    NICHTS weiterlaufen — sonst richtet das Root-Skript Schaden an:
    #    Es loescht die alte Swap-Datei ZUERST (swapoff, fstab-Zeile raus,
    #    rm -f) und legt den btrfs-Bereich ERST DANACH an. Fehlt `btrfs`,
    #    scheitern beide Zweige, `set -e` bricht ab, und mkswap/swapon werden
    #    nie erreicht. Der Nutzer haette hinterher WENIGER Swap als vorher.
    #    Zweiter Grund: Ohne diese Pruefung koennte (4) still danebengreifen —
    #    _lauf() liefert bei fehlendem Werkzeug '', und '' enthaelt 0x devid,
    #    die RAID-Warnung wuerde also nie anschlagen.
    if (platte['dateisystem'] == 'btrfs' and ziel_gb > 0
            and not _werkzeug('btrfs')):
        return t(
            'Für eine Swap-Datei auf btrfs wird das Paket btrfs-progs '
            'gebraucht — auf diesem Rechner fehlt es. Bitte erst '
            'installieren, dann noch einmal versuchen.\n\n'
            'Es wurde nichts verändert.',
            'A swap file on btrfs needs the package btrfs-progs — it '
            'is missing on this machine. Please install it first, then try '
            'again.\n\nNothing has been changed.')

    # 1) Ist gerade etwas ausgelagert, das zurueck muesste?
    benutzt = sum(x['benutzt'] for x in swap if not x['ist_zram'])
    if ziel_gb < ist_gb and benutzt > 0:
        frei = ram_messen()['verfuegbar']
        if benutzt > frei * 0.7:
            return t(
                'In der vorhandenen Swap-Datei liegen gerade '
                f'{groesse(benutzt)}. Beim Abschalten müssten die zurück '
                f'in den Arbeitsspeicher — dort sind aber nur '
                f'{groesse(frei)} frei. Das kann den Rechner zum Stehen '
                'bringen. Bitte erst Programme schließen.',
                f'{groesse(benutzt)} is currently held in the existing swap '
                f'file. Switching it off would move that back into RAM — but '
                f'only {groesse(frei)} is free there. That can freeze the '
                'machine. Please close some programs first.')

    # 2) Genug Platz auf der Platte?
    if ziel_gb > ist_gb:
        ausgabe = _lauf('findmnt', '-nbo', 'AVAIL', '/')
        try:
            frei_platte = int(ausgabe.split()[0])
        except Exception:
            frei_platte = None
        if frei_platte is not None:
            noetig = (ziel_gb - ist_gb) * 1024**3
            if noetig > frei_platte - 5 * 1024**3:      # 5 GiB Luft lassen
                return t(
                    f'Dafür werden {groesse(noetig)} gebraucht, frei sind '
                    f'nur {groesse(frei_platte)}. Das wäre zu knapp — '
                    'mindestens 5 GiB sollten frei bleiben.',
                    f'{groesse(noetig)} would be needed, but only '
                    f'{groesse(frei_platte)} is free. That is too tight — at '
                    'least 5 GiB should remain available.')

    # 3) Liegt an der Stelle schon etwas im Weg?
    if ziel_gb > 0 and os.path.isdir(SWAP_ORT):
        try:
            inhalt = os.listdir(SWAP_ORT)
        except Exception:
            inhalt = []
        eigenes = os.stat(SWAP_ORT).st_ino == 256
        if inhalt and not eigenes:
            return t(
                f'Unter {SWAP_ORT} liegt schon ein Ordner, und der ist '
                f'nicht leer ({len(inhalt)} Einträge). Dort soll aber der '
                'abgetrennte Bereich für die Swap-Datei hin. Bitte '
                'erst nachsehen, was das ist — das Programm räumt fremde '
                'Ordner nicht von selbst weg.',
                f'There is already a folder at {SWAP_ORT} and it is not empty '
                f'({len(inhalt)} entries). That is where the separate '
                'subvolume for the swap file should go. Please check what it '
                'is first — this program does not remove folders it did not '
                'create.')

    # 4) btrfs auf mehreren Platten kann keine Auslagerungsdatei
    if platte['dateisystem'] == 'btrfs' and ziel_gb > 0:
        zeilen = _lauf('btrfs', 'filesystem', 'show', '/')
        if zeilen.count('devid') > 1:
            return t(
                'Dein btrfs erstreckt sich über mehrere Platten (RAID). '
                'Darauf kann Linux keine Swap-Datei betreiben. '
                'Hier hilft nur eine eigene Swap-Partition.',
                'Your btrfs spans several disks (RAID). Linux cannot run a '
                'swap file on that. Only a dedicated swap partition works '
                'here.')
    return None


def skript_bauen(schritte, sys_):
    """Ein einziges Bash-Skript, das EINMAL mit Root-Rechten laeuft."""
    zeilen = ['#!/bin/bash', 'set -e',
              'export PATH=/sbin:/usr/sbin:/bin:/usr/bin']
    for _text, shell, _sicherung in schritte:
        zeilen += shell
    alle = [z for _t, sh, _s in schritte for z in sh]
    # Den zram-Dienst NUR neu starten, wenn seine Einstellungen angefasst
    # wurden. Bei einer reinen Reserve-Änderung waere das unnoetig — und ein
    # Neustart schiebt alles Ausgelagerte kurz zurueck in den Arbeitsspeicher.
    # ⚠️ Nicht doppelt: beim Einrichten steht der Start schon in den Schritten.
    schon_gestartet = any('zramswap' in z and
                          ('restart' in z or 'start' in z) for z in alle)
    if any('zramswap' in z for z in alle) and not schon_gestartet:
        zeilen.append(dienst_befehl(sys_) + ' || true')
    zeilen.append('echo RIKUSZRAM-FERTIG')
    return '\n'.join(zeilen) + '\n'


def braucht_installation(schritte):
    """Wird ein Paket nachinstalliert? Dann darf es laenger dauern (Netz)."""
    return any('apt-get install' in z for _t, sh, _s in schritte for z in sh)


def sicherungen_finden():
    """Alle Sicherungen, die dieses Programm angelegt hat (fuer Rueckgaengig)."""
    treffer = []
    for muster in ('/etc/default/zramswap.bak-%s-*' % STEMPEL,
                   '/etc/sysctl.d/*.bak-%s-*' % STEMPEL):
        treffer += glob.glob(muster)
    return sorted(treffer)


def bewerten(ram, zram, swap, swp, einst, empf=None, gen=None):
    """Ampel und Klartext-Urteil fuer die erste Seite.

    ⚠️⚠️ `empf` ist NICHT optional im Sinne von „egal" — ohne die Empfehlung
    kann die Ampel nur sagen, OB zram laeuft, nicht ob es GROSS GENUG ist.
    Genau das war bis 22.07.2026 der Fall, und es war der gefaehrlichste
    Fehler des ganzen Programms:

    Auf Gilberts pi5 lief zram mit 8 GiB bei 15,8 GiB Arbeitsspeicher — also
    der HALBEN empfohlenen Groesse. Die Ampel sagte trotzdem **gruen: „Alles
    in Ordnung. zram laeuft sauber."** Die Empfehlung (100 %) stand auf der
    zweiten Seite und wusste nichts von der Ampel; die Ampel nichts von ihr.

    Gilbert dazu: *„Das Problem ist, das Programm zeigt aber es ist optimal
    eingestellt. Das du es nicht siehst sowas macht mir angst."*

    ➡️ Wer „gruen" liest, schaut nicht weiter. Ein Pruefprogramm, das
    „alles gut" sagt, waehrend die Haelfte verschenkt wird, ist schlimmer
    als gar keines — es beendet die Suche.
    """
    hinweise = []
    zram_laeuft = len(zram) > 0
    swap_platte = [s for s in swap if not s['ist_zram']]

    # --- Regelt hier ein ANDERES Werkzeug? (siehe generator_messen) --------
    # Steht ganz vorne, weil in diesem Fall JEDE andere Empfehlung in die
    # Irre fuehren wuerde: Das Programm koennte zwar messen, aber sein
    # Aendern wuerde eine zweite, konkurrierende Einrichtung erzeugen.
    if gen and gen['aktiv']:
        g = gen['werte']
        wie = []
        if g.get('zram-size'): wie.append(t(f'Groesse {sicher(g["zram-size"])}',
                                            f'size {sicher(g["zram-size"])}'))
        if g.get('compression-algorithm'):
            wie.append(t(f'Verfahren {sicher(g["compression-algorithm"])}',
                         f'algorithm {sicher(g["compression-algorithm"])}'))
        if g.get('swap-priority'): wie.append(t(f'Prioritaet {sicher(g["swap-priority"])}',
                                                f'priority {sicher(g["swap-priority"])}'))
        detail = (' (' + ' · '.join(wie) + ')') if wie else ''
        return ('gelb',
                t('Auf diesem Rechner regelt ein anderes Werkzeug das zram.',
                  'Another tool manages zram on this machine.'),
                [t(f'zram wird hier von <b>systemd-zram-generator</b> '
                   f'eingestellt{detail} — nicht von <tt>zram-tools</tt>, das '
                   f'dieses Programm bedient. Die Einstellungen stehen in '
                   f'<tt>{sicher(gen["pfad"])}</tt>.',
                   f'zram here is configured by <b>systemd-zram-generator</b>'
                   f'{detail} — not by <tt>zram-tools</tt>, which this program '
                   f'operates. The settings live in '
                   f'<tt>{sicher(gen["pfad"])}</tt>.'),
                 t('<b>Dieses Programm ändert hier nichts.</b> Es würde sonst '
                   'eine zweite, konkurrierende Einrichtung anlegen — zwei '
                   'Werkzeuge für dieselbe Sache vertragen sich nicht. '
                   'Anschauen und Messen funktioniert weiterhin.',
                   '<b>This program changes nothing here.</b> Doing so would '
                   'create a second, competing setup — two tools for the same '
                   'job do not get along. Viewing and measuring still work.'),
                 t('Wer die Einstellung ändern will, bearbeitet die Datei oben '
                   'von Hand und lädt sie mit <tt>systemctl restart '
                   'systemd-zram-setup@zram0</tt> neu.',
                   'To change it, edit the file above by hand and reload with '
                   '<tt>systemctl restart systemd-zram-setup@zram0</tt>.')])

    if not zram_laeuft and not swap:
        return ('rot',
                t('Dein Rechner hat weder zram noch Swap.',
                  'This machine has neither zram nor swap.'),
                [t('Wird der Arbeitsspeicher voll, bricht der Rechner ab, '
                   'statt auszulagern. zram würde das verhindern.',
                   'When RAM runs out, programs are killed instead of being '
                   'swapped out. zram would prevent that.'),
                 t('▶ Dieses Programm kann zram für dich einrichten — auf der '
                   'nächsten Seite. Du brauchst dafür kein Terminal.',
                   '▶ This program can set zram up for you — on the next page. '
                   'You do not need a terminal for that.')])

    if not zram_laeuft:
        if einst['vorhanden']:
            hinweise.append(t(
                f'zram ist in {sicher(einst["pfad"])} eingerichtet, läuft aber '
                'gerade NICHT. Auf der nächsten Seite kann dieses Programm den '
                'Dienst einschalten und starten.',
                f'zram is configured in {sicher(einst["pfad"])} but is NOT '
                'running. On the next page this program can switch the service '
                'on and start it.'))
        else:
            hinweise.append(t(
                'Auf diesem Rechner ist zram noch gar nicht eingerichtet. '
                'Dieses Programm kann das auf der nächsten Seite für dich '
                'erledigen: Paket installieren, einstellen, einschalten.',
                'zram is not set up on this machine at all. On the next page '
                'this program can do it for you: install the package, '
                'configure it, switch it on.'))

    w = einst['werte']
    if w.get('SIZE') and w.get('PERCENT'):
        ist = zram[0]['groesse'] if zram_laeuft else 0
        hinweise.append(t(
            f'In der Einstellungsdatei stehen SIZE={w["SIZE"]} und '
            f'PERCENT={w["PERCENT"]} nebeneinander. Wirksam sind gerade '
            f'{groesse(ist)}. Fällt PERCENT einmal weg, greift plötzlich '
            'SIZE — zram wäre dann viel kleiner. Sauberer wäre, SIZE '
            'mit einem # stillzulegen.',
            f'The config file has both SIZE={w["SIZE"]} and '
            f'PERCENT={w["PERCENT"]}. Currently {groesse(ist)} is in effect. '
            'Should PERCENT ever be removed, SIZE takes over and zram would '
            'shrink dramatically. Better to comment SIZE out with a #.'))

    if len(swp['dateien']) > 1:
        liste = ', '.join(os.path.basename(d['datei']) for d in swp['dateien'])
        hinweise.append(t(
            f'Gleich {len(swp["dateien"])} Dateien stellen denselben Wert ein '
            f'({liste}). Es gewinnt die alphabetisch letzte — das ist leicht '
            'zu übersehen.',
            f'{len(swp["dateien"])} files set the same value ({liste}). The '
            'last one alphabetically wins — easy to overlook.'))

    if swp['dateien'] and swp['laufend'] is not None:
        soll = swp['dateien'][-1]['wert']
        if soll.isdigit() and int(soll) != swp['laufend']:
            hinweise.append(t(
                f'In der Datei steht {soll}, in Betrieb ist aber '
                f'{swp["laufend"]}. Die Einstellung wurde noch nicht '
                'übernommen (oder etwas überschreibt sie).',
                f'The file says {soll}, but {swp["laufend"]} is active. The '
                'setting has not been applied yet (or something overrides it).'))

    if zram_laeuft and swap_platte:
        p_zram = max((s['prio'] for s in swap if s['ist_zram']), default=-99)
        p_platte = max((s['prio'] for s in swap_platte), default=-99)
        if p_zram <= p_platte:
            hinweise.append(t(
                'Die langsame Platte wird gleich stark oder früher genutzt '
                'als das schnelle zram. zram sollte die höhere Priorität '
                'haben.',
                'The slow disk is used as much as, or before, fast zram. '
                'zram should have the higher priority.'))

    # --- Ist zram GROSS GENUG? (siehe Erklaerung oben) ---------------------
    if zram_laeuft and empf and ram.get('gesamt'):
        ist_bytes = sum(z['groesse'] for z in zram)
        ist_proz = ist_bytes * 100 / ram['gesamt']
        soll_proz = empf.get('zram_prozent')
        if soll_proz and ist_proz < soll_proz * 0.75:
            soll_bytes = ram['gesamt'] * soll_proz / 100
            anteil = ist_bytes / soll_bytes
            wie = (t('nicht einmal die Hälfte', 'not even half') if anteil < 0.5
                   else t('etwa die Hälfte', 'about half') if anteil < 0.65
                   else t('deutlich weniger', 'noticeably less'))
            hinweise.append(t(
                f'<b>zram ist kleiner als es sein könnte.</b> Eingestellt sind '
                f'{groesse(ist_bytes)} ({zahl(ist_proz, 0)} % des '
                f'Arbeitsspeichers) — empfohlen wären {groesse(soll_bytes)} '
                f'({soll_proz} %). Das ist {wie} dessen, was möglich wäre. '
                f'Auf der nächsten Seite kannst du den Regler verschieben.',
                f'<b>zram is smaller than it could be.</b> It is set to '
                f'{groesse(ist_bytes)} ({zahl(ist_proz, 0)} % of RAM) — the '
                f'recommendation would be {groesse(soll_bytes)} '
                f'({soll_proz} %). That is {wie} of what is possible. '
                f'You can move the slider on the next page.'))

    if zram_laeuft and swp['laufend'] is not None and swp['laufend'] < 100:
        hinweise.append(t(
            f'Der Wert steht auf {swp["laufend"]}. Mit zram im '
            'Arbeitsspeicher darf er höher sein (etwa 150) — Auslagern '
            'kostet hier ja kaum Zeit.',
            f'The value is {swp["laufend"]}. With zram in RAM it can be '
            'higher (around 150) — swapping costs almost nothing here.'))

    if not zram_laeuft:
        return ('gelb',
                t('Es läuft Swap, aber kein zram.',
                  'Swap is active, but zram is not.'),
                hinweise + [t(
                    'zram würde den Rechner bei vollem Speicher deutlich '
                    'flüssiger halten.',
                    'zram would keep the machine noticeably smoother when '
                    'memory fills up.')])
    if hinweise:
        return ('gelb',
                t('zram läuft — es gibt aber Punkte zum Anschauen.',
                  'zram is running — but there are things worth a look.'),
                hinweise)
    return ('gruen',
            t('Alles in Ordnung. zram läuft sauber.',
              'All good. zram is running properly.'), [])


# ---------------------------------------------------------------------------
# OBERFLAECHE
# ---------------------------------------------------------------------------

# ⚠️ Bewusst der schlichte Punkt ● (U+25CF), KEIN farbiges Emoji.
# Die Emoji-Variante 🟢 (U+1F7E2) kennen nur wenige Schriften: auf yoga genau
# EINE (Noto Sans Symbols2), auf Gilberts pi5 KEINE — dort erschien statt der
# Ampel ein leeres Kästchen (22.07.2026, von Gilbert im Bild entdeckt).
# ● dagegen kann praktisch jede Schrift (yoga 168, pi5 161 Schriften).
# Die Farbe kommt ohnehin aus dem Programm, nicht aus dem Zeichen — das
# Emoji war doppelt gemoppelt und hat nur die Zuverlässigkeit gekostet.
AMPEL = {'gruen': ('#2e7d32', '●'), 'gelb': ('#ef6c00', '●'),
         'rot': ('#c62828', '●')}


def swappiness_wort(wert):
    if wert < 20:
        return t('nur im Notfall auslagern', 'swap only as a last resort')
    if wert < 50:
        return t('sehr zurückhaltend', 'very reluctant')
    if wert < 80:
        return t('ausgewogen (Standard ist 60)', 'balanced (60 is the default)')
    if wert < 120:
        return t('eher freigiebig', 'fairly willing')
    if wert < 170:
        return t('offensiv — passend bei aktivem zram',
                 'aggressive — a good match for active zram')
    return t('sehr offensiv', 'very aggressive')


class RikusZram(Gtk.Window):

    @staticmethod
    def _fensterhoehe():
        """So hoch wie der Bildschirm erlaubt, hoechstens so hoch wie noetig.

        ⚠️ Vorher stand hier fest 800 Pixel. Auf Gilberts pi5 (1920x1080) war
        dadurch alles ab „Einstellungen" abgeschnitten — drei ganze Kaesten
        (Einstellungen · Dieses System · Und weiter?) waren unsichtbar,
        obwohl der Bildschirm reichlich Platz hatte. Man KONNTE rollen, aber
        nichts wies darauf hin: GTK blendet die Rollleiste aus, solange die
        Maus nicht darueber steht. Wer nicht zufaellig scrollt, haelt die
        Seite fuer zu Ende.
        Gefunden 22.07.2026 von Gilbert im Bildschirmfoto.

        1000 Pixel reichen fuer alle sieben Kaesten der Uebersicht; auf
        kleinen Bildschirmen bleiben 90 % der Hoehe uebrig, damit Titelleiste
        und Kontrollleisten Platz behalten.
        """
        try:
            bs = Gdk.Screen.get_default()
            if bs:
                hoch = bs.get_height()
                if hoch > 0:
                    return max(600, min(1000, int(hoch * 0.9)))
        except Exception:
            pass
        return 800

    def __init__(self):
        super().__init__(title='Rikus Zram')
        self.set_default_size(720, self._fensterhoehe())

        aussen = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(aussen)

        titel = Gtk.Label()
        titel.set_markup(
            '<span size="xx-large" weight="bold">Rikus Zram</span>\n'
            + t('<span size="small">zram, swappiness und Swap-Dateien '
                'einstellen — ohne Terminal</span>\n'
                '<span size="x-small">Geändert wird nur, was du ausdrücklich '
                'bestätigst.</span>',
                '<span size="small">Set up zram, swappiness and swap files '
                '— without a terminal</span>\n'
                '<span size="x-small">Nothing is changed unless you '
                'explicitly confirm it.</span>'))
        titel.set_justify(Gtk.Justification.CENTER)
        titel.set_margin_top(14)
        titel.set_margin_bottom(10)
        aussen.pack_start(titel, False, False, 0)

        # Update-Hinweis: bleibt UNSICHTBAR, solange nichts Neues da ist.
        # set_no_show_all verhindert, dass ein spaeteres show_all() ihn doch einblendet
        # — dieses Fenster baut sich nach jeder Aenderung neu auf.
        self.update_label = Gtk.Label()
        self.update_label.set_no_show_all(True)
        self.update_label.set_justify(Gtk.Justification.CENTER)
        self.update_label.set_margin_bottom(8)
        aussen.pack_start(self.update_label, False, False, 0)
        threading.Thread(target=self._update_pruefen, daemon=True).start()

        self.reiter = Gtk.Notebook()
        aussen.pack_start(self.reiter, True, True, 0)

        self.seite_uebersicht = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.seite_regler = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for seite, name in ((self.seite_uebersicht,
                             t('Übersicht', 'Overview')),
                            (self.seite_regler,
                             t('Empfehlung & Regler',
                               'Recommendation & sliders'))):
            rolle = Gtk.ScrolledWindow()
            rolle.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            rolle.add(seite)
            seite.set_border_width(16)
            seite.set_spacing(14)
            self.reiter.append_page(rolle, Gtk.Label(label=name))

        leiste = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        leiste.set_border_width(10)
        neu = Gtk.Button(label=t('Neu messen', 'Measure again'))
        neu.set_can_focus(False)
        neu.connect('clicked', lambda *_: self.aufbauen())
        leiste.pack_start(neu, True, True, 0)
        aussen.pack_start(leiste, False, False, 0)

        fuss = Gtk.Label()
        fuss.set_markup(
            f'<span size="small">Rikus Zram {VERSION} · '
            + t('von Gilbert Rikus · jede Änderung wird vorher gezeigt und '
                'gesichert</span>',
                'by Gilbert Rikus · every change is previewed and backed up '
                'first</span>'))
        fuss.set_margin_bottom(8)
        aussen.pack_start(fuss, False, False, 0)

        self.aufbauen()

    # -- Bausteine ----------------------------------------------------------

    def _update_pruefen(self):
        """Laeuft im EIGENEN Faden, damit das Fenster nie auf das Netz wartet.

        Das Ergebnis darf nicht von hier aus in die Oberflaeche geschrieben werden —
        GTK vertraegt keine Zugriffe aus fremden Faeden. Deshalb der Rueckweg ueber
        GLib.idle_add, das die Anzeige im Oberflaechen-Faden erledigt.
        """
        try:
            neu = neuere_version()
            if neu:
                GLib.idle_add(self._update_zeigen, neu)
        except Exception:
            pass                  # ein Hinweis darf das Programm niemals stoeren

    def _update_zeigen(self, neu):
        """Blendet die Hinweiszeile ein. Laeuft im Oberflaechen-Faden (via idle_add)."""
        try:
            # ⚠️ Die Versionsnummer kommt AUS DEM INTERNET und landet in set_markup.
            # Ein "&" darin macht ohne Absicherung die GANZE Zeile unsichtbar — ohne
            # jede Fehlermeldung. Genau dieser Fehler steckte bis 6.10 in Rikus Mintshot.
            text = GLib.markup_escape_text(
                t(f'▶ Version {neu} ist verfügbar', f'▶ Version {neu} is available'))
            link = GLib.markup_escape_text(t('ansehen', 'view'))
            self.update_label.set_markup(
                f'<span size="small" foreground="#2e7d32">{text} — '
                f'<a href="{GLib.markup_escape_text(UPDATE_SEITE)}">{link}</a></span>')
            self.update_label.show()
        except Exception:
            pass
        return False              # idle_add: nur einmal ausfuehren

    def _kasten(self, eltern, titel):
        rahmen = Gtk.Frame()
        rahmen.set_shadow_type(Gtk.ShadowType.IN)
        kopf = Gtk.Label()
        kopf.set_markup(f'<b>{titel}</b>')
        rahmen.set_label_widget(kopf)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(12)
        rahmen.add(box)
        eltern.pack_start(rahmen, False, False, 0)
        return box

    def _zeile(self, box, text, klein=False):
        lbl = Gtk.Label()
        lbl.set_markup(text)
        lbl.set_halign(Gtk.Align.START)
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        lbl.set_xalign(0)
        if klein:
            lbl.get_style_context().add_class('dim-label')
        box.pack_start(lbl, False, False, 0)
        return lbl

    def _regler(self, box, von, bis, ist, soll, schritt, beschriftung):
        """Schieberegler: steht auf dem IST-Wert, Empfehlung als Markierung.

        ⚠️ Bitte nicht umbauen — das ist Absicht, nicht Zufall:
        Der Regler zeigt, was auf dem Rechner WIRKLICH eingestellt ist. Die
        Empfehlung steht als Markierung auf der Skala daneben; verschieben
        muss der Nutzer selbst. Ein Regler, der von sich aus auf der
        Empfehlung steht, verwischt genau diesen Unterschied — man sieht dann
        nicht mehr, was man gerade hat, und veraendert womoeglich etwas, ohne
        es zu merken.
        """
        skala = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, von, bis, schritt)
        skala.set_value(ist)
        skala.ist_wert = ist          # fuer „Zurueck auf meine Werte"
        skala.soll_wert = soll
        skala.set_digits(0)
        skala.set_hexpand(True)
        skala.set_can_focus(False)
        # Markierungen: wo stehst du gerade, was ist empfohlen
        skala.add_mark(soll, Gtk.PositionType.BOTTOM,
                       t(f'empfohlen: {soll}', f'recommended: {soll}'))
        if abs(ist - soll) > schritt:
            skala.add_mark(ist, Gtk.PositionType.TOP,
                           t(f'jetzt: {ist}', f'now: {ist}'))
        box.pack_start(skala, False, False, 0)

        wirkung = self._zeile(box, '', klein=False)

        def geaendert(s):
            wert = int(s.get_value())
            text = beschriftung(wert)
            if wert == ist and ist != soll:
                text += t(
                    f'\n<span foreground="#1565c0">Das ist dein jetziger '
                    f'Stand. Empfohlen wären <b>{soll}</b> — schieb den '
                    f'Regler dorthin, wenn du magst.</span>',
                    f'\n<span foreground="#1565c0">This is your current '
                    f'setting. <b>{soll}</b> would be recommended — move the '
                    f'slider there if you like.</span>')
            elif wert == soll and ist != soll:
                text += t(
                    '\n<span foreground="#2e7d32">Das entspricht der '
                    f'Empfehlung. Bei dir läuft gerade {ist}.</span>',
                    '\n<span foreground="#2e7d32">That matches the '
                    f'recommendation. Currently running: {ist}.</span>')
            elif wert != ist:
                text += t(
                    f'\n<span foreground="#ef6c00">Das ist eine Änderung — '
                    f'bei dir läuft gerade {ist}, empfohlen wären {soll}.</span>',
                    f'\n<span foreground="#ef6c00">That is a change — '
                    f'currently {ist} is running, {soll} is recommended.</span>')
            wirkung.set_markup(text)

        skala.connect('value-changed', geaendert)
        geaendert(skala)
        return skala

    # -- Aufbau -------------------------------------------------------------

    def aufbauen(self):
        # Beim „Neu messen" soll der Nutzer auf seinem Reiter bleiben.
        # Beim ersten Aufbau steht das auf 0 = Uebersicht.
        vorher = self.reiter.get_current_page()

        for seite in (self.seite_uebersicht, self.seite_regler):
            for kind in seite.get_children():
                seite.remove(kind)

        ram = ram_messen()
        zram = zram_messen()
        swap = swap_messen()
        swp = swappiness_messen()
        einst = einstellung_messen()
        gen = generator_messen()
        sys_ = system_messen()
        platte = platte_messen()
        ruhe = ruhezustand_messen()
        # ⚠️ REIHENFOLGE IST PFLICHT: erst rechnen, dann bewerten.
        # Die Ampel braucht die Empfehlung, um zu erkennen, ob zram zwar
        # laeuft, aber zu klein ist. Vertauscht man beide Zeilen, bekommt
        # bewerten() ein leeres empf und meldet wieder faelschlich „gruen"
        # bei halb eingestelltem zram (Gilberts pi5, 22.07.2026).
        empf = empfehlung_rechnen(ram, zram, swap, swp, platte, ruhe)
        ampel, urteil, hinweise = bewerten(ram, zram, swap, swp, einst, empf, gen)

        # fuer den Uebernehmen-Knopf merken
        # ⚠️ 'zram' MUSS hier stehen: _uebernehmen() reicht es an
        # aenderungen_sammeln() weiter, damit erkannt wird, ob zram erst
        # eingerichtet werden muss. Es fehlte von v1.1 bis v1.4 — dadurch
        # brachen "Vorschau" und "Uebernehmen" mit KeyError ab, das Programm
        # konnte NICHTS mehr aendern, sondern nur noch anzeigen.
        self.daten = {'sys': sys_, 'swp': swp, 'einst': einst, 'ram': ram,
                      'swap': swap, 'platte': platte, 'ruhe': ruhe,
                      'zram': zram, 'gen': gen}

        self._seite1(ram, zram, swap, swp, einst, sys_, platte, ruhe,
                     ampel, urteil, hinweise, empf)
        self._seite2(ram, zram, swap, swp, platte, ruhe, empf)

        self.show_all()

        # WICHTIG: show_all() gibt dem ersten bedienbaren Element den Fokus —
        # das ist ein Schieberegler auf Seite 2. Ein Gtk.Notebook wechselt
        # dann automatisch auf die Seite mit dem Fokus. Ohne diese Zeile
        # startet das Programm also bei den Reglern statt bei der Uebersicht,
        # obwohl die Anleitung „die erste Seite zeigt deinen Ist-Zustand"
        # verspricht. Der Nutzer soll zuerst SEHEN, nicht gleich schieben.
        self.reiter.set_current_page(vorher if vorher >= 0 else 0)

    def _seite1(self, ram, zram, swap, swp, einst, sys_, platte, ruhe,
                ampel, urteil, hinweise, empf=None):
        s = self.seite_uebersicht

        farbe, zeichen = AMPEL[ampel]
        box = self._kasten(s, t('Kurz gesagt', 'In short'))
        self._zeile(box, f'<span size="large" foreground="{farbe}" '
                         f'weight="bold">{zeichen}  {urteil}</span>')
        if hinweise:
            self._zeile(box, '')
            for h in hinweise:
                self._zeile(box, f'•  {h}', klein=True)

        box = self._kasten(s, t('Arbeitsspeicher', 'RAM'))
        anteil = ram['belegt'] / ram['gesamt'] if ram['gesamt'] else 0
        b = Gtk.ProgressBar()
        b.set_fraction(min(max(anteil, 0.0), 1.0))
        b.set_show_text(True)
        b.set_text(t(f'{groesse(ram["belegt"])} von {groesse(ram["gesamt"])} belegt',
                     f'{groesse(ram["belegt"])} of {groesse(ram["gesamt"])} in use'))
        box.pack_start(b, False, False, 2)
        self._zeile(box, t(f'Noch verfügbar: <b>{groesse(ram["verfuegbar"])}</b>',
                           f'Still available: <b>{groesse(ram["verfuegbar"])}</b>'))
        self._zeile(box, t('Das ist der Schreibtisch, auf dem der Rechner '
                           'arbeitet. Wird er voll, muss etwas weichen.',
                           'This is the desk the computer works on. When it '
                           'fills up, something has to give way.'), klein=True)

        box = self._kasten(s, t('zram — komprimierter Auslagerungsspeicher im RAM',
                                'zram — compressed swap inside RAM'))
        if zram:
            for g in zram:
                self._zeile(box, t(
                    f'<b>Läuft.</b>  Größe <b>{groesse(g["groesse"])}</b> · '
                    f'Kompression <b>{sicher(g["verfahren"])}</b>',
                    f'<b>Running.</b>  Size <b>{groesse(g["groesse"])}</b> · '
                    f'compression <b>{sicher(g["verfahren"])}</b>'))

                # --- Eingestellt vs. moeglich, DIREKT hier ------------------
                # 🔴 Gilbert 22.07.2026: „auf der ersten seite steht nicht
                # wieviel es eingestellt ist das swap, und was noch fehlt.
                # wie z.B. bei pi5 jetzt. er könnte 16gb hat aber nur 8 gb
                # eingestellt. das ist der fehler."
                # Der Kasten nannte nur die eingestellte Groesse — ob das viel
                # oder wenig ist, stand nirgends. Wer 8,0 GiB liest, kann
                # nicht wissen, dass 15,8 moeglich waeren. Die Einordnung
                # gehoert GENAU HIER hin, wo die Zahl steht — nicht nur oben
                # in der Ampel und nicht nur auf der zweiten Seite.
                if ram.get('gesamt'):
                    proz = g['groesse'] * 100 / ram['gesamt']
                    soll_proz = (empf or {}).get('zram_prozent')
                    zeile = t(f'Das sind <b>{zahl(proz, 0)} %</b> deines '
                              f'Arbeitsspeichers ({groesse(ram["gesamt"])}).',
                              f'That is <b>{zahl(proz, 0)} %</b> of your RAM '
                              f'({groesse(ram["gesamt"])}).')
                    if soll_proz:
                        soll_b = ram['gesamt'] * soll_proz / 100
                        fehlt = soll_b - g['groesse']
                        if fehlt > 0.05 * ram['gesamt']:
                            zeile += t(
                                f' Empfohlen wären <b>{groesse(soll_b)}</b> '
                                f'({soll_proz} %) — es fehlen '
                                f'<b>{groesse(fehlt)}</b>.',
                                f' The recommendation would be '
                                f'<b>{groesse(soll_b)}</b> ({soll_proz} %) — '
                                f'<b>{groesse(fehlt)}</b> short.')
                        else:
                            zeile += t(' Das entspricht der Empfehlung.',
                                       ' That matches the recommendation.')
                    self._zeile(box, zeile)
                # ⚠️ Die Rate erst ab einer ERNSTHAFTEN Datenmenge zeigen.
                # Bis 22.07.2026 lag die Schwelle bei 4 KiB — auf Gilberts pi5
                # standen 16 KiB drin, und daraus wurde „16,0 KiB belegen
                # 48,0 KiB — das ist 0,3-fach". Das liest sich wie eine
                # miserable Kompression, ist aber nur der Verwaltungsaufwand
                # von zram, der bei fast leerem Speicher naturgemaess groesser
                # ist als die Daten selbst. Erst ab einigen Megabyte sagt die
                # Zahl etwas aus.
                if g['daten'] >= 10 * 1024**2 and g['belegt_echt'] > 0:
                    faktor = g['daten'] / g['belegt_echt']
                    self._zeile(box, t(
                        f'Gerade zusammengepresst: {groesse(g["daten"])} Daten '
                        f'belegen nur {groesse(g["belegt_echt"])} — das ist '
                        f'<b>{zahl(faktor)}-fach</b>',
                        f'Currently compressed: {groesse(g["daten"])} of data '
                        f'occupy only {groesse(g["belegt_echt"])} — that is '
                        f'<b>{zahl(faktor)}×</b>'))
                elif g['daten'] > 0:
                    self._zeile(box, t(
                        f'Zurzeit ist so gut wie nichts ausgelagert '
                        f'({groesse(g["daten"])}) — dein Arbeitsspeicher reicht '
                        f'gerade aus. Wie stark zram zusammenpresst, zeigt sich '
                        f'erst, wenn wirklich etwas drin liegt.',
                        f'Practically nothing is swapped out right now '
                        f'({groesse(g["daten"])}) — your RAM is sufficient. How '
                        f'well zram compresses only shows once there is real '
                        f'data in it.'), klein=True)
                else:
                    self._zeile(box, t(
                        'Zurzeit ist nichts ausgelagert — dein '
                        'Arbeitsspeicher reicht gerade aus.',
                        'Nothing is swapped out right now — your RAM is '
                        'sufficient at the moment.'), klein=True)
        else:
            self._zeile(box, t('<b>Läuft nicht.</b>', '<b>Not running.</b>'))
        self._zeile(box, t(
            'zram legt Ausgelagertes nicht auf der Platte ab, sondern presst '
            'es im Arbeitsspeicher zusammen — wie ein Vakuumbeutel für '
            'Winterkleidung.',
            'Instead of putting swapped data on disk, zram compresses it '
            'inside RAM — like a vacuum bag for winter clothes.'), klein=True)

        box = self._kasten(s, t('Swap — Auslagerung auf die Platte',
                                'Swap — paging to disk'))
        platte_swap = [x for x in swap if not x['ist_zram']]
        if platte_swap:
            for x in platte_swap:
                self._zeile(box, t(
                    f'<b>{sicher(x["name"])}</b> ({sicher(x["art"])}) · {groesse(x["groesse"])} '
                    f'· benutzt {groesse(x["benutzt"])} · Priorität {x["prio"]}',
                    f'<b>{sicher(x["name"])}</b> ({sicher(x["art"])}) · {groesse(x["groesse"])} '
                    f'· used {groesse(x["benutzt"])} · priority {x["prio"]}'))
        else:
            self._zeile(box, t('Keine vorhanden.', 'None present.'))

        # --- Auch hier: eingestellt gegen empfohlen (Gilbert 22.07.) --------
        # Dieselbe Luecke wie beim zram-Kasten: Die Groesse stand da, aber
        # nicht, ob sie passt. Wer „200,0 MiB" liest, weiss nicht, ob das
        # viel oder wenig ist.
        soll_gb = (empf or {}).get('swap_gb')
        if soll_gb is not None:
            ist_b = sum(x['groesse'] for x in platte_swap if x.get('art') == 'file')
            soll_b = soll_gb * 1024**3
            unterschied = soll_b - ist_b
            if abs(unterschied) > 0.3 * 1024**3:
                if unterschied > 0:
                    self._zeile(box, t(
                        f'Empfohlen wären <b>{groesse(soll_b)}</b> als Reserve '
                        f'— es fehlen <b>{groesse(unterschied)}</b>.',
                        f'The recommendation would be <b>{groesse(soll_b)}</b> '
                        f'as a reserve — <b>{groesse(unterschied)}</b> short.'))
                else:
                    self._zeile(box, t(
                        f'Empfohlen wären <b>{groesse(soll_b)}</b> — du hast '
                        f'<b>{groesse(-unterschied)}</b> mehr als nötig. '
                        f'Der Platz bleibt auf der Platte belegt.',
                        f'The recommendation would be <b>{groesse(soll_b)}</b> '
                        f'— you have <b>{groesse(-unterschied)}</b> more than '
                        f'needed. That space stays occupied on disk.'))
            elif ist_b:
                self._zeile(box, t('Das entspricht der Empfehlung.',
                                   'That matches the recommendation.'))

        # --- Die Zahl, die JEDES andere Werkzeug zeigt ----------------------
        # 🔴 Gilbert 22.07.2026: „schau mal die auslagerungsdatei. da steht
        # 2 gb. in fastfetch steht aber 17 gb" — und danach: „fuer mich
        # funktioniert das programm nicht. weil es zeigt nicht das was reel
        # ist."  Er hatte recht, auch wenn beide Zahlen stimmten:
        # fastfetch/htop/free zeigen die SUMME aus zram + Datei, weil Linux
        # zram ebenfalls als Auslagerung fuehrt (in /proc/swaps steht es
        # sogar als „partition"). Dieses Programm zeigte die Teile — die
        # Summe aber nirgends. Wer die beiden Zahlen nebeneinander sah,
        # musste schliessen, dass eine davon luegt.
        # ➡️ Die Summe steht jetzt hier, mit dem Grund fuer den Unterschied.
        summe = sum(x['groesse'] for x in swap)
        zram_teil = sum(x['groesse'] for x in swap if x['ist_zram'])
        datei_teil = summe - zram_teil
        if summe:
            if zram_teil and datei_teil:
                aufteilung = t(
                    f' — davon {groesse(zram_teil)} zram (im Arbeitsspeicher) '
                    f'und {groesse(datei_teil)} auf der Platte',
                    f' — of that {groesse(zram_teil)} zram (inside RAM) '
                    f'and {groesse(datei_teil)} on disk')
            elif zram_teil:
                aufteilung = t(' — alles davon zram (im Arbeitsspeicher)',
                               ' — all of it zram (inside RAM)')
            else:
                aufteilung = t(' — alles davon auf der Platte',
                               ' — all of it on disk')
            self._zeile(box, t(
                f'<b>Zusammen {groesse(summe)} Auslagerung</b>{aufteilung}.',
                f'<b>{groesse(summe)} of swap in total</b>{aufteilung}.'))
            if zram_teil:
                self._zeile(box, t(
                    'Andere Programme wie <i>fastfetch</i>, <i>htop</i> oder '
                    '<i>free</i> zeigen <b>nur diese Summe</b> — sie zählen '
                    'zram mit, weil Linux es ebenfalls als Auslagerung führt. '
                    'Dort steht deshalb eine größere Zahl als oben bei der '
                    'einzelnen Datei. Beides stimmt, es wird nur '
                    'unterschiedlich zusammengefasst.',
                    'Other tools such as <i>fastfetch</i>, <i>htop</i> or '
                    '<i>free</i> show <b>only this total</b> — they count zram '
                    'in, because Linux treats it as swap too. That is why they '
                    'show a larger number than the individual file above. Both '
                    'are correct, they are just grouped differently.'),
                    klein=True)

        # --- Ruhezustand: erklaeren, nicht nur benennen ---------------------
        # Gilbert 21.07.2026: „was bedeutet den ruhestand nutzen?" — der
        # Begriff stand vorher nackt da, ohne die noetige GROESSE und ohne den
        # Hinweis, dass die Datei allein nicht reicht. Wer daraufhin nur den
        # Regler hochschiebt, wundert sich, dass es trotzdem nicht geht.
        noetig_gb = max(1, int(ram['gesamt'] / 1024**3) + 1)
        ist_swapdatei_gb = gb_gerundet(
            sum(x['groesse'] for x in swap
                if not x['ist_zram'] and x.get('art') == 'file'))
        if ruhe['eingerichtet']:
            self._zeile(box, t(
                f'<b>Ruhezustand (Hibernate): eingerichtet.</b> Dabei schreibt '
                f'der Rechner den ganzen Arbeitsspeicher auf die Platte und '
                f'schaltet sich komplett aus — nach dem Einschalten ist alles '
                f'wieder offen wie vorher. Dafür muss die Swap-Datei '
                f'mindestens {noetig_gb} GiB groß sein (du hast '
                f'{ist_swapdatei_gb} GiB).',
                f'<b>Hibernation: configured.</b> The computer writes the '
                f'entire RAM to disk and switches off completely — after '
                f'switching on, everything is open again as before. The swap '
                f'file has to be at least {noetig_gb} GiB for that (you have '
                f'{ist_swapdatei_gb} GiB).'), klein=True)
        elif ruhe['kann']:
            self._zeile(box, t(
                f'<b>Ruhezustand (Hibernate): nicht eingerichtet.</b> Damit '
                f'würde der Rechner den ganzen Arbeitsspeicher auf die Platte '
                f'schreiben und sich <i>komplett</i> ausschalten — kein Strom, '
                f'und nach dem Einschalten ist alles wieder offen wie vorher. '
                f'Das ist etwas anderes als die Bereitschaft, in die dein '
                f'Laptop beim Zuklappen geht: die ist schneller, braucht aber '
                f'weiter Strom, und bei leerem Akku ist alles weg.',
                f'<b>Hibernation: not configured.</b> It would write the entire '
                f'RAM to disk and switch the machine off <i>completely</i> — no '
                f'power at all, and after switching on everything is open again '
                f'as before. That is different from the standby your laptop '
                f'enters when you close the lid: faster, but it keeps drawing '
                f'power, and when the battery runs out everything is lost.'),
                klein=True)
            self._zeile(box, t(
                f'Wenn du ihn nutzen willst, brauchst du <b>zwei</b> Dinge: '
                f'eine Swap-Datei von <b>mindestens {noetig_gb} GiB</b> '
                f'(du hast {ist_swapdatei_gb} GiB — auf der nächsten Seite '
                f'einstellbar) <b>und</b> einen Eintrag in der '
                f'Startkonfiguration, den <b>dieses Programm nicht setzt</b>. '
                f'zram hilft hier nicht: Es liegt im Arbeitsspeicher und ist '
                f'beim Ausschalten mit weg.',
                f'To use it you need <b>two</b> things: a swap file of '
                f'<b>at least {noetig_gb} GiB</b> (you have {ist_swapdatei_gb} '
                f'GiB — adjustable on the next page) <b>and</b> an entry in the '
                f'boot configuration that <b>this program does not set</b>. '
                f'zram cannot help here: it lives in RAM and is gone when the '
                f'power goes off.'), klein=True)

        box = self._kasten(s, t('Einstellungen', 'Settings'))
        if swp['laufend'] is not None:
            self._zeile(box, f'<b>swappiness: {swp["laufend"]}</b> — '
                             f'{swappiness_wort(swp["laufend"])}')
        if einst['vorhanden']:
            w = ' · '.join(f'{sicher(k)}={sicher(v)}'
                           for k, v in einst['werte'].items())
            self._zeile(box, t(f'Eingerichtet in <tt>{sicher(einst["pfad"])}</tt>:',
                               f'Configured in <tt>{sicher(einst["pfad"])}</tt>:'))
            self._zeile(box, f'<tt>{w}</tt>', klein=True)

        box = self._kasten(s, t('Dieses System', 'This machine'))
        self._zeile(box, sicher(sys_['name']))
        self._zeile(box, t('Startsystem: <b>%s</b>', 'Init system: <b>%s</b>')
                    % sicher(sys_['start']))
        art = (t('SSD', 'SSD') if platte['ssd']
               else t('drehende Festplatte', 'spinning disk')) \
            if platte['ssd'] is not None else t('unbekannt', 'unknown')
        self._zeile(box, t(
            'Systemplatte: <b>%s</b> · Dateisystem <b>%s</b> · noch frei %s',
            'System disk: <b>%s</b> · filesystem <b>%s</b> · %s still free')
            % (art, sicher(platte['dateisystem']),
               sicher(platte['frei_text'])))

        # --- Weg zur zweiten Seite -----------------------------------------
        # Bewusster Ablauf: erst schauen, was ist — dann per Knopf weiter zu
        # den Einstellungen. Kein Nebeneinander zweier Reiter.
        weiter = self._kasten(s, t('Und weiter?', 'What next?'))
        self._zeile(weiter, t(
            'Oben steht, <b>was auf deinem Rechner läuft</b>. Auf der nächsten '
            'Seite siehst du dazu die <b>Empfehlung für genau dieses System</b> '
            '— mit Erklärung, was jeder Wert bedeutet. Verstellen tust du '
            'dort selbst; von allein ändert sich nichts.',
            'Above you see <b>what is running on your machine</b>. The next '
            'page shows the <b>recommendation for exactly this system</b> — '
            'with an explanation of what each value means. You adjust things '
            'there yourself; nothing changes on its own.'))
        knopf_weiter = Gtk.Button(
            label=t('Empfehlung für diesen Rechner ansehen  →',
                    'See the recommendation for this machine  →'))
        knopf_weiter.set_can_focus(False)
        knopf_weiter.connect('clicked',
                             lambda *_: self.reiter.set_current_page(1))
        weiter.pack_start(knopf_weiter, False, False, 4)

    def _seite2(self, ram, zram, swap, swp, platte, ruhe, e):
        s = self.seite_regler
        gb = ram['gesamt'] / 1024**3

        kopf = self._kasten(s, t('Was für diesen Rechner passt',
                                 'What suits this machine'))
        self._zeile(kopf, t(
            f'Erkannt: <b>{zahl(gb)} GiB</b> Arbeitsspeicher · '
            f'<b>{"SSD" if platte["ssd"] else "drehende Platte"}</b> · '
            f'Dateisystem <b>{sicher(platte["dateisystem"])}</b> · Ruhezustand '
            f'<b>{"eingerichtet" if ruhe["eingerichtet"] else "nicht eingerichtet"}</b>',
            f'Detected: <b>{zahl(gb)} GiB</b> RAM · '
            f'<b>{"SSD" if platte["ssd"] else "spinning disk"}</b> · '
            f'filesystem <b>{sicher(platte["dateisystem"])}</b> · hibernation '
            f'<b>{"configured" if ruhe["eingerichtet"] else "not configured"}</b>'))
        self._zeile(kopf, t(
            '<b>Die Regler stehen auf dem, was bei dir gerade läuft.</b> '
            'Unter jedem Regler steht auf der Skala, was für dieses System '
            '<b>empfohlen</b> wäre — dorthin schiebst du selbst, wenn du '
            'möchtest. <b>Geschrieben wird nichts, bevor du es unten '
            'bestätigst.</b>',
            '<b>The sliders show what is currently running on your machine.</b> '
            'Below each slider the scale marks what would be <b>recommended</b> '
            'for this system — you move it there yourself if you want. '
            '<b>Nothing is written until you confirm below.</b>'), klein=True)

        # Ist-Zustand auf dieser Seite noch einmal in einer Zeile — man soll
        # nicht zurückblättern müssen, um zu sehen, wovon man ausgeht.
        zram_txt = (f'{groesse(zram[0]["groesse"])} {zram[0]["verfahren"]}'
                    if zram else t('aus', 'off'))
        swap_txt = (f'{gb_gerundet(sum(x["groesse"] for x in swap if not x["ist_zram"]))} GiB'
                    if [x for x in swap if not x['ist_zram']]
                    else t('keine', 'none'))
        self._zeile(kopf, t(
            f'<b>Bei dir läuft gerade:</b>  zram <b>{zram_txt}</b>  ·  '
            f'swappiness <b>{swp["laufend"]}</b>  ·  Swap-Datei <b>{swap_txt}</b>',
            f'<b>Currently running:</b>  zram <b>{zram_txt}</b>  ·  '
            f'swappiness <b>{swp["laufend"]}</b>  ·  swap file <b>{swap_txt}</b>'))

        # --- Turbo-Groesse ---
        ist_prozent = 100
        if zram and ram['gesamt']:
            ist_prozent = int(round(zram[0]['groesse'] / ram['gesamt'] * 100))
        elif not zram:
            ist_prozent = 0

        box = self._kasten(s, t('1. zram-Größe (Anteil am Arbeitsspeicher)',
                                '1. zram size (share of RAM)'))

        def turbo_text(p):
            mb = ram['gesamt'] * p / 100
            if p == 0:
                return t('Kein zram — es wird nichts komprimiert.',
                         'No zram — nothing gets compressed.')
            # 🔴🔴 RECHENFEHLER bis v1.12 — von Gilbert entdeckt (22.07.2026):
            # Hier stand `gewinn = mb * 3.5` und daraus „bei 3,5-facher
            # Kompression passen 54 GiB hinein". FALSCH: Die zram-Groesse
            # (DISKSIZE) ist BEREITS die unkomprimierte Datenmenge, die
            # hineinpasst — das System rechnet sie schon so. Die Zahl wurde
            # also ein zweites Mal multipliziert.
            #   zramctl: DISKSIZE 15,4G  =  15,4 GiB Daten passen hinein
            #            TOTAL           =  was davon ECHTEN RAM belegt
            # Der Gewinn liegt nicht darin, dass mehr hineinpasst, sondern
            # dass das Hineingelegte WENIGER PLATZ BRAUCHT.
            # ⚠️ Ebenso wichtig: zram ist KEIN zusaetzlicher Speicher. Es
            # liegt IM Arbeitsspeicher (gemessen: MemTotal bleibt gleich).
            belegt = mb / 3.5
            frei = mb - belegt
            return t(
                f'zram-Größe <b>{groesse(mb)}</b> ({p} % vom '
                f'Arbeitsspeicher).\nSo viele Daten passen hinein — sie '
                f'belegen dabei bei etwa 3,5-facher Kompression nur rund '
                f'<b>{groesse(belegt)}</b> echten Arbeitsspeicher. '
                f'Es bleiben also rund <b>{groesse(frei)}</b> mehr für '
                f'deine Programme übrig.',
                f'zram size <b>{groesse(mb)}</b> ({p} % of RAM).\nThat much '
                f'data fits in — occupying only about <b>{groesse(belegt)}</b> '
                f'of real RAM at roughly 3.5× compression. That leaves around '
                f'<b>{groesse(frei)}</b> more for your programs.')

        self.regler_turbo = self._regler(
            box, 0, 200, ist_prozent, e['zram_prozent'], 10, turbo_text)
        self._zeile(box, f'💡 {e["zram_warum"]}', klein=True)

        # --- swappiness ---
        box = self._kasten(s, t('2. swappiness — wie bereitwillig ausgelagert wird',
                                '2. swappiness — how readily data is swapped'))

        def swp_text(v):
            return t(
                f'Wert <b>{v}</b> — {swappiness_wort(v)}.\n'
                'Je höher, desto eher schiebt der Rechner selten '
                'gebrauchte Daten beiseite, um Platz zu schaffen.',
                f'Value <b>{v}</b> — {swappiness_wort(v)}.\n'
                'The higher, the sooner the system moves rarely used data '
                'aside to free up space.')

        self.regler_freude = self._regler(
            box, 0, 200, swp['laufend'] or 60, e['swappiness'], 10, swp_text)
        self._zeile(box, f'💡 {e["swappiness_warum"]}', klein=True)

        # --- Reserve auf der Platte ---
        # Grundsatz: Ein Regler, den man bewegen kann, VERSPRICHT etwas — was
        # nicht geht, wird gesperrt und nicht mit Kleingedrucktem erklaert.
        box = self._kasten(s, t('3. Swap-Datei (Auslagerungsdatei)',
                                '3. Swap file'))
        ist_swap_gb = gb_gerundet(sum(x['groesse'] for x in swap
                                       if not x['ist_zram']))

        def swap_text(v):
            if v == 0:
                return t('Keine Swap-Datei.\nSolange zram und Arbeitsspeicher '
                         'reichen, fehlt dir nichts.',
                         'No swap file.\nAs long as zram and RAM suffice, you '
                         'are not missing anything.')
            return t(
                f'Swap-Datei von <b>{v} GiB</b>.\nSie bleibt im Alltag leer '
                'und greift nur, wenn Arbeitsspeicher UND zram voll sind — '
                'als Sicherheitsnetz.',
                f'Swap file of <b>{v} GiB</b>.\nIt stays empty in daily use '
                'and only kicks in when both RAM and zram are full — a safety '
                'net.')

        self.regler_reserve = self._regler(
            box, 0, max(int(gb) + 4, 16), ist_swap_gb, e['swap_gb'], 1,
            swap_text)
        self._zeile(box, f'💡 {e["swap_warum"]}', klein=True)
        # Der Ruhezustand ist der EINZIGE Grund fuer eine sehr grosse Datei —
        # dann aber zwingend >= RAM. Ohne diese Zahl kann niemand entscheiden.
        if ruhe['kann'] and not ruhe['eingerichtet']:
            noetig = max(1, int(gb) + 1)
            self._zeile(box, t(
                f'<b>Ab {noetig} GiB wäre der Ruhezustand möglich</b> '
                f'(Rechner ganz aus, alles bleibt offen). Darunter lehnt Linux '
                f'ihn ab, weil der Arbeitsspeicher nicht hineinpasst. '
                f'⚠️ Die Größe allein genügt aber nicht — es fehlt dann noch '
                f'ein Eintrag in der Startkonfiguration, den dieses Programm '
                f'nicht setzt.',
                f'<b>From {noetig} GiB up, hibernation would be possible</b> '
                f'(machine fully off, everything stays open). Below that Linux '
                f'refuses it, because RAM would not fit. ⚠️ The size alone is '
                f'not enough though — an entry in the boot configuration is '
                f'still missing, and this program does not set it.'),
                klein=True)
        if platte['dateisystem'] == 'btrfs':
            self._zeile(box, t(
                f'⚠ <b>Auf deinem Dateisystem (btrfs) mit Vorsicht:</b> Die '
                f'Datei bekommt einen <b>eigenen abgetrennten Bereich '
                f'({SWAP_ORT})</b>. Sonst könnte Timeshift keine '
                'Sicherungspunkte mehr anlegen — lautlos. Das Programm legt '
                'ihn selbst richtig an.',
                f'⚠ <b>Careful on btrfs:</b> the file gets its <b>own '
                f'subvolume ({SWAP_ORT})</b>. Otherwise Timeshift could no '
                'longer create snapshots — silently. This program sets it up '
                'correctly by itself.'))

        # --- Übernehmen ---------------------------------------------------
        box = self._kasten(s, t('Übernehmen', 'Apply'))
        self._zeile(box, t(
            'Wenn die Regler so stehen, wie du es haben willst, geht es '
            'hier weiter. <b>Erst „Zeigen" drücken</b> — dann siehst du in '
            'Ruhe, was passieren würde, ohne dass etwas passiert.',
            'Once the sliders are where you want them, continue here. '
            '<b>Press "Preview" first</b> — then you can see calmly what '
            'would happen, without anything happening.'))
        self._zeile(box, t(
            'Jede Datei, die dabei angefasst wird, wird vorher gesichert — '
            'und es gibt einen Rückgängig-Knopf.',
            'Every file that gets touched is backed up first — and there is '
            'an undo button.'), klein=True)

        zurueck_ist = Gtk.Button(label=t('Zurück auf meine jetzigen Werte',
                                         'Back to my current values'))
        zurueck_ist.set_can_focus(False)
        zurueck_ist.connect('clicked', lambda *_: self._regler_zuruecksetzen())
        box.pack_start(zurueck_ist, False, False, 4)

        knoepfe = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        k1 = Gtk.Button(label=t('Zeigen, was geändert würde',
                                'Preview what would change'))
        k1.set_can_focus(False)
        k1.connect('clicked', lambda *_: self._uebernehmen(nur_zeigen=True))
        knoepfe.pack_start(k1, True, True, 0)

        k2 = Gtk.Button(label=t('Übernehmen …', 'Apply …'))
        k2.set_can_focus(False)
        k2.connect('clicked', lambda *_: self._uebernehmen(nur_zeigen=False))
        knoepfe.pack_start(k2, True, True, 0)
        box.pack_start(knoepfe, False, False, 4)

        # --- Fremdes Werkzeug: Knöpfe SPERREN, nicht nur warnen ------------
        # Bauregel: „Was nicht geht, wird gesperrt — nicht mit Kleingedrucktem
        # erklärt." Läuft hier systemd-zram-generator, würde jede Änderung
        # eine zweite, konkurrierende Einrichtung anlegen. Die Ampel auf
        # Seite 1 erklärt den Grund ausführlich; hier steht die Kurzfassung
        # direkt bei den grauen Knöpfen, damit niemand rätselt.
        gen = self.daten.get('gen') or {}
        if gen.get('aktiv'):
            for knopf in (k1, k2):
                knopf.set_sensitive(False)
            self._zeile(box, t(
                '<b>Ändern ist hier gesperrt.</b> Auf diesem Rechner regelt '
                '<b>systemd-zram-generator</b> das zram, nicht das Werkzeug, '
                'das dieses Programm bedient. Eine Änderung von hier aus '
                'würde eine zweite, konkurrierende Einrichtung anlegen. '
                'Die Übersicht auf der ersten Seite erklärt es genauer.',
                '<b>Changing is disabled here.</b> On this machine '
                '<b>systemd-zram-generator</b> manages zram, not the tool this '
                'program operates. Changing from here would create a second, '
                'competing setup. The overview page explains it in detail.'))

        sich = sicherungen_finden()
        if sich:
            zurueck = Gtk.Button(
                label=t(f'Rückgängig ({len(sich)} Sicherung(en) vorhanden)',
                        f'Undo ({len(sich)} backup(s) available)'))
            zurueck.set_can_focus(False)
            zurueck.connect('clicked', lambda *_: self._rueckgaengig())
            box.pack_start(zurueck, False, False, 2)

    # -- Ändern -------------------------------------------------------------

    def _regler_zuruecksetzen(self):
        """Alle Regler auf das stellen, was gerade auf dem Rechner laeuft.

        Gegengewicht dazu, dass die Regler auf der EMPFEHLUNG starten: Wer
        nichts aendern will, kommt mit einem Klick zurueck zum Ist-Zustand.
        """
        for regler in (self.regler_turbo, self.regler_freude,
                       self.regler_reserve):
            wert = getattr(regler, 'ist_wert', None)
            if wert is not None:
                regler.set_value(wert)

    def _dialog(self, art, kopf, text):
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=art, buttons=Gtk.ButtonsType.OK,
                              text=kopf)
        d.format_secondary_text(text)
        d.run()
        d.destroy()

    def _uebernehmen(self, nur_zeigen):
        # Zweite Sicherung: Auch wenn der Knopf je wieder klickbar würde (etwa
        # weil jemand die Sperre oben umbaut), wird hier nichts geändert,
        # solange ein anderes Werkzeug zuständig ist.
        gen = self.daten.get('gen') or {}
        if gen.get('aktiv'):
            self._dialog(
                Gtk.MessageType.WARNING,
                t('Hier ist ein anderes Werkzeug zuständig',
                  'Another tool is in charge here'),
                t(f'Auf diesem Rechner stellt systemd-zram-generator das zram '
                  f'ein ({gen.get("pfad")}). Dieses Programm bedient '
                  f'zram-tools. Würde es hier etwas ändern, entstünde eine '
                  f'zweite, konkurrierende Einrichtung — zwei Werkzeuge für '
                  f'dieselbe Sache vertragen sich nicht.\n\nEs wurde nichts '
                  f'verändert.',
                  f'On this machine systemd-zram-generator configures zram '
                  f'({gen.get("pfad")}). This program operates zram-tools. '
                  f'Changing anything here would create a second, competing '
                  f'setup — two tools for the same job do not get along.'
                  f'\n\nNothing was changed.'))
            return
        ziel_p = int(self.regler_turbo.get_value())
        ziel_s = int(self.regler_freude.get_value())
        ziel_sw = int(self.regler_reserve.get_value())

        # Sicherheitspruefung ZUERST — lieber gar nicht anfangen als mittendrin
        # steckenbleiben (zu wenig Platz, Daten in Benutzung, RAID).
        grund = swap_pruefen(ziel_sw, self.daten['swap'], self.daten['platte'])
        if grund:
            self._dialog(Gtk.MessageType.WARNING,
                         t('So geht das nicht', 'That will not work'), grund)
            return

        schritte, _datum = aenderungen_sammeln(
            self.daten['sys'], self.daten['swp'], self.daten['einst'],
            ziel_p, ziel_s, ziel_sw, self.daten['swap'], self.daten['platte'],
            self.daten['zram'])

        if not schritte:
            self._dialog(Gtk.MessageType.INFO,
                         t('Nichts zu tun', 'Nothing to do'),
                         t('Die Regler stehen bereits auf den Werten, die dein '
                           'System gerade benutzt. Es gibt nichts zu ändern.',
                           'The sliders already match what your system is '
                           'using. There is nothing to change.'))
            return

        was = '\n'.join(f'•  {txt}' for txt, _z, _s in schritte)
        gesichert = [s for _t, _z, s in schritte if s]
        sicherungstext = ((t('\n\nVorher gesichert wird:\n',
                             '\n\nBacked up beforehand:\n') +
                           '\n'.join(f'•  {s}' for s in gesichert))
                          if gesichert else '')
        dienst = dienst_befehl(self.daten['sys'])
        installiert_mit = braucht_installation(schritte)
        netzhinweis = (t('\n\n⚠️ Dafür wird ein Paket aus dem Internet '
                         'nachgeladen — du brauchst eine Verbindung. '
                         'Das kann eine Minute dauern.',
                         '\n\n⚠️ This downloads a package from the internet — '
                         'you need a connection. It may take a minute.')
                       if installiert_mit else '')

        if nur_zeigen:
            self._dialog(
                Gtk.MessageType.INFO,
                t('Das würde geändert (nichts passiert)',
                  'This would change (nothing happened)'),
                f'{was}{sicherungstext}{netzhinweis}\n\n' +
                t(f'Danach wird der zram-Dienst neu gestartet:\n•  {dienst}\n\n'
                  'Es wurde NICHTS verändert — das war nur die Vorschau.',
                  f'Afterwards the zram service is restarted:\n•  {dienst}\n\n'
                  'NOTHING was changed — this was only the preview.'))
            return

        frage = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=t('Jetzt wirklich ändern?', 'Really apply now?'))
        frage.format_secondary_text(
            f'{was}{sicherungstext}{netzhinweis}\n\n' +
            t(f'Danach: {dienst}\n\nDu wirst gleich nach deinem Passwort '
              'gefragt.',
              f'Then: {dienst}\n\nYou will be asked for your password next.'))
        antwort = frage.run()
        frage.destroy()
        if antwort != Gtk.ResponseType.OK:
            return

        skript = skript_bauen(schritte, self.daten['sys'])
        befehl = root_praefix() + ['/bin/bash', '-c', skript]
        try:
            # Beim Nachinstallieren mehr Zeit: apt muss die Paketliste holen
            # und herunterladen. 120 s reichen dafuer bei langsamer Leitung
            # NICHT — und ein Abbruch mitten in apt ist das Letzte, was man
            # auf einem fremden Rechner auslösen will.
            e = subprocess.run(befehl, capture_output=True, text=True,
                               timeout=600 if installiert_mit else 120)
        except Exception as fehler:
            self._dialog(Gtk.MessageType.ERROR,
                         t('Fehlgeschlagen', 'Failed'), str(fehler))
            return

        if 'RIKUSZRAM-FERTIG' not in e.stdout:
            self._dialog(
                Gtk.MessageType.ERROR,
                t('Nicht durchgelaufen', 'Did not complete'),
                t('Es wurde abgebrochen (vielleicht kein Passwort eingegeben).',
                  'It was cancelled (perhaps no password was entered).') +
                f'\n\n{(e.stderr or "").strip()[:400]}\n\n' +
                t('Die Sicherungen liegen unangetastet auf der Platte.',
                  'The backups remain untouched on disk.'))
            self.aufbauen()
            return

        # NACHMESSEN statt behaupten (Gesetz 5)
        neu_swp = swappiness_messen()
        neu_einst = einstellung_messen()
        neu_zram = zram_messen()
        neu_swap = swap_messen()
        ist_p = neu_einst['werte'].get('PERCENT')
        neu_sw_gb = gb_gerundet(sum(x['groesse'] for x in neu_swap
                                     if not x['ist_zram']))
        pruef = []
        pruef.append((t('zram-Größe in der Datei', 'zram size in the file'),
                      f'{ist_p} %',
                      str(ist_p) == str(ziel_p)))
        pruef.append((t('swappiness in Betrieb', 'swappiness in effect'),
                      str(neu_swp['laufend']),
                      neu_swp['laufend'] == ziel_s))
        pruef.append((t('zram läuft', 'zram running'),
                      t('ja', 'yes') if neu_zram else t('NEIN', 'NO'),
                      bool(neu_zram)))
        if ziel_sw > 0 or neu_sw_gb > 0:
            pruef.append((t('Swap-Datei auf der Platte', 'swap file on disk'),
                          f'{neu_sw_gb} GiB',
                          neu_sw_gb == ziel_sw))
        # ⭐ Nach jeder Swap-Änderung prüfen, ob Timeshift noch sichern kann.
        #    Eine Auslagerungsdatei am falschen Ort legt es lautlos lahm.
        if ziel_sw > 0 and self.daten['platte']['dateisystem'] == 'btrfs':
            ok_ts, text_ts = timeshift_pruefen()
            pruef.append((t('Timeshift kann noch sichern',
                            'Timeshift can still snapshot'), text_ts, ok_ts))

        zeilen = '\n'.join(f'{"✔" if ok else "✖"}  {name}: {wert}'
                           for name, wert, ok in pruef)
        alles_gut = all(ok for _n, _w, ok in pruef)
        self._dialog(
            Gtk.MessageType.INFO if alles_gut else Gtk.MessageType.WARNING,
            t('Übernommen — und nachgemessen', 'Applied — and verified')
            if alles_gut else
            t('Teilweise übernommen', 'Partially applied'),
            f'{zeilen}\n\n' + (
                t('Alles hat gegriffen.', 'Everything took effect.')
                if alles_gut else
                t('Nicht alles hat gegriffen. Mit „Rückgängig" kommst du '
                  'zurück.',
                  'Not everything took effect. Use "Undo" to go back.')))
        self.aufbauen()

    def _rueckgaengig(self):
        sich = sicherungen_finden()
        if not sich:
            return
        # je Zieldatei die NEUESTE Sicherung
        neuste = {}
        for pfad in sorted(sich):
            ziel = re.sub(r'\.bak-%s-.*$' % STEMPEL, '', pfad)
            neuste[ziel] = pfad
        liste = '\n'.join(f'•  {z}\n     ← {q}' for z, q in neuste.items())

        frage = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=t('Änderungen zurücknehmen?', 'Undo changes?'))
        frage.format_secondary_text(
            t('Diese Dateien werden aus der Sicherung wiederhergestellt:',
              'These files will be restored from backup:') +
            f'\n\n{liste}\n\n' +
            t('Danach wird der zram-Dienst neu gestartet.',
              'Afterwards the zram service is restarted.'))
        antwort = frage.run()
        frage.destroy()
        if antwort != Gtk.ResponseType.OK:
            return

        zeilen = ['#!/bin/bash', 'set -e',
                  'export PATH=/sbin:/usr/sbin:/bin:/usr/bin']
        for ziel, quelle in neuste.items():
            zeilen.append(f'cp -a "{quelle}" "{ziel}"')
        zeilen.append('sysctl --system >/dev/null 2>&1')
        zeilen.append(dienst_befehl(self.daten['sys']) + ' || true')
        zeilen.append('echo RIKUSZRAM-FERTIG')

        befehl = root_praefix() + ['/bin/bash', '-c', '\n'.join(zeilen)]
        e = subprocess.run(befehl, capture_output=True, text=True, timeout=120)
        if 'RIKUSZRAM-FERTIG' in e.stdout:
            self._dialog(Gtk.MessageType.INFO,
                         t('Zurückgenommen', 'Undone'),
                         t('Der Zustand von vor der Änderung ist '
                           'wiederhergestellt.',
                           'The state from before the change has been '
                           'restored.'))
        else:
            self._dialog(Gtk.MessageType.ERROR,
                         t('Nicht zurückgenommen', 'Undo failed'),
                         (e.stderr or '').strip()[:400])
        self.aufbauen()


def main():
    fenster = RikusZram()
    fenster.connect('destroy', Gtk.main_quit)
    fenster.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
