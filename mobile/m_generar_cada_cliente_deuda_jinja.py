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
    clientes = cur.fetchall()
    for cliente in clientes:
        cur.execute("SELECT * FROM cuentasCorrientes WHERE cliente = %s" % cliente[0])
        data_raw = cur.fetchall()
        data = []
        total = 0
        for item in data_raw:
            total += item[4]
            fecha = datetime.strptime(item[2], "%Y-%m-%d %H:%M:%S")
            fechap = "%s-%s-%s" % (fecha.day, fecha.month, fecha.year)
            if item[4] >= 0:
                data.append((fechap, item[3], item[4], " ", total))
            else:
                data.append((fechap, item[3], " ", item[4], total))
        deuda_pendiente = []
        # total_general = total
        data_raw.reverse()

        clienteFileName = cliente[1].replace(' ', '-')
        clienteFileName += '-deudas.html'

        data.reverse()
        tmpl = env.get_template('cada_cliente_deuda_template.html')
        html_template_string = tmpl.render(cliente=cliente[1], data=data)
        template_file = open(clienteFileName, 'w').write(html_template_string)

if __name__ == '__main__':
    main()
