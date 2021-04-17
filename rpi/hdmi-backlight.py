import time
import signal
import sys
import queue
import threading
import numpy as np
# import numexpr as ne
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
    "processing mean": 0,
    "led io": 0,
    "iter": 0,
}
iters = 0

# register interrupt handler
signal.signal(signal.SIGINT, signal_handler)

leds = Leds()
leds.open()

cap = VideoCapture(-1)#cv2.VideoCapture(0)
# cap.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
# cap.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.cap.set(cv2.CAP_PROP_FPS, 1)#30)

if cap.cap.isOpened() and cap.cap.grab():
    print("Capturing video")
else:
    cleanup()
    sys.exit("Unable to open capture device")

cap.start()

def mean_color(frame):
    # colwise_sums = frame.sum(axis=0)
    # num_nonzero = (colwise_sums != [0,0,0]).sum()
    # colwise_sums.mean(axis=0) / num_nonzero
    # TODO: ignore (0,0,0) pixels
    return frame.mean(axis=0).mean(axis=0)

def sqrt_mean(frame):
    # sqrt(sum(pixel**2)/count)
    return np.sqrt(np.square(frame).mean(axis=0).mean(axis=0))

def dominant_color(a):
    a2D = a.reshape(-1, a.shape[-1])
    a2D = np.round(a2D)
    col_range = (256, 256, 256) # generically : a2D.max(0)+1
    a1D = np.ravel_multi_index(a2D.T, col_range)
    return np.unravel_index(np.bincount(a1D).argmax(), col_range)

def get_sorted_top_k(array, top_k=1, axis=-1, reverse=False):
    if reverse:
        axis_length = array.shape[axis]
        partition_index = np.take(np.argpartition(array, kth=-top_k, axis=axis),
                                  range(axis_length - top_k, axis_length), axis)
    else:
        partition_index = np.take(np.argpartition(array, kth=top_k, axis=axis), range(0, top_k), axis)
    top_scores = np.take_along_axis(array, partition_index, axis)
    # resort partition
    sorted_index = np.argsort(top_scores, axis=axis)
    if reverse:
        sorted_index = np.flip(sorted_index, axis=axis)
    top_sorted_indexes = np.take_along_axis(partition_index, sorted_index, axis)
    return top_sorted_indexes

def dominant_colors(a):
    a2D = a.reshape(-1, a.shape[-1])
    a2D = np.round(a2D)
    col_range = (256, 256, 256) # generically : a2D.max(0)+1
    a1D = np.ravel_multi_index(a2D.T, col_range)
    bins = np.bincount(a1D)
    first, second = get_sorted_top_k(bins, top_k=2, reverse=True)
    return np.unravel_index(first, col_range), np.unravel_index(second, col_range)

# def dominant_color_parallel(a):
#     a2D = a.reshape(-1, a.shape[-1])
#     a2D = np.round(a2D)
#     col_range = (256, 256, 256) # generically : a2D.max(0)+1
#     eval_params = {'a0':a2D[:,0],'a1':a2D[:,1],'a2':a2D[:,2],
#                    's0':col_range[0],'s1':col_range[1]}
#     a1D = ne.evaluate('a0*s0*s1+a1*s0+a2',eval_params)
#     return np.unravel_index(np.bincount(a1D).argmax(), col_range)

# def dominant_colors_parallel(a):
#     a2D = a.reshape(-1, a.shape[-1])
#     a2D = np.round(a2D)
#     col_range = (256, 256, 256) # generically : a2D.max(0)+1
#     eval_params = {'a0':a2D[:,0],'a1':a2D[:,1],'a2':a2D[:,2],
#                    's0':col_range[0],'s1':col_range[1]}
#     a1D = ne.evaluate('a0*s0*s1+a1*s0+a2',eval_params)
#     bins = np.bincount(a1D)
#     indices = get_sorted_top_k(bins, top_k=4, reverse=True)
#     return [np.unravel_index(index, col_range) for index in indices]

pool = ThreadPool(4)

bounds = None
while True:
    iter_start = time.perf_counter()

    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break

    if iters % 100 == 0:
        print(iters)

    # save preview
    # if iters % 100 == 0:
    #     cv2.imwrite('latest.png', frame)
    #     print("Wrote to latest.png")

    # bgr to rgb
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # flip horizontally
    # frame = np.flip(frame, axis=1)
    # if iters % 100 == 0:
    #     y_nonzero, x_nonzero, _ = np.nonzero(frame)
    #     # print(f"bounds before {bounds}")
    #     bounds = [np.min(y_nonzero), np.max(y_nonzero), np.min(x_nonzero), np.max(x_nonzero)]
    #     if bounds[1] - bounds[0] % 2 != 0:
    #         bounds[1] += 1
    #     if bounds[3] - bounds[2] % 2 != 0:
    #         bounds[3] -= 1
    #     # print(f"bounds after {bounds}")
    # if bounds is not None:
    #     frame = frame[bounds[0]:bounds[1], bounds[2]:bounds[3]]

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
    # dom_colors = [mean_color(area) for area in [upper_left, upper_right, lower_left, lower_right]]
    counters["processing mean"] += time.perf_counter() - start

    # start = time.perf_counter()
    # dom_colors = [dominant_color_parallel(area) for area in [upper_left, upper_right, lower_left, lower_right]]
    # # dom_colors = dominant_colors_parallel(frame)
    # counters["processing dominant"] += time.perf_counter() - start
    # print(sqrt_colors, dom_colors)

    colors = [ [int(c[0]), int(c[1]), int(c[2])] for c in dom_colors]

    # print(f"upper left {colors[0]} upper right {colors[1]} lower left {colors[2]} lower right {colors[3]}")

    start = time.perf_counter()
    leds.write(colors)
    counters["led io"] += time.perf_counter() - start

    iters += 1

    counters["iter"] += time.perf_counter() - iter_start

cleanup()
