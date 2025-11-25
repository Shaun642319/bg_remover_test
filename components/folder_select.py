from PySide6.QtWidgets import QFileDialog

class FolderSelector:
    def select_folder(self, parent=None):
        folder = QFileDialog.getExistingDirectory(
            parent,
            "Select Output Folder"
        )

        return folder