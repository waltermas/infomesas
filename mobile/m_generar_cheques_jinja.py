#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import os
from jinja2 import Template, FileSystemLoader, Environment

env = Environment()
env.loader = FileSystemLoader('.')


def main():
    def devuelvo_cliente(idCliente):
        cur.execute("SELECT * from clientes WHERE idCliente = %s" % idCliente)
        data = cur.fetchall()
        return data[0]

    def devuelvo_proveedor(idprov):
        cur.execute("SELECT * from proveedores WHERE idProveedor = %s" % idprov)
        data = cur.fetchall()
        return data[0]

    conn = sqlite3.connect('../infomesas.db')
    cur = conn.cursor()
    cur.execute("SELECT * from pedidos")
    data = cur.fetchall()
    cur.execute("SELECT * FROM cheques")
    data = cur.fetchall()
    cheques = []
    importe_total = 0
    # orden = 0
    for item in data:
        fecha = datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")
        fecha_recibido = "%s-%s-%s" % (fecha.day, fecha.month, fecha.year)
        cliente = devuelvo_cliente(item[2])
        fecha =  datetime.strptime(item[3], "%Y-%m-%d %H:%M:%S")
        fecha_cheque = "%s-%s-%s" % (fecha.day, fecha.month, fecha.year)
        diferencia = fecha - datetime.today()
        diferenciaint = int(diferencia.days)
        if diferenciaint < 0:
            diferenciatexto = str(diferenciaint)
        else:
            diferenciatexto = str(diferenciaint)
        if item[7] == None:
            fecha_entregado = ''
            entregadoA = "disponible"
            importe_total = importe_total + int(item[6])
        else:
            fecha_entregado =  datetime.strptime(item[7], "%Y-%m-%d %H:%M:%S")
            fecha_entregado = "%s-%s-%s" % (fecha.day, fecha.month, fecha.year)
            entregadoA = devuelvo_proveedor(item[8])[1]
            diferenciatexto = ""

        cheques.append((fecha_recibido,cliente[1],fecha_cheque,diferenciatexto,item[4],item[5],item[6],fecha_entregado,entregadoA))

    cheques.reverse()
    tmpl = env.get_template('cheques_template.html')
    html_template_string = tmpl.render(cheques=cheques)
    template_file = open("cheques.html", 'w').write(html_template_string)

if __name__ == '__main__':
    main()
