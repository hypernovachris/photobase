import queue
import threading
from PyQt6.QtGui import QPixmap

class ImageLoaderThread(threading.Thread):
  def __init__(self, task_queue, result_queue):
    super().__init__()
    self.task_queue = task_queue
    self.result_queue = result_queue
    self.running = True
    self.condition = threading.Condition()

  def run(self):
    while self.running:
      with self.condition:
        # Wait until notified that there's work to do
        self.condition.wait_for(lambda: not self.task_queue.empty() or not self.running)

        if not self.running:
          break

        try:
          action, thumb_widget = self.task_queue.get(timeout=1)
          if action == "load":
            # verify that image is still visible
            if thumb_widget.is_in_view:
              pixmap = QPixmap(thumb_widget.thumb_path)
              self.result_queue.put((thumb_widget, pixmap))
          elif action == "unload":
            self.result_queue.put((thumb_widget, None))
        except queue.Empty:
          continue # shouldn't happen
  
  def stop(self):
    self.running = False
    with self.condition:
      self.condition.notify() # Wake up the thread to exit
    # ChatGPT wrote this and I doubt this will work
  