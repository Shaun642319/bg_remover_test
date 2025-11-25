from PySide6.QtCore import QThread, Signal
from rembg import remove
from PIL import Image
import os

class WorkerThread(QThread):
    progress = Signal(int)
    finished = Signal()
    status = Signal(str)

    def __init__(self, images, output_folder):
        super().__init__()
        self.images = images
        self.output_folder = output_folder

    def run(self):
        total = len(self.images)

        for index, image_path in enumerate(self.images):

            if self.isInterruptionRequested():
                self.status.emit("Cancelled.")
                break

            try:
                
                self.status.emit(f"Processing: {os.path.basename(image_path)}")

                # Load image with Pillow
                input_image = Image.open(image_path)

                # Remove background
                output = remove(input_image)

                # Output filename
                base = os.path.basename(image_path)
                name_without_ext = os.path.splitext(base)[0]
                output_path = os.path.join(
                    self.output_folder,
                    f"{name_without_ext}_removed.png"
                )

                # Save result
                output.save(output_path)

            except Exception as e:
                self.status.emit(f"Error: {e}")

            # Update progress
            percent = int(((index + 1) / total) * 100)
            self.progress.emit(percent)

        self.finished.emit()
