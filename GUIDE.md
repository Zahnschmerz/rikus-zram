# Rikus Zram — Guide (English)

**Use your memory better — without typing a single command.**
By Gilbert Rikus · Free software (GPL-3.0)

---

## 1. What is this about?

Think of your RAM as a **desk**. Everything the computer is currently working on lies on it. When the desk fills up, something has to give way.

Linux has two options for that:

**Swap — the filing cabinet on the disk.**
Rarely used items move from the desk into a cabinet. The desk frees up, but fetching things back takes time — the disk is far slower than RAM.

**zram — the vacuum bag.**
Instead of moving things away, the system **compresses them on the desk itself**. Like a vacuum bag for winter clothes: much more fits, and nothing has to leave the desk. That makes it **many times faster** than the cabinet.

Typically data becomes **3–4× smaller**. 4 GB of data ends up occupying about 1 GB.

**And what does this program do?**
On Linux, zram and swap can only be configured by typing commands and editing system files. Rikus Zram turns that into a window with sliders — explaining what each value means, and recommending what fits your particular machine.

---

## 2. What you need

- **Debian, Ubuntu, Linux Mint, LMDE, MX Linux, antiX, Zorin, Pop!\_OS** or a relative
- Your normal user password (only for changes, not for looking)
- Nothing else — the package brings what it needs

The program works with **systemd** and with **SysVinit** (so also on MX Linux and antiX). It detects which one your system uses.

---

## 3. Installing

Download `rikus-zram_1.0_all.deb` and double-click it — your system asks for the password and installs it.

Or in a terminal:

```
sudo apt install ./rikus-zram_1.0_all.deb
```

Afterwards you will find **Rikus Zram** in the menu under *System*.

---

## 4. First page: what is there?

After starting you see the current state of your machine. **Nothing is changed here — it only looks.**

**In short** — a traffic light with a plain verdict:
- 🟢 **Green:** all good
- 🟡 **Yellow:** running, but there is something to look at
- 🔴 **Red:** neither zram nor swap — programs get killed when memory runs out

Below it are the points the program noticed, in plain words rather than error codes.

**RAM** — how much is in use and how much is free.

**zram** — whether it runs, how big it is, which compression algorithm (usually `zstd`) and **how well it is compressing right now**. If it says "3 GB of data occupy only 0.8 GB", zram is currently working at almost 4×.

**Swap** — whether a swap file or partition exists, how big, how full, and at which **priority**.

**Settings** — the **swappiness** value and what the configuration file contains.

**This system** — which distribution, which init system, SSD or spinning disk, which filesystem.

A button at the bottom leads to the second page.

---

## 5. Second page: what would be better?

Here you find **three sliders**. They sit on **what is currently running** on your machine. The scale below marks what would be **recommended** for your system — you move the slider there yourself if you want.

Under each slider a line explains what the chosen value means; it updates as you move. And in colour it tells you whether you are on your current setting, on the recommendation, or on something else.

### Slider 1 — zram size

As a percentage of RAM. **100 % is the proven value:** zram as large as your RAM. That sounds like a lot, but it is not — the space is only claimed when needed, and the data inside is compressed.

With a lot of RAM (32 GB and up) half is enough.

### Slider 2 — swappiness

A value between 0 and 200. It says **how readily** the system moves rarely used data aside.

| Value | Meaning |
|---|---|
| 0–20 | swap only as a last resort |
| 60 | the default without zram |
| **150** | **aggressive — a good match when zram runs** |
| 200 | very aggressive |

**Why can it be so high with zram?** Because swapping then goes into fast RAM instead of the slow disk. It costs almost nothing.

### Slider 3 — swap file

The reserve on disk, in gigabytes. It stays empty in daily use and only kicks in when RAM **and** zram are full — a safety net.

**When do you need it?**
- **Little RAM (up to 4 GB):** yes, definitely
- **8 to 16 GB:** a small 2 GB reserve does no harm
- **32 GB and up with zram running:** not really
- **If you want hibernation:** it must be **at least the size of your RAM** — hibernation writes the entire memory to disk, and **zram cannot do that**

---

## 6. Applying a change — what happens

Once the sliders are where you want them:

**Step 1 — "Preview what would change"**
A window lists in plain words what would happen, which files get backed up first, and which service is restarted. **Nothing happens at this point** — it is only the preview.

**Step 2 — "Apply …"**
The same list, but headed "Really apply now?". Only after your click comes the **password prompt**.

**Step 3 — the verification**
Afterwards the program **measures again itself** whether the change actually took effect, and shows you ✔ or ✖ per item. No "should be fine now" — it checks.

### What the program safeguards for you

- **Every file is backed up first** (`<file>.bak-rikuszram-<date>`)
- **It checks for free space beforehand** — and stops with a reason if there is not enough
- **It warns if data is currently swapped out** and would have to move back into RAM
- **It never touches swap partitions**, only files — changing partitions could destroy data
- **It does not remove folders it did not create**

---

## 7. Undoing a change

If backups exist, an **"Undo"** button appears on the second page. One click restores the state from before the change.

By hand it works too:

```
sudo cp /etc/default/zramswap.bak-rikuszram-<date> /etc/default/zramswap
sudo service zramswap restart      # with systemd: systemctl restart zramswap
```

---

## 8. Special case btrfs — please read if you use btrfs

If your system sits on **btrfs** (the program detects this and tells you), there is a catch:

**A subvolume with an active swap file can no longer be snapshotted.** If the file simply sat in `/`, **Timeshift could no longer create restore points** — silently, without an error. You would only notice when you actually need a backup.

**That is why Rikus Zram puts the file into its own separate subvolume** (`/swap`) and creates it with the btrfs-native command that sets everything correctly. After creating it, the program verifies that Timeshift can still work and shows you the result.

You do not have to do anything for this — it happens by itself. The note is here so you know **why** that extra area exists.

---

## 9. Frequently asked questions

**Is this dangerous?**
Viewing and recommending runs entirely without a password and without writing. Only what you explicitly confirm gets changed — with a preview, a backup and an undo button.

**Do I even need zram?**
If your machine gets sluggish with many programs open: yes. zram gives you noticeably more room without anything going to the slow disk. It is widely used on modern systems.

**Why does another tool show me different numbers?**
A 2 GB swap file reports itself to the system as 1.999996 GB — the first few kilobytes are an internal header and not usable. Some tools truncate that to "1 GB". Rikus Zram rounds to **2 GB**, because that is the size you set.

**What about hibernation?**
It writes your entire RAM to disk. For that you need a swap **file or partition at least the size of your RAM**. zram cannot do it — it lives in RAM itself, which is empty after power off.

**Can I remove it again?**
`sudo apt remove rikus-zram`. Your settings and any swap file you created stay in place — the program does not take away what you set up.

**What if something goes wrong?**
The backups sit next to the original files (`*.bak-rikuszram-*`). The undo button restores them. And changes to zram or swappiness never affect your data — this is memory management only.

---

## Help and feedback

**Website:** [zram.rikus.info](https://zram.rikus.info)
**Source and bug reports:** [github.com/Zahnschmerz/rikus-zram](https://github.com/Zahnschmerz/rikus-zram)

Found a bug or have an idea? Please report it — the program lives on feedback.

**Rikus Zram** — by Gilbert Rikus · GPL-3.0
Sister project: **Rikus Mintshot** ([mintshot.rikus.info](https://mintshot.rikus.info)) — a one-click bootable clone of your Linux Mint system.
