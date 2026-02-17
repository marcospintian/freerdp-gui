#!/usr/bin/env python3
"""
FreeRDP-GUI - Interface gráfica moderna para conexões RDP
"""

import sys
import logging
import atexit
import signal
from pathlib import Path
import subprocess

# Adicionar diretório do projeto ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Variáveis globais
shared_memory = None
logger = None

def mostrar_erro_dialog(titulo, mensagem):
    """
    Tenta mostrar erro em caixa de diálogo gráfica.
    Se falhar, mostra no terminal.
    """
    try:
        # Tentar zenity (GNOME/general Linux)
        subprocess.run([
            "zenity",
            "--error",
            f"--title={titulo}",
            f"--text={mensagem}",
            "--no-wrap"
        ], timeout=10, check=False, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            # Tentar kdialog (KDE)
            subprocess.run([
                "kdialog",
                "--error",
                mensagem,
                f"--title={titulo}"
            ], timeout=10, check=False, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback para terminal
            print(f"\n❌ {titulo}")
            print("-" * 50)
            print(mensagem)
            print("-" * 50)

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
    
    # Verificar dependências críticas de importação
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import QSharedMemory
    except ImportError:
        mensagem = "PySide6 não está instalado.\n\nInstale com:\npip install PySide6"
        mostrar_erro_dialog("Erro de Dependência", mensagem)
        return 1
    
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        mensagem = "Biblioteca 'cryptography' não está instalada.\n\nInstale com:\npip install cryptography"
        mostrar_erro_dialog("Erro de Dependência", mensagem)
        return 1
    
    try:
        from core.utils import setup_logging, verificar_comando_disponivel
        from gui.main_window import FreeRDPGUIWindow
    except ImportError as e:
        mensagem = f"Erro ao importar módulos do projeto:\n\n{e}"
        mostrar_erro_dialog("Erro de Importação", mensagem)
        return 1

    # Criar a aplicação Qt primeiro
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("FreeRDP-GUI")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("FreeRDP-GUI")

    # Configurar logging
    logger = setup_logging()
    logger.info("=== FreeRDP-GUI iniciado ===")

    # Ativar handler para sinais do sistema
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Definir função de verificar dependências (precisa estar após importações)
    def verificar_dependencias():
        """Verifica dependências críticas"""
        dependencias_faltando = []
        
        # Verificar xfreerdp
        if not verificar_comando_disponivel("xfreerdp3"):
            dependencias_faltando.append("xfreerdp (instale: sudo apt install freerdp3-x11)")
        
        if dependencias_faltando:
            erro = "Dependências faltando:\n\n" + "\n".join([f"• {dep}" for dep in dependencias_faltando])
            erro += "\n\nInstale as dependências e tente novamente."
            
            # Tentar notificação desktop
            try:
                if verificar_comando_disponivel("notify-send"):
                    subprocess.run([
                        "notify-send", 
                        "-i", "error",
                        "FreeRDP-GUI - Dependências", 
                        "Dependências faltando. Veja o terminal."
                    ], timeout=5)
            except Exception:
                pass  # Ignorar erro de notificação
            
            return False, erro
        
        return True, ""

    # Verificar dependências críticas
    deps_ok, deps_erro = verificar_dependencias()
    if not deps_ok:
        logger.error("Dependências faltando")
        QMessageBox.critical(None, "Dependências Faltando", deps_erro)
        return 1

    # Verificar instância única
    app_id = 'freerdp-gui-b6166164-9b26-4c4f-9e7d-1c39c277f9c8'
    shared_memory = QSharedMemory(app_id)

    # Forçar detach se houver memória "fantasma"
    if shared_memory.isAttached():
        logger.warning("Memória compartilhada fantasma encontrada, liberando...")
        shared_memory.detach()

    # Tentar anexar à memória compartilhada. Se conseguir, outra instância está rodando
    if shared_memory.attach():
        logger.warning("Outra instância já está rodando")
        QMessageBox.information(None, "FreeRDP-GUI",
                               "Outra instância da aplicação já está rodando.\n\n"
                               "Verifique a bandeja do sistema ou feche a instância anterior.")
        return 0

    # Criar a memória compartilhada
    if not shared_memory.create(1):
        logger.warning("Falha ao criar memória compartilhada")
        # Tentar notificação
        try:
            if verificar_comando_disponivel("notify-send"):
                subprocess.run([
                    "notify-send",
                    "-i", "error",
                    "FreeRDP-GUI - Aviso",
                    "Possível problema de permissões. Aplicação pode não funcionar corretamente."
                ], timeout=5)
        except Exception:
            pass
        
        # Não falhar por causa da memória compartilhada, apenas avisar
        logger.warning("Continuando sem controle de instância única")

    # Garantir que a memória compartilhada seja limpa na saída
    atexit.register(cleanup_shared_memory)

    # Criar a janela principal
    try:
        window = FreeRDPGUIWindow()
        logger.info("Janela principal criada com sucesso")
    except ImportError as e:
        logger.exception(f"Erro de importação: {e}")
        QMessageBox.critical(None, "Erro de Inicialização",
                           f"Erro de dependência: {e}\n\n"
                           f"Verifique se todas as bibliotecas estão instaladas:\n"
                           f"• pip install PySide6\n"
                           f"• pip install cryptography")
        return 1
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar janela: {e}")
        QMessageBox.critical(None, "Erro de Inicialização",
                           f"Erro inesperado: {e}\n\n"
                           f"Verifique os logs para mais detalhes.")
        return 1

    # Conectar sinais de encerramento
    app.aboutToQuit.connect(cleanup_shared_memory)
    
    # Conectar sinal personalizado da janela principal
    try:
        window.aplicacao_deve_sair.connect(app.quit)
    except AttributeError:
        logger.warning("Sinal aplicacao_deve_sair não encontrado na janela principal")

    # Mostrar janela
    try:
        window.show()
        logger.info("Interface inicializada com sucesso")
        
        # Notificação de início (opcional)
        try:
            if verificar_comando_disponivel("notify-send"):
                subprocess.run([
                    "notify-send",
                    "-i", "krdc",
                    "FreeRDP-GUI",
                    "Aplicação iniciada com sucesso"
                ], timeout=5)
        except Exception:
            pass  # Ignorar erro de notificação
            
    except Exception as e:
        logger.exception(f"Erro ao mostrar janela: {e}")
        QMessageBox.critical(None, "Erro",
                           f"Erro ao inicializar interface: {e}")
        return 1

    # Executar aplicação
    try:
        result = app.exec()
        logger.info(f"Aplicação encerrada com código: {result}")
        return result
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário (Ctrl+C)")
        return 0
    except Exception as e:
        logger.exception(f"Erro durante execução: {e}")
        return 1
    finally:
        cleanup_shared_memory()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário")