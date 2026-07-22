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

> ⚠️ **Important: zram does NOT make your RAM bigger.**
> It sits **inside** it. The vacuum bag stands on the same desk — it takes up space itself, but compresses whatever goes in.
>
> **An example with 16 GB of RAM:** 16 GB of data fit into zram. Compressed, they occupy only about 4.5 GB of it — so **roughly 11 GB stay free on top**. The machine still reports 16 GB of RAM, but gets much further with it.
>
> A **swap file on disk**, by contrast, is genuinely *additional* space — but around 160 times slower.


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

You do **not** need a terminal for this.

**Step 1 — Download.**
Open the download page and click the file starting with **`rikus-zram_`** and ending in **`.deb`** (e.g. `rikus-zram_1.10_all.deb` — the number is the release):

👉 **https://github.com/Zahnschmerz/rikus-zram/releases/latest**

It lands in your **Downloads** folder.

**Step 2 — Double-click.**
Open your **Downloads** folder and **double-click** the file you just downloaded. Your system's package installer opens, you click **"Install Package"** and enter your password.

**Step 3 — Start it.**
**Rikus Zram** is now in your menu under *System*.

### Prefer the terminal?

This single command is enough — it works from **any** folder:

```
sudo apt install ~/Downloads/rikus-zram*.deb
```

The `*` stands for the changing part of the file name. The command therefore matches **any** of the offered files — whichever release you downloaded — and stays correct for future releases.

⚠️ Use `apt install`, **not** `dpkg -i`: only `apt` pulls in missing dependencies by itself.

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

### ⭐ If your machine has no zram at all yet

Then the traffic light shows **red** or **amber**, and below it you will read that zram is not set up on your machine. **That is not a problem — it is exactly what this program is for.**

The second page then offers to **set it up completely**:
1. the package `zram-tools` gets installed (you need internet briefly for that),
2. the settings file is created,
3. the service is switched on — **for every future boot as well**, not just for now.

You see exactly what will happen beforehand, and you have to confirm it.

**Why this is not a given:** The package `zram-tools` ships only a startup file for **systemd**. On systems using a different init — **MX Linux, antiX, Devuan** — nothing at all would start after installing it, without any error message. Rikus Zram writes the matching start script there as well. That is why it works on those systems too.

---

### ⭐ Why does it say „GiB" and not „GB"?

Because they are **not the same thing** — and the gap grows with size:

| | counts in | 16 billion bytes are |
|---|---|---|
| **GB** (gigabyte) | 1000 | 16.56 GB |
| **GiB** (gibibyte) | 1024 | **15.43 GiB** |

**Linux counts in 1024.** That is why `fastfetch`, `htop`, `free` and this program all show **GiB** — and why a stick labelled "16 GB" shows up as 15.4 in your system. Nothing is missing, it is just counted differently.

Rikus Zram deliberately says **GiB** so its numbers match the rest of your system.

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

**What is hibernation, and do I need it?**

There are three ways to "turn off" a computer:

| | What happens | Back in | Power |
|---|---|---|---|
| **Shut down** | everything is closed | 30–60 s (reopen everything) | none |
| **Standby** (suspend) | everything stays open in RAM | 1–2 seconds | a little — **when the battery dies, it is all gone** |
| **Hibernation** | RAM is written to disk | 15–30 seconds | **none at all** — everything is kept |

Closing your laptop lid normally puts it into **standby**. **Hibernation** is something else: it saves a complete image of your RAM to disk and switches the machine off **entirely**. On the next start everything is open again as before — same programs, same position in the text.

**You need two things for it:**

1. **A swap file at least the size of your RAM.** With 16 GB of RAM, at least 16 GB. If it is smaller, Linux refuses hibernation outright. Slider 3 sets the size — the program tells you from which value it would be enough.
2. **An entry in the boot configuration** (`resume=`), so the machine knows where the image is on startup. **Rikus Zram does not do this step** — it touches the boot process, which is deliberately outside what this program changes.

**zram cannot help here.** It lives in RAM itself and is gone when the power goes off — you cannot store the image inside the room you are imaging.

**Do you need it?** For everyday use standby is plenty and ten times faster. Hibernation pays off if you leave the machine untouched for days and still want everything open, or if you often run out of battery.

**Whether your machine can do it** is shown on the first page under "This machine". You can also check yourself:
```
cat /sys/power/state
```
If `disk` appears there, hibernation is technically possible.

**Can I remove it again?**
`sudo apt remove rikus-zram`. Your settings and any swap file you created stay in place — the program does not take away what you set up.

**What if something goes wrong?**
The backups sit next to the original files (`*.bak-rikuszram-*`). The undo button restores them. And changes to zram or swappiness never affect your data — this is memory management only.

---

## 10. The update hint

From version 1.10 on, the program checks once at startup whether a newer version
exists. If so, a small green line with a link to the download page appears below the
title. **That is all it does** — nothing is downloaded and nothing is installed.
Without internet the line simply does not appear; the window opens instantly as usual.

**Why this exists:** The program is shipped as a `.deb` via GitHub, so it is *not* an
apt source. `apt update` never learns about newer versions — without this hint you
would silently stay on an old release.

**Turn it off** — a single line in a terminal:

```
touch ~/.config/rikus-zram/kein-update-hinweis
```

The program then stops asking altogether. To turn it back on:

```
rm ~/.config/rikus-zram/kein-update-hinweis
```


**Website:** [zram.rikus.info](https://zram.rikus.info)
**Source and bug reports:** [github.com/Zahnschmerz/rikus-zram](https://github.com/Zahnschmerz/rikus-zram)

Found a bug or have an idea? Please report it — the program lives on feedback.

**Rikus Zram** — by Gilbert Rikus · GPL-3.0
Sister project: **Rikus Mintshot** ([snapshot.rikus.info](https://snapshot.rikus.info)) — a one-click bootable clone of your Linux Mint system.

## Help and feedback
