#!/usr/bin/env python
# vim:fileencoding=utf-8
# License: GPL v3 Copyright: 2016, Kovid Goyal <kovid at kovidgoyal.net>

import shlex

from .config import to_layout_names
from .constants import shell_path
from .layout import all_layouts


class Tab:

    def __init__(self, opts, name):
        self.windows = []
        self.name = name.strip()
        self.active_window_idx = 0
        self.enabled_layouts = opts.enabled_layouts
        self.layout = (self.enabled_layouts or ['tall'])[0]
        self.cwd = None


class Session:

    def __init__(self):
        self.tabs = []
        self.active_tab_idx = 0

    def add_tab(self, opts, name=''):
        if self.tabs and not self.tabs[-1].windows:
            del self.tabs[-1]
        self.tabs.append(Tab(opts, name))

    def set_layout(self, val):
        if val not in all_layouts:
            raise ValueError('{} is not a valid layout'.format(val))
        self.tabs[-1].layout = val

    def add_window(self, cmd):
        if cmd:
            cmd = shlex.split(cmd) if isinstance(cmd, str) else cmd
        else:
            cmd = None
        self.tabs[-1].windows.append(cmd)

    def focus(self):
        self.active_tab_idx = max(0, len(self.tabs) - 1)
        self.tabs[-1].active_window_idx = max(0, len(self.tabs[-1].windows) - 1)

    def set_enabled_layouts(self, raw):
        self.tabs[-1].enabled_layouts = to_layout_names(raw)

    def set_cwd(self, val):
        self.tabs[-1].cwd = val


def parse_session(raw, opts):
    ans = Session()
    ans.add_tab(opts)
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            cmd, rest = line.partition(' ')[::2]
            cmd, rest = cmd.strip(), rest.strip()
            if cmd == 'new_tab':
                ans.add_tab(opts, rest)
            elif cmd == 'layout':
                ans.set_layout(rest)
            elif cmd == 'launch':
                ans.add_window(rest)
            elif cmd == 'focus':
                ans.focus()
            elif cmd == 'enabled_layouts':
                ans.set_enabled_layouts(rest)
            elif cmd == 'cd':
                ans.set_cwd(rest)
            else:
                raise ValueError('Unknown command in session file: {}'.format(cmd))
    for t in ans.tabs:
        if not t.windows:
            t.windows.append([shell_path])
    return ans


def create_session(opts, args):
    if args.session:
        with open(args.session) as f:
            return parse_session(f.read(), opts)
    ans = Session()
    if args.window_layout:
        if args.window_layout not in opts.enabled_layouts:
            opts.enabled_layouts.insert(0, args.window_layout)
        current_layout = args.window_layout
    else:
        current_layout = opts.enabled_layouts[0] if opts.enabled_layouts else 'tall'
    ans.add_tab(opts)
    ans.tabs[-1].layout = current_layout
    cmd = args.args or [shell_path]
    ans.add_window(cmd)
    return ans
