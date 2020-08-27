from tinamit.mod import Variable


class VariableEnchufe(Variable):
    def __init__(símismo, nombre, código, unid, ingr, egr, inic=0, esmatriz=True, líms=None, info='', forma=1):
        símismo.código = código
        símismo.esmatriz=esmatriz
        símismo.forma = forma
        super().__init__(nombre, unid, ingr, egr, inic, líms, info)

def obt_info_vars(archivo):
            return{
        #'HRU_CHA_mod': {'código': 'hru_cha_mod', 'char': True, 'egr': False, 'val': {'',''}},
        #'Unidades_de_paisaje'
        #'HRU_manejo_de_tierra': {'código': 'hru%lumv'}
        #'HRU_uso_de_tierra': {'código': 'hrulus', 'unid': 'key', 'ingr': True, 'egr': False, 'val': []},
        'Algas': {'código': 'algae', 'unid': 'mg/L', 'ingr': False, 'egr': True, 'val': [2.0, 2.2, 0.3]},
        'Fluir_a_canal': {'código': 'flwin', 'unid': 'ha*m', 'ingr': False,
            'egr': True, 'val': [0.0]},
        'Lluvia': {'código': 'Lluvia', 'unid': 'm*m*m/mes', 'ingr': True, 'egr': True, 'val': [200]},
        'Bosques': {'código': 'Bosque', 'unid': 'm*m', 'ingr': True, 'egr': True, 'val': [200]}
}

# management schedule of hru
# landuse of hru
# nutrient in rivers
# inlets und outlets Wassermenge und