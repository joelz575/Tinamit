import datetime as ft
import pickle
from multiprocessing import Pool as Reserva
from warnings import warn as avisar

import numpy as np

from tinamit.config import _, conf_mods
from .corrida import Corrida, Rebanada
from .extern import gen_extern
from .res import ResultadosGrupo
from .tiempo import EspecTiempo
from .vars_mod import VariablesMod


class Modelo(object):
    """
    Todas las cosas en Tinamit son instancias de `Modelo`, que sea un modelo de dinámicas de los sistemas, un modelo de
    cultivos o de suelos o de clima, o un modelo conectado.
    Cada tipo de modelo se representa por subclases específicas. Por eso, la gran mayoría de los métodos definidos
    aquí se implementan de manera independiente en cada subclase de `Modelo`.
    """

    idioma_orig = 'es'  # Cambiar en tu modelo si el idioma de sus variables, etc. no es el castellano

    def __init__(símismo, variables, nombre):
        """
        La función de inicialización de todos modelos, conectados o no.

        Parameters
        ----------
        variables : VariablesMod
            Los variables del modelo.
        nombre : str
            El nombre del modelo.

        """

        símismo.nombre = nombre
        símismo.variables = variables
        símismo.corrida = None
        símismo.vars_clima = {}

    def unidad_tiempo(símismo):
        """
        Esta función debe devolver la unidad de tiempo empleada por el modelo.

        Returns
        -------
        str
            La unidad de tiempo (p. ej., 'meses', 'مہینہ', etc.)
        """

        raise NotImplementedError

    def simular(símismo, t, nombre='Tinamït', extern=None, clima=None, vars_interés=None):
        t = t if isinstance(t, EspecTiempo) else EspecTiempo(t)

        corrida = Corrida(
            nombre, t=t.gen_tiempo(símismo.unidad_tiempo()),
            extern=gen_extern(extern),
            vars_mod=símismo.variables,
            vars_interés=vars_interés,
            clima=clima
        )

        símismo.iniciar_modelo(corrida)
        símismo.correr()
        símismo.cerrar()

        return corrida.resultados

    def simular_grupo(símismo, ops_grupo, nombre='Tinamït', paralelo=False):

        if paralelo and not símismo.paralelizable():
            avisar(_(
                '\nEl modelo no se identifica como paralelizable. Para evitar el riesgo'
                '\nde errores de paralelización, correremos las corridas como simulaciones secuenciales '
                '\nnormales. '
                '\nSi tu modelo sí es paralelizable, crear un método nombrado `.paralelizable()` '
                '\nque devuelve ``True`` en tu clase de modelo para activar la paralelización.'
            ))
            paralelo = False

        res_grupo = ResultadosGrupo(nombre)
        if paralelo:
            l_trabajos = []
            copia_mod = pickle.dumps(símismo)  # Una copia de este modelo.

            # Crear la lista de información necesaria para las simulaciones en paralelo...
            for ops in ops_grupo:
                l_trabajos.append((copia_mod, ops))

            # Hacer las corridas en paralelo
            with Reserva() as r:
                res_paralelo = r.map(_correr_modelo, l_trabajos)
            for res in res_paralelo:
                res_grupo[str(res)] = res

        else:
            for ops in ops_grupo:
                res = símismo.simular(**ops)
                res_grupo[str(res)] = res

        return res_grupo

    def iniciar_modelo(símismo, corrida):
        símismo.corrida = corrida
        corrida.variables.reinic()

        if corrida.extern:
            símismo.cambiar_vals(
                {vr: vl.values for vr, vl in corrida.obt_extern_act().items() if vr in símismo.variables})
        if corrida.clima:
            símismo.cambiar_vals(
                {vr: vl.values for vr, vl in corrida.clima.obt_todos_vals(símismo.vars_clima).items()})
        corrida.actualizar_res()

    def correr(símismo):
        intento = símismo._correr_hasta_final()
        if intento is not None:
            símismo.corrida.resultados.poner_vals_t(intento)
        else:
            while símismo.corrida.t.avanzar():
                símismo.incrementar(
                    Rebanada(
                        símismo.corrida.t.pasos_avanzados(símismo.unidad_tiempo()),
                        resultados=símismo.corrida.resultados
                    )
                )
                símismo.corrida.actualizar_res()

    def _correr_hasta_final(símismo):
        return None

    def incrementar(símismo, rebanada):
        if símismo.corrida.extern:
            símismo.cambiar_vals({vr: vl.values for vr, vl in símismo.corrida.obt_extern_act().items()})

        if símismo.corrida.clima and símismo.vars_clima:
            t = símismo.corrida.t
            símismo._act_vals_clima(t.fecha(), t.fecha_próxima())

    def cerrar(símismo):
        """
        Esta función debe tomar las acciones necesarias para terminar la simulación y cerrar el modelo, si aplica.
        Si no aplica, usar ``pass``.
        """
        pass

    def cambiar_vals(símismo, valores):
        """
        Esta función cambia el valor de uno o más variables del modelo.

        Parameters
        ----------
        valores : dict
            Un diccionario de variables y sus valores para cambiar.
        """

        # Cambia primero el valor en el diccionario interno del Modelo
        símismo.variables.cambiar_vals(valores=valores)

    @classmethod
    def obt_conf(cls, llave, auto=None, cond=None, mnsj_err=None):

        auto = auto or []
        if isinstance(auto, str):
            auto = [auto]

        try:
            op = conf_mods[cls.__name__][llave]
            if cond is None or cond(op):
                return op
        except KeyError:
            pass

        for op in auto:
            if cond is None or cond(op):
                conf_mods[cls.__name__, llave] = op
                return op

        if mnsj_err:
            avisar(mnsj_err)

    @classmethod
    def estab_conf(cls, llave, valor):
        conf_mods[cls.__name__, llave] = valor

    @classmethod
    def instalado(cls):
        """
        Si tu modelo depiende en una instalación de otro programa externo a Tinamït, puedes reimplementar esta función
        para devolver ``True`` si el modelo está instalado y ``False`` sino.

        Returns
        -------
        bool
            Si el modelo está instalado completamente o no.
        """

        return True

    def paralelizable(símismo):
        """
        Indica si el modelo actual se puede paralelizar de manera segura o no. Si implementas una subclase
        paralelizable, reimplementar esta función para devolver ``True``.
        ¿No sabes si es paralelizable tu modelo?
        Si el modelo se puede paralelizar (con corridas de nombres distintos) sin encontrar dificultades
        técnicas (sin riesgo que las corridas paralelas terminen escribiendo en los mismos archivos de egreso),
        entonces sí es paralelizable tu modelo.

        Returns
        -------
        bool:
            Si el modelo es paralelizable o no.
        """

        return False

    def __str__(símismo):
        return símismo.nombre

    def conectar_var_clima(símismo, var, var_clima, conv, combin=None):
        """
        Conecta un variable climático.

        Parameters
        ----------
        var : str
            El nombre interno del variable en el modelo.
        var_clima : str
            El nombre oficial del variable climático.
        conv : number
            La conversión entre el variable clima en Tinamït y el variable correspondiente en el modelo.
        combin : str
            Si este variable se debe adicionar o tomar el promedio entre varios pasos.
        """

        combins = {
            'prom': np.mean,
            'total': np.sum
        }
        if isinstance(combin, str):
            combin = combins[combin.lower()]

        símismo.vars_clima[var] = {
            'nombre_tqdr': var_clima,
            'combin': combin,
            'conv': conv
        }

    def _act_vals_clima(símismo, f_0, f_1):
        """
        Actualiza los variables climáticos. Esta función es la automática para cada modelo. Si necesitas algo más
        complicado (como, por ejemplo, predicciones por estación), la puedes cambiar en tu subclase.

        Parameters
        ----------
        f_0 : ft.date | ft.datetime
            La fecha actual.
        f_1 : ft.date | ft.datetime
            La próxima fecha.
        """

        datos = símismo.corrida.clima.combin_datos(vars_clima=símismo.vars_clima, f_inic=f_0, f_final=f_1)

        símismo.cambiar_vals(valores=datos)


def _correr_modelo(x):
    """
    Función para inicializar y correr un modelo en paralelo.

    Parameters
    ----------
    x : tuple[Modelo, dict]
        Los parámetros. El primero es el modelo, el segundo el diccionario de parámetros para la simulación.

    Returns
    -------
    dict
        Los resultados de la simulación.
    """

    estado_mod, d_args = x

    mod = pickle.loads(estado_mod)

    # Después, simular el modelo y devolver los resultados, si hay.
    return mod.simular(**d_args)
