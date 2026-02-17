"""
Gerenciador do system tray (ícone na bandeja do sistema)
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

try:
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtGui import QIcon, QPixmap, QAction
except ImportError as e:
    raise ImportError(f"PySide6 não encontrado: {e}")

from core.utils import get_project_root, arquivo_existe

logger = logging.getLogger(__name__)

class SystemTrayManager(QObject):
    """Gerenciador do ícone na bandeja do sistema"""
    
    # Sinais
    conectar_servidor = Signal(str)  # Emitido quando usuário quer conectar a um servidor
    mostrar_janela = Signal()       # Emitido quando usuário quer mostrar janela principal
    mostrar_logs = Signal()         # Emitido quando usuário quer ver logs
    sair_aplicacao = Signal()       # Emitido quando usuário quer sair
    
    def __init__(self, parent_window):
        super().__init__()
        
        self.parent_window = parent_window
        self.tray_icon = None
        self.tray_menu = None
        self.servidores = {}
        
        self._init_system_tray()
    
    def _init_system_tray(self):
        """Inicializa ícone na bandeja do sistema"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray não disponível")
            return
        
        # Criar ícone
        self.tray_icon = QSystemTrayIcon(self.parent_window)
        
        # Carregar ícone personalizado
        icon = self._load_icon()
        self.tray_icon.setIcon(icon)
        
        # Configurar menu
        self._create_menu()
        
        # Conectar sinais
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Mostrar ícone
        self.tray_icon.show()
        
        logger.info("System tray inicializado")
    
    def _load_icon(self) -> QIcon:
        """Carrega ícone para o system tray"""
        # Caminhos possíveis para o ícone
        icon_paths = [
            get_project_root() / "assets" / "rdp-icon.png",
            get_project_root() / "rdp-icon.png",
            Path.home() / ".config" / "rdp-connector" / "icon.png",
            Path("/usr/share/pixmaps/rdp-connector.png")
        ]
        
        # Tentar carregar ícone personalizado
        for icon_path in icon_paths:
            if arquivo_existe(str(icon_path)):
                try:
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        logger.info(f"Ícone personalizado carregado: {icon_path}")
                        return icon
                except Exception as e:
                    logger.warning(f"Erro ao carregar ícone {icon_path}: {str(e)}")
        
        # Fallback para ícones do sistema
        system_icons = ["krdc", "network-connect", "applications-internet"]
        
        for icon_name in system_icons:
            icon = QIcon.fromTheme(icon_name)
            if not icon.isNull():
                logger.info(f"Usando ícone do sistema: {icon_name}")
                return icon
        
        # Último recurso: criar ícone simples
        pixmap = QPixmap(16, 16)
        pixmap.fill(0x0066CC)  # Azul
        icon = QIcon(pixmap)
        logger.info("Usando ícone padrão (azul)")
        
        return icon
    
    def _create_menu(self):
        """Cria menu do system tray"""
        self.tray_menu = QMenu()
        
        # Será preenchido quando servidores forem atualizados
        self._update_menu()
        
        # Configurar menu no ícone
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def _update_menu(self):
        """Atualiza menu do system tray"""
        if not self.tray_menu:
            return
        
        # Limpar menu atual
        self.tray_menu.clear()
        
        # Adicionar servidores (exceto "Manual")
        servidores_disponiveis = [
            nome for nome in self.servidores.keys() 
            if nome != "Manual"
        ]
        
        if servidores_disponiveis:
            # Seção de conexões rápidas
            for servidor in sorted(servidores_disponiveis):
                action = QAction(f"Conectar a {servidor}", self.tray_menu)
                action.triggered.connect(
                    lambda checked, s=servidor: self.conectar_servidor.emit(s)
                )
                self.tray_menu.addAction(action)
            
            # Separador
            self.tray_menu.addSeparator()
        
        # Ações principais
        show_action = QAction("Mostrar", self.tray_menu)
        show_action.triggered.connect(lambda: self.mostrar_janela.emit())
        self.tray_menu.addAction(show_action)
        
        logs_action = QAction("Ver Logs", self.tray_menu)
        logs_action.triggered.connect(lambda: self.mostrar_logs.emit())
        self.tray_menu.addAction(logs_action)
        
        # Separador
        self.tray_menu.addSeparator()
        
        # Sair
        quit_action = QAction("Sair", self.tray_menu)
        quit_action.triggered.connect(lambda: self.sair_aplicacao.emit())
        self.tray_menu.addAction(quit_action)
    
    def _on_tray_activated(self, reason):
        """Trata ativação do ícone do tray"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.mostrar_janela.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Clique esquerdo único também mostra a janela
            self.mostrar_janela.emit()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Clique do meio mostra logs
            self.mostrar_logs.emit()
    
    def atualizar_menu_servidores(self, servidores: Dict[str, Tuple[str, str]]):
        """
        Atualiza lista de servidores no menu
        
        Args:
            servidores: Dict com nome_servidor -> (ip, usuario)
        """
        self.servidores = servidores.copy()
        self._update_menu()
        logger.debug(f"Menu do tray atualizado com {len(servidores)} servidores")
    
    def notificar(self, titulo: str, mensagem: str, tipo: str = "information"):
        """
        Mostra notificação via system tray
        
        Args:
            titulo: Título da notificação
            mensagem: Texto da mensagem
            tipo: Tipo da notificação (information, warning, critical)
        """
        if not self.tray_icon:
            return
        
        # Mapear tipos para ícones do Qt
        icon_map = {
            "information": QSystemTrayIcon.MessageIcon.Information,
            "warning": QSystemTrayIcon.MessageIcon.Warning,
            "critical": QSystemTrayIcon.MessageIcon.Critical,
            "error": QSystemTrayIcon.MessageIcon.Critical
        }
        
        icon = icon_map.get(tipo, QSystemTrayIcon.MessageIcon.Information)
        
        try:
            self.tray_icon.showMessage(titulo, mensagem, icon, 5000)  # 5 segundos
        except Exception as e:
            logger.warning(f"Erro ao mostrar notificação do tray: {str(e)}")
    
    def definir_tooltip(self, texto: str):
        """
        Define tooltip do ícone do tray
        
        Args:
            texto: Texto do tooltip
        """
        if self.tray_icon:
            self.tray_icon.setToolTip(texto)
    
    def is_available(self) -> bool:
        """
        Verifica se system tray está disponível
        
        Returns:
            True se system tray está disponível
        """
        return self.tray_icon is not None and self.tray_icon.isSystemTrayAvailable()
    
    def esconder(self):
        """Esconde ícone do system tray"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def mostrar(self):
        """Mostra ícone do system tray"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def conectar_sinais_janela_principal(self, janela):
        """
        Conecta sinais do tray com a janela principal
        
        Args:
            janela: Instância da janela principal
        """
        # Conectar sinais
        self.mostrar_janela.connect(janela.show_window)
        self.mostrar_logs.connect(janela.mostrar_logs)
        self.sair_aplicacao.connect(janela.close)
        
        # Conectar sinal de conectar servidor se janela principal tiver o método
        if hasattr(janela, '_conectar_rapido'):
            self.conectar_servidor.connect(janela._conectar_rapido)
        
        logger.debug("Sinais do tray conectados à janela principal")

def criar_system_tray_manager(parent_window) -> Optional[SystemTrayManager]:
    """
    Factory function para criar gerenciador do system tray
    
    Args:
        parent_window: Janela principal da aplicação
        
    Returns:
        Instância do SystemTrayManager ou None se não disponível
    """
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.warning("System tray não disponível neste sistema")
        return None
    
    try:
        manager = SystemTrayManager(parent_window)
        
        # Conectar sinais automaticamente se possível
        if hasattr(parent_window, 'show_window'):
            manager.conectar_sinais_janela_principal(parent_window)
        
        return manager
        
    except Exception as e:
        logger.exception("Erro ao criar gerenciador do system tray")
        return None