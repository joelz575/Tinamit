from tinamit.mod import Variable


class VariableEnchufe(Variable):
    def __init__(símismo, nombre, código, unid, ingr, egr, inic=0, líms=None, info=''):
        símismo.código = código
        super().__init__(nombre, unid, ingr, egr, inic, líms, info)


def obt_info_vars(archivo):
            return{
        #'HRU_CHA_mod': {'código': 'hru_cha_mod', 'char': True, 'egr': False, 'val': {'',''}},
        #'Unidades_de_paisaje'
        #'HRU_manejo_de_tierra': {'código': 'hru%lumv'}
        'HRU_uso_de_tierra': {'código': 'hru%luse', 'unid': 'key', 'ingr': True, 'egr': False, 'val': []},
        'Algas': {'código': 'algae', 'unid': 'mg/L', 'ingr': False, 'egr': True, 'val': 0},
        'Fluir_a_canal': {'código': 'flwin', 'unid': 'ha*m', 'ingr': False,
            'egr': True, 'val': 0},
        'Lluvia': {'código': 'Lluvia', 'unid': 'm*m*m/mes', 'ingr': True, 'egr': True, 'val': 200},
        'Bosques': {'código': 'Bosques', 'unid': 'm*m', 'ingr': True, 'egr': True, 'val': 200}
}