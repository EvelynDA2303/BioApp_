import io
import unicodedata
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import scipy.io as sio

FS = 250


def suma(a, b, c, d):
    return a + b + c + d


def resta(a, b, c, d):
    return a - b - c - d


def multiplicacion(a, b, c, d):
    return a * b * c * d


def normalizarUint8(corte):
    """Lleva un corte a uint8 (0 a 255) para poder mostrarlo y procesarlo con OpenCV."""
    corte = np.nan_to_num(np.asarray(corte, dtype=np.float32))
    return cv2.normalize(corte, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)


class ArchivoCSV:

    def __init__(self, ruta):
        self.__ruta = ruta
        self.__tiempo = 'Tiempo'
        self.__condicion = 'Condición'
        self.__diferencias = []
        tabla = self.__leer(ruta)
        tabla = tabla.dropna(axis=1, how='all')
        colTiempo = self.__buscarColumna(tabla, ['Tiempo', 'time_ms', 'time', 'tiempo_ms'])
        colCond = self.__buscarColumna(tabla, ['Condición', 'condition', 'condicion'])
        if colTiempo is None:
            raise ValueError('El CSV no tiene una columna de tiempo (Tiempo / time_ms).')
        if colCond is None:
            raise ValueError('El CSV no tiene una columna de condicion (Condición / condition).')
        tabla = tabla.rename(columns={colTiempo: self.__tiempo, colCond: self.__condicion})
        for c in tabla.columns:
            if c != self.__condicion and (not pd.api.types.is_numeric_dtype(tabla[c])):
                conv = pd.to_numeric(tabla[c].astype(str).str.replace(',', '.', regex=False), errors='coerce')
                if conv.notna().mean() > 0.9:
                    tabla[c] = conv
        tabla[self.__tiempo] = pd.to_numeric(tabla[self.__tiempo], errors='raise')
        if not np.isfinite(tabla[self.__tiempo]).all():
            raise ValueError('Tiempo invalido')
        self.__tabla = tabla.set_index(self.__tiempo)

    def __leer(self, ruta):
        if str(ruta).lower().endswith('.xlsx'):
            return pd.read_excel(ruta)
        for enc in ('utf-8-sig', 'latin-1'):
            try:
                tabla = pd.read_csv(ruta, sep=';', encoding=enc)
                if tabla.shape[1] == 1:
                    tabla = pd.read_csv(ruta, sep=None, engine='python', encoding=enc)
                tabla.columns = [str(c).strip() for c in tabla.columns]
                return tabla
            except UnicodeDecodeError:
                continue
        raise ValueError('No se pudo leer el archivo (codificacion desconocida).')

    def __buscarColumna(self, tabla, nombres):

        def limpiar(t):
            t = unicodedata.normalize('NFD', str(t))
            t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
            return t.strip().lower()

        buscados = [limpiar(n) for n in nombres]
        for c in tabla.columns:
            if limpiar(c) in buscados:
                return c
        return None

    def __str__(self):
        buffer = io.StringIO()
        self.__tabla.info(buf=buffer)
        return '\n===== INFORMACION DEL ARCHIVO CSV =====\nArchivo: {}\n{}\n===== ESTADISTICOS (describe) =====\n{}\n\nCondiciones: {}\nCanales disponibles: {}'.format(
            self.__ruta, buffer.getvalue(), self.__tabla.describe().to_string(),
            self.verCondiciones(), self.verCanales())

    def verTabla(self):
        return self.__tabla

    def verCol(self):
        return self.__tabla.columns

    def verCondiciones(self):
        return self.__tabla[self.__condicion].unique().tolist()

    def verCanales(self):
        """Columnas numericas (canales y diferencias creadas), sin la condicion."""
        noCanales = [self.__condicion.lower(), 'subject', 'sujeto', 'paciente', 'id']
        canales = []
        for c in self.__tabla.columns:
            if str(c).strip().lower() in noCanales:
                continue
            if pd.api.types.is_numeric_dtype(self.__tabla[c]):
                canales.append(c)
        return canales

    def filtrarCondicion(self, condicion):
        """Devuelve solo las filas de la condicion indicada (sirve para el stem y el histograma)."""
        if condicion not in self.verCondiciones():
            raise ValueError("La condicion '{}' no existe en el archivo.".format(condicion))
        return self.__tabla[self.__tabla[self.__condicion] == condicion]

    def diferenciaInterhemisferica(self, canal1, canal2, nombre):
        if canal1 not in self.verCanales() or canal2 not in self.verCanales() or canal1 == canal2:
            raise ValueError('Seleccione dos canales numericos diferentes')
        nombre = str(nombre).strip()
        if nombre == '':
            raise ValueError('El nombre de la nueva columna no puede estar vacio.')
        if nombre in (self.__condicion, self.__tiempo):
            raise ValueError('Ese nombre esta reservado para la condicion.')
        if nombre in self.__tabla.columns and nombre not in self.__diferencias:
            raise ValueError("Ya existe una columna del archivo con el nombre '{}'.".format(nombre))
        self.__tabla[nombre] = self.__tabla[canal1] - self.__tabla[canal2]
        if nombre not in self.__diferencias:
            self.__diferencias.append(nombre)
        return self.__tabla[nombre]

    def exportar(self, ruta):
        """Guarda la tabla, con las diferencias creadas, en un archivo .csv o .xlsx."""
        ruta = str(ruta)
        tabla = self.__tabla.reset_index()
        if ruta.lower().endswith('.xlsx'):
            tabla.to_excel(ruta, index=False)
        elif ruta.lower().endswith('.csv'):
            tabla.to_csv(ruta, sep=';', index=False, encoding='utf-8-sig')
        else:
            raise ValueError('Solo se puede exportar a .csv o .xlsx')


