from PyQt5.QtWidgets import QMessageBox


class ControladorVentanas:
    def __init__(self, ventana_bienvenida, ventana_login, base_datos, ventana_menu):
        self.ventana_bienvenida = ventana_bienvenida
        self.ventana_login = ventana_login
        self.base_datos = base_datos
        self.ventana_menu = ventana_menu

        self.ventana_bienvenida.comenzarButton.clicked.connect(self.abrir_login)
        self.ventana_login.loginButton.clicked.connect(self.iniciar_sesion)

    def abrir_login(self):
        self.ventana_bienvenida.hide()
        self.ventana_login.show()

    def iniciar_sesion(self):
        nombre = self.ventana_login.identificationInput.text().strip()
        clave = self.ventana_login.passwordInput.text()

        try:
            datos = self.base_datos.ingresar(nombre, clave)

            id_usuario, nombre, rol, fecha = datos

            self.ventana_menu.usuarioTextoLabel.setText(nombre)
            self.ventana_menu.rolTextoLabel.setText(rol)
            self.ventana_menu.ingresoTextoLabel.setText(fecha)

            if rol == "imagenes":
                self.ventana_menu.menuStackedWidget.setCurrentWidget(
                    self.ventana_menu.paginaImagenes
                )

            elif rol == "senales":
                self.ventana_menu.menuStackedWidget.setCurrentWidget(
                    self.ventana_menu.paginaSenales
                )

            else:
                QMessageBox.warning(
                    self.ventana_login,
                    "Error",
                    "El usuario no tiene un rol válido."
                )
                return

            self.ventana_login.hide()
            self.ventana_menu.show()

        except ValueError as error:
            QMessageBox.warning(
                self.ventana_login,
                "Error de inicio de sesión",
                str(error)
            )
