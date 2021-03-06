import sys
from subprocess import Popen
from unittest import TestCase

import numpy.testing as npt

from pruebas3.ejemplo_cliente import datos
from tinamit3.idm.puertos import IDMEnchufes

t_final = 3287


class PruebaIDM(TestCase):

    def setUp(símismo):
        símismo.clientes = []

    def _empezar_cliente(símismo, dirección, puerto):
        #cliente = Popen(["/home/joelz/PycharmProjects/swatplus/build/bin/swatplus_exe", str(puerto), dirección],
        #                cwd="/home/joelz/modular_swatplus/data/Texas_large_gully")
        cliente = Popen(["/home/joelz/PycharmProjects/swatplus/build/bin/swatplus_exe", str(puerto), dirección],
                        cwd="/home/joelz/modular_swatplus/data/saturated_buffer")
        #cliente = Popen(["/home/joelz/Documents/Prof Adamowski/Iximulew/SWAT+/swat+EXE/swatplusrev59", str(puerto), dirección],
        #                cwd="/home/joelz/PycharmProjects/swatplus/Trial Robit/Scenarios/Default/TxtInOut")
        #cliente = Popen([sys.executable, "ejemplo_cliente.py", dirección, str(puerto), str(t_final)])
        símismo.clientes.append(cliente)
        return cliente

    def test_abrir_cerrar(símismo):
        with IDMEnchufes() as servidor:
            símismo._empezar_cliente(servidor.dirección, servidor.puerto)
            servidor.activar()
            servidor.cerrar()

    def test_mandar_datos(símismo):
        for nmbr_dts, dts in datos.items():
            with símismo.subTest(datos=nmbr_dts), IDMEnchufes() as servidor:
                símismo._empezar_cliente(servidor.dirección, servidor.puerto)
                servidor.activar()
                servidor.cambiar('var', dts)

                recibido = servidor.recibir('var')
                npt.assert_equal(dts, recibido)

    def test_recibir_datos(símismo):
        for nmbr_dts, dts in datos.items():
            with símismo.subTest(datos=nmbr_dts), IDMEnchufes() as servidor:
                símismo._empezar_cliente(servidor.dirección, servidor.puerto)
                servidor.activar()
                recibido = servidor.recibir(nmbr_dts)
                npt.assert_equal(dts, recibido)

    def test_incrementar(símismo):
        n_pasos = 5
        with IDMEnchufes() as servidor:
            símismo._empezar_cliente(servidor.dirección, servidor.puerto)
            servidor.activar()
            servidor.incrementar(n_pasos)
            t = servidor.recibir('t')
            print("T is: ", t)
            símismo.assertEqual(t, n_pasos)

    def test_finalizar(símismo):
        with IDMEnchufes() as servidor:
            símismo._empezar_cliente(servidor.dirección, servidor.puerto)
            servidor.activar()
            servidor.finalizar()
            t = servidor.recibir('t')
            print("T is: ", t)
            símismo.assertEqual(t, t_final)

    def tearDown(símismo):
        for cliente in símismo.clientes:
            cliente.wait()