class ArchivoMAT:

    def __init__(self, ruta, fs=FS):
        self.__ruta = ruta
        if not np.isfinite(fs) or fs <= 0:
            raise ValueError('Frecuencia invalida')
        self.__fs = fs
        self.__datos = sio.loadmat(ruta)
        self.__variables = sio.whosmat(ruta)
        self.__matriz = None
        self.__nombreVar = None

    def __str__(self):
        ancho = max([len(v[0]) for v in self.__variables] + [8])
        linea = '-' * (ancho + 44)
        texto = '\n===== VARIABLES DEL ARCHIVO MAT =====\n'
        texto += 'Archivo: {}\n'.format(self.__ruta)
        texto += linea + '\n'
        texto += '{:<4}{:<{w}}  {:<18}{}\n'.format('N°', 'Variable', 'Dimensiones', 'Tipo', w=ancho)
        texto += linea + '\n'
        for i, v in enumerate(self.__variables):
            texto += '{:<4}{:<{w}}  {:<18}{}\n'.format(i, v[0], str(v[1]), v[2], w=ancho)
        texto += linea + '\n'
        texto += 'Llaves del archivo: {}'.format(self.verLlaves())
        return texto

    def verLlaves(self):
        """Nombres de las variables reales del archivo (sin __header__, __version__ ni __globals__)."""
        return [v[0] for v in self.__variables]

    def verVariables(self):
        return self.__variables

    def verFs(self):
        return self.__fs

    def cargarLlave(self, llave):
        """Carga la variable elegida. Si no es un arreglo numerico lanza ValueError."""
        matriz = self.__datos.get(llave)
        if not isinstance(matriz, np.ndarray) or not np.issubdtype(matriz.dtype, np.number) or np.iscomplexobj(matriz) or matriz.ndim != 3 or not matriz.size:
            raise ValueError('No es un arreglo, vuelva a intentarlo')
        self.__matriz = matriz
        self.__nombreVar = llave
        return self.__matriz

    def cargarMatriz(self, numero):
        """Igual que cargarLlave pero eligiendo la variable por su posicion en la lista."""
        return self.cargarLlave(self.__variables[numero][0])

    def verMatriz(self):
        return self.__matriz

    def verNombreVariable(self):
        return self.__nombreVar

    def convertir2D(self):
        """Devuelve la matriz como (canales, puntos*ensayos). No modifica la original."""
        if self.__matriz is None:
            raise ValueError('Primero debe cargar una variable.')
        if self.__matriz.ndim == 3:
            canales, puntos, ensayos = self.__matriz.shape
            return np.reshape(self.__matriz, (canales, puntos * ensayos), order='F')
        if self.__matriz.ndim == 1:
            return self.__matriz.reshape(1, -1)
        return self.__matriz

    def operarCanales(self, funcion, canales, pmin, pmax):
        """Aplica suma, resta o multiplicacion a 4 canales entre dos puntos.

        Devuelve (tiempo en segundos, datos de los 4 canales, resultado)."""
        a = self.convertir2D()
        if len(canales) != 4 or len(set(canales)) != 4:
            raise ValueError('Debe elegir 4 canales diferentes')
        if min(canales) < 0 or max(canales) >= a.shape[0]:
            raise ValueError('Hay un canal fuera de rango (0 a {})'.format(a.shape[0] - 1))
        if not 0 <= pmin <= pmax < a.shape[1]:
            raise ValueError('Rango de puntos invalido (0 a {})'.format(a.shape[1] - 1))
        datos = a[canales, pmin:pmax + 1].astype(float)
        tiempo = np.arange(pmin, pmax + 1) / self.__fs
        return tiempo, datos, funcion(*datos)

    def estadisticos3D(self, eje1, eje2):
        """Promedio y desviacion estandar de la matriz 3D original a lo largo de dos ejes."""
        if self.__matriz is None:
            raise ValueError('Primero seleccione una matriz')
        if self.__matriz.ndim != 3:
            raise ValueError('La matriz debe ser 3D para calcular promedio y desviacion')
        if eje1 not in (0, 1, 2) or eje2 not in (0, 1, 2):
            raise ValueError('Los ejes validos son 0, 1 y 2')
        if eje1 == eje2:
            raise ValueError('Seleccione dos ejes diferentes')
        promedio = np.mean(self.__matriz, axis=(eje1, eje2))
        desviacion = np.std(self.__matriz, axis=(eje1, eje2))
        return promedio, desviacion


