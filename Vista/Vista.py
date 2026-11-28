
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog
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

class VentanaDatosDICOM(QDialog):
    def __init__(self):
        super().__init__()
        ruta = os.path.join(os.path.dirname(__file__), "datos_dicom.ui")
        uic.loadUi(ruta, self)


class VentanaProcesamiento(QDialog):
    def __init__(self):
        super().__init__()
        ruta = os.path.join(os.path.dirname(__file__), "procesamiento.ui")
        uic.loadUi(ruta, self)


class VentanaReconstruccion3D(QDialog):
    def __init__(self):
        super().__init__()
        ruta = os.path.join(os.path.dirname(__file__), "reconstruccion_3d.ui")
        uic.loadUi(ruta, self)


class VentanaAnalisisCSV(QDialog):
    def __init__(self):
        super().__init__()
        ruta = os.path.join(os.path.dirname(__file__), "analisis_csv.ui")
        uic.loadUi(ruta, self)


class VentanaAnalisisMAT(QDialog):
    def __init__(self):
        super().__init__()
        ruta = os.path.join(os.path.dirname(__file__), "analisis_mat.ui")
        uic.loadUi(ruta, self)
