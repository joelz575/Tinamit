import json
import socket
from abc import abstractmethod
import sys
import numpy as np
from tinamit.envolt.bf import ModeloBF


class ModeloEnchufe(ModeloBF):
    def __init__(símismo, dirección='127.0.0.1', puerto=0, variablesMod=[], nombre="enchufe"):
        símismo.enchufe = enchf = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        enchf.bind((dirección, puerto))
        símismo.dirección, símismo.puerto = enchf.getsockname()
        enchf.listen()
        símismo.activo = False
        símismo.con = None
        super().__init__(variablesMod, nombre)

    def activar(símismo):
        símismo.con, dir_ = símismo.enchufe.accept()
        símismo.activo = True

    @property
    def unids(símismo):
        raise NotImplementedError

    @abstractmethod
    def iniciar_proceso(símismo):
        pass

    def cambiar_var(símismo, var):
        MensajeCambiar(símismo.con, variable=var, valor=var.obt_val()).mandar()

    def leer_var(símismo, var):
        val = MensajeLeer(símismo.con, var).mandar()
        return val

    def incrementar(símismo, rebanada):
        super().incrementar(rebanada)

    def incrementarProceso(símismo, n_pasos):
        MensajeIncrementar(símismo.con, pasos=n_pasos).mandar()

    def cerrar(símismo):
        MensajeCerrar(símismo.con).mandar()
        try:
            símismo.con.close()
        finally:
            símismo.enchufe.close()
        símismo.activo = False

    def finalizar(símismo):
        símismo.incrementarProceso(0)

    def __enter__(símismo):
        return símismo

    def __exit__(símismo, *args):
        if símismo.activo:
            símismo.cerrar()

class Mensaje(object):
    def __init__(símismo, con, contenido=''):
        símismo.con = con
        símismo.contenido = json.dumps((np.array(contenido).tolist()), ensure_ascii=False).encode('utf8')

    @property
    def orden(símismo):
        raise NotImplementedError

    def _encabezado(símismo):
        if símismo.orden is "TOMAR_":
            return {'orden': símismo.orden, 'tamaño': len(símismo.contenido)}
        else:
            return {'orden': símismo.orden}

    def mandar(símismo):
        print("IN MANDAR NOW")
        encabezado = símismo._encabezado()
        encabezado_bytes = json.dumps(encabezado, ensure_ascii=False).encode('utf8')
        # Mandar tmñ encabezado
        símismo.con.sendall(len(encabezado_bytes).to_bytes(1, byteorder="big"))
        print("Letting C know this size: ", len(encabezado_bytes))
        sys.stdout.flush()


        msg = ""
        while len(msg) < 4:
            data = str(np.unicode(símismo.con.recv(1), errors='ignore'))
            msg += data
            print("Current msg: ", msg)
            if msg == "":
                exit(-3)
            sys.stdout.flush()
        if not msg == "RCVD":
            raise ConnectionError

        # Mandar encabezado json
        símismo.con.sendall(encabezado_bytes)
        print("Encabezado bytes: ", encabezado_bytes)
        sys.stdout.flush()
        msg = ""
        while len(msg) < 4:
            data = str(np.unicode(símismo.con.recv(1), errors='ignore'))
            msg += data
            print("Current msg: ", msg)
            if msg == "":
                exit(-3)
            sys.stdout.flush()

        if not msg == "RCVD":
            raise ConnectionError

        if símismo.orden is "TOMAR_":
            # Mandar contenido json
            símismo.con.sendall(símismo.contenido)
            print("Contenido bytes: ", símismo.contenido)
            sys.stdout.flush()
            msg = ""
            while len(msg) < 4:
                data = str(np.unicode(símismo.con.recv(1), errors='ignore'))
                msg += data
                print("Current msg: ", msg)
                if msg == "":
                    exit(-3)
                sys.stdout.flush()

            if not msg == "RCVD":
                raise ConnectionError

        return símismo._procesar_respuesta()

    def _procesar_respuesta(símismo):
        pass


class MensajeCambiar(Mensaje):
    orden = 'TOMAR_'

    def __init__(símismo, enchufe, variable, valor):
        símismo.variable = variable
        super().__init__(enchufe, contenido=valor)

    def _encabezado(símismo):
        encab = super()._encabezado()
        encab['var'] = str(símismo.variable.código)
        encab['matr'] = ~(símismo.variable.obt_val().size <= 1)
        val = símismo.variable.obt_val()

        #-------------------------------------Made A Change Here--------------------------------------------------------
        if isinstance(val, np.ndarray):
            if np.issubdtype(val.dtype, np.int_):
                encab['tipo_cont'] = "int"
            elif np.issubdtype(val.dtype, np.float_):
                encab['tipo_cont'] = "flt"
            elif np.issubdtype(val.dtype, object):
                encab['tipo_cont'] = "str"
            else:
                raise TypeError
        else:
            if isinstance(val, int):
                encab['tipo_cont'] = "int"
            elif isinstance(val, float):
                encab['tipo_cont'] = "flt"
            elif isinstance(val, str):
                encab['tipo_cont'] = "str"
                raise UserWarning("Currently string types are not supported in the modified SWAT+ model")
            else:
                raise TypeError
        return encab


class MensajeLeer(Mensaje):
    orden = 'DAR___'

    def __init__(símismo, con, variable):
        símismo.variable = variable
        super().__init__(con)

    def _encabezado(símismo):
        encab = super()._encabezado()
        encab['var'] = str(símismo.variable.código)
        return encab

    def _procesar_respuesta(símismo):
        val = RecepciónVariable(símismo.con).recibir()
        if símismo.variable.esmatriz:
            if isinstance(val, np.ndarray):
                val = val.reshape(símismo.variable.forma)
            else:
                val = np.full(símismo.variable.forma, val)
        elif isinstance(val, np.ndarray):
            raise TypeError
        return val


class MensajeIncrementar(Mensaje):
    orden = 'CORRER'

    def __init__(símismo, enchufe, pasos):
        símismo.pasos = pasos
        super().__init__(enchufe)

    def _encabezado(símismo):
        encab = super()._encabezado()
        encab['n_pasos'] = símismo.pasos
        return encab


class MensajeCerrar(Mensaje):
    orden = 'CERRAR'


class Recepción(object):
    def __init__(símismo, con):
        símismo.con = con

    def recibir(símismo):
            tmñ = símismo.con.recv(4).decode('utf-8')
            print("Tamano: ", tmñ)
            contenido = símismo.con.recv(int(tmñ)).decode('utf8')
            print("Contenido: ", contenido)
            return símismo._procesar(contenido)

    def _procesar(símismo, contenido):
        raise NotImplementedError


class RecepciónVariable(Recepción):

    def _procesar(símismo, contenido):
        try:
            return np.frombuffer(contenido)
        except TypeError as e:
            return np.fromstring('0', dtype=int, sep=' ')