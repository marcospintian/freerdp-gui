#!/usr/bin/env python3
"""
RDP Connector Pro - Ponto de entrada da aplicação
"""

import sys
import logging
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
    from PySide6.QtCore import Qt, QSharedMemory
except ImportError:
    print("Erro: PySide6 não está instalado.")
    print("Instale com: pip install PySide6")
    sys.exit(1)

# Adicionar diretório do projeto ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils import setup_logging
from gui.main_window import RDPConnectorWindow

# Variável global para manter a referência da memória compartilhada
# É importante que ela não seja coletada pelo garbage collector
shared_memory = None

def main():
    """Função principal da aplicação"""
    global shared_memory

    # Configurar logging
    logger = setup_logging()
    logger.info("=== RDP Connector Pro iniciado ===")

    # Criar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("RDP Connector Pro")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("RDPConnector")

    # --- INÍCIO DA VERIFICAÇÃO DE INSTÂNCIA ÚNICA ---
    # Usar um nome único para a chave de memória compartilhada
    # Uma string única, como o nome da sua aplicação, é suficiente
    key = "RDPConnectorPro-SingleInstance"
    shared_memory = QSharedMemory(key)

    # Tenta se anexar a um segmento de memória compartilhada existente
    if shared_memory.attach():
        # Se conseguiu, outra instância já está em execução.
        logger.warning("Outra instância da aplicação já está em execução. Encerrando.")
        QMessageBox.warning(None, "RDP Connector Pro", 
                            "A aplicação já está em execução. Encerrando esta nova instância.")
        return 0

    # Se não conseguiu anexar, esta é a primeira instância.
    # Tenta criar o segmento de memória.
    # O tamanho do segmento pode ser 1 para fins de sinalização.
    if not shared_memory.create(1):
        # Se falhou em criar, algo deu errado (talvez por permissão).
        logger.error("Falha ao criar o segmento de memória compartilhada. Encerrando.")
        QMessageBox.critical(None, "Erro Crítico", 
                             "Falha ao inicializar a aplicação (memória compartilhada).")
        return 1
    
    # Se a criação foi bem-sucedida, a aplicação continua a execução normal.
    logger.info("Verificação de instância única concluída. Primeira instância.")
    # --- FIM DA VERIFICAÇÃO DE INSTÂNCIA ÚNICA ---
    
    # Não fechar quando a última janela é fechada (por causa do system tray)
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
        result = app.exec()
        
        # Desanexar a memória compartilhada na saída para liberar o lock
        shared_memory.detach()
        return result
        
    except Exception as e:
        logger.exception("Erro crítico na aplicação")
        QMessageBox.critical(None, "Erro Crítico", 
                           f"Erro crítico na aplicação: {str(e)}")
        # Em caso de erro, certifique-se de liberar o lock antes de sair.
        if shared_memory:
            shared_memory.detach()
        return 1

if __name__ == "__main__":
    sys.exit(main())