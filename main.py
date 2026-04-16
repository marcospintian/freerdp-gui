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
local_server = None
activation_pending = False

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
        from PySide6.QtCore import QIODevice
        from PySide6.QtGui import QIcon
        from PySide6.QtNetwork import QLocalServer, QLocalSocket
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
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("FreeRDP-GUI")

    # Definir ícone global da aplicação (usar assets/rdp-icon.png quando disponível)
    try:
        # Importante: logger ainda não existe aqui, então usamos prints em caso de falha silenciosa
        icon_path = PROJECT_ROOT / "assets" / "rdp-icon.png"
        app_icon = None
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
        else:
            # tentar ícone do tema do sistema como fallback
            app_icon = QIcon.fromTheme("krdc")
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
    except Exception:
        pass

    # Configurar logging
    logger = setup_logging()
    logger.info("=== FreeRDP-GUI iniciado ===")

    # Ativar handler para sinais do sistema
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Definir função de verificar dependências (precisa estar após importações)
    def verificar_dependencias():
        """Verifica dependências críticas"""
        import shutil
        
        dependencias_faltando = []
        
        # Verificar FreeRDP (sistema ou Flathub)
        freerdp_disponivel = False
        
        # Primeiro, tentar FreeRDP do Flathub
        try:
            result = subprocess.run(
                ["flatpak", "run", "com.freerdp.FreeRDP", "/help"],
                capture_output=True, timeout=10
            )
            # Aceitar qualquer código de retorno que não seja erro de comando não encontrado
            if result.returncode != 127:  # 127 = comando não encontrado
                freerdp_disponivel = True
                print("✅ FreeRDP do Flathub detectado")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Se não encontrou no Flathub, verificar no sistema
        if not freerdp_disponivel:
            # Tentar diferentes nomes de comando
            for cmd in ["xfreerdp3", "xfreerdp", "freerdp"]:
                if shutil.which(cmd):
                    freerdp_disponivel = True
                    print(f"✅ FreeRDP do sistema detectado ({cmd})")
                    break
        
        if not freerdp_disponivel:
            dependencias_faltando.append("FreeRDP (instale: sudo apt install freerdp2-x11 OU flatpak install flathub com.freerdp.FreeRDP)")
        
        if dependencias_faltando:
            erro = "Dependências faltando:\n\n" + "\n".join([f"• {dep}" for dep in dependencias_faltando])
            erro += "\n\nInstale as dependências e tente novamente."
            return False, erro
        
        return True, ""

    # Verificar dependências críticas
    deps_ok, deps_erro = verificar_dependencias()
    if not deps_ok:
        logger.error("Dependências faltando")
        print("\n" + "="*60)
        print("❌ DEPENDÊNCIAS FALTANDO")
        print("="*60)
        print(deps_erro)
        print("="*60)
        return 1

    # Verificar instância única e permitir ativação da instância existente
    app_id = 'freerdp-gui-b6166164-9b26-4c4f-9e7d-1c39c277f9c8'
    activation_server_name = f"{app_id}-activation"
    local_server = QLocalServer()

    def handle_local_activation():
        """Ativa a janela quando outra instância pedir."""
        global activation_pending
        connection = local_server.nextPendingConnection()
        if not connection:
            return
        try:
            if connection.waitForReadyRead(1000):
                # Define flag para ativar a janela depois que ela for criada
                activation_pending = True
                logger.info("Ativação pendente recebida - janela será ativada quando criada")
        finally:
            connection.disconnectFromServer()

    # Tentar criar o servidor local para esta instância
    logger.info(f"Tentando criar servidor de ativação: {activation_server_name}")
    if not local_server.listen(activation_server_name):
        # Se não conseguir ouvir, significa que já existe uma instância rodando
        logger.info("Instância já existe, tentando ativar...")

        # Tentar ativar a instância existente
        existing_socket = QLocalSocket()
        existing_socket.connectToServer(activation_server_name, QIODevice.WriteOnly)
        logger.info("Tentando conectar ao servidor existente...")
        if existing_socket.waitForConnected(3000):
            logger.info("Conexão estabelecida, enviando ativação...")
            try:
                existing_socket.write(b"ACTIVATE")
                existing_socket.flush()
                # Não esperar por confirmação - apenas desconectar
                existing_socket.disconnectFromServer()
                logger.info("Instância existente ativada com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao enviar ativação: {e}")
                existing_socket.disconnectFromServer()
            return 0  # Sair desta instância
        else:
            error_msg = existing_socket.errorString()
            logger.warning(f"Não foi possível conectar ao servidor existente: {error_msg}")
            # Tentar limpar e criar novo servidor
            logger.info("Tentando limpar servidor zombie...")
            QLocalServer.removeServer(activation_server_name)
            if not local_server.listen(activation_server_name):
                logger.error("Falha crítica: não foi possível criar servidor de ativação após limpeza")
                # Continuar sem controle de instância única como fallback
            else:
                logger.info("Servidor de ativação criado após limpeza")

    else:
        logger.info("Servidor de ativação criado com sucesso - primeira instância")

    # Se chegou aqui, esta é a primeira instância ou conseguimos criar o servidor
    local_server.newConnection.connect(handle_local_activation)

    # Garantir que o servidor de ativação seja fechado na saída
    atexit.register(lambda: local_server.close())

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
        
        # Verificar se há ativação pendente
        global activation_pending
        if activation_pending:
            window.show_window()
            activation_pending = False
            logger.info("Janela ativada devido a solicitação de outra instância")
            
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