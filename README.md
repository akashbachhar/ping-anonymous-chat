# Ping

**Anonymous, peer-to-peer chat over Tor.** No servers, no accounts, no phone
numbers. Two people each run Ping, exchange their `.onion` addresses, and talk
directly through the Tor network — with an optional file transfer.

- 🧅 **Onion-routed** — every connection is a Tor hidden service; there is no
  central server and no metadata middleman.
- 🔑 **Fixed identity** — your address is derived from a local 32-byte seed, so
  it stays the same across restarts (and is generated fresh on first run).
- 💬 **Simple chat** — colour-coded messages with timestamps.
- 📎 **File transfer** — send files up to 5 MB, saved wherever the recipient
  chooses.
- 🖥️ **Bundled Tor** — Ping launches and manages its own `tor.exe`; nothing to
  configure.

---

## How it works

On startup Ping launches Tor, publishes an **ephemeral onion service** (its
address derived deterministically from `tor_data/onion_seed`), and listens for
an incoming peer. You can either share your address for someone to connect to,
or paste a peer's address to connect to them. Whoever connects first wins; the
conversation is a single direct TCP stream tunnelled through Tor, framed with a
small length-prefixed protocol so text and files never get mixed up.

Your address is a pure function of your seed, so it is shown **instantly** at
launch — you don't have to wait for Tor to finish bootstrapping to copy it.

---

## Requirements

- **Windows** (Ping runs a bundled `tor.exe`)
- **Python 3.10+**
- Python packages (installed below): `PyQt6`, `PySocks`, `stem`

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/ping.git
cd ping
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python main.py
```

The bundled `tor_bin/tor.exe` is included in the repo, so there's nothing else
to set up. On first launch Ping generates your onion identity
(`tor_data/onion_seed`) and bootstraps Tor. The `tor_data/` folder is created at
runtime and is git-ignored (it holds your private identity).

---

## Usage

1. Launch Ping on both machines (`python main.py`).
2. Wait for **"Ready"** — this means Tor has published your onion service and
   you're reachable. (Your address appears immediately, but a peer can only
   reach you once you're Ready.)
3. **To be contacted:** copy your onion address and share it with your peer.
4. **To start a chat:** paste the peer's `.onion` address into *Connect to a
   peer* and hit **Connect**.
5. Chat away. Use the **📎** button to attach a file (max 5 MB); the recipient
   chooses whether to save it and where. Press **Leave** to end the chat and
   return to the start screen.

> Ping is **1-to-1** — one live conversation at a time.

---

## Project structure

```
main.py              Entry point — python main.py
requirements.txt     Python dependencies
pingapp/             Application package
  config.py            Paths, ports, constants
  protocol.py          Length-prefixed text/file framing
  onion_address.py     Local v3 onion address derivation
  keystore.py          Seed-based onion identity
  tor_manager.py       Tor process + onion service lifecycle
  connection.py        Listener, outbound dialing, send/receive
  signals.py           Qt cross-thread signals
  util.py              File-transfer helpers
  ui/                  PyQt6 screens (setup, chat, styles, window)
tor_bin/tor.exe      Tor executable (bundled)
tor_data/            Tor runtime data + your onion identity (git-ignored)
```

---

## Security notes

- **`tor_data/onion_seed` is your identity.** Anyone who has it can impersonate
  your onion address. It is git-ignored — never commit or share it.
- **Your onion address is semi-private.** Anyone who has it can reach your chat
  while Ping is running. Share it only with people you want to talk to.
- Incoming message text is escaped before display, and incoming filenames are
  stripped to a bare name to prevent path-traversal on save.
- Delete `tor_data/onion_seed` to abandon your current address; a new one is
  generated on the next launch.

---

## License

No license is specified yet. Add one (e.g. MIT) before publishing if you want to
allow others to reuse the code.
