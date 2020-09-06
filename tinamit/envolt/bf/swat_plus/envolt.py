import os
import shutil
import socket
import subprocess
import tempfile
from ast import literal_eval
import pandas as pandas
import numpy as np
from ctypes import *
import json

from tinamit.envolt.bf import ModeloBF
from tinamit.envolt.bf.swat_plus._vars import VariableEnchufe, obt_info_vars
from tinamit.envolt.bf.swat_plus.enchufe import ModeloEnchufe
from tinamit.mod import VariablesMod, Variable
from tinamit.config import _



class ModeloSWATPlus(ModeloEnchufe):
    def __init__(símismo, archivo, nombre='SWATPlus', connectar=True):
        # Buscar la ubicación del modelo SWATPlus.
        símismo.exe_SWATPlus = símismo.obt_conf(
            'exe',
            cond=os.path.isfile,
            mnsj_err=_(
                '\nDebes especificar la ubicación del ejecutable SWATPlus, p. ej.'
                '\n\tModeloSWATPlus.estab_conf("exe", "C:\\Camino\\hacia\\mi\\SWATPlus.exe")'
                '\npara poder hacer simulaciones con modelos SWATPlus.'
                '\nSi no instalaste SWATPlus, lo puedes conseguir para Linux, Mac o Windows de '
                'https://github.com/joelz575/swatplus.'
            ))

        símismo.HUÉSPED = socket.gethostbyname(socket.gethostname())
        símismo.archivo = archivo
        símismo.dic_ingr = {}
        símismo.dic_ingr = obt_info_vars(símismo.archivo)

        variables = []
        for nmbr, info in símismo.dic_ingr.items():
            variables.append(
                VariableEnchufe(nombre=nmbr, código=info["código"], unid=info["unid"], inic=info["val"], ingr=info["ingr"], egr=info["egr"]))
        variablesMod = VariablesMod(variables)

        #símismo.hru_cha_mod = np.zeros(4)  # [hru, hlt, cha, sdc (lcha)]
        # values assigned in símismo.deter_HRU_cha_mod() later
        símismo.connectar = connectar
        super().__init__(dirección=símismo.HUÉSPED, variablesMod=variablesMod, nombre=nombre)
        print("DONE INIT")

    def escribir(símismo, archivo):
        return obt_info_vars(archivo)

    def unidad_tiempo(símismo):
        return 'días'

    def incrementar(símismo, rebanada):
        print("IN INCREMENTAR")
        if símismo.connectar:
            # Mandar los valores nuevas a SWATPlus
            for var in rebanada.resultados:
                símismo.cambiar_var(var.var)
            print("Are we done with the variables now?")

            # Correr un paso de simulaccion
            símismo.incrementarProceso(rebanada.n_pasos)
            print("done with s")

            # Obtiene los valores de eso paso de la simulaccion
            for var in rebanada.resultados:
                símismo.variables[str(var)].poner_val(símismo.leer_var(var.var))

            super().incrementar(rebanada=rebanada)
            print("DONE INCREMENTAR")

    def paralelizable(símismo):
        return True

    def iniciar_modelo(símismo, corrida):
        if símismo.connectar:
            símismo.direc_trabajo = shutil.copytree(símismo.archivo, '_' + str(hash(corrida)))
            print(símismo.direc_trabajo)
            if corrida.t.f_inic is None:
                raise ValueError('A start date is necessary when using SWAT+')
            super().iniciar_modelo(corrida=corrida)

            #iniciate SWATPlus Model
            símismo.proc = subprocess.Popen(
                [símismo.obt_conf('exe'), str(símismo.puerto), str(símismo.dirección)],
                cwd=símismo.direc_trabajo
            )
            print("Done iniciar")
            símismo.activar()
            símismo.proceso = símismo.iniciar_proceso()
            #símismo.deter_uso_de_tierra()
            #símismo.deter_HRU_cha_mod()
        else:
            símismo.direc_trabajo = shutil.copytree(símismo.archivo, '_' + str(hash(corrida)))
            símismo.proc = subprocess.Popen(
                [símismo.obt_conf('exe')],
                cwd=símismo.direc_trabajo
            )
        print("DONE INICIAR")


    # def deter_HRU_cha_mod(símismo):
    # #     símismo.clientsocket.sendall(bytes("OBT:" + "hru_cha_mod", "utf-8"))
    # #     símismo.clientsocket.sendall(bytes(";", "utf-8"))
    # #     msg = ""
    # #     while True:
    # #         data = str(np.unicode(símismo.clientsocket.recv(1), errors='ignore'))
    # #         msg += data
    # #         if not msg.__contains__("["):
    # #             msg = ""
    # #         elif msg.__contains__(";") and msg.__contains__("]"):
    # #             break
    # #     split_msg = msg.split('[')
    # #     if split_msg.__len__() != 1:
    # #         split_msg = split_msg[1].split("]")
    # #         [hru_mod, cha_mod] = split_msg[0].split(" ")
    # #         símismo.hru_mod = hru_mod
    # #         símismo.cha_mod = cha_mod
    # #         print(símismo.hru_mod)
    # #         print(símismo.cha_mod)
    #     with open(símismo.direc_trabajo + '\\object.cnt') as objects:
    #     # NAME,AREA_LS_HA,AREA_TOT_HA,OBJ,HRU,LTE,RU,MODFLOW,AQU,CHA,RES,REC,EXCO,DR,CANAL,PUMP,OUT,CHANDEG,2DAQU
    #     # for line in
    #     #specs = pandas.DataFrame(objects.readlines())
    #         specs_all = objects.readlines()[2].split(' ')
    #         specs = []
    #         for i in range(0, len(specs_all)):
    #             if not len(specs_all[i]) < 1:
    #                 specs.append(specs_all[i])
    #
    #         símismo.hru_cha_mod[0] = int(specs[4])
    #         símismo.hru_cha_mod[1] = int(specs[5])
    #         símismo.hru_cha_mod[2] = int(specs[9])
    #         símismo.hru_cha_mod[3] = int(specs[17])


    def deter_uso_de_tierra(símismo):
        símismo.archivo_uso_de_tierra = open(símismo.direc_trabajo + '\\landuse.lum', 'r')
        símismo.uso_de_tierra = []
        counter = 0
        for line in símismo.archivo_uso_de_tierra:
            if 1 < counter:
                split_line = line.split(' ')
                uso_de_tierra = split_line[0]
                símismo.uso_de_tierra.append(uso_de_tierra)
                print(uso_de_tierra)
            counter += 1
        símismo.archivo_uso_de_tierra.close()


    def cerrar(símismo):
        # close model
        if símismo.connectar:
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

