from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QHBoxLayout
)
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QMovie
from PySide6.QtCore import Qt, QSize, QMimeData


import os
import subprocess
import platform


from components.file_select import ImageSelector
from components.folder_select import FolderSelector
from components.progress_bar import ProgressBar
from components.worker import WorkerThread


class ImageListWidget(QListWidget):
    """Custom QListWidget with drag & drop support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                    files.append(path)

        if files:
            self.parent().add_images_from_drop(files)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BG Remover - Bulk Tool")
        self.setMinimumWidth(450)

        # Store paths
        self.selected_images = []
        self.output_folder = ""

        # Components
        self.file_selector = ImageSelector()
        self.folder_selector = FolderSelector()
        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()

        # Buttons
        self.selectImagesBtn = QPushButton("Select Images")
        self.selectFolderBtn = QPushButton("Select Output Folder")
        self.startBtn = QPushButton("Start Processing")
        self.clearListBtn = QPushButton("Clear List")
        self.cancelBtn = QPushButton("Cancel")

        self.cancelBtn.setEnabled(False)
        self.cancelBtn.hide()

        # Apply icons
        self.selectImagesBtn.setIcon(QIcon("resources/image.png"))
        self.selectFolderBtn.setIcon(QIcon("resources/folder.png"))
        self.startBtn.setIcon(QIcon("resources/start.png"))
        self.cancelBtn.setIcon(QIcon("resources/cancel.png"))
        self.clearListBtn.setIcon(QIcon("resources/clear.png"))

        # Button sizes
        for btn in [self.selectImagesBtn, self.selectFolderBtn, self.startBtn, self.clearListBtn, self.cancelBtn]:
            btn.setIconSize(QSize(18, 18))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    border: 1px solid #555;
                    padding: 7px;
                    border-radius: 6px;
                    color: #eee;
                }
                QPushButton:hover {
                    background-color: #444;
                    border-color: #888;
                }
                QPushButton:disabled {
                    background-color: #222;
                    color: #666;
                    border-color: #333;
                }
            """)

        self.statusLabel = QLabel("Select images and output folder to begin.")
        self.startBtn.setEnabled(False)

        # Custom list widget with drag & drop
        self.imageList = ImageListWidget(self)
        self.imageList.setMaximumHeight(170)
        self.imageList.setSpacing(6)

        # Dark styling
        self.imageList.setStyleSheet("""
            QListWidget {
                background-color: #1f1f1f;
                border: 1px solid #444;
                border-radius: 6px;
                color: #ddd;
                padding: 6px;
            }
            QListWidget::item {
                padding: 7px;
            }
            QListWidget::item:selected {
                background-color: #444;
                color: white;
            }
        """)

        # Layouts
        main_layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.selectImagesBtn)
        button_layout.addWidget(self.selectFolderBtn)
        button_layout.addWidget(self.startBtn)
        button_layout.addWidget(self.clearListBtn)
        button_layout.addWidget(self.cancelBtn)

        main_layout.addWidget(self.imageList)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.statusLabel)


        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Signals
        self.selectImagesBtn.clicked.connect(self.handle_select_images)
        self.selectFolderBtn.clicked.connect(self.handle_select_folder)
        self.startBtn.clicked.connect(self.handle_start)
        self.cancelBtn.clicked.connect(self.handle_cancel)
        self.clearListBtn.clicked.connect(self.clear_list)


    # -----------------------------
    # Add Images (external + drag & drop)
    # -----------------------------
    def add_images_from_drop(self, files):
        """Add images dropped into the ListWidget."""
        self.selected_images.extend(files)
        self.update_image_list()
        self.check_ready()

    def update_image_list(self):
        """Refresh the QListWidget with thumbnails + badges."""
        self.imageList.clear()

        for img in self.selected_images:
            item = QListWidgetItem()

            # Thumbnail
            pixmap = QPixmap(img).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(pixmap))

            # Badge: prepend "1) filename"
            index = self.selected_images.index(img) + 1
            filename = os.path.basename(img)

            item.setText(f"{index}.  {filename}")
            self.imageList.addItem(item)


    # -----------------------------
    # Button Handlers
    # -----------------------------
    def handle_select_images(self):
        images = self.file_selector.select_images(self)
        if images:
            self.selected_images.extend(images)
            self.update_image_list()
            self.statusLabel.setText(f"Selected {len(self.selected_images)} images.")
            self.check_ready()

    def handle_select_folder(self):
        folder = self.folder_selector.select_folder(self)
        if folder:
            self.output_folder = folder
            self.statusLabel.setText(f"Output folder: {folder}")
            self.check_ready()

    def handle_start(self):
        self.statusLabel.setText("Processing started...")
        self.progress_bar.show()
        self.progress_bar.update_value(0)

        self.selectImagesBtn.setEnabled(False)
        self.selectFolderBtn.setEnabled(False)
        self.startBtn.setEnabled(False)

        self.cancelBtn.show()
        self.cancelBtn.setEnabled(True)

        self.worker = WorkerThread(self.selected_images, self.output_folder)
        self.worker.progress.connect(self.progress_bar.update_value)
        self.worker.status.connect(lambda msg: self.statusLabel.setText(msg))
        self.worker.finished.connect(self.handle_finished)

        self.worker.start()

    def check_ready(self):
        if self.selected_images and self.output_folder:
            self.startBtn.setEnabled(True)
            self.statusLabel.setText(
                f"Ready to process {len(self.selected_images)} images."
            )

    def handle_cancel(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.requestInterruption()
            self.statusLabel.setText("Cancelling...")

    def clear_list(self):
        self.imageList.clear()
        self.selected_images = []
        self.startBtn.setEnabled(False)
        self.statusLabel.setText("Image list cleared.")

    def handle_finished(self):
        self.statusLabel.setText("Processing complete!")
        self.progress_bar.hide()
        self.progress_bar.update_value(0)

        self.cancelBtn.hide()
        self.cancelBtn.setEnabled(False)

        self.imageList.clear()
        self.selected_images = []

        self.selectImagesBtn.setEnabled(True)
        self.selectFolderBtn.setEnabled(True)
        self.startBtn.setEnabled(False)

        self.open_output_folder()


    def open_output_folder(self):
        if not self.output_folder:
            return

        system = platform.system()

        try:
            if system == "Darwin":   # macOS
                subprocess.Popen(["open", self.output_folder])

            elif system == "Windows":
                subprocess.Popen(["explorer", self.output_folder])

            elif system == "Linux":
                subprocess.Popen(["xdg-open", self.output_folder])

        except Exception as e:
            self.statusLabel.setText(f"Could not open folder: {e}")

