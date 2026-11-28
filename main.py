import sys
import os
from PyQt5.QtWidgets import QApplication

from Vista.Vista import (VentanaBienvenida, VentanaLogin, VentanaMenuRol, VentanaDatosDICOM, VentanaProcesamiento, VentanaReconstruccion3D, VentanaAnalisisCSV, VentanaAnalisisMAT)
from Controlador.Controlador import ControladorVentanas
from BaseDatos.BaseDatos import BaseDatos


app = QApplication(sys.argv)

ventana_bienvenida = VentanaBienvenida()
ventana_login = VentanaLogin()
ventana_menu = VentanaMenuRol() 
ventana_dicom = VentanaDatosDICOM()
ventana_procesamiento = VentanaProcesamiento()
ventana_3d = VentanaReconstruccion3D()
ventana_csv = VentanaAnalisisCSV()
ventana_mat = VentanaAnalisisMAT()

ruta_bd = os.path.join(os.path.dirname(__file__), "BaseDatos", "bioapp.db")
base_datos = BaseDatos(ruta_bd)

controlador = ControladorVentanas(
    ventana_bienvenida,
    ventana_login,
    base_datos,
    ventana_menu,
    ventana_dicom,
    ventana_procesamiento,
    ventana_3d,
    ventana_csv,
    ventana_mat
)

ventana_bienvenida.show()

sys.exit(app.exec_())

