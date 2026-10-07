#!/usr/bin/env python3

# https://realpython.com/python-pyqt-database/
# sqlitebrowser
# designer: sudo apt install qttools5-dev-tools
# reference: https://doc.bccnsoft.com/docs/PyQt5/class_reference.html
BROWSER = "/usr/bin/firefox"
TERMINALCOMMAND = "xterm -e"

import os, sys, subprocess
os.environ["QT_QPA_PLATFORM"] = "wayland"

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPalette, QColor, QBrush, QFont
from PyQt6.QtWidgets import QMainWindow, QDialog, QApplication, QAbstractItemView, QTableWidgetItem, QMessageBox, QInputDialog, QLineEdit
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt6 import uic
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from datetime import datetime, timedelta, date, timezone
import calendar
import iconosResource_rc # pyrcc5 iconosResource.qrc -o iconosResource_rc.py
from functools import partial

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
def dias_desde_ultimo_push(repo_path=".", rama="origin/main"):
    resultado = subprocess.run(
        ["git", "-C", repo_path, "log", "-1", "--format=%ct", rama],
        capture_output=True, text=True, check=True
    )
    timestamp = int(resultado.stdout.strip())
    fecha_push = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    dias = (datetime.now(timezone.utc) - fecha_push).days
    dia_semana = DIAS_SEMANA[fecha_push.weekday()]
    return dias, dia_semana, fecha_push


class InfomesasWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("infomesasmain.ui", self)
        self.initUI()

    def initUI(self):
        self.actionSalir.triggered.connect(self.close)
        self.actionAbrirDB.triggered.connect(self.abrirDB)
        self.actionAdministrarModelos.triggered.connect(self.administrarModelos)
        self.actionAdministrarClientes.triggered.connect(self.administrarClientes)
        self.actionAdministrarProveedores.triggered.connect(self.administrarProveedores)
        self.actionAdministrarLugaresEntrega.triggered.connect(self.administrarLugaresEntrega)
        self.nuevoPushButton.clicked.connect(self.nuevoPedido)
        self.pendientesCheckBox.stateChanged.connect(self.vistaChanged)
        self.enproduccionCheckBox.stateChanged.connect(self.vistaChanged)
        self.terminadasCheckBox.stateChanged.connect(self.vistaChanged)
        self.entregadasCheckBox.stateChanged.connect(self.vistaChanged)
        self.anuladasCheckBox.stateChanged.connect(self.vistaChanged)
        self.pedidosTableWidget.setColumnCount(14)
        self.pedidosTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pedidosTableWidget.setHorizontalHeaderLabels(["ID", "Fecha", "Cliente", "Modelo", "Chapa", "Notas", "cerrada", "abierta", "ancho", "Precio", "Estado", "F.entrega", "L.entrega", "Demora"])
        self.pedidosTableWidget.itemDoubleClicked.connect(self.editarPedido)
        self.pedidosTableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pedidosTableWidget.customContextMenuRequested.connect(self.clienteSolo)
        self.hastaDateEdit.setDate(QDate.currentDate())
        self.desdeDateEdit.dateChanged.connect(self.vistaChanged)
        self.hastaDateEdit.dateChanged.connect(self.vistaChanged)
        clientes = llenoClientes()
        self.clienteComboBox.addItems(clientes)
        self.clienteComboBox.currentTextChanged.connect(self.vistaChanged)
        self.clientesPushButton.clicked.connect(self.showClientes)
        self.productosSeguidosPushButton.clicked.connect(self.showProductosSeguidos)
        self.chequesPushButton.clicked.connect(self.showCheques)
        self.salirPushButton.clicked.connect(self.close)
        self.pushPushButton.clicked.connect(self.pushear)
        self.notasPushButton.clicked.connect(self.showNotas)
        self.soloPendientesPushButton.clicked.connect(partial(self.solo, self.pendientesCheckBox))
        self.soloEnProduccionPushButton.clicked.connect(partial(self.solo, self.enproduccionCheckBox))
        self.soloTerminadasPushButton.clicked.connect(partial(self.solo, self.terminadasCheckBox))
        self.soloEntregadasPushButton.clicked.connect(partial(self.solo, self.entregadasCheckBox))
        self.soloAnuladasPushButton.clicked.connect(partial(self.solo, self.anuladasCheckBox))
        self.pedidosTableWidget.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)

        self.vistaChanged()

    def visualizarQuery(self, queryString):
        contadorPendientes = 0
        contadorEnProduccion = 0
        contadorTerminadas = 0
        self.pedidosTableWidget.setRowCount(0)
        query = QSqlQuery(queryString)
        while query.next():
            rows = self.pedidosTableWidget.rowCount()
            self.pedidosTableWidget.setRowCount(rows + 1)
            self.pedidosTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            fechaPedido = datetime.strptime(query.value(1), "%Y-%m-%d %H:%M:%S")
            fechap = fechaPedido.strftime("%d-%m-%Y")
            self.pedidosTableWidget.setItem(rows, 1, QTableWidgetItem(fechap))
            cliente = QTableWidgetItem(devuelvoNombreCliente(query.value(2)))
            self.pedidosTableWidget.setItem(rows, 2, cliente)
            self.pedidosTableWidget.setItem(rows, 3, QTableWidgetItem(devuelvoNombreModelo(query.value(3))))
            self.pedidosTableWidget.setItem(rows, 4, QTableWidgetItem(devuelvoNombreChapa(query.value(4))))
            self.pedidosTableWidget.setItem(rows, 5, QTableWidgetItem(str(query.value(5))))
            medidaCerrada = QTableWidgetItem(str(query.value(6)))
            medidaCerrada.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.pedidosTableWidget.setItem(rows, 6, medidaCerrada)
            medidaAbierta = QTableWidgetItem(str(query.value(7)))
            medidaAbierta.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.pedidosTableWidget.setItem(rows, 7, medidaAbierta)
            medidaAncho = QTableWidgetItem(str(query.value(8)))
            medidaAncho.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.pedidosTableWidget.setItem(rows, 8, medidaAncho)
            precio = QTableWidgetItem(str(query.value(9)))
            precio.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.pedidosTableWidget.setItem(rows, 9, precio)
            estado = QTableWidgetItem(str(query.value(10)))
            if query.value(10) == 'pendiente':
                contadorPendientes += 1
            elif query.value(10) == 'en produccion':
                contadorEnProduccion += 1
            elif query.value(10) == 'terminada':
                contadorTerminadas += 1
            estado.setForeground(self.establecerColorEstado(query.value(10)))
            self.pedidosTableWidget.setItem(rows, 10, estado)
            if query.value(11):
                fecha = datetime.strptime(query.value(11), "%Y-%m-%d %H:%M:%S")
                fechap = fecha.strftime("%d-%m-%Y")
            else:
                fechap = None
            self.pedidosTableWidget.setItem(rows, 11, QTableWidgetItem(fechap))
            if query.value(12):
                queryLugar =  QSqlQuery("SELECT nombre FROM lugaresEntrega WHERE idLugarEntrega = %s"% query.value(12))
                queryLugar.first()
                lugarEntrega = queryLugar.value(0)
            else:
                lugarEntrega = ''
            self.pedidosTableWidget.setItem(rows, 12, QTableWidgetItem(lugarEntrega))
            demora = datetime.today() - fechaPedido 
            if query.value(10) == 'pendiente' or query.value(10) == 'en produccion':
                self.pedidosTableWidget.setItem(rows, 13, QTableWidgetItem(str(demora.days)))
        self.pedidosTableWidget.resizeColumnsToContents()
        self.pedidosTableWidget.setColumnWidth(5, 150)
        self.pedidosTableWidget.scrollToBottom()
        dias, dia_semana, fecha = dias_desde_ultimo_push(".git", "origin/main")

        mensajeStatus = "%i registros. %i pendientes, %i en produccion, %i terminadas. Ultimo push hace %i dias (%s)" % (self.pedidosTableWidget.rowCount(), contadorPendientes, contadorEnProduccion, contadorTerminadas, dias, dia_semana)
        self.statusbar.showMessage(mensajeStatus)

    def editarPedido(self):
        self.pedido = PedidoDialog(self.pedidosTableWidget.selectedItems())
        if self.pedido.exec() == QDialog.DialogCode.Accepted:
            for i in range(len(self.pedido.returnValues)):
                self.pedidosTableWidget.selectedItems()[i].setText(self.pedido.returnValues[i])
                self.pedidosTableWidget.selectedItems()[10].setForeground(self.establecerColorEstado(self.pedido.returnValues[10]))

    def establecerColorEstado(self, estado):
        brush = QBrush(QColor('black'))
        if estado == 'pendiente':
            brush = QBrush(QColor('green'))
        elif estado == 'en produccion':
            brush = QBrush(QColor('brown'))
        elif estado == 'terminada':
            brush = QBrush(QColor(200,160,50))
        return brush

    def nuevoPedido(self):
        self.pedido = PedidoDialog(0)
        if self.pedido.exec() == QDialog.DialogCode.Accepted:
            self.vistaChanged()

    def showClientes(self):
        self.cliente = ClientesWindow()
        self.cliente.show()

    def showProductosSeguidos(self):
        self.productosSeguidos = ProductosSeguidosWindow()
        self.productosSeguidos.show()

    def showCheques(self):
        self.cheques = ChequesWindow()
        self.cheques.show()

    def showNotas(self):
        self.notas = NotasWindow()
        self.notas.show()

    def closeEvent(self, event):
        con.close()
        event.accept()
        
    def vistaChanged(self):
        queryString = ''
        if self.pendientesCheckBox.isChecked():
            queryString = queryString + " OR estado='pendiente'"
        if self.enproduccionCheckBox.isChecked():
            queryString = queryString + " OR estado='en produccion'"
        if self.terminadasCheckBox.isChecked():
            queryString = queryString + " OR estado='terminada'"
        if self.entregadasCheckBox.isChecked():
            queryString = queryString + " OR estado='entregada'"
        if self.anuladasCheckBox.isChecked():
            queryString = queryString + " OR estado='anulada'"
        queryString = queryString[3:]
        diaDesde = self.desdeDateEdit.date().toPyDate()
        diaDesdeString = datetime.strftime(diaDesde, "%Y-%m-01")
        diaHasta = self.hastaDateEdit.date().toPyDate()
        diaHastaString = datetime.strftime(diaHasta, "%Y-%m-")
        ultimoDiaMes = calendar.monthrange(int(datetime.strftime(diaHasta,"%y")), int(datetime.strftime(diaHasta,"%m")))[1]
        diaHastaString = diaHastaString + str(ultimoDiaMes) + " 23:59:59"
        queryStringFecha = "SELECT * FROM pedidos WHERE (fecha >= '" + diaDesdeString + "'AND fecha <= '" + diaHastaString + "') AND ("
        queryString = queryStringFecha + queryString + ")"
        if self.clienteComboBox.currentText() != " [elegir]":
            queryString = queryString + " AND cliente=" + str(devuelvoIdCliente(self.clienteComboBox.currentText()))
        self.visualizarQuery(queryString)

    def solo(self, soloItem):
        self.pendientesCheckBox.setChecked(False)
        self.enproduccionCheckBox.setChecked(False)
        self.terminadasCheckBox.setChecked(False)
        self.entregadasCheckBox.setChecked(False)
        self.anuladasCheckBox.setChecked(False)
        soloItem.setChecked(True)

    def pushear(self):
        # os.system("gnome-terminal -e 'bash ./actualizar.sh &'" )
        # print("push")
        os.system("%s 'bash ./actualizar.sh'" % TERMINALCOMMAND)

    def abrirDB(self):
        os.system("xdg-open infomesas.db &")

    def clienteSolo(self):
        if self.clienteComboBox.currentText() == " [elegir]":
            self.clienteComboBox.setCurrentText(self.pedidosTableWidget.selectedItems()[2].text())
        else:
            self.clienteComboBox.setCurrentText(" [elegir]")

    def duplicarPedido(self):
        if len(self.pedidosTableWidget.selectedItems()) == 0:
            mensaje('no hay pedido seleccionado')
            return()
        query = QSqlQuery()
        query.prepare("INSERT INTO pedidos (fecha, cliente, modelo, chapa, notas, medidaCerrada, medidaAbierta, medidaAncho, precio, estado, fechaEntrega, lugarEntrega) VALUES (:fecha, :cliente, :modelo, :chapa, :notas, :medidaCerrada, :medidaAbierta, :medidaAncho, :precio, :estado, :fechaEntrega, :lugarEntrega)")
        fechaDT = datetime.strptime(self.pedidosTableWidget.selectedItems()[1].text(), "%d-%m-%Y")
        diaString = datetime.strftime(fechaDT, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fecha", diaString)
        query.bindValue(":cliente", devuelvoIdCliente(self.pedidosTableWidget.selectedItems()[2].text()))
        modelo = self.pedidosTableWidget.selectedItems()[3].text()
        queryModelo = QSqlQuery("SELECT idModelo FROM modelos WHERE modelo = '%s'" % modelo)
        queryModelo.first()
        query.bindValue(":modelo", queryModelo.value(0))
        chapa = self.pedidosTableWidget.selectedItems()[4].text()
        queryChapa = QSqlQuery("SELECT idChapa FROM chapas WHERE chapa = '%s'" % chapa)
        queryChapa.first()
        query.bindValue(":chapa", queryChapa.value(0))
        query.bindValue(":notas", self.pedidosTableWidget.selectedItems()[5].text())
        query.bindValue(":medidaCerrada", self.pedidosTableWidget.selectedItems()[6].text())
        query.bindValue(":medidaAbierta", self.pedidosTableWidget.selectedItems()[7].text())
        query.bindValue(":medidaAncho", self.pedidosTableWidget.selectedItems()[8].text())
        query.bindValue(":precio", int(self.pedidosTableWidget.selectedItems()[9].text()))
        query.bindValue(":estado", self.pedidosTableWidget.selectedItems()[10].text())
        if self.pedidosTableWidget.selectedItems()[11].text() != '':
            fechaDT = datetime.strptime(self.pedidosTableWidget.selectedItems()[11].text(), "%d-%m-%Y")
            diaString = datetime.strftime(fechaDT, "%Y-%m-%d %H:%M:%S")
            query.bindValue(":fechaEntrega", diaString)
            queryEntrega = QSqlQuery("SELECT idLugarEntrega FROM lugaresEntrega WHERE nombre = '%s'" % self.pedidosTableWidget.selectedItems()[12].text())
            queryEntrega.first()
            query.bindValue(":lugarEntrega", queryEntrega.value(0))
        query.exec()
        self.vistaChanged()

    def onHeaderClicked(self, indice):
        self.pedidosTableWidget.sortItems(indice, Qt.SortOrder.AscendingOrder)

    def administrarModelos(self):
        self.tabla = TableWindow("modelos")
        self.tabla.show()

    def administrarClientes(self):
        self.tabla = TableWindow("clientes")
        self.tabla.show()

    def administrarProveedores(self):
        self.tabla = TableWindow("proveedores")
        self.tabla.show()

    def administrarLugaresEntrega(self):
        self.tabla = TableWindow("lugaresEntrega")
        self.tabla.show()


class PedidoDialog(QDialog):
    def __init__(self, id):
        super().__init__()
        uic.loadUi("pedidoDialog.ui", self)
        self.id = id
        self.returnValues = []
        self.initUI()

    def initUI(self):
        if self.id == 0:
            self.pasarAccPushButton.setEnabled(False)
        clientes = llenoClientes()
        self.clienteComboBox.addItems(clientes)
        query = QSqlQuery("SELECT modelo FROM modelos")
        while query.next():
            self.modeloListWidget.addItem(query.value(0))
        query = QSqlQuery("SELECT chapa FROM chapas")
        while query.next():
            self.chapaListWidget.addItem(query.value(0))
        estados = ['pendiente', 'en produccion', 'terminada', 'entregada', 'anulada']
        self.estadoListWidget.addItems(estados)
        query = QSqlQuery("SELECT nombre FROM lugaresEntrega ORDER BY nombre")
        while query.next():
            self.lugarEntregaComboBox.addItem(query.value(0))
        # lleno los items correspondientes
        # id = 0 implica nuevo pedido
        if self.id == 0:
            self.fechaDateEdit.setDate(QDate.currentDate())
            self.precioLineEdit.setText('0')
            estadoItem = self.estadoListWidget.findItems('pendiente', Qt.MatchFlag.MatchExactly)
            self.estadoListWidget.setCurrentItem(estadoItem[0])
        else:
            dialist = self.id[1].text().split('-')
            dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
            self.fechaDateEdit.setDate(dia)
            self.clienteComboBox.setCurrentText(self.id[2].text())
            modeloItem = self.modeloListWidget.findItems(self.id[3].text(), Qt.MatchFlag.MatchExactly)
            self.modeloListWidget.setCurrentItem(modeloItem[0])
            chapaItem = self.chapaListWidget.findItems(self.id[4].text(), Qt.MatchFlag.MatchExactly)
            self.chapaListWidget.setCurrentItem(chapaItem[0])
            self.notasPlainTextEdit.setPlainText(self.id[5].text())
            self.medidaCerradaSpinBox.setValue(int(self.id[6].text()))
            self.medidaAbiertaSpinBox.setValue(int(self.id[7].text()))
            self.anchoSpinBox.setValue(int(self.id[8].text()))
            self.precioLineEdit.setText(self.id[9].text())
            estadoItem = self.estadoListWidget.findItems(self.id[10].text(), Qt.MatchFlag.MatchExactly)
            self.estadoListWidget.setCurrentItem(estadoItem[0])
            if self.id[11].text() != '':
                dialist = self.id[11].text().split('-')
                dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
                self.fechaEntregaDateEdit.setDate(dia)
                self.lugarEntregaComboBox.setCurrentText(self.id[12].text())
            else:
                self.fechaEntregaDateEdit.setDate(QDate.currentDate())
                self.fechaEntregaDateEdit.setEnabled(False)
                self.lugarEntregaComboBox.setEnabled(False)
            # self.lugarEntregaComboBox.setCurrentText(self.id[12].text())
            query = QSqlQuery("SELECT pasadoACC FROM pedidos WHERE idPedido = '%s'" % self.id[0].text())
            query.last()
            if query.value(0) == 1:
                self.pasarAccPushButton.setEnabled(False)


        self.estadoListWidget.itemSelectionChanged.connect(self.cambioEstado)
        self.okPushButton.clicked.connect(self.save)
        self.cancelPushButton.clicked.connect(self.reject)
        self.filterListaLineEdit.textChanged.connect(self.mostrarLista)
        self.calcularPushButton.setShortcut("Ctrl+Return")
        self.calcularPushButton.clicked.connect(self.calcular)
        self.ultimaLista=open('ultimalista.txt').readlines()
        self.pasarAccPushButton.clicked.connect(self.pasarAcc)
        self.medidaCerradaSpinBox.valueChanged.connect(self.autoFilterUltimaLista)

        self.llenarRapidFill()
        self.rapidFillComboBox.currentTextChanged.connect(self.rapidFillChanged)

    def cambioEstado(self):
        if self.estadoListWidget.currentItem().text() == 'entregada':
            if self.lugarEntregaComboBox.isEnabled() == False:
                query = QSqlQuery("SELECT lugarEntrega FROM pedidos WHERE cliente = '%s' AND lugarEntrega IS NOT NULL ORDER BY fechaEntrega" % devuelvoIdCliente(self.clienteComboBox.currentText()))
                query.last()
                self.lugarEntregaComboBox.setCurrentText(devuelvoNombreLugarEntrega(query.value(0)))
            self.fechaEntregaDateEdit.setEnabled(True)
            self.lugarEntregaComboBox.setEnabled(True)
        else:
            self.fechaEntregaDateEdit.setEnabled(False)
            self.lugarEntregaComboBox.setEnabled(False)
 
    def calcular(self):
        res = round(eval(self.precioLineEdit.text()))
        self.precioLineEdit.setText(str(res))

    def save(self):
        # checks
        if self.modeloListWidget.currentRow() == -1:
            mensaje("modelo no seleccionado")
            return
        if self.chapaListWidget.currentRow() == -1:
            mensaje("chapa no seleccionada")
            return
        if self.clienteComboBox.currentText() == " [elegir]":
            mensaje("cliente no seleccionado")
            return
        try:
            res = int(self.precioLineEdit.text())
        except:
            mensaje("importe no correcto")
            return
        #save
        query = QSqlQuery()
        if self.id == 0:
            query.prepare("INSERT INTO pedidos (fecha, cliente, modelo, chapa, notas, medidaCerrada, medidaAbierta, medidaAncho, precio, estado, fechaEntrega, lugarEntrega) VALUES (:fecha, :cliente, :modelo, :chapa, :notas, :medidaCerrada, :medidaAbierta, :medidaAncho, :precio, :estado, :fechaEntrega, :lugarEntrega)")
            self.returnValues.append(0)
        else:
            query.prepare("UPDATE pedidos SET fecha=:fecha, cliente=:cliente, modelo=:modelo, chapa=:chapa, notas=:notas, medidaCerrada=:medidaCerrada, medidaAbierta=:medidaAbierta, medidaAncho=:medidaAncho, precio=:precio, estado=:estado, fechaEntrega=:fechaEntrega, lugarEntrega=:lugarEntrega WHERE idPedido = :idPedido")
            query.bindValue(":idPedido", int(self.id[0].text()))
            self.returnValues.append(self.id[0].text())
        dia = self.fechaDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fecha", diaString)
        query.bindValue(":cliente", devuelvoIdCliente(self.clienteComboBox.currentText()))
        modelo = self.modeloListWidget.currentItem().text()
        queryModelo = QSqlQuery("SELECT idModelo FROM modelos WHERE modelo = '%s'" % modelo)
        queryModelo.first()
        query.bindValue(":modelo", queryModelo.value(0))
        chapa = self.chapaListWidget.currentItem().text()
        queryChapa = QSqlQuery("SELECT idChapa FROM chapas WHERE chapa = '%s'" % chapa)
        queryChapa.first()
        query.bindValue(":chapa", queryChapa.value(0))
        query.bindValue(":notas", self.notasPlainTextEdit.toPlainText())
        query.bindValue(":medidaCerrada", self.medidaCerradaSpinBox.value())
        query.bindValue(":medidaAbierta", self.medidaAbiertaSpinBox.value())
        query.bindValue(":medidaAncho", self.anchoSpinBox.value())
        query.bindValue(":precio", int(self.precioLineEdit.text()))
        query.bindValue(":estado", self.estadoListWidget.currentItem().text())
        if self.fechaEntregaDateEdit.isEnabled() == True:
            dia = self.fechaEntregaDateEdit.date().toPyDate()
            diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
            query.bindValue(":fechaEntrega", diaString)
            queryEntrega = QSqlQuery("SELECT idLugarEntrega FROM lugaresEntrega WHERE nombre = '%s'" % self.lugarEntregaComboBox.currentText())
            queryEntrega.first()
            query.bindValue(":lugarEntrega", queryEntrega.value(0))
        query.exec()
        dia = self.fechaDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%d-%m-%Y")
        self.returnValues.append(diaString)
        self.returnValues.append(self.clienteComboBox.currentText())
        self.returnValues.append(self.modeloListWidget.currentItem().text())
        self.returnValues.append(self.chapaListWidget.currentItem().text())
        self.returnValues.append(self.notasPlainTextEdit.toPlainText())
        self.returnValues.append(str(self.medidaCerradaSpinBox.value()))
        self.returnValues.append(str(self.medidaAbiertaSpinBox.value()))
        self.returnValues.append(str(self.anchoSpinBox.value()))
        self.returnValues.append(self.precioLineEdit.text())
        self.returnValues.append(self.estadoListWidget.currentItem().text())
        if self.fechaEntregaDateEdit.isEnabled() == True:
            dia = self.fechaEntregaDateEdit.date().toPyDate()
            diaString = datetime.strftime(dia, "%d-%m-%Y")
            self.returnValues.append(diaString)
            self.returnValues.append(self.lugarEntregaComboBox.currentText())
        self.accept()
    
    def mostrarLista(self):
        filtradoLista = []
        for item in self.ultimaLista:
            if self.filterListaLineEdit.text() in item:
                filtradoLista.append(item)
        filtradoString = ''.join(filtradoLista)
        self.listaPlainTextEdit.setPlainText(filtradoString)

    def pasarAcc(self):
        query = QSqlQuery()
        query.prepare("INSERT INTO cuentasCorrientes (cliente, fecha, concepto, importe) VALUES (:cliente, :fecha, :concepto, :importe)")
        query.bindValue(":cliente", devuelvoIdCliente(self.clienteComboBox.currentText()))
        dia = self.fechaDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fecha", diaString)
        concepto = "%s %s %s %s %s" % (self.modeloListWidget.currentItem().text(), self.chapaListWidget.currentItem().text(), self.medidaCerradaSpinBox.value(), self.medidaAbiertaSpinBox.value(), self.anchoSpinBox.value())
        query.bindValue(":concepto", concepto)
        query.bindValue(":importe", int(self.precioLineEdit.text()))
        query.exec()
        #actualizo saldo en tabla clientes
        queryImportes = QSqlQuery("SELECT importe FROM cuentasCorrientes WHERE cliente = '%s'" % devuelvoIdCliente(self.clienteComboBox.currentText()))
        saldo = 0
        while queryImportes.next():
            saldo += queryImportes.value(0)
        queryCliente = QSqlQuery("UPDATE clientes SET saldo = '%s' WHERE idCliente = '%s'" % (saldo, devuelvoIdCliente(self.clienteComboBox.currentText())))
        #marco como actualizado en tabla pedidos
        query2 = QSqlQuery("UPDATE pedidos SET pasadoACC = 1 WHERE idPedido = '%s'" % self.id[0].text())
        self.pasarAccPushButton.setEnabled(False)

    def autoFilterUltimaLista(self):
        self.filterListaLineEdit.setText(self.medidaCerradaSpinBox.cleanText())

    def llenarRapidFill(self):
        pedidosComunes = []
        pedidosComunes.append("")
        pedidosComunes.append("120 a 160 x 80")
        pedidosComunes.append("140 a 180 x 85")
        pedidosComunes.append("160 a 200 x 85")
        pedidosComunes.append("180 a 220 x 90")
        pedidosComunes.append("180 a 220 x 90")
        pedidosComunes.append("200 a 240 x 90")
        pedidosComunes.append("120 a 120 x 80")
        pedidosComunes.append("140 a 140 x 85")
        pedidosComunes.append("160 a 160 x 85")
        pedidosComunes.append("180 a 180 x 90")
        pedidosComunes.append("200 a 200 x 90")

        self.rapidFillComboBox.addItems(pedidosComunes)

    def rapidFillChanged(self):
        medidas = self.rapidFillComboBox.currentText().split()
        self.medidaCerradaSpinBox.setValue(int(medidas[0]))
        self.medidaAbiertaSpinBox.setValue(int(medidas[2]))
        self.anchoSpinBox.setValue(int(medidas[4]))


class SumasSaldosDialog(QDialog):
    def __init__(self, id):
        super().__init__()
        uic.loadUi("sumasSaldos.ui", self)
        self.id = id
        self.initUI()

    def initUI(self):
        self.setWindowTitle(devuelvoNombreCliente(self.id))
        self.nuevoPushButton.clicked.connect(self.nuevoMovimiento)
        self.salirPushButton.clicked.connect(self.accept)
        self.sumasSaldosTableWidget.setColumnCount(6)
        self.sumasSaldosTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sumasSaldosTableWidget.setHorizontalHeaderLabels(["Id", "Fecha", "Concepto", "Debe", "Haber", "Saldo"])
        self.sumasSaldosTableWidget.itemDoubleClicked.connect(self.movimiento)
        self.cargarTabla()

    def cargarTabla(self):
        self.sumasSaldosTableWidget.setRowCount(0)
        queryString = "SELECT * FROM cuentasCorrientes WHERE cliente = '%s'" % self.id
        query = QSqlQuery(queryString)
        saldo = 0
        while query.next():        
            rows = self.sumasSaldosTableWidget.rowCount()
            self.sumasSaldosTableWidget.setRowCount(rows + 1)
            self.sumasSaldosTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            fecha = datetime.strptime(query.value(2), "%Y-%m-%d %H:%M:%S")
            fechap = fecha.strftime("%d-%m-%Y")
            self.sumasSaldosTableWidget.setItem(rows, 1, QTableWidgetItem(fechap))
            self.sumasSaldosTableWidget.setItem(rows, 2, QTableWidgetItem(query.value(3)))
            sumaItem = QTableWidgetItem(str(query.value(4)))
            sumaItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if query.value(4) >= 0:
                self.sumasSaldosTableWidget.setItem(rows, 3, sumaItem)
            else:
                sumaItem.setText(sumaItem.text()[1:]) # le saco el signo negativo
                self.sumasSaldosTableWidget.setItem(rows, 4, sumaItem)
            saldo += query.value(4)
            saldoItem = QTableWidgetItem(str(saldo))
            saldoItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.sumasSaldosTableWidget.setItem(rows, 5, saldoItem)
        self.sumasSaldosTableWidget.scrollToBottom()
        self.sumasSaldosTableWidget.resizeColumnsToContents()

    def movimiento(self):
        self.mov = Movimiento(self.sumasSaldosTableWidget.selectedItems(), self.id)
        if self.mov.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()

    def nuevoMovimiento(self):
        self.mov = Movimiento(0, self.id)
        if self.mov.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()
 

class ClientesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("clientes.ui", self)
        self.initUI()

    def initUI(self):
        self.clientesTableWidget.setColumnCount(3)
        self.clientesTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.clientesTableWidget.setHorizontalHeaderLabels(["ID", "Cliente", "Saldo"])
        self.clientesTableWidget.itemDoubleClicked.connect(self.sumasSaldosShow)
        self.salirPushButton.clicked.connect(self.close)
        self.cargarTabla()

    def sumasSaldosShow(self):
        self.sumasSaldos = SumasSaldosDialog(self.clientesTableWidget.selectedItems()[0].text())
        if self.sumasSaldos.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()

    def cargarTabla(self):
        self.clientesTableWidget.setRowCount(0)
        query = QSqlQuery("SELECT * FROM clientes ORDER BY nombre ASC")
        totalsaldo = 0
        while query.next():        
            rows = self.clientesTableWidget.rowCount()
            self.clientesTableWidget.setRowCount(rows + 1)
            self.clientesTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            cliente = QTableWidgetItem(devuelvoNombreCliente(query.value(0)))
            self.clientesTableWidget.setItem(rows, 1, cliente)
            saldo = QTableWidgetItem(str(query.value(5)))
            totalsaldo += query.value(5)
            saldo.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.clientesTableWidget.setItem(rows, 2, QTableWidgetItem(saldo))
        self.clientesTableWidget.resizeColumnsToContents()
        self.clientesTableWidget.sortItems(2, Qt.SortOrder.DescendingOrder)
        self.statusbar.showMessage("total por cobrar %s " % str(totalsaldo))


class Movimiento(QDialog):
    def __init__(self, id, provId):
        super().__init__()
        uic.loadUi("movimiento.ui", self)
        self.id = id
        self.provId = provId
        self.initUI()

    def initUI(self):
        self.pagoPushButton.clicked.connect(self.pago)
        self.debeRadioButton.setChecked(True)
        self.setWindowTitle(devuelvoNombreCliente(self.provId))
        # lleno los items correspondientes
        # id = 0 implica nuevo pedido
        if self.id == 0:
            self.fechaDateEdit.setDate(QDate.currentDate())
            self.importeLineEdit.setText('0')
        else:
            dialist = self.id[1].text().split('-')
            dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
            self.fechaDateEdit.setDate(dia)
            self.conceptoLineEdit.setText(self.id[2].text())
            queryString = "SELECT importe FROM cuentasCorrientes WHERE idcc = '%i'" % int(self.id[0].text())
            querySigno = QSqlQuery(queryString)
            querySigno.first()
            if querySigno.value(0) >= 0:
                self.debeRadioButton.setChecked(True)
            else:
                self.haberRadioButton.setChecked(True)
            importe = int(self.id[3].text())
            self.importeLineEdit.setText(str(importe))
        self.okPushButton.clicked.connect(self.save)
        self.cancelPushButton.clicked.connect(self.reject)

    def save(self):
        query = QSqlQuery()
        if self.id == 0:
            queryString = "INSERT INTO cuentasCorrientes (cliente, fecha, concepto, importe) VALUES (:proveedor, :fecha, :concepto, :importe)"
            query.prepare(queryString)
        else:
            queryString = "UPDATE cuentasCorrientes SET cliente=:proveedor, fecha=:fecha, concepto=:concepto, importe=:importe WHERE idcc = :idDeuda"
            query.prepare(queryString)
            query.bindValue(":idDeuda", int(self.id[0].text()))
        query.bindValue(":proveedor", self.provId)
        dia = self.fechaDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fecha", diaString)
        query.bindValue(":concepto", self.conceptoLineEdit.text())
        importe = int(self.importeLineEdit.text())
        if self.haberRadioButton.isChecked() == True:
          importe = importe * (-1) 
        query.bindValue(":importe", importe)
        query.exec()
        # actualizo saldo en tabla clientes
        queryImportes = QSqlQuery("SELECT importe FROM cuentasCorrientes WHERE cliente = '%s'" % self.provId)
        saldo = 0
        while queryImportes.next():
            saldo += queryImportes.value(0)
        queryProveedor = QSqlQuery("UPDATE clientes SET saldo = '%s' WHERE idCliente = '%s'" % (saldo, self.provId))
        self.accept()
        
    def pago(self):
        query = QSqlQuery("SELECT saldo FROM clientes WHERE idCliente = '%s'" % self.provId)
        query.last()
        self.haberRadioButton.setChecked(True)
        self.conceptoLineEdit.setText("pago")
        self.importeLineEdit.setText(str(query.value(0)))
        self.importeLineEdit.setFocus()
        self.importeLineEdit.selectAll()


class ProductosSeguidosWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("productosSeguidos.ui", self)
        self.initUI()

    def initUI(self):
        self.nuevoPushButton.clicked.connect(self.nuevoProducto)
        self.salirPushButton.clicked.connect(self.close)
        self.productosSeguidosTableWidget.setColumnCount(5)
        self.productosSeguidosTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.productosSeguidosTableWidget.setHorizontalHeaderLabels(["ID", "Descripcion", "Fecha", "Proveedor", "Precio"])
        self.productosSeguidosTableWidget.itemDoubleClicked.connect(self.historialPreciosShow)
        self.productosSeguidosTableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.productosSeguidosTableWidget.customContextMenuRequested.connect(self.productoFavorito)
        # self.filtroLineEdit.textChanged.connect(self.cargarTabla)
        self.filtroLineEdit.textChanged.connect(self.cargarTabla)
        self.cargarTabla()

    def historialPreciosShow(self):
        self.historialPrecios = HistorialPreciosDialog(self.productosSeguidosTableWidget.selectedItems())
        if self.historialPrecios.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()

    def cargarTabla(self):
        self.productosSeguidosTableWidget.setRowCount(0)
        filtro = "%" + self.filtroLineEdit.text() + "%"
        # query = QSqlQuery("SELECT * FROM productosSeguidos WHERE descripcion LIKE '%s' ORDER BY descripcion ASC" % filtro)
        query = QSqlQuery("SELECT * FROM productosSeguidos WHERE descripcion LIKE '%s' ORDER BY favorito DESC" % filtro)
        while query.next():        
            rows = self.productosSeguidosTableWidget.rowCount()
            self.productosSeguidosTableWidget.setRowCount(rows + 1)
            self.productosSeguidosTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            # self.productosSeguidosTableWidget.setItem(rows, 1, QTableWidgetItem(query.value(1)))
            item = QTableWidgetItem(query.value(1))
            if query.value(2) == 1:
                item.setBackground(QBrush(QColor("lightgreen")))
            self.productosSeguidosTableWidget.setItem(rows, 1, item)

            queryPrecio = QSqlQuery("SELECT * FROM productosSeguidosPrecios WHERE idProducto = '%s'" % query.value(0))
            queryPrecio.last()
            if queryPrecio.value(1):
                fecha = datetime.strptime(queryPrecio.value(4), "%Y-%m-%d %H:%M:%S")
                fechap = fecha.strftime("%d-%m-%Y")
                self.productosSeguidosTableWidget.setItem(rows, 2, QTableWidgetItem(fechap))
                prov = devuelvoNombreProveedor(queryPrecio.value(3))
                self.productosSeguidosTableWidget.setItem(rows, 3, QTableWidgetItem(prov))
                precioItem = QTableWidgetItem(str(queryPrecio.value(2)))
                precioItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.productosSeguidosTableWidget.setItem(rows, 4, precioItem)
        self.productosSeguidosTableWidget.resizeColumnsToContents()
        self.filtroLineEdit.setFocus()

    def nuevoProducto(self):
        descripcion, okPressed = QInputDialog.getText(self, "Nuevo producto","Descripcion", QLineEdit.EchoMode.Normal, "")
        if okPressed and descripcion != '':
            query = QSqlQuery("INSERT INTO productosSeguidos (descripcion) VALUES ('%s')" % descripcion) 
            self.cargarTabla()

    def productoFavorito(self):
        producto = self.productosSeguidosTableWidget.selectedItems()[0].text()
        query = QSqlQuery("SELECT favorito FROM productosSeguidos WHERE idProducto = '%s'" % producto) 
        query.first()
        if query.value(0) == 0:
            query = QSqlQuery("UPDATE productosSeguidos SET favorito = 1 WHERE idProducto = '%s'" % producto) 
        else:
            query = QSqlQuery("UPDATE productosSeguidos SET favorito = 0 WHERE idProducto = '%s'" % producto) 

        self.cargarTabla()


class HistorialPreciosDialog(QDialog):
    def __init__(self, id):
        super().__init__()
        uic.loadUi("historialPrecios.ui", self)
        self.id = id
        self.initUI()

    def initUI(self):
        # self.dialogButtonBox.accepted.connect(self.save)
        self.setWindowTitle(self.id[1].text())
        self.historialPreciosTableWidget.setColumnCount(5)
        self.historialPreciosTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.historialPreciosTableWidget.setHorizontalHeaderLabels(["ID", "Proveedor", "Fecha", "Precio", "Dif"])
        self.historialPreciosTableWidget.itemDoubleClicked.connect(self.editMov)
        self.nuevoPushButton.clicked.connect(self.nuevoPrecioShow)
        # self.dialogButtonBox.accepted.connect(self.accept)
        self.okPushButton.clicked.connect(self.accept)
        self.cargarTabla()

    def cargarTabla(self):
        self.historialPreciosTableWidget.setRowCount(0)
        query = QSqlQuery("SELECT * FROM productosSeguidosPrecios WHERE idProducto = '%s'" % self.id[0].text())
        while query.next():        
            rows = self.historialPreciosTableWidget.rowCount()
            self.historialPreciosTableWidget.setRowCount(rows + 1)
            self.historialPreciosTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            self.historialPreciosTableWidget.setItem(rows, 1, QTableWidgetItem(devuelvoNombreProveedor(query.value(3))))
            fecha = datetime.strptime(query.value(4), "%Y-%m-%d %H:%M:%S")
            fechap = fecha.strftime("%d-%m-%Y")
            self.historialPreciosTableWidget.setItem(rows, 2, QTableWidgetItem(fechap))
            self.historialPreciosTableWidget.setItem(rows, 3, QTableWidgetItem(str(query.value(2))))
            if rows > 0:
                precioAnterior = int(self.historialPreciosTableWidget.item(rows-1, 3).text())
                precioActual = int(self.historialPreciosTableWidget.item(rows, 3).text())
                porcentaje = (precioActual * 100 / precioAnterior) - 100
                self.historialPreciosTableWidget.setItem(rows, 4, QTableWidgetItem(str(round(porcentaje, 2))))

    def nuevoPrecioShow(self):
        # self.nuevoPrecio = NuevoPrecioDialog(self.historialPreciosTableWidget.selectedItems())
        self.nuevoPrecio = NuevoPrecioDialog(0, self.id)
        if self.nuevoPrecio.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()

    def editMov(self):
        self.nuevoPrecio = NuevoPrecioDialog(self.historialPreciosTableWidget.selectedItems(), self.id)
        if self.nuevoPrecio.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()


class NuevoPrecioDialog(QDialog):
    def __init__(self, tablaAnterior, id):
        super().__init__()
        uic.loadUi("historialPreciosMov.ui", self)
        self.tablaAnterior = tablaAnterior
        self.id = id
        self.initUI()

    def initUI(self):
        proveedores = llenoProveedores()
        self.setWindowTitle(self.id[1].text())
        self.proveedoresComboBox.addItems(proveedores)
        self.okPushButton.clicked.connect(self.save)
        self.cancelPushButton.clicked.connect(self.reject)
        if self.tablaAnterior == 0:
            self.fechaDateEdit.setDate(QDate.currentDate())
            self.importeLineEdit.setText('0')
            if len(self.id) != 2:
                self.proveedoresComboBox.setCurrentText(self.id[3].text())
        else:
            dialist = self.tablaAnterior[2].text().split('-')
            dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
            self.fechaDateEdit.setDate(dia)
            self.importeLineEdit.setText(self.tablaAnterior[3].text())
            self.proveedoresComboBox.setCurrentText(self.tablaAnterior[1].text())
        self.importeLineEdit.setFocus()

    def save(self):
        query = QSqlQuery() 
        if self.tablaAnterior == 0:
            query.prepare("INSERT INTO productosSeguidosPrecios (idProducto, precio, proveedor, fecha) VALUES (:idProducto, :precio, :proveedor, :fecha)")
        else:
            query.prepare("UPDATE productosSeguidosPrecios SET idProducto=:idProducto, precio=:precio, proveedor=:proveedor, fecha=:fecha WHERE idProductoPrecio=:idProductoPrecio")
            query.bindValue(":idProductoPrecio", self.tablaAnterior[0].text())
        query.bindValue(":idProducto", self.id[0].text())
        query.bindValue(":precio", self.importeLineEdit.text())
        query.bindValue(":proveedor", devuelvoIdProveedor(self.proveedoresComboBox.currentText()))
        dia = self.fechaDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fecha", diaString)
        query.exec()
        self.accept()


class ChequesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("cheques.ui", self)
        self.initUI()

    def initUI(self):
        self.chequesTableWidget.setColumnCount(9)
        self.chequesTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.chequesTableWidget.setHorizontalHeaderLabels(["ID", "Recibido", "Cliente", "Fecha", "Banco", "Numero", "Importe", "Entregado", "Proveedor"])
        self.chequesTableWidget.itemDoubleClicked.connect(self.editarCheque)
        self.nuevoPushButton.clicked.connect(self.nuevoCheque)
        self.salirPushButton.clicked.connect(self.close)
        self.cargarTabla()

    def cargarTabla(self):
        saldo = 0
        self.chequesTableWidget.setRowCount(0)
        query = QSqlQuery("SELECT * FROM cheques ORDER BY fechaRecibido DESC")
        while query.next():        
            rows = self.chequesTableWidget.rowCount()
            self.chequesTableWidget.setRowCount(rows + 1)
            self.chequesTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            fecha = datetime.strptime(query.value(1), "%Y-%m-%d %H:%M:%S")
            fechap = fecha.strftime("%d-%m-%Y")
            self.chequesTableWidget.setItem(rows, 1, QTableWidgetItem(fechap))
            self.chequesTableWidget.setItem(rows, 2, QTableWidgetItem(devuelvoNombreCliente(query.value(2))))
            fecha = datetime.strptime(query.value(3), "%Y-%m-%d %H:%M:%S")
            fechap = fecha.strftime("%d-%m-%Y")
            self.chequesTableWidget.setItem(rows, 3, QTableWidgetItem(fechap))
            self.chequesTableWidget.setItem(rows, 4, QTableWidgetItem(query.value(4)))
            self.chequesTableWidget.setItem(rows, 5, QTableWidgetItem(str(query.value(5))))
            importe = QTableWidgetItem(str(query.value(6)))
            importe.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.chequesTableWidget.setItem(rows, 6, QTableWidgetItem(importe))
            if query.value(7):
                fecha = datetime.strptime(query.value(7), "%Y-%m-%d %H:%M:%S")
                fechap = fecha.strftime("%d-%m-%Y")
                proveedorWidget = QTableWidgetItem(devuelvoNombreProveedor(query.value(8)))
            else:
                fechap = None
                proveedorWidget = QTableWidgetItem('disponible')
                proveedorWidget.setForeground(QBrush(QColor('green')))
                saldo += query.value(6)
            self.chequesTableWidget.setItem(rows, 7, QTableWidgetItem(fechap))
            self.chequesTableWidget.setItem(rows, 8, proveedorWidget)
        self.chequesTableWidget.resizeColumnsToContents()
        self.statusbar.showMessage("Total disponible: %s" % saldo)

    def editarCheque(self):
        self.cheque = ChequeDialog(self.chequesTableWidget.selectedItems())
        if self.cheque.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()

    def nuevoCheque(self):
        self.cheque = ChequeDialog(0)
        if self.cheque.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()


class ChequeDialog(QDialog):
    def __init__(self, id):
        super().__init__()
        uic.loadUi("chequeDialog.ui", self)
        self.id = id
        self.initUI()

    def initUI(self):
        self.proveedorComboBox.currentTextChanged.connect(self.chequeEntregado)
        # self.dialogButtonBox.accepted.connect(self.save)
        self.okPushButton.clicked.connect(self.save)
        self.cancelPushButton.clicked.connect(self.reject)
        clientes = llenoClientes()
        self.clienteComboBox.addItems(clientes)
        proveedores = llenoProveedores()
        self.proveedorComboBox.addItems(proveedores)
        if self.id == 0:
            self.recibidoDateEdit.setDate(QDate.currentDate())
            self.fechaChequeDateEdit.setDate(QDate.currentDate())
            self.fechaEntregadoDateEdit.setDate(QDate.currentDate())
            self.fechaEntregadoDateEdit.setEnabled(False)
            self.proveedorComboBox.setCurrentText("[elegir]")
        else:
            dialist = self.id[1].text().split('-')
            dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
            self.recibidoDateEdit.setDate(dia)
            self.clienteComboBox.setCurrentText(self.id[2].text())
            dialist = self.id[3].text().split('-')
            dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
            self.fechaChequeDateEdit.setDate(dia)
            self.bancoLineEdit.setText(self.id[4].text())
            self.numeroLineEdit.setText(self.id[5].text())
            self.importeLineEdit.setText(self.id[6].text())
            if self.id[7].text() != '':
                dialist = self.id[7].text().split('-')
                dia = QDate(int(dialist[2]), int(dialist[1]), int(dialist[0]))
                self.fechaEntregadoDateEdit.setDate(dia)
                self.proveedorComboBox.setCurrentText(self.id[8].text())
            else:
                self.fechaEntregadoDateEdit.setDate(QDate.currentDate())
                self.fechaEntregadoDateEdit.setEnabled(False)
                self.proveedorComboBox.setCurrentText("[elegir]")

    def chequeEntregado(self):
        if self.proveedorComboBox.currentText() != "[elegir]":
            self.fechaEntregadoDateEdit.setEnabled(True)

    def save(self):
        # check
        if self.clienteComboBox.currentText() == " [elegir]":
            mensaje("cliente no seleccionado")
            return
        if self.bancoLineEdit.text() == '':
            mensaje("banco no seleccionado")
            return
        if self.numeroLineEdit.text() == '':
            mensaje("numero no seleccionado")
            return
        if self.importeLineEdit.text() == '':
            mensaje("importe no seleccionado")
            return

        #save
        query = QSqlQuery()
        if self.id == 0:
            query.prepare("INSERT INTO cheques (fechaRecibido, cliente, fechaCheque, banco, numero, importe, fechaEntregado, entregadoA) VALUES (:fechaRecibido, :cliente, :fechaCheque, :banco, :numero, :importe, :fechaEntregado, :entregadoA)")
        else:
            query.prepare("UPDATE cheques SET fechaRecibido=:fechaRecibido, cliente=:cliente, fechaCheque=:fechaCheque, banco=:banco, importe=:importe, fechaEntregado=:fechaEntregado, entregadoA=:entregadoA WHERE idCheque=:idCheque")
            query.bindValue(":idCheque", int(self.id[0].text()))
        dia = self.recibidoDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fechaRecibido", diaString)
        query.bindValue(":cliente", devuelvoIdCliente(self.clienteComboBox.currentText()))
        dia = self.fechaChequeDateEdit.date().toPyDate()
        diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
        query.bindValue(":fechaCheque", diaString)
        query.bindValue(":banco", self.bancoLineEdit.text())
        query.bindValue(":numero", self.numeroLineEdit.text())
        query.bindValue(":importe", int(self.importeLineEdit.text()))
        if self.fechaEntregadoDateEdit.isEnabled() == True:
            dia = self.fechaEntregadoDateEdit.date().toPyDate()
            diaString = datetime.strftime(dia, "%Y-%m-%d %H:%M:%S")
            query.bindValue(":fechaEntregado", diaString)
            query.bindValue(":entregadoA", devuelvoIdProveedor(self.proveedorComboBox.currentText()))
        query.exec()
        self.accept()

 
class NotasWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("notas.ui", self)
        self.initUI()

    def initUI(self):
        self.nuevoPushButton.clicked.connect(self.nuevaNota)
        self.eliminarPushButton.clicked.connect(self.eliminarNota)
        self.salirPushButton.clicked.connect(self.close)
        self.notasTableWidget.setColumnCount(2)
        self.notasTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.notasTableWidget.setHorizontalHeaderLabels(["ID", "Titulo"])
        self.notasTableWidget.itemDoubleClicked.connect(self.notaShow)
        self.cargarTabla()

    def notaShow(self):
        self.nota = NotaDialog(self.notasTableWidget.selectedItems())
        if self.nota.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()

    def cargarTabla(self):
        self.notasTableWidget.setRowCount(0)
        query = QSqlQuery("SELECT * FROM notas ORDER BY titulo ASC")
        while query.next():        
            rows = self.notasTableWidget.rowCount()
            self.notasTableWidget.setRowCount(rows + 1)
            self.notasTableWidget.setItem(rows, 0, QTableWidgetItem(str(query.value(0))))
            self.notasTableWidget.setItem(rows, 1, QTableWidgetItem(query.value(1)))
        self.notasTableWidget.resizeColumnsToContents()
        
    def nuevaNota(self):
        self.nota = NotaDialog(0)
        if self.nota.exec() == QDialog.DialogCode.Accepted:
            self.cargarTabla()
    
    def eliminarNota(self):
        if len(self.notasTableWidget.selectedItems()) == 0:
            mensaje("no hay nota seleccionada")
            return

        reply = QMessageBox.question(self, 'Eliminar', 'Esta seguro de eliminar esta nota?',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            query = QSqlQuery("DELETE FROM notas WHERE idNota = %s" % self.notasTableWidget.selectedItems()[0].text())
            self.cargarTabla()
            
       
class NotaDialog(QDialog):
    def __init__(self, id):
        super().__init__()
        uic.loadUi("nota.ui", self)
        self.id = id
        self.initUI()

    def initUI(self):
        self.guardarPushButton.setShortcut("Ctrl+Return")
        if self.id == 0:
            self.tituloLineEdit.setText("nueva nota")
        else:
            self.tituloLineEdit.setText(self.id[1].text())
            query = QSqlQuery("SELECT nota FROM notas WHERE idNota = %s" % self.id[0].text())
            query.first()
            self.notaPlainTextEdit.setPlainText(query.value(0))
        # self.setWindowTitle(self.id[1].text())
        self.guardarPushButton.clicked.connect(self.save)
        self.cancelPushButton.clicked.connect(self.reject)
        self.tituloLineEdit.textChanged.connect(self.actualizarTitulo)

    def actualizarTitulo(self):
        self.setWindowTitle(self.tituloLineEdit.text())

    def save(self):
        query = QSqlQuery() 
        if self.id == 0:
            query.prepare("INSERT INTO notas (titulo, nota) VALUES (:titulo, :nota)")
        else:
            query.prepare("UPDATE notas SET titulo=:titulo, nota=:nota WHERE idNota=:idNota")
            query.bindValue(":idNota", self.id[0].text())
        query.bindValue(":titulo", self.tituloLineEdit.text())
        query.bindValue(":nota", self.notaPlainTextEdit.toPlainText())
        query.exec()
        self.accept()


class TableWindow(QMainWindow):
    def __init__(self, tabla):
        super().__init__()
        uic.loadUi("tabla.ui", self)
        self.tabla = tabla
        self.initUI()

    def initUI(self):
        self.model = QSqlTableModel()
        self.model.setTable(self.tabla)
        self.model.select()
        self.tableViewTabla.setModel(self.model)
        self.tableViewTabla.setSortingEnabled(True)
        self.tableViewTabla.verticalHeader().setVisible(False)
        self.model.sort(0,Qt.SortOrder.AscendingOrder)
        self.newPushButton.clicked.connect(self.new)
        self.salirPushButton.clicked.connect(self.close)
        self.setWindowTitle(self.tabla)

    def new(self):
        ret = self.model.insertRow(self.model.rowCount())


def llenoClientes():
    clientes = []
    clientes.append(" [elegir]")
    query = QSqlQuery("SELECT nombre FROM clientes")
    while query.next():
        clientes.append(query.value(0))
    clientes.sort()
    return(clientes)

def llenoProveedores():
    proveedores = []
    query = QSqlQuery("SELECT nombre FROM proveedores")
    while query.next():
        proveedores.append(query.value(0))
    proveedores.sort()
    return(proveedores)

def devuelvoIdCliente(nombre):
    queryCliente = QSqlQuery("SELECT idCliente FROM clientes WHERE nombre = '%s'" % nombre)
    queryCliente.first()
    return(queryCliente.value(0))

def devuelvoNombreCliente(id):
    queryCliente = QSqlQuery("SELECT nombre FROM clientes WHERE idCliente = '%s'" % id)
    queryCliente.first()
    return(queryCliente.value(0))

def devuelvoIdProveedor(nombre):
    queryProveedor = QSqlQuery("SELECT idProveedor FROM proveedores WHERE nombre = '%s'" % nombre)
    queryProveedor.first()
    return(queryProveedor.value(0))

def devuelvoNombreProveedor(id):
    queryProveedor = QSqlQuery("SELECT nombre FROM proveedores WHERE idProveedor = '%s'" % id)
    queryProveedor.first()
    return(queryProveedor.value(0))

def devuelvoNombreModelo(id):
    queryModelo = QSqlQuery("SELECT modelo FROM modelos WHERE idModelo = '%s'" % id)
    queryModelo.first()
    return(queryModelo.value(0))

def devuelvoNombreChapa(id):
    queryChapa =  QSqlQuery("SELECT chapa FROM chapas WHERE idChapa = '%s'" % id)
    queryChapa.first()
    return(queryChapa.value(0))
 
def devuelvoNombreLugarEntrega(id):
    queryLugarEntrega = QSqlQuery("SELECT nombre FROM lugaresEntrega WHERE idLugarEntrega = '%s'" % id)
    queryLugarEntrega.first()
    return(queryLugarEntrega.value(0))

def devuelvoUltimoPrecio(id):
    query = QSqlQuery("SELECT precio FROM productosSeguidosPrecios WHERE idProducto = '%s' ORDER BY fecha" % id)
    query.last()
    return(query.value(0))

def mensaje(texto):
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Icon.Information)
    msgBox.setText(texto)
    msgBox.setWindowTitle("Error")
    msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
    msgBox.exec()

def window():
    app = QApplication(sys.argv)
    app.setApplicationName("infomesas-gui.py")
    app.setDesktopFileName("infomesas")
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QPushButton { 
            font-weight: normal; 
        }
        QDateEdit:disabled, QComboBox:disabled, QPushButton:disabled { 
            background-color: #e0e0e0; 
            color: #787878; 
        }
    """)
    # 2. Forzamos una paleta de colores clara por defecto
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 233, 233))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    # ← la conexión va acá, después de QApplication
    global con
    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName("infomesas.db")

    if not con.open():
        QMessageBox.critical(
            None,
            "App Name - Error!",
            "Database Error: %s" % con.lastError().databaseText(),
        )
        sys.exit(1)

    win = InfomesasWindow()
    win.show()
    sys.exit(app.exec())

window()
