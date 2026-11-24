
class ControladorVentanas:
    def __init__(self, ventana_bienvenida, ventana_login):
        self.ventana_bienvenida = ventana_bienvenida
        self.ventana_login = ventana_login

        self.ventana_bienvenida.comenzarButton.clicked.connect(self.abrir_login)

    def abrir_login(self):
        self.ventana_bienvenida.hide()
        self.ventana_login.show()
