#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import os
# import codecs
from devuelvos import *
from jinja2 import Template, FileSystemLoader, Environment
# from coloresClientes import devuelvoColorCliente

env = Environment()
env.loader = FileSystemLoader('.')
conn = sqlite3.connect('../infomesas.db')

def main():
    cur = conn.cursor()
    cur.execute("SELECT * FROM clientes ORDER BY nombre")
    # clientes = []
    clientes = cur.fetchall()
    for cliente in clientes:
        # colorCliente = devuelvoColorCliente(cliente[1])
        curPedidos = conn.cursor()
        curPedidos.execute("SELECT * FROM pedidos WHERE cliente = '%s' ORDER BY fecha DESC" % cliente[0])
        pedidos = []
        pedidos2 = []
        dataPedidos = curPedidos.fetchall()
        for pedido in dataPedidos:
            # print(pedido)
            fechaPedido = datetime.strptime(pedido[1], "%Y-%m-%d %H:%M:%S")
            fechap = fechaPedido.strftime("%d-%m-%Y")
            modelo = devuelvoNombreModelo(pedido[3])
            chapa = devuelvoNombreChapa(pedido[4])
            if pedido[11]:
                fechaEntregada = datetime.strptime(pedido[11], "%Y-%m-%d %H:%M:%S")
                # fechapentregada = fechaPedido.strftime("%d-%m-%Y") 🐛
                fechapentregada = fechaEntregada.strftime("%d-%m-%Y")
                lugarEntrega = devuelvoNombreLugarEntrega(pedido[12])
            else:
                fechapentregada = ""
                lugarEntrega = ""
            # print(pedidos)
            if pedido[10] == 'entregada' or pedido[10] == 'anulada':
                pedidos2.append((fechap, modelo, chapa, pedido[5], pedido[6], pedido[7], pedido[8], pedido[9], pedido[10], fechapentregada, lugarEntrega))
            else:
                pedidos.append((fechap, modelo, chapa, pedido[5], pedido[6], pedido[7], pedido[8], pedido[9], pedido[10], fechapentregada, lugarEntrega))
        pedidos.extend(pedidos2)
        clienteFileName = cliente[1].replace(' ', '-')
        clienteFileName += '.html'


        tmpl = env.get_template('cada_cliente_template.html')
        html_template_string = tmpl.render(cliente=cliente[1], pedidos=pedidos)
        template_file = open(clienteFileName, 'w').write(html_template_string)

if __name__ == '__main__':
    main()
