from PySide6.QtWidgets import QProgressBar

class ProgressBar(QProgressBar):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(True)

    def update_value(self, value):
        self.setValue(value)
