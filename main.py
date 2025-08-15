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
    from PySide6.QtCore import QSharedMemory, QTimer
except ImportError:
    print("Erro: PySide6 não está instalado.")
    print("Instale com: pip install PySide6")
    sys.exit(1)

# Adicionar diretório do projeto ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils import setup_logging, verificar_comando_disponivel
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

    # Ativar handler para sinais do sistema para fechar corretamente
    signal.signal(signal.SIGINT, signal_handler)

    # Adicionar diretório core ao path
    sys.path.insert(0, str(PROJECT_ROOT / "core"))

    # Criar um identificador único para a aplicação
    app_id = '{b6166164-9b26-4c4f-9e7d-1c39c277f9c8}'
    shared_memory = QSharedMemory(app_id)

    # Tentar anexar à memória compartilhada. Se falhar, outra instância está rodando.
    if shared_memory.attach():
        logger.warning("Outra instância já está rodando. Encerrando.")
        QMessageBox.warning(None, "RDP Connector Pro",
                            "Outra instância da aplicação já está rodando. Encerrando.")
        return 0

    # Criar a memória compartilhada e iniciar o aplicativo
    if not shared_memory.create(1):
        # Se a criação falhar por alguma razão
        logger.warning("Falha ao criar memória compartilhada. Pode ser por permissão.")
        if verificar_comando_disponivel("notify-send"):
            verificar_comando_disponivel(
                "Falha ao iniciar o aplicativo",
                "Falha ao criar memória compartilhada. Por favor, reinicie a máquina."
            )

    # Garantir que a memória compartilhada seja limpa na saída
    atexit.register(cleanup_shared_memory)

    # Criar a aplicação e a janela
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    try:
        window = RDPConnectorWindow()
    except ImportError as e:
        logger.exception(f"Erro de importação ao iniciar: {e}")
        QMessageBox.critical(None, "Erro de Inicialização",
                             f"Erro: {e}.\nVerifique se todas as bibliotecas estão instaladas.")
        return 1

    # Conectar o sinal de saída da aplicação para limpeza
    app.aboutToQuit.connect(cleanup_shared_memory)
    
    # Conectar a janela a verificação de saída real
    window.aplicacao_deve_sair.connect(window.sair_aplicacao)

    window.show()

    logger.info("Interface inicializada com sucesso")

    # Executar aplicação
    result = app.exec()

    logger.info("Aplicação encerrada normalmente")
    return result

if __name__ == "__main__":
    sys.exit(main())