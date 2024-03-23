import sys
from queue import Queue
from time import sleep
from gpt4all import GPT4All
from PyQt5 import QtWidgets, uic, QtCore, QtTest
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QComboBox, QTextEdit, QTextBrowser, QPushButton, QMainWindow

q = Queue()

class ChatBot(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    end = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        with self.model.chat_session():
            while True:
                prompt = q.get(block=True, timeout=None)
                for token in self.model.generate(prompt, streaming=True):
                    self.progress.emit(token)
                self.finished.emit()
            self.end.emit()


class Window(QMainWindow):

    def __init__(self):
        super(Window, self).__init__() # Call the inherited classes __init__ method
        self.available_models = [
            "orca-2-7b.Q4_0.gguf",
            "orca-2-13b.Q4_0.gguf",
            "orca-mini-3b-gguf2-q4_0.gguf"
        ]
        self.model = None
        self.current_model = None
        self.new_session = True

        self.init_ui()
        self.show() # Show the GUI

    def init_ui(self):
        # set width and height
        self.setWindowTitle("LLM Chatbot")
        self.setFixedHeight(1080)
        self.setFixedWidth(960)

        # initialize widgets
        self.comboBox = QComboBox(self)
        self.inputBox = QTextEdit("", self)
        self.responseBox = QTextBrowser(self)
        self.genBtn = QPushButton(text="Generate Response", parent=self)
        self.clearInputBtn = QPushButton(text="Clear Input", parent=self)
        self.clearResponseBtn = QPushButton(text="Clear Response", parent=self)
        self.newSessionBtn = QPushButton(text="New Session", parent=self)

        # ---------------------------------
        # Set position and size for widgets
        # ---------------------------------
        # combo box
        self.comboBox.setGeometry(10, 10, 400, 50)
        self.comboBox.addItems(self.available_models)
        self.comboBox.currentIndexChanged.connect(self.comboBoxChanged)
        self.current_model = self.available_models[self.comboBox.currentIndex()]
        
        # new session button
        self.newSessionBtn.setGeometry(650, 10, 300, 50)
        self.newSessionBtn.clicked.connect(self.newSessionBtnClicked)

        # input box
        self.inputBox.setGeometry(10, 70, 940, 335)
        self.inputBox.setPlaceholderText("Message me")

        # response box
        self.responseBox.setGeometry(10, 475, 940, 535)
        self.responseBox.setPlaceholderText("Here are the responses")

        # generate button
        self.genBtn.setGeometry(650, 415, 300, 50)
        self.genBtn.clicked.connect(self.genBtnClicked)

        # clear input button
        self.clearInputBtn.setGeometry(10, 415, 300, 50)
        self.clearInputBtn.clicked.connect(self.clearInputBtnClicked)

        # clear response button
        self.clearResponseBtn.setGeometry(330, 1020, 300, 50)
        self.clearResponseBtn.clicked.connect(self.clearResponseBtnClicked)

    def newSessionBtnClicked(self):
        self.new_session = True
        self.inputBox.clear()
        self.responseBox.clear()
        self.worker.end.emit()

    def comboBoxChanged(self, idx):
        self.model = None
        self.current_model = self.available_models[idx]
        self.worker = None
        self.new_session = True
        self.inputBox.clear()
        self.responseBox.clear()
        self.worker.end.emit()

    def genInit(self):
        if self.model is None:
            self.model = GPT4All(self.current_model, model_path="./models")
        self.worker = ChatBot(self.model)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        
        self.worker.progress.connect(self.stream_response)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.end.connect(self.thread.quit)
        self.worker.end.connect(self.worker.deleteLater)
        self.thread.start()

        self.genBtn.setEnabled(False)
        self.worker.finished.connect(
            lambda: self.genBtn.setEnabled(True)
        )
        self.comboBox.setEnabled(False)
        self.worker.finished.connect(
            lambda: self.comboBox.setEnabled(True)
        )
        self.newSessionBtn.setEnabled(False)
        self.worker.finished.connect(
            lambda: self.newSessionBtn.setEnabled(True)
        )

    def genBtnClicked(self):
        if self.new_session:
            self.genInit()
            self.new_session = False
            self.responseBox.insertPlainText("=" * 50 + "\n")
        else:
            self.responseBox.insertPlainText("\n" + "=" * 50 + "\n")
        prompt = self.inputBox.toPlainText()
        q.put(prompt)
        self.responseBox.insertPlainText(f"Q: {prompt}\nA: ")
        self.inputBox.clear()

    def stream_response(self, token):
        self.responseBox.insertPlainText(token)

    def clearInputBtnClicked(self):
        self.inputBox.clear()

    def clearResponseBtnClicked(self):
        self.responseBox.clear()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window() # Create an instance of our class
    app.exec_() # Start the application
