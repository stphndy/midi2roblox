# midi2roblox

Play Roblox piano games with a real MIDI keyboard or digital piano.

Roblox can't read MIDI. Its piano games are played with the computer
keyboard instead, with each letter or number key mapped to a note. `midi2roblox`
listens to your MIDI keyboard and presses the matching computer key every time
you play a note, so you can play in-game on a real piano.

Tested with a Yamaha P-125 and the Roblox game **Digital Piano** on Windows.

## How it works

Most Roblox pianos use the standard 61-key "virtual piano" layout:

| Keys | Notes |
| --- | --- |
| `1 2 3 4 5 6 7 8 9 0 q w e r t y u i o p a s d f g h j k l z x c v b n m` | White keys, C2 to C7 (middle C is `t`) |
| Shift + a white key | The black key just above it (e.g. Shift+`t` = C#4) |

Run `python midi2roblox.py --map` to see the full note-to-key table.

Notes outside the 61-key range (an 88-key piano has extra keys at each end)
are moved up or down by octaves into range, unless you pass `--ignore-out-of-range`.

## Requirements

- **Windows**. Sending key presses uses Windows `SendInput`. `--map` and
  `--dry-run` work on any OS.
- **Python 3.12 or earlier**. `python-rtmidi` only publishes ready-built
  Windows packages up to Python 3.12. On newer versions pip tries to compile
  it and fails unless you have a C++ compiler installed.
- A MIDI keyboard or digital piano connected by USB.

## Installation

```
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Connect the keyboard and switch it on. Close any other app using it
   (Windows lets only one program open a MIDI port at a time).
2. Run:
   ```
   python midi2roblox.py
   ```
   If more than one MIDI input is connected, pick yours from the list.
3. Open your Roblox piano game, sit at the piano, and **click into the Roblox
   window**.
4. Play. Press Ctrl+C in the terminal to stop.

Turn your keyboard's own volume down, or you'll hear both it and the game.

### Options

| Option | What it does |
| --- | --- |
| `--list` | List MIDI inputs and exit |
| `--port NAME` | Use the MIDI input whose name contains `NAME` |
| `--map` | Print the note-to-key table and exit |
| `--dry-run` | Print the keys that would be sent, without sending them |
| `--any-window` | Send keys even when Roblox isn't the front window |
| `--ignore-out-of-range` | Drop notes outside the 61-key range instead of folding them in |
| `--sustain-key KEY` | Hold `KEY` while the sustain pedal is down (e.g. `space`, if your game uses it) |
| `--lowest-note N` | MIDI note sent as `1` (default 36 = C2; use 24 or 48 to shift an octave) |
| `--key-gap SECONDS` | Pause between Shift and key events (default 0.004) |

## Safety

- Keys are only sent while the window titled **Roblox** is in front. If you
  switch to another program, notes are skipped rather than typed into it.
- Keys still go into Roblox's chat box if it's open, so make sure chat isn't
  selected.
- Shift and the sustain key are released when the program exits.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `pip install` fails building `python-rtmidi` | You're on Python 3.13 or later. Create the venv with `py -3.12`. |
| "No MIDI inputs found" | Check the USB cable and that the keyboard is on. Close other MIDI apps. |
| Nothing happens in Roblox | Click into the Roblox window. Check the game uses letter keys (not its own MIDI mode). |
| Notes are an octave out | Use `--lowest-note 24` or `--lowest-note 48`. |
| Black keys play the white note | Increase `--key-gap`, e.g. `--key-gap 0.01`. |
| All notes play at the same volume | Expected: letter-key games can't receive how hard you pressed. |

## Limitations

- Velocity (how hard you press) isn't sent: letter-key games have no way to receive it.
- Each note is a short key tap, so how long you hold a note doesn't matter to the game.
- Only games using the standard layout will play the right notes. Games with
  their own MIDI protocol, such as Piano Rooms, need their own tools.

## Notes

Simulating keyboard input in games may be against some games' rules. This
tool only plays what you play, but check the rules of the game you use it with.
