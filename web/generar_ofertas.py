#!/usr/bin/env python3

import os
from jinja2 import Template, FileSystemLoader, Environment
from pathlib import Path

env = Environment()
env.loader = FileSystemLoader('.')

def main():
    carpeta = Path("../fotos/ofertas")
    imagenes = [f.name for f in carpeta.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")]

    tmpl = env.get_template('ofertas_template.html')
    html_template_string = tmpl.render(ofertas=imagenes)
    template_file = open("ofertas.html", 'w').write(html_template_string)

if __name__ == '__main__':
    main()
