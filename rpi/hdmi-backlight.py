import time
import signal
import sys
import queue
import threading
import numpy as np
import cv2
from serial import Serial
from multiprocessing.pool import ThreadPool

class Leds:
    def __init__(self):
        self.device = Serial('/dev/ttyS0', 115200)

    def open(self):
        try:
            self.device.open()
            print("Opened serial port to LED peripheral")
        except IOError:
            self.close()
            self.device.open()
            print("Serial port to LED peripheral was already open, closed and opened again")

    def close(self):
        self.device.close()

    def read(self):
        return self.device.readline().decode('utf-8')

    def write(self, colors):
        # color: [[int;3];4]
        data = [52, 25]
        for color in colors:
            data += color
        return self.device.write(bytes(data))

# bufferless VideoCapture
class VideoCapture:

    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True

    def start(self):
        self.t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put((ret, frame))
            if not ret:
                break

    def read(self):
        try:
            return self.q.get(timeout=3)
        except queue.Empty:
            return False, None

def cleanup():
    # ignore additional signals
    print("Cleaning up resources...")
    if leds is not None:
        leds.write([ [0, 0, 0] for _ in range(3)])
        leds.close()
        print("Closed serial port")
    if cap is not None:
        cap.cap.release()
        print("Released video capture")
    if iters is not 0:
        print(f"Performance statistics (average over {iters} iters):")
        print(f"  read frame:  {np.format_float_positional(counters['read frame'] / iters, trim='-')} sec")
        print(f"  calc mean:   {np.format_float_positional(counters['processing mean'] / iters, trim='-')} sec")
        print(f"  led io:      {np.format_float_positional(counters['led io'] / iters, trim='-')} sec")
        print(f"  iter:        {np.format_float_positional(counters['iter'] / iters, trim='-')} sec")

def signal_handler(signum, frame):
    # ignore additional signals
    signal.signal(signum, signal.SIG_IGN)
    cleanup()
    sys.exit(0)

# performance counters
counters = {
    "read frame": 0,
    "processing mean": 0,
    "led io": 0,
    "iter": 0,
}
iters = 0

# register interrupt handler
signal.signal(signal.SIGINT, signal_handler)

leds = Leds()
leds.open()

cap = VideoCapture(-1)
cap.cap.set(cv2.CAP_PROP_FPS, 1)

if cap.cap.isOpened() and cap.cap.grab():
    print("Capturing video")
else:
    cleanup()
    sys.exit("Unable to open capture device")

cap.start()

def mean_color(frame):
    return frame.mean(axis=0).mean(axis=0)

pool = ThreadPool(4)

bounds = None
while True:
    iter_start = time.perf_counter()

    start = time.perf_counter()
    ret, frame = cap.read()
    counters["read frame"] += time.perf_counter() - start
    if not ret:
        print("Failed to read frame")
        break

    if iters % 100 == 0:
        print(iters)

    # bgr to rgb
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    upper_half, lower_half = np.vsplit(frame, 2)
    upper_left, upper_right = np.hsplit(upper_half, 2)
    lower_left, lower_right = np.hsplit(lower_half, 2)

    # run computation in threadpool
    start = time.perf_counter()
    areas = [upper_left, upper_right, lower_left, lower_right]
    dom_colors = np.zeros((len(areas), 3))
    def process_area(i):
        dom_colors[i] = mean_color(areas[i])
    pool.map(process_area, range(len(areas)))
    counters["processing mean"] += time.perf_counter() - start

    colors = [ [int(c[0]), int(c[1]), int(c[2])] for c in dom_colors]

    start = time.perf_counter()
    leds.write(colors)
    counters["led io"] += time.perf_counter() - start

    iters += 1

    counters["iter"] += time.perf_counter() - iter_start

cleanup()
