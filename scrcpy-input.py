#!/usr/bin/env python3
"""This tool copies your input to system clipboard and then synchronises it
with android's clipboard and pastes it with Alt-v command. Obviously this will
overwrite your clipboard contents. Make sure you focus on the text input on the
scrcpy window before you attempt to paste. - epilys 2021-06-21

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import tkinter.simpledialog
from tkinter import *
from tkinter import messagebox
from threading import Thread
from subprocess import Popen, PIPE
import subprocess
import datetime
import signal
import time
import textwrap
import os
from typing import Union, List, Tuple

# dependencies:
# apt install xdotool xclip

"""
usage: scrcpy-input.py [-h] [-m] [-nh] [-ns] window_name

This tool copies your input to system clipboard and then synchronises it with
android's clipboard and pastes it with Alt-v command. Obviously this will
overwrite your clipboard contents. Make sure you focus on the text input on
the scrcpy window before you attempt to paste.

positional arguments:
  window_name      window name to target

optional arguments:
  -h, --help       show this help message and exit
  -m, --manual     don't auto send on ctrl+Enter
  -nh, --no-hide   don't auto hide on send
  -ns, --no-strip  don't auto strip whitespace on send
"""

# For xte: apt install xautomation

# Xte examples: (not used by default)
# see https://manpages.debian.org/stretch/xautomation/xte.1
# use like so:
# time.sleep(0.2)
# keypress(ALT_TAB_SEQUENCE)
# time.sleep(0.5)
# keypress(NORMAL_PASTE_SEQUENCE) # or
# keypress(PASTE_SEQUENCE)

COPY_SEQUENCE = """keydown Control_L
keydown c
keyup c
keyup Control_L
"""
ALT_TAB_SEQUENCE = """keydown Alt_L
keydown Tab
keyup Tab
keyup Alt_L
"""
PASTE_SEQUENCE = """usleep 100000
keydown Alt_L
key v
usleep 100
keyup Alt_L
"""
NORMAL_PASTE_SEQUENCE = """keydown Control_L
keydown Shift_L
key v
keyup Shift_L
keyup Control_L
"""
# https://stackoverflow.com/a/5714298/15652264
def keypress(sequence: Union[str, bytes]):
    if isinstance(sequence, str):
        sequence = sequence.encode("utf-8")
    p = Popen(["xte"], stdin=PIPE)
    p.communicate(input=sequence)


def set_clipboard(data: Union[str, bytes]):
    if isinstance(data, str):
        data = data.encode("utf-8")
    p = Popen(["xclip", "-selection", "clipboard"], stdin=PIPE)
    p.communicate(input=data)


class Application(Frame):
    def __init__(
        self,
        window_name: str,
        auto_send: bool,
        auto_hide: bool,
        auto_strip: bool,
        master=None,
    ):
        super().__init__(master)
        self.window_name = StringVar()
        self.window_name.set(window_name)
        self.master = master
        self.auto_send_initial = auto_send
        self.auto_hide_initial = auto_hide
        self.auto_strip_initial = auto_strip
        self.history: List[Tuple[datetime.datetime, str]] = []
        self.create_widgets()
        master.bind("<Control-KeyRelease-q>", self.quit_ask)

    def create_widgets(self):
        Grid.rowconfigure(self.master, 0, weight=0)
        Grid.rowconfigure(self.master, 1, weight=1)
        Grid.rowconfigure(self.master, 2, weight=0)
        Grid.columnconfigure(self.master, 0, weight=0)
        Grid.columnconfigure(self.master, 1, weight=1)
        Grid.columnconfigure(self.master, 2, weight=0)
        # menu
        self.menubar = Menu(self.master)
        self.menubar.add_command(label="scrcpy-input")
        self.menubar.add_command(label="quit", command=self.quit_ask)
        self.master.config(menu=self.menubar)

        # window name
        Label(self.master, text="window name", padx=10, pady=10).grid(column=0, row=0)
        Label(self.master, textvariable=self.window_name, padx=10, pady=10).grid(
            column=1, row=0
        )
        button = Button(self.master)
        button["text"] = "change"
        button["command"] = self.set_window_name
        button.grid(column=2, row=0, sticky=W + E + N + S)

        # textarea
        Label(self.master, text="enter text", padx=10, pady=10).grid(column=0, row=1)
        self.entry = Text(
            self.master, exportselection=False, undo=True, maxundo=-1, wrap="word"
        )
        self.entry.grid(column=1, row=1, sticky=W + E + N + S)
        self.entry.bind("<Control-KeyRelease-Return>", self.auto_send)
        self.entry.bind("<Control-Key-a>", self.select_all)
        self.entry.bind(
            "<Control-Key-z>", lambda s: self.entry.event_generate("<<Undo>>")
        )
        self.entry.bind(
            "<Control-Key-y>", lambda s: self.entry.event_generate("<<Redo>>")
        )
        self.entry.bind(
            "<Control-Key-e>", lambda s: self.entry.event_generate("<<LineEnd>>")
        )
        self.entry.bind("<Control-Key-w>", self.delete_word)
        self.entry.bind("<Control-BackSpace>", self.delete_word)
        self.entry.bind(
            "<Control-Key-f>", lambda s: self.entry.event_generate("<<NextChar>>")
        )
        self.entry.bind(
            "<Control-Key-b>", lambda s: self.entry.event_generate("<<PrevChar>>")
        )
        button_frame = Frame(self.master)
        Grid.rowconfigure(button_frame, 0, weight=1)
        Grid.rowconfigure(button_frame, 1, weight=0)
        Grid.columnconfigure(button_frame, 0, weight=1)
        Grid.columnconfigure(button_frame, 1, weight=1)
        button_frame.grid(column=2, row=1, sticky=NSEW)
        button = Button(button_frame)
        button["command"] = self.send_content
        button.grid(column=0, row=0, sticky=NSEW)
        auto_send_var = IntVar()
        ## Auto send toggle
        self.entry._auto_send = auto_send_var
        self.entry._button = button
        if self.auto_send_initial:
            self.entry._auto_send.set(1)
        else:
            self.entry._auto_send.set(0)
        self.entry._toggle_btn = Checkbutton(
            button_frame,
            text="send on ctrl+enter",
            variable=self.entry._auto_send,
            command=self.update_send_button,
            width=20,
        )
        self.entry._toggle_btn.grid(
            column=0, row=1, pady=5, padx=5, sticky=W + E + N + S
        )
        self.update_send_button()
        ## Auto hide toggle
        self.entry._auto_hide = IntVar()
        if self.auto_hide_initial:
            self.entry._auto_hide.set(1)
        else:
            self.entry._auto_hide.set(0)
        self.entry._hide_btn = Checkbutton(
            button_frame, text="auto hide", variable=self.entry._auto_hide, width=20
        )
        self.entry._hide_btn.grid(column=0, row=2, pady=5, padx=5, sticky=W + E + N + S)
        ## Auto strip toggle
        self.entry._auto_strip = IntVar()
        if self.auto_strip_initial:
            self.entry._auto_strip.set(1)
        else:
            self.entry._auto_strip.set(0)
        self.entry._strip_btn = Checkbutton(
            button_frame,
            text="auto strip whitespace",
            variable=self.entry._auto_strip,
            width=20,
        )
        self.entry._strip_btn.grid(
            column=0, row=3, pady=5, padx=5, sticky=W + E + N + S
        )

        # history
        self.history_selection = StringVar()
        self.history_selection.set("select text from session history")

        Label(self.master, text="history", padx=10, pady=10).grid(column=0, row=2)
        self.history_menu = OptionMenu(self.master, self.history_selection, [])
        self.history_menu.grid(column=1, row=2, sticky=W + E + N + S)
        button = Button(self.master)
        button["text"] = "clear"
        button["command"] = self.clear_history
        button.grid(column=2, row=2, sticky=NSEW)

        # status bar
        self.status = StringVar()
        self.status.set("")
        self.status_bar = Label(
            self.master, textvariable=self.status, bd=1, relief=SUNKEN, anchor=W
        )
        self.status_bar.grid(column=0, row=3, columnspan=2, sticky=W + E + N + S)

    def update_send_button(self):
        self.entry._button["text"] = (
            "send\n(ctrl+Enter)" if self.entry._auto_send.get() == 1 else "send"
        )

    def update_option_menu(self):
        def set_value(text: Entry, value: str):
            if messagebox.askyesno(
                "Copy to clipboard?",
                f"Copy\n{textwrap.shorten(value, width=66, placeholder='...')}\nto clipboard?",
            ):
                text.delete(1.0, END)
                text.insert(END, value)

        menu = self.history_menu["menu"]
        menu.delete(0, "end")
        for (timestamp, s) in reversed(self.history):
            menu.add_command(
                label=f"{timestamp.isoformat(sep=' ', timespec='minutes')} | {textwrap.shorten(s, width=20, placeholder='...')}",
                command=lambda value=s: set_value(self.entry, value),
            )

    def quit_ask(self, force: bool = False):
        if not force and not messagebox.askyesno("Quit", "You sure?"):
            return
        self.master.quit()

    def set_window_name(self):
        window_name = tkinter.simpledialog.askstring("new window name", "")
        if window_name is not None:
            self.window_name.set(window_name)

    def clear_history(self):
        if messagebox.askyesno("Clear history", "You sure?"):
            self.history.clear()
            self.update_option_menu()
            self.status.set("Cleared.")

    def auto_send(self, event=None):
        if self.entry._auto_send.get() == 1:
            self.send_content()

    def send_content(self, event=None):
        now = datetime.datetime.now()
        contents = self.entry.get(1.0, END)
        if self.entry._auto_strip.get() == 1:
            contents = contents.strip()
        self.entry.delete(1.0, END)
        if len(contents) == 0:
            if self.entry._auto_strip.get() == 1:
                self.status.set("Empty input or only whitespace.")
            else:
                self.status.set("Empty input.")
            return
        # self.master.clipboard_clear()
        set_clipboard(contents)

        self.history.append((now, contents))

        self.update_option_menu()
        time.sleep(0.5)
        """
        clipboard_has = self.master.clipboard_get()
        if contents != clipboard_has:
            error_msg = f"Used tkinter's clipboard_append() but clipboard contents didn't match afterwards. Use another python library and solution.\n\nClipboard contents: {clipboard_has}"
            self.status.set(error_msg)
            messagebox.showerror("Could not set clipboard", error_msg)
        """

        if self.entry._auto_hide.get() == 1:
            self.master.iconify()
        p = Popen(
            [
                "xdotool",
                "search",
                "--name",
                self.window_name.get(),
                "sleep",
                "0.2",
                "key",
                "Alt_L+v",
            ]
        )

    def select_all(self, event):
        if self.entry.index(INSERT) == "1.0":
            self.entry.event_generate("<<SelectAll>>")
        else:
            self.entry.mark_set(INSERT, "1.0")
        return "break"

    def delete_word(self, event):
        self.entry.event_generate("<<SelectPrevWord>>")
        self.entry.event_generate("<<Delete>>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""This tool copies your input to system clipboard and then synchronises it with android's clipboard and pastes it with Alt-v command. Obviously this will overwrite your clipboard contents. Make sure you focus on the text input on the scrcpy window before you attempt to paste."""
    )
    parser.add_argument("window_name", help="window name to target")
    parser.add_argument(
        "-m",
        "--manual",
        action="store_true",
        default=False,
        help="don't auto send on ctrl+Enter",
    )
    parser.add_argument(
        "-nh",
        "--no-hide",
        action="store_true",
        default=False,
        help="don't auto hide on send",
    )
    parser.add_argument(
        "-ns",
        "--no-strip",
        action="store_true",
        default=False,
        help="don't auto strip whitespace on send",
    )
    args = parser.parse_args()

    # Disable tkinter's expected input methods. No idea why this is required
    # since documentation is scarce, but I could not get greek accents to work
    # (e.g. ά, ΐ) otherwise: they'd get inserted as 'α etc.
    os.environ["XMODIFIERS"] = "@im=none"
    os.environ["GTK_IM_MODULE"] = "gtk-im-context-simple"
    os.environ["QT_IM_MODULE"] = "simple"

    root = Tk(className="scrcpy-input")
    Grid.rowconfigure(root, 0, weight=1)  # type: ignore
    Grid.columnconfigure(root, 0, weight=1)  # type: ignore

    app = Application(
        args.window_name,
        not args.manual,
        not args.no_hide,
        not args.no_strip,
        master=root,
    )

    def sigint_handler(sig, frame):
        app.master.destroy()

    # Set signal before starting
    signal.signal(signal.SIGINT, sigint_handler)

    app.mainloop()
