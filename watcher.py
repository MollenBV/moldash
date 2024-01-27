import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    """ Handler for file system changes. Restarts the Flask app when a change is detected. """
    def on_any_event(self, event):
        print(f"Change detected in {event.src_path}. Restarting Flask app...")
        subprocess.run(["pkill", "-f", "app.py"])
        time.sleep(1)  # Give some time to release resources
        subprocess.Popen(["nohup", "python", "app.py", "&"])

def start_observer(path):
    """ Start the watchdog observer """
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"Watching for file changes in {path}")
    start_observer(path)
