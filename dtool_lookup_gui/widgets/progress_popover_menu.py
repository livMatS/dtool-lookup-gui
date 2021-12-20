#
# Copyright 2021 Lars Pastewka
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from gi.repository import GObject, Gtk


class DtoolProgressStatusBox(Gtk.Box):
    __gtype_name__ = 'DtoolProgressStatusBox'

    _margin = 12
    _pb_margin = 3

    def __init__(self, update_notification, label, on_cancel, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self._step = 0
        self._length = 1
        self._text = None
        self._done = False

        self._update_notification = update_notification

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=self._margin, margin_bottom=self._margin,
                       margin_start=self._margin, margin_end=self._margin)
        vbox.pack_start(Gtk.Label(label, xalign=0), True, False, 0)
        self._progress_bar = Gtk.ProgressBar(margin_top=self._pb_margin, margin_bottom=self._pb_margin)
        vbox.pack_start(self._progress_bar, False, False, 0)
        self._progress_label = Gtk.Label(xalign=0)
        vbox.pack_start(self._progress_label, True, False, 0)
        self.pack_start(vbox, False, False, 0)
        if on_cancel is not None:
            button = Gtk.Button(image=Gtk.Image.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON))
            button.get_style_context().add_class('circular')
            button.connect('clicked', on_cancel)
            self.pack_end(button, False, False, 0)

    def set_step(self, step, length):
        self._step = step
        self._length = length
        self._progress_bar.set_fraction(self.fraction)
        self._progress_label.set_text(f'{step} / {length}')
        self._update_notification()

    def set_text(self, value):
        self._text = value

    def __len__(self):
        return self._length

    @property
    def step(self):
        return self._step

    @property
    def fraction(self):
        return self._step / self._length

    @property
    def is_done(self):
        return self._done

    def set_done(self):
        self._done = True
        self._progress_label.set_text('Copy operation succeeded.')


class DtoolProgressPopoverMenu(Gtk.PopoverMenu):
    __gtype_name__ = 'DtoolProgressPopoverMenu'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.hbox)
        self.hbox.show_all()

    def clear(self):
        for child in self.hbox.get_children():
            child.destroy()

    def add_status_box(self, update_notification, label, on_cancel=None):
        status_box = DtoolProgressStatusBox(update_notification, label, on_cancel)
        self.hbox.pack_end(status_box, False, False, 0)
        status_box.show_all()
        return status_box

    @property
    def status_boxes(self):
        return self.hbox.get_children()

GObject.type_register(DtoolProgressStatusBox)
GObject.type_register(DtoolProgressPopoverMenu)
