import io, unicodedata
import numpy as np
import pandas as pd
import scipy.io as sio
FS=250

def suma(a, b, c, d):
    return a + b + c + d

def resta(a, b, c, d):
    return a - b - c - d

def multiplicacion(a, b, c, d):
    return a * b * c * d

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
        self.__tabla = tabla.set_index(self.__tiempo)
        self.__columnas = self.__tabla.columns

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
            t = ''.join((ch for ch in t if unicodedata.category(ch) != 'Mn'))
            return t.strip().lower()
        buscados = [limpiar(n) for n in nombres]
        for c in tabla.columns:
            if limpiar(c) in buscados:
                return c
        return None

    def __str__(self):
        buffer = io.StringIO()
        self.__tabla.info(buf=buffer)
        return '\n===== INFORMACION DEL ARCHIVO CSV =====\nArchivo: {}\n{}\n===== ESTADISTICOS (describe) =====\n{}\n\nCondiciones: {}\nCanales disponibles: {}'.format(self.__ruta, buffer.getvalue(), self.__tabla.describe().to_string(), self.verCondiciones(), self.verCanales())

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

    def diferenciaInterhemisferica(self, canal1, canal2, nombre):
        nombre = str(nombre).strip()
        if nombre == '':
            raise ValueError('El nombre de la nueva columna no puede estar vacio.')
        if nombre == self.__condicion:
            raise ValueError('Ese nombre esta reservado para la condicion.')
        if nombre in self.__tabla.columns and nombre not in self.__diferencias:
            raise ValueError("Ya existe una columna del archivo con el nombre '{}'.".format(nombre))
        self.__tabla[nombre] = self.__tabla[canal1] - self.__tabla[canal2]
        if nombre not in self.__diferencias:
            self.__diferencias.append(nombre)
        return self.__tabla[nombre]

class ArchivoMAT:

    def __init__(self, ruta):
        self.__ruta = ruta
        self.__datos = sio.loadmat(ruta)
        self.__variables = sio.whosmat(ruta)
        self.__llaves = list(self.__datos.keys())
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
        texto += 'Llaves del diccionario: {}'.format(self.__llaves)
        return texto

    def verLlaves(self):
        return self.__llaves

    def verVariables(self):
        return self.__variables

    def cargarMatriz(self, numero):
        nombre = self.__variables[numero][0]
        matriz = self.__datos[nombre]
        if not isinstance(matriz, np.ndarray) or not np.issubdtype(matriz.dtype, np.number):
            raise ValueError("La variable '{}' no es una matriz numerica.".format(nombre))
        self.__matriz = matriz
        self.__nombreVar = nombre
        return self.__matriz

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
import cv2
from contextlib import closing
import sqlite3, hashlib, hmac, secrets, json
from pathlib import Path
from datetime import datetime

def normalizarUint8(corte):
    corte=np.nan_to_num(np.asarray(corte,dtype=np.float32))
    return cv2.normalize(corte,None,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)

