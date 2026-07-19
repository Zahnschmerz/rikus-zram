#!/bin/bash
# ---------------------------------------------------------------------------
# Rikus Zram — Paket bauen
#
# Aufruf:  ./bauen.sh          (im Wurzelverzeichnis des Projekts)
# Ergebnis: rikus-zram_<version>_all.deb + .sha256 im selben Ordner
#
# Die Versionsnummer wird AUS paket/DEBIAN/control gelesen — sie steht also
# nur an EINER Stelle. Die Anleitungen nennen bewusst gar keine Version mehr.
#
# ⚠️ ZWEI DINGE, DIE HIER NICHT VERHANDELBAR SIND:
#
#   -Zxz              Ohne diese Vorgabe packt neueres dpkg mit »zstd«.
#                     Aeltere Systeme auf Debian-11-Basis (MX 21, antiX 21)
#                     koennen zstd-Pakete NICHT oeffnen — genau die Systeme,
#                     mit denen dieses Programm wirbt. Der Fehler faellt auf
#                     dem eigenen Rechner nie auf.
#
#   --root-owner-group  Wird als normaler Benutzer gebaut, gehoerten sonst
#                     alle Dateien im Paket diesem Benutzer. Auf einem fremden
#                     Rechner gehoerte das Programm dann irgendeinem dortigen
#                     Benutzer — bei einem Programm mit Systemrechten ist das
#                     eine Sicherheitsluecke.
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

VERSION=$(grep '^Version:' paket/DEBIAN/control | awk '{print $2}')
PAKET="rikus-zram_${VERSION}_all.deb"
BAUM=$(mktemp -d)
trap 'rm -rf "$BAUM"' EXIT

echo "Baue Rikus Zram $VERSION"

# --- Baum zusammenstellen: IMMER frisch aus dem Projekt --------------------
# So koennen Paket und Projekt nicht auseinanderlaufen.
mkdir -p "$BAUM/opt/rikus-zram" "$BAUM/usr/share/doc/rikus-zram"
cp -r paket/DEBIAN "$BAUM/DEBIAN"
cp -r paket/usr "$BAUM/"
cp rikus-zram.py ANLEITUNG.md GUIDE.md README.md README.de.md \
   CHANGELOG.md LICENSE "$BAUM/opt/rikus-zram/"
cp -r daten "$BAUM/opt/rikus-zram/"

# --- Pflichtteile, die jedes Debian-Paket haben sollte ---------------------
cat > "$BAUM/usr/share/doc/rikus-zram/copyright" <<'ENDE'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Rikus Zram
Source: https://github.com/Zahnschmerz/rikus-zram

Files: *
Copyright: 2026 Gilbert Rikus <gilbert@rikus.info>
License: GPL-3.0+
 This program is free software: you can redistribute it and/or modify it
 under the terms of the GNU General Public License as published by the Free
 Software Foundation, either version 3 of the License, or (at your option)
 any later version.
 .
 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 more details.
 .
 On Debian systems the full text of the GNU General Public License version 3
 can be found in /usr/share/common-licenses/GPL-3, and with this program in
 /opt/rikus-zram/LICENSE.
ENDE

# -n = keinen Zeitstempel mitspeichern, damit gleiche Eingabe gleiches Paket ergibt
gzip -9n -c CHANGELOG.md > "$BAUM/usr/share/doc/rikus-zram/changelog.gz"

# --- Groesse eintragen (sonst meldet apt dem Nutzer "0 B") -----------------
GROESSE=$(du -sk --exclude=DEBIAN "$BAUM" | cut -f1)
sed -i "/^Installed-Size:/d" "$BAUM/DEBIAN/control"
sed -i "/^Architecture:/a Installed-Size: $GROESSE" "$BAUM/DEBIAN/control"

# --- Rechte glattziehen ----------------------------------------------------
# Als normaler Benutzer entstehen sonst 0664/0775 statt 0644/0755.
find "$BAUM" -type d -exec chmod 755 {} +
find "$BAUM" -type f -exec chmod 644 {} +
chmod 755 "$BAUM/opt/rikus-zram/rikus-zram.py" \
          "$BAUM/DEBIAN/postinst" "$BAUM/DEBIAN/postrm"

# --- Pruefsummen der Dateien ins Paket (fuer debsums/dpkg -V) --------------
( cd "$BAUM" && find . -path ./DEBIAN -prune -o -type f -print0 \
  | xargs -0 md5sum | sed 's| \./| |' > DEBIAN/md5sums )
chmod 644 "$BAUM/DEBIAN/md5sums"

# --- Bauen -----------------------------------------------------------------
dpkg-deb -Zxz --root-owner-group --build "$BAUM" "$PAKET" >/dev/null

# --- Pruefsumme: NUR der blosse Dateiname, kein Pfad -----------------------
# Sonst schlaegt "sha256sum -c" bei jedem Fremden fehl, weil es den Pfad
# nicht gibt — und der eigene Ordnername waere mitveroeffentlicht.
sha256sum "$PAKET" > "${PAKET}.sha256"

# --- Gegenprobe: lieber hier scheitern als beim Nutzer ---------------------
echo
echo "Gegenprobe:"
ar t "$PAKET" | grep -q 'data.tar.xz' \
  && echo "  ✅ mit xz gepackt (laeuft auch auf aelteren MX/antiX)" \
  || { echo "  ❌ NICHT xz — Abbruch"; exit 1; }
dpkg-deb -c "$PAKET" | grep -qv 'root/root' \
  && { echo "  ❌ Dateien gehoeren nicht root — Abbruch"; exit 1; } \
  || echo "  ✅ alle Dateien gehoeren root"
echo "  ✅ $PAKET ($(stat -c%s "$PAKET") Bytes)"
echo "  ✅ $(cat "${PAKET}.sha256")"
