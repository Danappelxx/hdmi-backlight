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
            if not self.cap:
                print("Exiting video capture loop")
                break
            ret, frame = self.cap.read()
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put((ret, frame))
            if not ret:
                print("Exiting video capture loop")
                break

    def read(self):
        try:
            return self.q.get(timeout=3)
        except queue.Empty:
            return False, None

def cleanup():
    # ignore additional signals
    print("Cleaning up resources...")
    if cap is not None:
        icap = cap.cap
        cap.cap = None
        time.sleep(1)
        icap.release()
        print("Released video capture")
    if leds is not None:
        leds.write([ [0, 0, 0] for _ in range(4)])
        leds.close()
        print("Closed serial port")
    if iters is not 0:
        print(f"Performance statistics (average over {iters} iters):")
        print(f"  read frame:  {np.format_float_positional(counters['read frame'] / iters, trim='-')} sec ({100 * counters['read frame'] / counters['iter'] :.2f}%)")
        print(f"  adjust bounds:  {np.format_float_positional(counters['bounds'] / iters, trim='-')} sec ({100 * counters['bounds'] / counters['iter'] :.2f}%)")
        print(f"  calc mean:   {np.format_float_positional(counters['processing mean'] / iters, trim='-')} sec ({100 * counters['processing mean'] / counters['iter'] :.2f}%)")
        print(f"  led io:      {np.format_float_positional(counters['led io'] / iters, trim='-')} sec ({100 * counters['led io'] / counters['iter'] :.2f}%)")
        print(f"  iter:        {np.format_float_positional(counters['iter'] / iters, trim='-')} sec ({100 * counters['iter'] / counters['iter'] :.2f}%)")

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
    "bounds": 0
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

def split(frame):
    upper_half, lower_half = np.array_split(frame, 2)
    upper_left, upper_right = np.array_split(upper_half, 2, axis=1)
    lower_left, lower_right = np.array_split(lower_half, 2, axis=1)
    return [upper_left, upper_right, lower_left, lower_right]

def find_bounds(frame):
    y_nonzero, x_nonzero, _ = np.nonzero(frame)
    bounds = [np.min(y_nonzero), np.max(y_nonzero), np.min(x_nonzero), np.max(x_nonzero)]
    return bounds

def apply_bounds(frame):
    return frame[bounds[0]:bounds[1]+1, bounds[2]:bounds[3]+1]

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

    start = time.perf_counter()
    if iters % 1000 == 0:
        # print(iters)
        bounds = find_bounds(frame)
    if bounds is not None:
        before_bounds_shape = frame.shape
        frame = apply_bounds(frame)
        after_bounds_shape = frame.shape
        if before_bounds_shape == after_bounds_shape:
            bounds = None
    counters["bounds"] += time.perf_counter() - start

    # areas: [upper_left, upper_right, lower_left, lower_right]
    areas = split(frame)

    # run computation in threadpool
    start = time.perf_counter()
    dom_colors = np.zeros((len(areas), 3))
    def process_area(i):
        dom_colors[i] = mean_color(areas[i])
    pool.map(process_area, range(len(areas)))
    counters["processing mean"] += time.perf_counter() - start

    # bgr to rgb
    colors = [ [int(c[2]), int(c[1]), int(c[0])] for c in dom_colors]

    start = time.perf_counter()
    leds.write(colors)
    counters["led io"] += time.perf_counter() - start

    iters += 1

    counters["iter"] += time.perf_counter() - iter_start

cleanup()