class SerieDicom:
    ORIENTACIONES = ('transversal', 'coronal', 'sagital')

    def __init__(self, nombre, ruta):
        self.__nombre = nombre
        self.__avisos = []
        self.__meta = {}
        self.__paciente = 'No disponible'
        self.__modalidad = ''
        self.__filas = None
        self.__columnas = None
        ruta = Path(ruta)
        if ruta.is_dir():
            self.__cargarCarpeta(ruta)
        elif ruta.name.lower().endswith(('.nii', '.nii.gz')):
            self.__cargarNifti(ruta)
        else:
            self.__cargarImagen(ruta)
        if self.__matriz.ndim != 3:
            raise ValueError('Se requieren cortes 2D de un solo canal')
        if self.__filas is None:
            self.__filas = self.__matriz.shape[1]
            self.__columnas = self.__matriz.shape[2]
        self.__escalar()

    def __str__(self):
        texto = '\n===== SERIE {} =====\n'.format(self.__nombre)
        for clave, valor in self.verInformacion().items():
            texto += '{}: {}\n'.format(clave, valor)
        for aviso in self.__avisos:
            texto += 'Aviso: {}\n'.format(aviso)
        return texto

    # ---------------- carga ----------------
    def __cargarCarpeta(self, ruta):
        from pydicom import dcmread
        datasets = []
        for archivo in sorted(ruta.iterdir()):
            if not archivo.is_file():
                continue
            try:
                ds = dcmread(archivo)
            except Exception:
                continue
            if 'PixelData' in ds:
                datasets.append(ds)
        if not datasets:
            raise ValueError('No hay archivos DICOM en la carpeta seleccionada')
        datasets = self.__unaSerie(datasets)
        ref = datasets[0]

        # Orden de los cortes: por posicion en el espacio si el DICOM la trae
        orient = ref.get('ImageOrientationPatient', None)
        tienePosicion = orient is not None and all('ImagePositionPatient' in d for d in datasets)
        diferencias = np.array([])
        if tienePosicion:
            orient = np.asarray(orient, dtype=float)
            normal = np.cross(orient[:3], orient[3:])
            posiciones = np.array([float(np.dot(d.ImagePositionPatient, normal)) for d in datasets])
            orden = np.argsort(posiciones)
            datasets = [datasets[i] for i in orden]
            diferencias = np.diff(posiciones[orden])
            if any('ImageOrientationPatient' not in d or not np.allclose(d.ImageOrientationPatient, orient, atol=0.001) for d in datasets):
                raise ValueError('Los cortes tienen orientaciones diferentes')
        else:
            datasets.sort(key=lambda d: int(d.get('InstanceNumber', 0)))
            self.__avisos.append('El DICOM no trae posicion espacial, los cortes se ordenaron por InstanceNumber')

        # Espaciado entre cortes
        esp = float(np.median(diferencias)) if len(diferencias) else 0.0
        if esp <= 0:
            esp = float(ref.get('SpacingBetweenSlices', ref.get('SliceThickness', 1.0)))
            if len(datasets) > 1:
                self.__avisos.append('No se pudo calcular el espaciado entre cortes, se uso {} mm'.format(esp))
        elif not np.allclose(diferencias, esp, rtol=0.05, atol=0.001):
            raise ValueError('Espaciado irregular entre cortes')

        ps = [float(x) for x in ref.get('PixelSpacing', [1.0, 1.0])]
        if 'PixelSpacing' not in ref:
            self.__avisos.append('El DICOM no trae PixelSpacing, se uso 1 mm')

        # Pixeles en unidades reales (pendiente e intercepto)
        cortes = []
        for d in datasets:
            pendiente = float(d.get('RescaleSlope', 1))
            intercepto = float(d.get('RescaleIntercept', 0))
            cortes.append(d.pixel_array.astype(np.float32) * pendiente + intercepto)
        if len({c.shape for c in cortes}) > 1:
            raise ValueError('Los cortes de la carpeta tienen tamaños diferentes')
        matriz = np.stack(cortes)
        if matriz.ndim != 3:
            raise ValueError('Se requieren cortes 2D de un solo canal')

        # Si la adquisicion esta alineada con los ejes, se reorienta a (z, y, x)
        ortogonal = False
        if tienePosicion:
            direcciones = np.stack([normal, orient[3:], orient[:3]])
            ejes = np.argmax(np.abs(direcciones), axis=1)
            ortogonal = len(set(ejes)) == 3 and np.allclose(np.max(np.abs(direcciones), axis=1), 1, atol=0.001)
        if ortogonal:
            orden = [list(ejes).index(i) for i in (2, 1, 0)]
            espacios = np.array([esp, ps[0], ps[1]])[orden]
            matriz = matriz.transpose(orden)
            for i, j in enumerate(orden):
                if direcciones[j, ejes[j]] < 0:
                    matriz = np.flip(matriz, axis=i)
            self.__voxel = (float(espacios[1]), float(espacios[2]), float(espacios[0]))
        else:
            if tienePosicion:
                raise ValueError('Serie oblicua: requiere remuestreo espacial')
            self.__voxel = (ps[0], ps[1], esp)

        self.__matriz = matriz
        self.__meta = {k: str(ref.get(k, 'No disponible')) for k in ('PatientID','PatientSex','PatientBirthDate','StudyDate','StudyDescription','InstitutionName')}
        self.__paciente = str(ref.get('PatientName', '')) or 'No disponible'
        self.__modalidad = str(ref.get('Modality', ''))
        self.__filas = int(ref.Rows)
        self.__columnas = int(ref.Columns)

    def __unaSerie(self, datasets):
        series = {}
        for d in datasets:
            series.setdefault(str(d.get('SeriesInstanceUID', '')), []).append(d)
        if len(series) == 1:
            return datasets
        uid = max(series, key=lambda u: len(series[u]))
        self.__avisos.append('La carpeta tiene {} series, se cargo la que tiene mas cortes'.format(len(series)))
        return series[uid]

    def __cargarNifti(self, ruta):
        import nibabel as nib
        img = nib.as_closest_canonical(nib.load(str(ruta)))
        a = img.get_fdata(dtype=np.float32)
        if a.ndim == 4:
            a = a[..., 0]
            self.__avisos.append('El NIFTI es 4D, se uso el primer volumen')
        if a.ndim != 3:
            raise ValueError('El NIFTI debe ser un volumen 3D')
        m = img.affine[:3, :3]
        if not np.allclose(m, np.diag(np.diag(m)), atol=0.001):
            raise ValueError('NIFTI oblicuo: requiere remuestreo espacial')
        x, y, z = img.header.get_zooms()[:3]
        self.__matriz = a[::-1, ::-1, :].transpose(2, 1, 0)
        self.__voxel = (float(y), float(x), float(z))
        self.__modalidad = 'NIFTI'

    def __cargarImagen(self, ruta):
        a = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
        if a is None:
            raise ValueError('Imagen inválida')
        self.__matriz = a[None, :, :]
        self.__voxel = (1.0, 1.0, 1.0)
        self.__modalidad = 'Imagen 2D (espaciado en píxeles)'

    def __escalar(self):
        """Escala cada corte al doble de su tamaño. El voxel en el plano queda a la mitad."""
        self.__volumen = np.stack([cv2.resize(corte, None, fx=2, fy=2) for corte in self.__matriz])
        alto, largo, ancho = self.__voxel
        self.__voxelEscalado = (alto / 2, largo / 2, ancho)

    # ---------------- consulta ----------------
    def verNombre(self):
        return self.__nombre

    def verPaciente(self):
        return self.__paciente

    def verModalidad(self):
        return self.__modalidad

    def verFilas(self):
        return self.__filas

    def verColumnas(self):
        return self.__columnas

    def verVoxel(self):
        """Tamaño del voxel original en mm: (alto, largo, ancho)."""
        return self.__voxel

    def verVoxelEscalado(self):
        return self.__voxelEscalado

    def verMatriz(self):
        """Matriz de pixeles original (cortes, filas, columnas)."""
        return self.__matriz

    def verVolumen(self):
        """Volumen con cada corte escalado al doble."""
        return self.__volumen

    def verAvisos(self):
        return self.__avisos

    def verNumeroCortes(self, orientacion):
        return self.__volumen.shape[self.ORIENTACIONES.index(orientacion)]

    def verInformacion(self):
        return {'Paciente': self.__paciente,
                'Modalidad': self.__modalidad,
                'Filas': self.__filas,
                'Columnas': self.__columnas,
                'Voxel original': self.__voxel,
                'Voxel escalado': self.__voxelEscalado,
                'Volumen': self.__volumen.shape, **self.__meta}

    # ---------------- procesamiento ----------------
    def verCorte(self, orientacion, indice, angulo=0):
        """Devuelve (corte en uint8, aspect) del plano elegido. Si hay angulo, rota el corte."""
        eje = self.ORIENTACIONES.index(orientacion)
        if not 0 <= indice < self.__volumen.shape[eje]:
            raise ValueError('El corte {} no existe en el plano {}'.format(indice, orientacion))
        corte = normalizarUint8(np.take(self.__volumen, indice, axis=eje))
        y, x, z = self.__voxelEscalado
        alto, ancho = [(y, x), (z, x), (z, y)][eje]
        if angulo:
            corte = cv2.resize(corte, (corte.shape[1], max(1, round(corte.shape[0] * alto / ancho))))
            alto = ancho
            h, w = corte.shape
            giro = cv2.getRotationMatrix2D(((w - 1) / 2, (h - 1) / 2), angulo, 1)
            corte = cv2.warpAffine(corte, giro, (w, h))
        return corte, alto / ancho

    def ecualizarCorte(self, corte):
        return cv2.equalizeHist(normalizarUint8(corte))

    def segmentarCorte(self, corte, umbral, kernel, tipo):
        if not 0 <= umbral <= 255 or not 1 <= int(kernel) <= 99:
            raise ValueError('Umbral o kernel fuera de rango')
        _, binaria = cv2.threshold(normalizarUint8(corte), umbral, 255, tipo)
        kernel = max(1, int(kernel))
        return cv2.morphologyEx(binaria, cv2.MORPH_OPEN, np.ones((kernel, kernel), np.uint8))


