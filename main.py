#!/usr/bin/env python3
"""
RDP Connector Pro - Ponto de entrada da aplicação
"""

import sys
import logging
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
    from PySide6.QtCore import Qt
except ImportError:
    print("Erro: PySide6 não está instalado.")
    print("Instale com: pip install PySide6")
    sys.exit(1)

# Adicionar diretório do projeto ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils import setup_logging
from gui.main_window import RDPConnectorWindow

def main():
    """Função principal da aplicação"""
    # Configurar logging
    logger = setup_logging()
    logger.info("=== RDP Connector Pro iniciado ===")
    
    # Criar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("RDP Connector Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("RDPConnector")
    
    # Não fechar quando última janela é fechada (por causa do system tray)
    app.setQuitOnLastWindowClosed(False)
    
    # Verificar suporte ao system tray
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Sistema Tray", 
                           "Sistema não suporta ícone na bandeja do sistema.")
    
    try:
        # Criar e mostrar janela principal
        window = RDPConnectorWindow()
        window.show()
        
        logger.info("Interface inicializada com sucesso")
        
        # Executar aplicação
        return app.exec()
        
    except Exception as e:
        logger.exception("Erro crítico na aplicação")
        QMessageBox.critical(None, "Erro Crítico", 
                           f"Erro crítico na aplicação: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())