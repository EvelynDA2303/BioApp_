from PyQt5.QtWidgets import QMessageBox, QPushButton, QAbstractButton 


class ControladorVentanas:
    def __init__(self, ventana_bienvenida, ventana_login, base_datos, ventana_menu,
             ventana_dicom, ventana_procesamiento, ventana_3d, ventana_csv, ventana_mat):
        self.ventana_bienvenida = ventana_bienvenida
        self.ventana_login = ventana_login
        self.base_datos = base_datos
        self.ventana_menu = ventana_menu
        self.ventana_dicom = ventana_dicom
        self.ventana_procesamiento = ventana_procesamiento
        self.ventana_3d = ventana_3d
        self.ventana_csv = ventana_csv
        self.ventana_mat = ventana_mat

        self.ventana_bienvenida.comenzarButton.clicked.connect(self.abrir_login)
        self.ventana_login.loginButton.clicked.connect(self.iniciar_sesion)

        self.ventana_menu.btnDatosDICOM.clicked.connect(self.abrir_dicom)
        self.ventana_menu.btnProcesamiento.clicked.connect(self.abrir_procesamiento)
        self.ventana_menu.btnReconstruccion3D.clicked.connect(self.abrir_3d)

        self.ventana_menu.analizarGraficasCSVButton.clicked.connect(self.abrir_csv)
        self.ventana_menu.abrirAnalisisMATButton.clicked.connect(self.abrir_mat)

        self.ventana_dicom.btnVolver.clicked.connect(self.ventana_dicom.close)
        self.ventana_procesamiento.btnVolver.clicked.connect(self.ventana_procesamiento.close)
        self.ventana_3d.btnVolver.clicked.connect(self.ventana_3d.close)

        for boton in self.ventana_menu.findChildren(QPushButton, "btnCerrar"):
            boton.clicked.connect(self.volver_login)

        for ventana in [self.ventana_dicom, self.ventana_procesamiento, self.ventana_3d]:
            for boton in ventana.findChildren(QPushButton):
                if boton.objectName() in ["btnCerrar","pushButton"]:
                    boton.clicked.connect(ventana.close)



        self.ventana_dicom.finished.connect(self.mostrar_menu)
        self.ventana_procesamiento.finished.connect(self.mostrar_menu)
        self.ventana_3d.finished.connect(self.mostrar_menu)
        self.ventana_csv.finished.connect(self.mostrar_menu)
        self.ventana_mat.finished.connect(self.mostrar_menu)
        self.ventana_menu.btnVolver.clicked.connect(self.volver_login)

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

    def abrir_dicom(self):
        self.ventana_menu.hide()
        self.ventana_dicom.show()


    def abrir_procesamiento(self):
        self.ventana_menu.hide()
        self.ventana_procesamiento.show()


    def abrir_3d(self):
        self.ventana_menu.hide()
        self.ventana_3d.show()


    def abrir_csv(self):
        self.ventana_menu.hide()
        self.ventana_csv.show()


    def abrir_mat(self):
        self.ventana_menu.hide()
        self.ventana_mat.show()

    def mostrar_menu(self):
        self.ventana_menu.show()

    def volver_login(self):
        self.ventana_menu.hide()
        self.ventana_login.show()