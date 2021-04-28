import cv2
import queue
import threading

class BufferlessVideoCapture:

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
