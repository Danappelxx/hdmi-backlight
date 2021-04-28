import time
import signal
import sys
import numpy as np
from serial import Serial
from multiprocessing.pool import ThreadPool
from leds import DMALeds
from videocapture import BufferlessVideoCapture

# performance counters
counters = {
    "read frame": 0,
    "processing mean": 0,
    "led io": 0,
    "iter": 0,
    "bounds": 0
}
iters = 0
cap = None
leds = None

def cleanup():
    global counters, iters, cap, leds

    # ignore additional signals
    print("Cleaning up resources...")
    if cap is not None:
        icap = cap.cap
        cap.cap = None
        time.sleep(1)
        icap.release()
        print("Released video capture")
    if leds is not None:
        leds.show([ [0, 0, 0] for _ in range(6)])
        leds.cleanup()
        print("Cleaned up LEDs")
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

def mean_color(frame):
    return frame.mean(axis=0, dtype=np.uint64).mean(axis=0, dtype=np.uint64)

def split(frame):
    upper_half, lower_half = np.array_split(frame, 2)
    upper_left, upper_middle, upper_right = np.array_split(upper_half, 3, axis=1)
    lower_left, lower_middle, lower_right = np.array_split(lower_half, 3, axis=1)
    return [upper_left, upper_middle, upper_right, lower_left, lower_middle, lower_right]

def find_bounds(frame):
    y_mid = frame.shape[0] // 2
    x_mid = frame.shape[1] // 2

    y_nonzero_min = 0
    for y in range(frame.shape[0]):
        if (frame[y,x_mid] != [0,0,0]).any():
            y_nonzero_min = y
            break

    y_nonzero_max = frame.shape[0]-1
    for y in range(frame.shape[0]-1, -1, -1): # range(start, stop, step)
        if (frame[y, x_mid] != [0,0,0]).any():
            y_nonzero_max = y
            break

    x_nonzero_min = 0
    for x in range(frame.shape[1]):
        if (frame[y_mid,x] != [0,0,0]).any():
            x_nonzero_min = x
            break

    x_nonzero_max = frame.shape[1]-1
    for x in range(frame.shape[1]-1, -1, -1): # range(start, stop, step)
        if (frame[y_mid, x] != [0,0,0]).any():
            x_nonzero_max = x
            break

    bounds = [y_nonzero_min, y_nonzero_max, x_nonzero_min, x_nonzero_max]
    return bounds

def apply_bounds(frame, bounds):
    return frame[bounds[0]:bounds[1]+1, bounds[2]:bounds[3]+1]

def run():
    global counters, iters, cap, leds

    # catch ctrl+c
    signal.signal(signal.SIGINT, signal_handler)
    # catch systemd stop
    signal.signal(signal.SIGTERM, signal_handler)

    leds = DMALeds()
    leds.start()

    cap = BufferlessVideoCapture(-1)

    if cap.cap.isOpened() and cap.cap.grab():
        print("Capturing video")
    else:
        cleanup()
        sys.exit("Unable to open capture device")

    cap.start()

    pool = ThreadPool(4)
    last_check_time = None
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
            bounds = find_bounds(frame)

            if last_check_time is not None:
                delta = time.monotonic() - last_check_time
                print(f"{iters} ({delta:.2f} sec per 1000 iter, approx. {1000/delta:.2f} fps), bounds: {bounds}")
            last_check_time = time.monotonic()
            sys.stdout.flush()

        if bounds is not None:
            before_bounds_shape = frame.shape
            frame = apply_bounds(frame, bounds)
            after_bounds_shape = frame.shape
            if before_bounds_shape == after_bounds_shape:
                bounds = None
        counters["bounds"] += time.perf_counter() - start

        # areas: [upper_left, upper_middle, upper_right, lower_left, lower_middle, lower_right]
        areas = split(frame)

        # run computation in threadpool
        start = time.perf_counter()
        dom_colors = np.zeros((len(areas), 3), dtype=np.uint64)
        def process_area(i):
            dom_colors[i] = mean_color(areas[i])
        pool.map(process_area, range(len(areas)))
        counters["processing mean"] += time.perf_counter() - start

        # bgr to rgb
        colors = [ [int(c[2]), int(c[1]), int(c[0])] for c in dom_colors]

        start = time.perf_counter()
        leds.show(colors)
        counters["led io"] += time.perf_counter() - start

        iters += 1

        counters["iter"] += time.perf_counter() - iter_start

    cleanup()

if __name__ == "__main__":
    run()
