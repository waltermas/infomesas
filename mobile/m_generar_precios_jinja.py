#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import os
from jinja2 import Template, FileSystemLoader, Environment
from datetime import datetime, timedelta

env = Environment()
env.loader = FileSystemLoader('.')

def main():
    conn = sqlite3.connect('../infomesas.db')
    cur = conn.cursor()
    cur.execute("SELECT idProducto from productosSeguidosPrecios ORDER BY idProducto")
    data = cur.fetchall()
    precios = []
    dataSinDuplicados = list(dict.fromkeys(data))
    for item in dataSinDuplicados:
        cur.execute("SELECT * from productosSeguidosPrecios WHERE idProducto = '%s'" % item[0])
        dataProducto = cur.fetchall()
        precioMaximo = max(dataProducto, key=lambda i: i[2])
        dataNombreProducto = cur.execute("SELECT * from productosSeguidos WHERE idProducto = '%s'" % precioMaximo[1])
        nombreProducto = cur.fetchall()

        fecha = datetime.strptime(dataProducto[-1][4], "%Y-%m-%d %H:%M:%S")
        diferencia = datetime.today() - fecha
        diferenciaint = int(diferencia.days)
        precios.append((nombreProducto[0][1], precioMaximo[2], diferenciaint))

    precios.sort()
    tmpl = env.get_template('precios_template.html')
    html_template_string = tmpl.render(precios=precios)
    template_file = open("precios.html", 'w').write(html_template_string)

if __name__ == '__main__':
    main()
