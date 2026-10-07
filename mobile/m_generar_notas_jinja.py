#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import os
from jinja2 import Template, FileSystemLoader, Environment

env = Environment()
env.loader = FileSystemLoader('.')


def main():
    conn = sqlite3.connect('../infomesas.db')
    cur = conn.cursor()
    cur.execute("SELECT * from notas")
    data = cur.fetchall()
    titulos = []
    for item in data:
        titulos.append((item[1].replace(' ', '-') + ".html", item[1]))

    tmpl = env.get_template('notas_template.html')
    html_template_string = tmpl.render(titulos=titulos)
    template_file = open("notas/notas.html", 'w').write(html_template_string)

    for item in data:
        tmpl = env.get_template('cada_nota_template.html')
        html_template_string = tmpl.render(nota=item)
        nombreNota = item[1].replace(' ', '-') + ".html"
        template_file = open("notas/" + nombreNota, 'w').write(html_template_string)

if __name__ == '__main__':
    main()
