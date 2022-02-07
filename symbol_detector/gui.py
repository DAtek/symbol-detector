import os
import tkinter
from queue import Queue
from tkinter import ttk
from asyncio import sleep
import numpy as np
from PIL import Image, ImageTk

from symbol_detector import sampler, symbols
from symbol_detector.detector import Detector
from symbol_detector.constants import PAD_X, PAD_Y, IMAGE_SIZE, SYMBOLS_DIR
from symbol_detector.settings import config
from symbol_detector.workers import BaseWorker


class MainWindow(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        self._px = PAD_X
        self._py = PAD_Y
        self.sym_dir = "%s/%s/" % (SYMBOLS_DIR, config.symbol_set)
        self.symbols = symbols.read_symbols(self.sym_dir, IMAGE_SIZE)
        self.core = Detector(self.symbols)
        self.wm_title("Symbol detector")
        self._window_help: WindowHelp = None

        # menu
        self.menu_bar = tkinter.Menu()
        self.file_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(
            label="Save current symbol", command=self.save_current
        )
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.edit_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Select symbol set", command=self.change_sym)
        self.edit_menu.add_command(label="Camera probe", command=self.display_help)
        self.menu_bar.add_cascade(label="Settings", menu=self.edit_menu)
        self.config(menu=self.menu_bar)
        # end menu

        self.im_thresh = FrameImage(self, self.core.thresh_queue, 640, 480)
        self.im_thresh.grid(row=1, column=1, rowspan=2, padx=self._px, pady=self._py)
        self.im_drawing = FrameImage(
            self, self.core.result_queue, IMAGE_SIZE, IMAGE_SIZE
        )
        self.im_drawing.grid(row=1, column=2, padx=self._px, pady=self._py)
        self.im_ref = FrameImage(self, self.core.ref_queue, IMAGE_SIZE, IMAGE_SIZE)
        self.im_ref.grid(row=2, column=2, padx=self._px, pady=self._py)
        self.btn_start = tkinter.Button(text="Start", command=self.start_core)
        self.btn_start.grid(row=3, column=1, columnspan=2, padx=self._px, pady=self._py)
        self.btn_stop = tkinter.Button(text="Stop", command=self.stop_core)

    def destroy(self):
        self.stop_core()
        self.stop_refreshing()
        super().destroy()

    def start_core(self):
        if not self.symbols:
            return
        self.core.loop_start()
        self.start_refreshing()
        self.btn_start.grid_forget()
        self.btn_stop.grid(row=3, column=1, columnspan=2, padx=self._px, pady=self._py)

    def stop_core(self):
        self.stop_refreshing()
        if self.core:
            self.core.loop_stop()
        self.btn_stop.grid_forget()
        self.btn_start.grid(row=3, column=1, columnspan=2, padx=self._px, pady=self._py)

    def change_sym(self):
        WindowSymbolsSelector(self)

    def display_help(self):
        self._window_help = WindowHelp(self)
        self._window_help.after(500, self.get_sample)

    def get_sample(self):
        s = sampler.Sampler()
        s.show_camera()
        self._window_help.destroy()

    def save_current(self):
        if self.core == 0:
            return
        WindowSymbolSaver(self)

    def start_refreshing(self):
        if not self.core:
            return
        self.im_thresh.loop_start()
        self.im_drawing.loop_start()
        self.im_ref.loop_start()

    def stop_refreshing(self):
        self.im_thresh.loop_stop()
        self.im_drawing.loop_stop()
        self.im_ref.loop_stop()


class WindowSymbolSaver(tkinter.Toplevel):
    def __init__(self, master: MainWindow):
        self._px = PAD_X
        self._py = PAD_Y
        self.master = master
        super().__init__(master)
        self.wm_title("Save current symbol")
        self.geometry("%dx%d%+d%+d" % (300, 100, 500, 300))
        tkinter.Label(self, text="Symbol name:").grid(
            row=1, column=1, padx=self._px, pady=self._py
        )
        self.textBox = tkinter.Text(self, width=25, height=1)
        self.textBox.grid(row=2, column=1, padx=self._px, pady=self._py)
        self.btnSave = tkinter.Button(self, text="Save", command=self.save)
        self.btnSave.grid(row=3, column=1, padx=self._px, pady=self._py)

    def save(self):
        s0 = self.textBox.get("1.0", "end-1c")
        hex_name = ""
        for c in s0:
            x = hex(ord(c))
            hex_name += x[2:]
        s = bytes.fromhex(hex_name).decode("utf-8")
        if s != "":
            n = symbols.get_next_nr(s, self.master.symbols)
            file_name = "%s-%s.png" % (s0, n)
            file_name = "%s%s" % (self.master.sym_dir, file_name)
            u_file_name = file_name.encode("utf-8")
            hex_name = ""
            for c in file_name:
                x = hex(ord(c))
                hex_name += x[2:]
            ascii_name = bytes.fromhex(hex_name).decode("ascii")
            self.master.core.save_im(ascii_name)
            try:
                os.rename(ascii_name, u_file_name.decode("utf-8"))
            except:
                pass
            self.master.symbols = symbols.read_symbols(self.master.sym_dir, IMAGE_SIZE)
            self.destroy()


class WindowSymbolsSelector(tkinter.Toplevel):
    def __init__(self, master):
        self._px = PAD_X
        self._py = PAD_Y
        self.master = master
        tkinter.Toplevel.__init__(self)
        self.wm_title("Symbol set selector")
        tkinter.Label(self, text="Load symbol set:").grid(
            row=1, column=2, padx=self._px, pady=self._py
        )
        self.geometry("%dx%d%+d%+d" % (300, 60, 500, 300))
        self.combo_syms = ttk.Combobox(self, width=30)
        self.combo_syms["values"] = [path.name for path in SYMBOLS_DIR.iterdir()]
        self.combo_syms.grid(row=2, column=2, padx=self._px, pady=self._py)
        self.combo_syms.bind("<<ComboboxSelected>>", self.select_settings)

    def select_settings(self, _):
        config.symbol_set = self.combo_syms.get()
        config.save()
        self.master.sym_dir = "%s/%s/" % (SYMBOLS_DIR, self.combo_syms.get())
        self.master.symbols = symbols.read_symbols(self.master.sym_dir, IMAGE_SIZE)
        self.destroy()


class WindowHelp(tkinter.Toplevel):
    def __init__(self, master):
        tkinter.Toplevel.__init__(self)
        self.wm_title("Help")
        self.master = master
        self.help_text = ""
        self.text_list = [
            ["r", "Refresh frame"],
            ["b", "Increase blur"],
            ["v", "Decrease blur"],
            ["+", "Increase lightness"],
            ["-", "Decrease lightness"],
            ["Left click", "Mark the center of the circle"],
            ["Right click", "Point on the radius"],
            ["Middle click", "Calculate parameters"],
            ["d", "Delete calculated parameters"],
            ["q", "Quit"],
        ]
        for part in self.text_list:
            self.help_text += part[0] + " : " + part[1] + "\n\n"
        self.label_help = tkinter.Label(self, text=self.help_text)
        self.label_help.pack()


class FrameImage(tkinter.Label, BaseWorker):
    def __init__(self, master: MainWindow, in_queue: Queue, width, height):
        BaseWorker.__init__(self)
        self.im = np.zeros([height, width, 3], np.uint8)
        self.im = symbols.cv2.cvtColor(self.im, symbols.cv2.COLOR_RGB2RGBA)
        self.im = Image.fromarray(self.im)
        self._in_queue = in_queue
        self.photo = ImageTk.PhotoImage(image=self.im)
        self.photo_next: ImageTk.PhotoImage = None
        super().__init__(master, image=self.photo)

    async def run(self):
        while self.running:
            if self._in_queue.empty():
                await sleep(0.01)
                continue
            self.im = self._in_queue.get()
            self.im = Image.fromarray(self.im)
            if self.photo:
                self.photo_next = ImageTk.PhotoImage(image=self.im)
                self.configure(image=self.photo_next)
                self.photo = None
            else:
                self.photo = ImageTk.PhotoImage(image=self.im)
                self.configure(image=self.photo)
                self.photo_next = None
            await sleep(0.01)
        self.run_end()


def run():
    config.load()
    app = MainWindow()
    app.mainloop()