class Sistema:

    def __init__(self):
        self.__archivos = {}

    def ingresarArchivo(self, nombre, archivo):
        self.__archivos[nombre] = archivo

    def verArchivo(self, nombre):
        return self.__archivos.get(nombre, None)

    def verArchivos(self):
        return self.__archivos

    def buscarPorTipo(self, tipo):
        """Devuelve los nombres de los archivos que son de la clase indicada."""
        return [n for n, a in self.__archivos.items() if isinstance(a, tipo)]


# Manejo de tablas generales, independiente de las señales ERP.
class DatosTabulares:
    def __init__(self, ruta):
        ruta = Path(ruta)
        if ruta.suffix.lower() == '.xlsx':
            self.__tabla = pd.read_excel(ruta)
        elif ruta.suffix.lower() == '.csv':
            self.__tabla = pd.read_csv(ruta, sep=None, engine='python')
        else:
            raise ValueError('Formato tabular no soportado')

    def verTabla(self):
        return self.__tabla.copy()

    def exportar(self, ruta):
        exportarTabla(self.__tabla, ruta)

def exportarTabla(tabla, ruta):
    if str(ruta).lower().endswith('.xlsx'):
        tabla.to_excel(ruta, index=False)
    elif str(ruta).lower().endswith('.csv'):
        tabla.to_csv(ruta, index=False, encoding='utf-8-sig')
    else:
        raise ValueError('Seleccione CSV o XLSX')
