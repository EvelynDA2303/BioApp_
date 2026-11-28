
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QWidget
import Recursos.bioapp_rc


class VentanaBienvenida(QMainWindow):
    def __init__(self):
        super().__init__()

        ruta = os.path.join(os.path.dirname(__file__), "bienvenida.ui")
        uic.loadUi(ruta, self)


class VentanaLogin(QWidget):
    def __init__(self):
        super().__init__()

        ruta = os.path.join(os.path.dirname(__file__), "login.ui")
        uic.loadUi(ruta, self)

class VentanaMenuRol(QMainWindow):
    def __init__(self):
        super().__init__()

        ruta = os.path.join(os.path.dirname(__file__), "menurol.ui")
        uic.loadUi(ruta, self)
