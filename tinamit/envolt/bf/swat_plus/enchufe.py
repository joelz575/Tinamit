import json
import socket
from abc import abstractmethod
from struct import pack

import numpy as np
from click import pause

from tinamit.mod import Modelo


class ModeloEnchufe(Modelo):
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

    def incrementar(símismo, rbnd):
        for paso in rbnd:
            MensajeIncrementar(símismo.con, pasos=paso.n_pasos).mandar()

    def cerrar(símismo):
        try:
            símismo._enchufe.close()
        finally:
            try:
                símismo.con.close()
            finally:
                MensajeCerrar().mandar()
                if símismo.proceso.poll() is None:
                    avisar(_(
                        'Proceso de modelo {} todavía estaba corriendo al final de la simulación.'
                    ).format(símismo))
                    símismo.proceso.kill()


class Mensaje(object):
    def __init__(símismo, con, contenido=''):
        símismo.con = con
        símismo.contenido = json.dumps((np.array(contenido).tolist()), ensure_ascii=False).encode('utf8')

    @property
    def orden(símismo):
        raise NotImplementedError

    def _encabezado(símismo):
        return {'orden': símismo.orden, 'tamaño': len(símismo.contenido)}

    def mandar(símismo):
        encabezado = símismo._encabezado()
        encabezado_bytes = json.dumps(encabezado, ensure_ascii=False).encode('utf8')
        # Mandar tmñ encabezado
        #
        símismo.con.sendall(len(encabezado_bytes).to_bytes(1, byteorder="big"))
        print("Sent this pack: ", len(encabezado_bytes).to_bytes(1, byteorder="big"))

        msg = ""
        while len(msg) < 4:
            data = str(np.unicode(símismo.con.recv(1), errors='ignore'))
            msg += data
            print("Current msg: ", msg)

        if not msg == "RCVD":
            raise ConnectionError

        # Mandar encabezado json
        símismo.con.sendall(encabezado_bytes)
        print("Encabezado bytes: ", encabezado_bytes)
        msg = ""
        while len(msg) < 4:
            data = str(np.unicode(símismo.con.recv(1), errors='ignore'))
            msg += data
            print("Current msg: ", msg)

        if not msg == "RCVD":
            raise ConnectionError

        # Mandar contenido
        if símismo.contenido:

            símismo.con.sendall(símismo.contenido)
            print("Contenido to send: ", símismo.contenido)

        msg = ""
        while len(msg) < 4:
            data = str(np.unicode(símismo.con.recv(1), errors='ignore'))
            msg += data
            print("Current msg: ", msg)

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
        tmñ = símismo.con.recv(4)
        encabezado = json.loads(símismo.con.recv(tmñ).decode('utf8'))
        contenido = símismo.con.recv(encabezado['tamaño'])
        return símismo._procesar(encabezado, contenido)

    def _procesar(símismo, encabezado, contenido):
        raise NotImplementedError


class RecepciónVariable(Recepción):

    def _procesar(símismo, encabezado, contenido):
        return np.frombuffer(contenido)
