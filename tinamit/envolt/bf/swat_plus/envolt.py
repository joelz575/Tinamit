import os
import shutil
import socket
import subprocess
import tempfile
from ast import literal_eval
import numpy as np

from tinamit.envolt.bf import ModeloBF
from tinamit.mod import VariablesMod, Variable
from tinamit.config import _



class ModeloSWATPlus(ModeloBF):
    def __init__(símismo, archivo, nombre='SWATPlus'):
        # Buscar la ubicación del modelo SWATPlus.
        símismo.exe_SWATPlus = símismo.obt_conf(
            'exe',
            cond=os.path.isfile,
            mnsj_err=_(
                '\nDebes especificar la ubicación del ejecutable SWATPlus, p. ej.'
                '\n\tModeloSWATPlus.estab_conf("exe", "C:\\Camino\\hacia\\mi\\SWATPlus.exe")'
                '\npara poder hacer simulaciones con modelos SWATPlus.'
                '\nSi no instalaste SWATPlus, lo puedes conseguir para Linux, Mac o Windows de '
                'https://github.com/julienmalard/sahysmod-sourcecode.'
            ))

        símismo.archivo = archivo

        símismo.dic_ingr = {}
        símismo.dic_ingr = símismo.obt_info_vars(símismo.archivo)

        variables = []
        for nmbr, info in símismo.dic_ingr.items():
            variables.append(
                Variable(nombre=nmbr, unid=info["unid"], inic=info["val"], ingr=info["ingr"], egr=info["egr"]))
        variablesMod = VariablesMod(variables)

        símismo.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        símismo.socket.bind((socket.gethostname(), 0))
        símismo.socket.listen(5)

        super().__init__(variablesMod, nombre)

    def obt_info_vars(símismo, archivo):
        return {'D': {"tipo": "Channel", "unid": "L", "ingr": True,
                      "egr": True, 'val': [1, 2, 2]},
                'cha 2': {"nombre": "cha2", "tipo": "Channel", "unid": "L", "ingr": True,
                          "egr": True, 'val': [1, 2, 2]},
                'Lluvia': {"nombre": "Lluvia", "unid": "m*m*m/mes", "ingr": True, "egr": True, "val": 200},
                'Bosques': {"nombre": "Bosque", "unid": "m*m", "ingr": True, "egr": True, "val": 200}}


    def escribir(símismo, archivo):
        return símismo.obt_info_vars(archivo)

    def unidad_tiempo(símismo):
        return 'días'

    def incrementar(símismo, rebanada):
        # run one step of SWATPlus

        #Mandar los valores nuevas a SWATPlus
        for var in rebanada.resultados:
            símismo.clientsocket.sendall(bytes("MAND: " + str(var) + ": " + str(símismo.variables[str(var)]._val), "utf-8"))
            msg = símismo.clientsocket.recv(1024).decode("utf-8")
            print(msg)

        #Correr un paso de simulaccion
        símismo.clientsocket.sendall(bytes("CORR: " + str(rebanada.n_pasos), "utf-8"))
        msg = símismo.clientsocket.recv(1024).decode("utf-8")
        print(msg)

        #Obtiene los valores de eso paso de la simulaccion
        for var in rebanada.resultados:
            símismo.clientsocket.sendall(bytes("OBT: " + str(var), "utf-8"))
            msg = símismo.clientsocket.recv(1024).decode("utf-8")
            símismo.variables[str(var)].poner_val(np.array(literal_eval(msg)))


        super().incrementar(rebanada=rebanada)

    def paralelizable(símismo):
        return True

    def iniciar_modelo(símismo, corrida):
        símismo.direc_trabajo = tempfile.mkdtemp('_' + str(hash(corrida)))
        super().iniciar_modelo(corrida=corrida)
        # iniciate SWATPlus Model
        símismo.proc = subprocess.Popen(["python", símismo.obt_conf('exe'), str(símismo.socket.getsockname()[1])],
                                        cwd=símismo.direc_trabajo)
        símismo.clientsocket, address = símismo.socket.accept()
        print("hello I am here")
        print(símismo.socket.getsockname())

    def cerrar(símismo):
        # close model
        símismo.clientsocket.sendall(b'FIN')
        símismo.proc.kill()
        #shutil.rmtree(símismo.direc_trabajo)

    def cambiar_vals(símismo, valores):
        super().cambiar_vals(valores)

    def _correr_hasta_final(símismo):
        return None

    def instalado(cls):
        return cls.obt_conf('exe') is not None
