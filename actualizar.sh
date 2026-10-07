#!/bin/bash
TIMEFORMAT='%3U'
# cd /media/data/infomesas2/mobile
cd mobile
python3 m_generar_clientes_jinja.py
python3 m_generar_pendientes_jinja.py
python3 m_generar_cada_cliente_jinja.py
python3 m_generar_cada_cliente_deuda_jinja.py
python3 m_generar_cheques_jinja.py
python3 m_generar_precios_jinja.py
python3 m_generar_notas_jinja.py
cd ../web
python3 generar_ofertas.py

git status
git add -A
git status
message=`date`
git commit -m "$message"
git push
read -n1 -s -r -p $'Press any key to continue...\n' key
