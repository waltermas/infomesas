#!/bin/python3

import sqlite3

conn = sqlite3.connect('../infomesas.db')


def devuelvoNombreCliente(id):
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM clientes WHERE idCliente = '%s'" % id)
    data = cur.fetchall()
    return data[0][0]

def devuelvoNombreModelo(id):
    cur = conn.cursor()
    cur.execute("SELECT modelo FROM modelos WHERE idModelo = '%s'" % id)
    data = cur.fetchall()
    return data[0][0]

def devuelvoNombreChapa(id):
    cur = conn.cursor()
    cur.execute("SELECT chapa FROM chapas WHERE idChapa = '%s'" % id)
    data = cur.fetchall()
    return data[0][0]
 
def devuelvoNombreLugarEntrega(id):
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM lugaresEntrega WHERE idLugarEntrega = '%s'" % id)
    data = cur.fetchall()
    return data[0][0]

# def main():
# if __name__ == '__main__':
#     main()
