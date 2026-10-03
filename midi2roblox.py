#!/usr/bin/env python3
"""Play Roblox letter-key piano games from a USB MIDI keyboard.

Each note played on the MIDI keyboard is sent to Roblox as the matching
computer key in the standard 61-key "virtual piano" layout (C2-C7, middle C
on 't', black keys on Shift). See README.md for setup and usage.

Real key sending is Windows only. --map and --dry-run work anywhere.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

WHITE_KEYS = "1234567890qwertyuiopasdfghjklzxcvbnm"  # 36 white keys, C2..C7
WHITE_STEPS = (0, 2, 4, 5, 7, 9, 11)                  # semitone offsets of C D E F G A B
HAS_SHARP = {0, 2, 5, 7, 9}                           # C D F G A have a black key above
KEY_RANGE = 60                                        # 61 keys = lowest note + 60 semitones
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# --------------------------------------------------------------------------
# Defaults (overridable on the command line)
# --------------------------------------------------------------------------

DEFAULT_LOWEST_NOTE = 36       # MIDI note sent as '1' (C2)
DEFAULT_KEY_GAP = 0.004        # seconds between Shift / key events
ROBLOX_WINDOW_TITLE = "Roblox"
POLL_INTERVAL = 0.001          # seconds between MIDI polls

KeyMap = dict[int, tuple[str, bool]]


def build_key_map(lowest_note: int) -> KeyMap:
    """Return {midi_note: (key, needs_shift)} for the 61-key layout."""
    highest_note = lowest_note + KEY_RANGE
    key_map: KeyMap = {}
    for i, key in enumerate(WHITE_KEYS):
        step = WHITE_STEPS[i % 7]
        note = lowest_note + 12 * (i // 7) + step
        key_map[note] = (key, False)
        if step in HAS_SHARP and note + 1 <= highest_note:
            key_map[note + 1] = (key, True)
    return key_map


def note_name(note: int) -> str:
    """Scientific pitch name, e.g. 60 -> 'C4'."""
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


def fit_to_range(note: int, lowest: int, highest: int, fold: bool) -> Optional[int]:
    """Bring a note into range by whole octaves, or return None to drop it."""
    if lowest <= note <= highest:
        return note
    if not fold:
        return None
    while note < lowest:
        note += 12
    while note > highest:
        note -= 12
    return note


# --------------------------------------------------------------------------
# Key output
# --------------------------------------------------------------------------

def roblox_is_foreground() -> bool:
    """True if the front window is the Roblox client (Windows only)."""
    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    title = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, title, length + 1)
    return title.value == ROBLOX_WINDOW_TITLE


class KeySender:
    """Sends key presses to Roblox, or prints them in dry-run mode."""

    def __init__(self, dry_run: bool, roblox_only: bool,
                 sustain_key: Optional[str], key_gap: float) -> None:
        self.dry_run = dry_run
        self.roblox_only = roblox_only and not dry_run
        self.sustain_key = sustain_key
        self.key_gap = key_gap
        self._sustain_down = False
        self._focus_warned = False
        self._pdi = None
        if not dry_run:
            if sys.platform != "win32":
                sys.exit("Sending keys only works on Windows. Use --dry-run to test elsewhere.")
            import pydirectinput
            pydirectinput.PAUSE = 0  # we control timing ourselves
            self._pdi = pydirectinput

    def _can_send(self) -> bool:
        if not self.roblox_only:
            return True
        if roblox_is_foreground():
            self._focus_warned = False
            return True
        if not self._focus_warned:
            print("  (Roblox isn't the front window - skipping notes. Click into Roblox.)")
            self._focus_warned = True
        return False

    def tap(self, key: str, shifted: bool, label: str) -> None:
        if self.dry_run:
            print(f"  {label:>5} -> {'Shift+' if shifted else ''}{key}")
            return
        if not self._can_send():
            return
        pdi = self._pdi
        if shifted:
            pdi.keyDown("shift")
            time.sleep(self.key_gap)
        pdi.keyDown(key)
        time.sleep(self.key_gap)
        pdi.keyUp(key)
        if shifted:
            time.sleep(self.key_gap)
            pdi.keyUp("shift")

    def set_sustain(self, down: bool) -> None:
        if not self.sustain_key or down == self._sustain_down:
            return
        if self.dry_run:
            self._sustain_down = down
            print(f"  pedal {'down' if down else 'up'} -> {self.sustain_key} "
                  f"{'held' if down else 'released'}")
            return
        if down and not self._can_send():
            return
        self._sustain_down = down
        (self._pdi.keyDown if down else self._pdi.keyUp)(self.sustain_key)

    def release_all(self) -> None:
        """Make sure no key is left held down when we exit."""
        if self._pdi is None:
            return
        self._pdi.keyUp("shift")
        if self.sustain_key:
            self._pdi.keyUp(self.sustain_key)


# --------------------------------------------------------------------------
# MIDI handling
# --------------------------------------------------------------------------

class MidiToKeys:
    """Translates MIDI messages into key presses."""

    def __init__(self, sender: KeySender, lowest_note: int, fold: bool) -> None:
        self.sender = sender
        self.lowest = lowest_note
        self.highest = lowest_note + KEY_RANGE
        self.fold = fold
        self.key_map = build_key_map(lowest_note)

    def handle(self, msg) -> None:
        if msg.type == "note_on" and msg.velocity > 0:  # velocity 0 means note off
            note = fit_to_range(msg.note, self.lowest, self.highest, self.fold)
            if note is not None:
                key, shifted = self.key_map[note]
                self.sender.tap(key, shifted, note_name(msg.note))
        elif msg.type == "control_change" and msg.control == 64:  # sustain pedal
            self.sender.set_sustain(msg.value >= 64)


def choose_port(names: list[str], wanted: Optional[str]) -> str:
    if not names:
        sys.exit("No MIDI inputs found. Is the keyboard connected and switched on?")
    if wanted:
        matches = [n for n in names if wanted.lower() in n.lower()]
        if not matches:
            sys.exit(f"No MIDI input matching '{wanted}'. Available: {', '.join(names)}")
        return matches[0]
    if len(names) == 1:
        return names[0]
    print("MIDI inputs:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    while True:
        choice = input("Pick a number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            return names[int(choice) - 1]


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Play Roblox letter-key piano games from a USB MIDI keyboard.")
    p.add_argument("--list", action="store_true", help="list MIDI inputs and exit")
    p.add_argument("--port", help="use the MIDI input whose name contains this text")
    p.add_argument("--map", action="store_true", help="print the note-to-key table and exit")
    p.add_argument("--dry-run", action="store_true", help="print keys instead of sending them")
    p.add_argument("--any-window", action="store_true",
                   help="send keys even when Roblox isn't the front window")
    p.add_argument("--ignore-out-of-range", action="store_true",
                   help="drop notes outside the 61-key range instead of folding them in")
    p.add_argument("--sustain-key", metavar="KEY",
                   help="key to hold while the sustain pedal is down, e.g. space")
    p.add_argument("--lowest-note", type=int, default=DEFAULT_LOWEST_NOTE, metavar="N",
                   help=f"MIDI note sent as '1' (default {DEFAULT_LOWEST_NOTE} = C2; "
                        "24 shifts down an octave, 48 up)")
    p.add_argument("--key-gap", type=float, default=DEFAULT_KEY_GAP, metavar="SECONDS",
                   help=f"pause between Shift and key events (default {DEFAULT_KEY_GAP})")
    return p.parse_args(argv)


def print_map(lowest_note: int) -> None:
    for note, (key, shifted) in sorted(build_key_map(lowest_note).items()):
        print(f"{note_name(note):>4} ({note:3d})  {'Shift+' if shifted else ''}{key}")


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)

    if args.map:
        print_map(args.lowest_note)
        return

    import mido

    if args.list:
        for name in mido.get_input_names():
            print(name)
        return

    port_name = choose_port(mido.get_input_names(), args.port)
    sender = KeySender(dry_run=args.dry_run, roblox_only=not args.any_window,
                       sustain_key=args.sustain_key, key_gap=args.key_gap)
    translator = MidiToKeys(sender, args.lowest_note, fold=not args.ignore_out_of_range)

    print(f"Listening to: {port_name}")
    print("Click into the Roblox window and play. Press Ctrl+C here to stop.")
    try:
        with mido.open_input(port_name) as inport:
            while True:
                # Poll rather than block, so Ctrl+C works promptly on Windows.
                for msg in inport.iter_pending():
                    translator.handle(msg)
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sender.release_all()


if __name__ == "__main__":
    main()
