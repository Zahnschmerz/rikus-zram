# Rikus Zram

**Set up zram, swappiness and swap files with sliders instead of a terminal.**

![Rikus Zram](daten/icon.png)

Linux can use your memory far better than most systems do out of the box. **zram** compresses rarely used data **inside RAM** instead of paging it out to a slow disk — typically 3–4× smaller. Your machine stays responsive even with a lot open.

The catch: configuring this means typing commands and editing system files. Rikus Zram turns it into a window.

---

## What it does

- **Show** — how much RAM is in use, whether zram is running, how well it is compressing right now, which swap areas exist. With a traffic light and a plain-language verdict.
- **Recommend** — works out what fits **this** machine from RAM size, SSD or spinning disk, filesystem and hibernation setup. With the reasoning in plain words.
- **Adjust** — three sliders: zram size, swappiness, swap file. You move them yourself; the recommendation sits on the scale as a marker.
- **Apply** — with a preview, a backup of every file touched, a password prompt and a **verification step** that checks whether it actually took effect. Plus an undo button.

**Bilingual:** German or English, chosen automatically from your system language.

---

## Install

```
sudo apt install ./rikus-zram_1.0_all.deb
```

Then find **Rikus Zram** in your menu under *System*.

**Runs on:** Debian, Ubuntu, Linux Mint, LMDE, MX Linux, antiX, Zorin, Pop!\_OS and relatives.
**With systemd and with SysVinit** — it detects which one your system uses.

---

## Safety

- Viewing and recommending needs **no password and never writes**
- Changes happen **only after you explicitly confirm**, with a preview beforehand
- **Every file is backed up** before it is touched
- **Swap partitions are never modified** — only files
- On **btrfs** the swap file gets its own subvolume so **Timeshift can still take snapshots**

---

## Why another one?

There are older attempts (VMM from 2013, SwapChanger, Swappolube, SwapManager, z-manager), but none of them is finished, current and complete. None can:

- **set up** zram on a machine that does not have it yet
- handle zram **and** swappiness **and** swap files in one place
- run on **SysVinit** systems (MX, antiX, Devuan)
- create a swap file on **btrfs** without breaking Timeshift

---

## Full guide

→ **[GUIDE.md](GUIDE.md)** — step by step for beginners, every technical term explained

---

**Website:** [zram.rikus.info](https://zram.rikus.info)
**Author:** Gilbert Rikus · **Licence:** GPL-3.0
**Sister project:** [Rikus Mintshot](https://snapshot.rikus.info) — one-click bootable clone of your running Linux Mint

*Deutsche Fassung: [README.de.md](README.de.md)*
