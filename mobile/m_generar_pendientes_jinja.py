#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import os
from jinja2 import Template
from devuelvos import *
# import codecs
from jinja2 import Template, FileSystemLoader, Environment

env = Environment()
env.loader = FileSystemLoader('.')

def main():
    conn = sqlite3.connect('../infomesas.db')
    cur = conn.cursor()
    cur.execute("SELECT * from pedidos WHERE estado='pendiente' or estado='en produccion' or estado='terminada'")
    data = cur.fetchall()
    pedidos_fecha = []
    for item in data:
        pedidos_fecha.append((item[0], datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S"), item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12]))
    data = sorted(pedidos_fecha, key=lambda x: x[1])
 
    pedidos = []
    for item in data:
        fechap = "%s-%s-%s" % (item[1].day, item[1].month, item[1].year)
        nombreCliente = devuelvoNombreCliente(item[2])
        # ofuscado = codecs.encode(nombreCliente.replace(' ', '-'), 'rot_13')
        nombreSinEspacios = nombreCliente.replace(' ', '-')
        linkSinEspacios = "/mobile/%s.html" % nombreSinEspacios
        cliente = ((nombreCliente, linkSinEspacios))
        modelo = devuelvoNombreModelo(item[3])
        chapa = devuelvoNombreChapa(item[4])
        medidas = "%s-%s*%s" % (item[6], item[7], item[8])
        pedidos.append((fechap, cliente, modelo , chapa, medidas, item[5], item[9], item[10]))    

    tmpl = env.get_template('pendientes_template.html')
    html_template_string = tmpl.render(pedidos=pedidos)
    template_file = open("pendientes.html", 'w').write(html_template_string)
if __name__ == '__main__':
    main()
