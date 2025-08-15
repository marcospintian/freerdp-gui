#!/usr/bin/env python3
"""
RDP Connector Pro - Ponto de entrada da aplicação
"""

import sys
import logging
import atexit
import signal
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
    from PySide6.QtCore import Qt, QSharedMemory, QTimer
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
shared_memory = None
logger = None

def cleanup_shared_memory():
    """Limpa a memória compartilhada na saída"""
    global shared_memory, logger
    if shared_memory and shared_memory.isAttached():
        shared_memory.detach()
        if logger:
            logger.info("Memória compartilhada liberada")

def signal_handler(signum, frame):
    """Handler para sinais do sistema"""
    global logger
    if logger:
        logger.info(f"Sinal {signum} recebido, encerrando aplicação...")
    cleanup_shared_memory()
    sys.exit(0)

def main():
    """Função principal da aplicação"""
    global shared_memory, logger

    # Configurar logging
    logger = setup_logging()
    logger.info("=== RDP Connector Pro iniciado ===")

    # Registrar função de cleanup para ser executada na saída
    atexit.register(cleanup_shared_memory)
    
    # Registrar handlers para sinais do sistema
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Criar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("RDP Connector Pro")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("RDPConnector")

    # --- VERIFICAÇÃO DE INSTÂNCIA ÚNICA ---
    key = "RDPConnectorPro-SingleInstance"
    shared_memory = QSharedMemory(key)

    if shared_memory.attach():
        logger.warning("Outra instância da aplicação já está em execução. Encerrando.")
        QMessageBox.warning(None, "RDP Connector Pro", 
                            "A aplicação já está em execução. Encerrando esta nova instância.")
        return 0

    if not shared_memory.create(1):
        logger.error("Falha ao criar o segmento de memória compartilhada. Encerrando.")
        QMessageBox.critical(None, "Erro Crítico", 
                             "Falha ao inicializar a aplicação (memória compartilhada).")
        return 1
    
    logger.info("Verificação de instância única concluída. Primeira instância.")
    
    # Não fechar quando a última janela é fechada (por causa do system tray)
    app.setQuitOnLastWindowClosed(False)
    
    # Verificar suporte ao system tray
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Sistema Tray", 
                           "Sistema não suporta ícone na bandeja do sistema.")
    
    # Timer para verificar se a aplicação deve continuar rodando
    cleanup_timer = QTimer()
    cleanup_timer.timeout.connect(lambda: None)  # Apenas mantém o loop ativo
    cleanup_timer.start(1000)  # Verifica a cada segundo
    
    try:
        # Criar janela principal
        window = RDPConnectorWindow()
        
        # Conectar sinal de saída da aplicação para limpeza
        app.aboutToQuit.connect(cleanup_shared_memory)
        
        # Configurar callback para quando a aplicação deveria realmente sair
        def verificar_saida_real():
            """Verifica se a aplicação deve realmente sair"""
            logger.info("Verificando saída real da aplicação...")
            
            # Garantir que todas as threads RDP sejam finalizadas
            if hasattr(window, 'rdp_thread') and window.rdp_thread:
                logger.info("Aguardando finalização de thread RDP...")
                if not window._limpar_thread_rdp():
                    logger.warning("Thread RDP não finalizou, forçando saída")
            
            # Pequena pausa para permitir limpeza
            QTimer.singleShot(500, app.quit)
        
        # Conectar verificação de saída
        window.aplicacao_deve_sair.connect(verificar_saida_real)
        
        window.show()
        
        logger.info("Interface inicializada com sucesso")
        
        # Executar aplicação
        result = app.exec()
        
        logger.info("Aplicação encerrada normalmente")
        return result
        
    except Exception as e:
        logger.exception("Erro crítico na aplicação")
        QMessageBox.critical(None, "Erro Crítico", 
                           f"Erro crítico na aplicação: {str(e)}")
        return 1
    finally:
        # Garantir limpeza mesmo em caso de exceção
        cleanup_shared_memory()

if __name__ == "__main__":
    sys.exit(main())