import os
import shutil
import socket
import subprocess
import tempfile
from ast import literal_eval

import numpy as np
from ctypes import *
import json

from tinamit.envolt.bf import ModeloBF
from tinamit.envolt.bf.swat_plus._vars import obt_info_vars
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
        símismo.dic_ingr = obt_info_vars(símismo.archivo)

        variables = []
        for nmbr, info in símismo.dic_ingr.items():
            variables.append(
                Variable(nombre=nmbr, unid=info["unid"], inic=info["val"], ingr=info["ingr"], egr=info["egr"]))
        variablesMod = VariablesMod(variables)

        símismo.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        símismo.socket.bind((socket.gethostname(), 0))
        símismo.socket.listen(5)

        símismo.hru_mod = símismo.cha_mod = ''   # hru mode: 'hru' || 'hlt', cha mode: 'cha' || 'sdc'
        # values assigned in símismo.deter_HRU_cha_mod() later

        super().__init__(variablesMod, nombre)

    def escribir(símismo, archivo):
        return obt_info_vars(archivo)

    def unidad_tiempo(símismo):
        return 'días'

    def incrementar(símismo, rebanada):
        msg = ""
        # Mandar los valores nuevas a SWATPlus
        for var in rebanada.resultados:

            símismo.clientsocket.sendall(bytes("MAND:" + str(símismo.dic_ingr[str(var)]["nombre"]) + ":" +
                                               str(len(símismo.variables[str(var)]._val)) + ":" + str(
                símismo.variables[str(var)]._val), "utf-8"))

            símismo.clientsocket.sendall(bytes(";", "utf-8"))

            while True:
                data = str(np.unicode(símismo.clientsocket.recv(1), errors='ignore'))
                msg += data
                if msg.__contains__("recvd"):
                    msg = ""
                    data = ""
                    break

            #print("this is in python:" + msg)
            # only move on once a string is sent

        # Correr un paso de simulaccion
        símismo.clientsocket.sendall(bytes("CORR:" + str(rebanada.n_pasos), "utf-8"))
        símismo.clientsocket.sendall(bytes(";", "utf-8"))
        msg = ""
        while True:
            data = str(np.unicode(símismo.clientsocket.recv(1), errors='ignore'))
            msg += data
            if msg.__contains__("running"):
                msg = ""
                data = ""
                break
        #print(msg)

        # Obtiene los valores de eso paso de la simulaccion
        for var in rebanada.resultados:
            símismo.clientsocket.sendall(bytes("OBT:" + str(símismo.dic_ingr[str(var)]["nombre"]), "utf-8"))
            símismo.clientsocket.sendall(bytes(";", "utf-8"))
            msg = ""
            while True:
                data = str(np.unicode(símismo.clientsocket.recv(1), errors='ignore'))
                msg += data
                #print(msg)
                if '[' not in msg:
                    msg = ""
                elif msg.__contains__(";") and msg.__contains__("]"):
                    break
            split_msg = msg.split('[')
            if split_msg.__len__() != 1:
                split_msg = split_msg[1].split("]")
                split_msg = split_msg[0].split(" ")
                nums = []
                for i in range(len(split_msg)):
                    if símismo.isfloat(split_msg[i]):
                        nums.append(float(split_msg[i]))

                símismo.variables[str(var)].poner_val(np.array(nums))

        super().incrementar(rebanada=rebanada)

    def paralelizable(símismo):
        return True

    def iniciar_modelo(símismo, corrida):
        #símismo.direc_trabajo = tempfile.mkdtemp('_' + str(hash(corrida)))
        símismo.direc_trabajo = shutil.copytree(símismo.archivo, '_' + str(hash(corrida)))

        if corrida.t.f_inic is None:
            raise ValueError('A start date is necessary when using SWAT+')
        super().iniciar_modelo(corrida=corrida)

        # iniciate SWATPlus Model
        print(símismo.socket.getsockname())

        símismo.proc = subprocess.Popen(
            [símismo.obt_conf('exe'), str(símismo.socket.getsockname()[1]), str(símismo.socket.getsockname()[0])],
            cwd=símismo.direc_trabajo
        )
        print("Done iniciar")
        símismo.clientsocket, address = símismo.socket.accept()

        símismo.deter_HRU_cha_mod()

    def deter_HRU_cha_mod(símismo):
        símismo.clientsocket.sendall(bytes("OBT:" + "hru_cha_mod", "utf-8"))
        símismo.clientsocket.sendall(bytes(";", "utf-8"))
        msg = ""
        while True:
            data = str(np.unicode(símismo.clientsocket.recv(1), errors='ignore'))
            msg += data
            if not msg.__contains__("["):
                msg = ""
            elif msg.__contains__(";") and msg.__contains__("]"):
                break
        split_msg = msg.split('[')
        if split_msg.__len__() != 1:
            split_msg = split_msg[1].split("]")
            [hru_mod, cha_mod] = split_msg[0].split(" ")
            símismo.hru_mod = hru_mod
            símismo.cha_mod = cha_mod
            print(símismo.hru_mod)
            print(símismo.cha_mod)

    def cerrar(símismo):
        # close model
        símismo.clientsocket.sendall(b'FIN;')
        símismo.proc.kill()
        shutil.rmtree(símismo.direc_trabajo, ignore_errors=True)

    def cambiar_vals(símismo, valores):
        super().cambiar_vals(valores)

    def _correr_hasta_final(símismo):
        return None

    def instalado(cls):
        return cls.obt_conf('exe') is not None

    def isfloat(símismo, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    # class Landuse_Map():
    #     def __init__(símismo, áreas, hrus):
    #         return
    #
    #     def landuseChange(símismo, áreas):
    #         return
    #
    # class HRU():
    #     def __init__(símismo, nombre, posición, uso_de_suelo):
    #         return
    #
    # class HRU_LTE(HRU):
    #     def __init__(símismo, nombre, posición, uso_de_suelo):
    #         super.__init__(nombre, posición, uso_de_suelo)
    #         return

