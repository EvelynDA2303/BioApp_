
import sys
from PyQt5.QtWidgets import QApplication

from Vista.Vista import VentanaBienvenida, VentanaLogin
from Controlador.Controlador import ControladorVentanas


app = QApplication(sys.argv)

ventana_bienvenida = VentanaBienvenida()
ventana_login = VentanaLogin()

controlador = ControladorVentanas(ventana_bienvenida, ventana_login)

ventana_bienvenida.show()

sys.exit(app.exec_())
