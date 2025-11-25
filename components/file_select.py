from PySide6.QtWidgets import QFileDialog

class ImageSelector:
    def select_images(self, parent=None):
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        return files