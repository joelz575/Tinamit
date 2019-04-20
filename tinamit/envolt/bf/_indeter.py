from ._impac import ModeloImpaciente, VarPaso


class ModeloIndeterminado(ModeloImpaciente):

    def __init__(símismo, variables, nombre='bf'):
        super().__init__(tmñ_ciclo=0, variables=variables, nombre=nombre)

    def incrementar(símismo):
        # Para simplificar el código un poco.
        p = símismo.paso_en_ciclo
        n_pasos = símismo.corrida.t.pasos_avanzados(símismo.unidad_tiempo())

        # Aplicar el incremento de paso
        p += n_pasos

        # Guardar el pasito actual para la próxima vez.
        símismo.paso_en_ciclo = p

        # Actualizar el paso en los variables
        símismo.variables.act_paso(símismo.paso_en_ciclo)

        # Si hay que avanzar el modelo externo, lanzar una su simulación aquí.
        while p >= símismo.tmñ_ciclo:
            p -= símismo.tmñ_ciclo

            # Avanzar la simulación
            símismo.tmñ_ciclo = símismo.mandar_modelo()

    def unidad_tiempo(símismo):
        raise NotImplementedError

    def mandar_modelo(símismo):
        raise NotImplementedError


class VarPasoIndeter(VarPaso):

    def __init__(símismo, nombre, unid, ingr, egr, inic=0, líms=None, info=''):
        super().__init__(nombre, unid, ingr, egr, tmñ_ciclo=1, inic=inic, líms=líms, info=info)

    def poner_vals_paso(símismo, val):
        símismo._matr_paso = val
