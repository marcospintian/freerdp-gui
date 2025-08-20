#!/usr/bin/env python3
"""
RDP Connector Pro - Ponto de entrada da aplicação
"""

import sys
import logging
import atexit
import signal
from pathlib import Path
import subprocess

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QSharedMemory
except ImportError:
    print("Erro: PySide6 não está instalado.")
    print("Instale com: pip install PySide6")
    sys.exit(1)

# Adicionar diretório do projeto ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils import setup_logging, verificar_comando_disponivel
from gui.main_window import RDPConnectorWindow

# Variáveis globais
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
    # Migrar senhas em texto claro para criptografadas, se necessário
    from core.migracao_senhas import migrar_senhas_ini
    ini_path = str(PROJECT_ROOT / 'servidores.ini')
    migrar_senhas_ini(ini_path, logger)
    """Função principal da aplicação"""
    global shared_memory, logger

    # Criar a aplicação Qt primeiro
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Configurar logging
    logger = setup_logging()
    logger.info("=== RDP Connector Pro iniciado ===")

    # Ativar handler para sinais do sistema
    signal.signal(signal.SIGINT, signal_handler)

    # Adicionar diretório core ao path
    sys.path.insert(0, str(PROJECT_ROOT / "core"))

    # Criar um identificador único para a aplicação
    app_id = '{b6166164-9b26-4c4f-9e7d-1c39c277f9c8}'
    shared_memory = QSharedMemory(app_id)

    # Forçar detach se houver memória “fantasma”
    if shared_memory.isAttached():
        logger.warning("Memória compartilhada fantasma encontrada. Liberando...")
        shared_memory.detach()

    # Tentar anexar à memória compartilhada. Se falhar, outra instância está rodando
    if shared_memory.attach():
        logger.warning("Outra instância já está rodando. Encerrando.")
        QMessageBox.warning(None, "RDP Connector Pro",
                            "Outra instância da aplicação já está rodando. Encerrando.")
        return 0

    # Criar a memória compartilhada
    if not shared_memory.create(1):
        logger.warning("Falha ao criar memória compartilhada. Pode ser por permissão.")
        if verificar_comando_disponivel("notify-send"):
            subprocess.run([
                "notify-send",
                "Falha ao iniciar o aplicativo",
                "Falha ao criar memória compartilhada. Por favor, reinicie a máquina."
            ])
        QMessageBox.critical(None, "Erro",
                             "Falha ao criar memória compartilhada. Reinicie a máquina.")
        return 1

    # Garantir que a memória compartilhada seja limpa na saída
    atexit.register(cleanup_shared_memory)

    # Criar a janela principal
    try:
        window = RDPConnectorWindow()
    except ImportError as e:
        logger.exception(f"Erro de importação ao iniciar: {e}")
        QMessageBox.critical(None, "Erro de Inicialização",
                             f"Erro: {e}.\nVerifique se todas as bibliotecas estão instaladas.")
        return 1

    # Conectar sinais de encerramento
    app.aboutToQuit.connect(cleanup_shared_memory)
    window.aplicacao_deve_sair.connect(window.sair_aplicacao)

    window.show()
    logger.info("Interface inicializada com sucesso")

    # Executar aplicação
    result = app.exec()
    logger.info("Aplicação encerrada normalmente")
    return result

if __name__ == "__main__":
    sys.exit(main())
