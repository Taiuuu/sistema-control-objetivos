    def abrir_importar_excel(self):
        if not hasattr(self, 'importar_excel') or not self.importar_excel.isVisible():
            self.importar_excel = ImportarExcel()
            self.importar_excel.show()
        else:
            self.importar_excel.raise_()
            self.importar_excel.activateWindow()

    def abrir_auditoria(self):
        if not hasattr(self, 'auditoria') or not self.auditoria.isVisible():
            self.auditoria = VistaAuditoria()
            self.auditoria.show()
        else:
            self.auditoria.raise_()
            self.auditoria.activateWindow()