class SerieDicom:
    ORIENTACIONES=('transversal','coronal','sagital')
    def __init__(self,nombre,ruta):
        self.nombre=nombre
        ruta=Path(ruta)
        if ruta.is_dir():
            from pydicom import dcmread
            datasets=[]
            for archivo in sorted(ruta.iterdir()):
                if archivo.is_file():
                    try: ds=dcmread(archivo)
                    except Exception: continue
                    if 'PixelData' in ds: datasets.append(ds)
            if not datasets: raise ValueError('No hay DICOM en la carpeta seleccionada')
            if len({str(d.get('SeriesInstanceUID','')) for d in datasets})>1: raise ValueError('Seleccione una carpeta con una sola serie')
            ref=datasets[0]
            orient=np.asarray(ref.ImageOrientationPatient,float)
            normal=np.cross(orient[:3],orient[3:]); posiciones=lambda d: float(np.dot(d.ImagePositionPatient,normal))
            datasets.sort(key=posiciones)
            if any(not np.allclose(d.ImageOrientationPatient,orient) or not np.allclose(d.PixelSpacing,ref.PixelSpacing) for d in datasets): raise ValueError('Geometría inconsistente')
            diferencias=np.diff([posiciones(d) for d in datasets]); esp=float(np.median(diferencias)) if len(diferencias) else float(ref.SliceThickness)
            if esp<=0 or (len(diferencias) and not np.allclose(diferencias,esp,rtol=.05,atol=.001)): raise ValueError('Espaciado irregular')
            direcciones=np.stack([normal,orient[3:],orient[:3]])
            ejes=np.argmax(np.abs(direcciones),axis=1)
            if len(set(ejes))!=3 or not np.allclose(np.max(np.abs(direcciones),axis=1),1,atol=.001): raise ValueError('Serie oblicua: requiere remuestreo espacial')
            self.matrices=np.stack([d.pixel_array.astype(np.float32)*float(d.get('RescaleSlope',1))+float(d.get('RescaleIntercept',0)) for d in datasets])
            orden=[list(ejes).index(i) for i in (2,1,0)]
            espacios=np.array([esp,*map(float,ref.PixelSpacing)])[orden]
            self.matrices=self.matrices.transpose(orden)
            for i,j in enumerate(orden):
                if direcciones[j,ejes[j]]<0: self.matrices=np.flip(self.matrices,axis=i)
            self.voxel=(float(espacios[1]),float(espacios[2]),float(espacios[0])); self.paciente=str(ref.get('PatientName','')); self.modalidad=str(ref.get('Modality',''))
        elif ruta.name.lower().endswith(('.nii','.nii.gz')):
            import nibabel as nib
            img=nib.as_closest_canonical(nib.load(str(ruta))); a=img.get_fdata(dtype=np.float32)
            if a.ndim!=3 or not np.allclose(img.affine[:3,:3],np.diag(np.diag(img.affine[:3,:3])),atol=.001): raise ValueError('NIFTI debe ser 3D y alineado')
            self.matrices=a.transpose(2,1,0); x,y,z=img.header.get_zooms()[:3]; self.voxel=(float(y),float(x),float(z)); self.paciente='No disponible'; self.modalidad='NIFTI'
        else:
            a=cv2.imread(str(ruta),cv2.IMREAD_GRAYSCALE)
            if a is None: raise ValueError('Imagen inválida')
            self.matrices=a[None,:,:]; self.voxel=(1.,1.,1.); self.paciente='No disponible'; self.modalidad='Imagen 2D (espaciado en píxeles)'
        if self.matrices.ndim!=3: raise ValueError('Se requieren cortes 2D monocanal')
        self.volumen=np.stack([cv2.resize(a,None,fx=2,fy=2) for a in self.matrices]); self.voxelEscalado=(self.voxel[0]/2,self.voxel[1]/2,self.voxel[2])
    def verInformacion(self):
        return {'Paciente':self.paciente,'Modalidad':self.modalidad,'Filas':self.matrices.shape[1],'Columnas':self.matrices.shape[2],'Voxel original':self.voxel,'Voxel escalado':self.voxelEscalado,'Volumen':self.volumen.shape}
    def verCorte(self,orientacion,indice,angulo=0):
        eje=self.ORIENTACIONES.index(orientacion); a=normalizarUint8(np.take(self.volumen,indice,axis=eje)); y,x,z=self.voxelEscalado; alto,ancho=[(y,x),(z,x),(z,y)][eje]
        if angulo:
            a=cv2.resize(a,(a.shape[1],max(1,round(a.shape[0]*alto/ancho)))); alto=ancho
            h,w=a.shape; a=cv2.warpAffine(a,cv2.getRotationMatrix2D(((w-1)/2,(h-1)/2),angulo,1),(w,h))
        return a,alto/ancho
    def ecualizarCorte(self,a): return cv2.equalizeHist(a)
    def segmentarCorte(self,a,umbral,kernel,tipo):
        _,b=cv2.threshold(a,umbral,255,tipo)
        return cv2.morphologyEx(b,cv2.MORPH_OPEN,np.ones((kernel,kernel),np.uint8))

def cargarLlave(archivo,llave):
    a=archivo._ArchivoMAT__datos[llave]
    if not isinstance(a,np.ndarray) or not np.issubdtype(a.dtype,np.number) or np.iscomplexobj(a) or a.ndim!=3: raise ValueError('No es un arreglo, vuelva a intentarlo')
    archivo._ArchivoMAT__matriz=a
    archivo._ArchivoMAT__nombreVar=llave
    return a

def operarCanales(archivo,funcion,canales,pmin,pmax):
    a=archivo.convertir2D()
    if not 0<=pmin<=pmax<a.shape[1] or len(set(canales))!=4: raise ValueError('Rango inválido o canales repetidos')
    datos=a[canales,pmin:pmax+1].astype(float)
    return np.arange(pmin,pmax+1)/FS,datos,funcion(*datos)

def estadisticos3D(archivo,eje1,eje2):
    if archivo is None or archivo.verMatriz() is None: raise ValueError('Primero seleccione una matriz')
    if eje1==eje2: raise ValueError('Seleccione dos ejes diferentes')
    a=archivo.verMatriz(); return np.mean(a,axis=(eje1,eje2)),np.std(a,axis=(eje1,eje2))
