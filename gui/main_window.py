"""
Janela principal da aplicação FreeRDP-GUI com master password opcional
"""

import logging
from typing import Dict, Tuple, Optional

try:
    from PySide6.QtWidgets import (
        QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
        QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox, QMessageBox,
        QFormLayout, QSystemTrayIcon, QMenu, QTabWidget, QApplication
    )
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QIcon, QPixmap, QAction
except ImportError as e:
    raise ImportError(f"PySide6 não encontrado: {e}")

from core.servidores import get_servidor_manager
from core.settings import get_settings_manager, get_configuracoes_app
from core.rdp import RDPThread, criar_opcoes_padrao
from core.utils import (
    SOM_MAP, RESOLUCAO_MAP, QUALIDADE_MAP,
    notificar_desktop, verificar_comando_disponivel,
    validar_ip_porta, normalizar_ip_porta,
    get_project_root, arquivo_existe
)
from core.crypto import get_crypto_manager

from .gerenciador import GerenciadorServidoresWidget
from .logs_window import LogsWindow
from .system_tray import SystemTrayManager
from .master_password_dialog import solicitar_master_password, alterar_master_password

logger = logging.getLogger(__name__)

class FreeRDPGUIWindow(QMainWindow):
    """Janela principal da aplicação"""
    
    # Sinal que indica quando a aplicação deve realmente sair
    aplicacao_deve_sair = Signal()
    
    def __init__(self):
        super().__init__()
        self._fechar_de_verdade = False
        
        # Contador de conexões ativas
        self.conexoes_ativas = 0

        # Managers
        self.servidor_manager = get_servidor_manager()
        self.settings_manager = get_settings_manager()
        self.config_app = get_configuracoes_app()
        self.crypto_manager = get_crypto_manager()
        
        # Estado
        self.rdp_threads: Dict[str, RDPThread] = {}
        self.logs_window = None
        
        # Dados
        self.servidores = {}
        
        # Inicialização
        self._init_ui()
        self._init_system_tray()
        self._carregar_servidores()
        self._restaurar_configuracoes()
        
        # Mostrar info sobre o sistema de senhas (apenas se for primeira vez)
        self._mostrar_info_inicial_senhas()
        
        logger.info("Janela principal inicializada")
    
    def _mostrar_info_inicial_senhas(self):
        """Mostra informação inicial sobre o sistema de senhas"""
        status = self.crypto_manager.get_status_info()
        
        if not status['has_custom_password'] and not status['has_encrypted_data']:
            QMessageBox.information(
                self, "Sistema de Senhas", 
                "✅ <b>Sistema de criptografia ativo!</b><br/><br/>"
                "• Suas senhas RDP serão salvas <b>criptografadas</b> automaticamente<br/>"
                "• <b>Opcional:</b> Configure uma Master Password no menu 'Senhas' para maior segurança<br/>"
                "• Sem master password: suas senhas ficam criptografadas com chave padrão<br/><br/>"
                "<i>💡 Dica: A master password permite trancar/destrancar as senhas quando quiser</i>"
            )
    
    def incrementar_conexoes(self):
        """Incrementa contador de conexões ativas"""
        self.conexoes_ativas += 1
        logger.info(f"Conexões ativas: {self.conexoes_ativas}")
        
    def decrementar_conexoes(self):
        """Decrementa contador de conexões ativas"""
        self.conexoes_ativas = max(0, self.conexoes_ativas - 1)
        logger.info(f"Conexões ativas: {self.conexoes_ativas}")
    
    def verificar_saida_completa(self):
        """Verifica se a aplicação deve sair completamente"""
        return
    
    def considerar_saida(self):
        """Considera sair se ainda não há atividade"""
        return
    
    def sair_aplicacao(self):
        """Método para sair completamente da aplicação"""
        logger.info("Saindo da aplicação completamente")
        
        self.encerrar_todas_conexoes()
        self._salvar_configuracoes()
        
        self._fechar_de_verdade = True
        self.aplicacao_deve_sair.emit()
    
    def encerrar_todas_conexoes(self):
        """Encerra todas as conexões RDP ativas"""
        logger.info("Encerrando todas as conexões RDP")
        self._limpar_thread_rdp()
        self.conexoes_ativas = 0
    
    def _limpar_thread_rdp(self):
        """Limpa todas as threads RDP de forma segura"""
        if not self.rdp_threads:
            return True

        logger.info(f"Finalizando {len(self.rdp_threads)} threads RDP...")

        threads_a_remover = list(self.rdp_threads.keys())
        for thread_id in threads_a_remover:
            thread = self.rdp_threads.get(thread_id)
            if thread and thread.isRunning():
                logger.info(f"Finalizando thread {thread_id}...")
                thread.quit()
                if not thread.wait(3000):
                    logger.warning(f"Thread {thread_id} não finalizou graciosamente, forçando...")
                    thread.terminate()
                    if not thread.wait(2000):
                        logger.error(f"Thread {thread_id} não pôde ser finalizada!")
                        continue

            if thread:
                thread.deleteLater()

            if thread_id in self.rdp_threads:
                del self.rdp_threads[thread_id]

        logger.info("Todas as threads RDP finalizadas com sucesso")
        return True

    def _init_ui(self):
        """Inicializa interface do usuário"""
        self.setWindowTitle("FreeRDP-GUI")
        try:
            icon_path = get_project_root() / "assets" / "rdp-icon.png"
            if arquivo_existe(str(icon_path)):
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
            else:
                theme_icon = QIcon.fromTheme("krdc")
                if not theme_icon.isNull():
                    self.setWindowIcon(theme_icon)
        except Exception:
            pass
        self.setFixedSize(500, 650)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self._init_aba_conexao()
        self._init_aba_opcoes()
        self._init_aba_servidores()
        self._init_botoes_principais(layout)
        self._init_menu_senhas()
    
    def _init_menu_senhas(self):
        """Inicializa menu para gerenciamento de senhas"""
        menubar = self.menuBar()
        
        senha_menu = menubar.addMenu("&Senhas")
        
        config_action = QAction("&Configurar Master Password...", self)
        config_action.triggered.connect(self._configurar_master_password)
        senha_menu.addAction(config_action)
        
        change_action = QAction("&Alterar Master Password...", self)
        change_action.triggered.connect(self._alterar_master_password)
        senha_menu.addAction(change_action)
        
        remove_action = QAction("&Remover Master Password", self)
        remove_action.triggered.connect(self._remover_master_password)
        senha_menu.addAction(remove_action)
        
        senha_menu.addSeparator()
        
        self.lock_action = QAction("&Trancar Senhas", self)
        self.lock_action.triggered.connect(self._toggle_crypto_lock)
        senha_menu.addAction(self.lock_action)
        
        senha_menu.addSeparator()
        
        status_action = QAction("&Status do Sistema...", self)
        status_action.triggered.connect(self._mostrar_status_senhas)
        senha_menu.addAction(status_action)
        
        self._atualizar_menu_senhas()
    
    def _atualizar_menu_senhas(self):
        """Atualiza estado do menu de senhas"""
        status = self.crypto_manager.get_status_info()
        
        self.lock_action.setVisible(status['has_custom_password'])
        
        if status['has_custom_password']:
            if self.crypto_manager.is_unlocked():
                self.lock_action.setText("&Trancar Senhas")
            else:
                self.lock_action.setText("&Destrancar Senhas")
    
    def _configurar_master_password(self):
        """Configura master password pela primeira vez"""
        status = self.crypto_manager.get_status_info()
        
        if status['has_custom_password']:
            resposta = QMessageBox.question(
                self, "Master Password", 
                "Master password já está configurada.\n\nDeseja alterá-la?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resposta == QMessageBox.StandardButton.Yes:
                self._alterar_master_password()
            return
        
        resposta = QMessageBox.question(
            self, "Configurar Master Password",
            "🔐 <b>Configurar Master Password Personalizada?</b><br/><br/>"
            "<b>Atualmente:</b> Suas senhas ficam criptografadas com chave padrão<br/>"
            "<b>Com Master Password:</b> Você pode trancar/destrancar as senhas<br/><br/>"
            "📝 <b>Vantagens:</b><br/>"
            "• Controle total sobre acesso às senhas<br/>"
            "• Pode trancar temporariamente<br/>"
            "• Segurança adicional<br/><br/>"
            "⚠️ <b>Importante:</b> Se esquecer a master password, perderá acesso às senhas!<br/><br/>"
            "Deseja configurar uma master password personalizada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        senha = solicitar_master_password(self, is_first_time=True)
        if senha:
            QMessageBox.information(
                self, "Sucesso", 
                "✅ <b>Master Password configurada!</b><br/><br/>"
                "• Suas senhas foram migradas para a nova chave<br/>"
                "• Agora você pode trancar/destrancar no menu Senhas<br/>"
                "• Sistema de criptografia mais seguro ativado"
            )
            self._atualizar_menu_senhas()
            self._on_servidor_changed(self.combo_servidor.currentText())
    
    def _alterar_master_password(self):
        """Altera master password existente"""
        status = self.crypto_manager.get_status_info()
        
        if not status['has_custom_password']:
            QMessageBox.information(
                self, "Aviso", 
                "Primeiro configure uma master password personalizada."
            )
            self._configurar_master_password()
            return
        
        if not self.crypto_manager.is_unlocked():
            QMessageBox.information(
                self, "Aviso", 
                "Primeiro desbloqueie as senhas para alterar a master password."
            )
            return
        
        if alterar_master_password(self):
            self._atualizar_menu_senhas()
    
    def _remover_master_password(self):
        """Remove master password e volta para chave padrão"""
        status = self.crypto_manager.get_status_info()
        
        if not status['has_custom_password']:
            QMessageBox.information(
                self, "Aviso",
                "Master password personalizada não está configurada.\n\n"
                "Suas senhas já estão usando criptografia com chave padrão."
            )
            return
        
        resposta = QMessageBox.question(
            self, "Remover Master Password",
            "⚠️ <b>Remover Master Password Personalizada?</b><br/><br/>"
            "<b>Isso irá:</b><br/>"
            "• Voltar para criptografia com chave padrão<br/>"
            "• Remover opção de trancar/destrancar senhas<br/>"
            "• Re-criptografar todas as senhas existentes<br/><br/>"
            "<b>Suas senhas continuarão seguras</b> (criptografadas com chave padrão)<br/><br/>"
            "Tem certeza que deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        if self.crypto_manager.remove_master_password():
            QMessageBox.information(
                self, "Sucesso",
                "✅ <b>Master Password removida!</b><br/><br/>"
                "• Voltou para criptografia com chave padrão<br/>"
                "• Suas senhas continuam seguras<br/>"
                "• Sistema simplificado ativado"
            )
            self._atualizar_menu_senhas()
            self._on_servidor_changed(self.combo_servidor.currentText())
        else:
            QMessageBox.critical(
                self, "Erro",
                "Erro ao remover master password.\nVerifique os logs para mais detalhes."
            )
    
    def _toggle_crypto_lock(self):
        """Alterna trava do crypto (só se tem master password personalizada)"""
        status = self.crypto_manager.get_status_info()
        
        if not status['has_custom_password']:
            QMessageBox.information(
                self, "Aviso",
                "Esta funcionalidade requer master password personalizada.\n\n"
                "Configure uma no menu Senhas > Configurar Master Password."
            )
            return
        
        if self.crypto_manager.is_unlocked():
            self.crypto_manager.lock()
            self._notificar("FreeRDP-GUI", "Senhas trancadas")
            self._limpar_senhas_interface()
        else:
            senha = solicitar_master_password(self)
            if senha:
                self._notificar("FreeRDP-GUI", "Senhas destrancadas")
                self._on_servidor_changed(self.combo_servidor.currentText())
        
        self._atualizar_menu_senhas()
    
    def _limpar_senhas_interface(self):
        """Limpa senhas da interface quando trancado"""
        if self.edit_senha.text() and self.edit_senha.text().startswith("[SENHA TRANCADA"):
            return
        
        self.edit_senha.clear()
        self._atualizar_indicador_senha_salva(False)
    
    def _mostrar_status_senhas(self):
        """Mostra status detalhado do sistema de senhas"""
        status = self.crypto_manager.get_status_info()
        servidores_com_senha = self.servidor_manager.listar_servidores_com_senha()
        
        if status['has_custom_password']:
            titulo = "🔐 Master Password Personalizada"
            chave_info = f"Status: {'🔓 Destrancado' if status['is_unlocked'] else '🔒 Trancado'}"
        else:
            titulo = "🔑 Chave Padrão"
            chave_info = "Status: ✅ Sempre ativo (não pode ser trancado)"
        
        if servidores_com_senha:
            senha_info = f"📊 Senhas salvas: {len(servidores_com_senha)}\n"
            senha_info += "\n".join([f"   • {servidor}" for servidor in sorted(servidores_com_senha)])
        else:
            senha_info = "📊 Nenhuma senha salva"
        
        sistema_info = f"📁 Diretório: {status['config_dir']}"
        
        mensagem = f"<h3>{titulo}</h3><br/>" \
                  f"{chave_info}<br/><br/>" \
                  f"{senha_info}<br/><br/>" \
                  f"{sistema_info}<br/><br/>" \
                  f"<i>💡 Configure master password personalizada para mais controle</i>"
        
        QMessageBox.information(self, "Status do Sistema de Senhas", mensagem)
    
    def _init_aba_conexao(self):
        """Inicializa aba de conexão"""
        self.tab_conexao = QWidget()
        self.tabs.addTab(self.tab_conexao, "Conexão")
        
        layout = QVBoxLayout(self.tab_conexao)
        
        servidor_layout = QFormLayout()
        
        self.combo_servidor = QComboBox()
        self.combo_servidor.currentTextChanged.connect(self._on_servidor_changed)
        servidor_layout.addRow("Servidor:", self.combo_servidor)
        
        self.edit_ip_manual = QLineEdit()
        self.edit_ip_manual.setPlaceholderText("Digite IP/hostname (ex: 192.168.1.100 ou servidor.com)")
        self.edit_ip_manual.setVisible(False)
        servidor_layout.addRow("IP/Hostname:", self.edit_ip_manual)
        
        layout.addLayout(servidor_layout)
        
        self._init_credenciais_form(layout)
    
    def _init_credenciais_form(self, parent_layout):
        """Inicializa formulário de credenciais"""
        cred_layout = QFormLayout()
        
        self.edit_usuario = QLineEdit()
        cred_layout.addRow("Usuário:", self.edit_usuario)
        
        senha_layout = QHBoxLayout()
        
        self.edit_senha = QLineEdit()
        self.edit_senha.setEchoMode(QLineEdit.EchoMode.Password)
        senha_layout.addWidget(self.edit_senha)
        
        self.label_senha_salva = QLabel()
        self.label_senha_salva.setStyleSheet("color: green; font-weight: bold;")
        self.label_senha_salva.setVisible(False)
        senha_layout.addWidget(self.label_senha_salva)
        
        senha_widget = QWidget()
        senha_widget.setLayout(senha_layout)
        cred_layout.addRow("Senha:", senha_widget)
        
        parent_layout.addLayout(cred_layout)
    
    def _init_aba_opcoes(self):
        """Inicializa aba de opções"""
        self.tab_opcoes = QWidget()
        self.tabs.addTab(self.tab_opcoes, "Opções")
        
        layout = QVBoxLayout(self.tab_opcoes)
        
        self.check_clipboard = QCheckBox("Compartilhar área de transferência")
        self.check_clipboard.setChecked(True)
        layout.addWidget(self.check_clipboard)
        
        self.check_home = QCheckBox("Montar pasta pessoal como drive C:")
        layout.addWidget(self.check_home)
        
        self.check_salvar_senha = QCheckBox("Salvar senha automaticamente")
        self.check_salvar_senha.setToolTip("Salva senha criptografada automaticamente")
        self.check_salvar_senha.setChecked(True)
        layout.addWidget(self.check_salvar_senha)
        
        som_layout = QFormLayout()
        self.combo_som = QComboBox()
        self.combo_som.addItems(list(SOM_MAP.keys()))
        som_layout.addRow("Som:", self.combo_som)
        layout.addLayout(som_layout)
        
        self.check_impressoras = QCheckBox("Compartilhar impressoras")
        layout.addWidget(self.check_impressoras)
        
        self._init_opcoes_display(layout)
    
    def _init_opcoes_display(self, parent_layout):
        """Inicializa opções de display"""
        display_layout = QFormLayout()
        
        self.check_multimonitor = QCheckBox("Usar múltiplos monitores")
        parent_layout.addWidget(self.check_multimonitor)
        
        self.combo_resolucao = QComboBox()
        self.combo_resolucao.addItems(list(RESOLUCAO_MAP.keys()))
        display_layout.addRow("Resolução:", self.combo_resolucao)
        
        self.combo_qualidade = QComboBox()
        self.combo_qualidade.addItems(list(QUALIDADE_MAP.keys()))
        self.combo_qualidade.setCurrentText("Broadband")
        display_layout.addRow("Qualidade:", self.combo_qualidade)
        
        parent_layout.addLayout(display_layout)
        
        seguranca_layout = QFormLayout()
        
        self.check_ignorar_cert = QCheckBox("Ignorar certificado SSL/TLS")
        self.check_ignorar_cert.setChecked(True)
        self.check_ignorar_cert.setToolTip("Ignora avisos de certificado inválido (/cert:ignore)")
        seguranca_layout.addRow(self.check_ignorar_cert)
        
        # Protocolos de segurança globais (fallback quando servidor não tem sec definido)
        protocolos_label = QLabel("<b>Protocolos de segurança (padrão global):</b>")
        protocolos_label.setToolTip(
            "Usado quando o servidor não tem protocolo de segurança específico definido.\n"
            "Para configurar por servidor, acesse a aba 'Gerenciar Servidores'."
        )
        seguranca_layout.addRow(protocolos_label)
        
        self.check_sec_rdp = QCheckBox("RDP")
        self.check_sec_rdp.setToolTip("Protocolo RDP nativo")
        seguranca_layout.addRow("", self.check_sec_rdp)
        
        self.check_sec_tls = QCheckBox("TLS")
        self.check_sec_tls.setChecked(True)
        self.check_sec_tls.setToolTip("Transport Layer Security")
        seguranca_layout.addRow("", self.check_sec_tls)
        
        self.check_sec_nla = QCheckBox("NLA")
        self.check_sec_nla.setToolTip("Network Level Authentication")
        seguranca_layout.addRow("", self.check_sec_nla)
        
        self.check_sec_ext = QCheckBox("EXT")
        self.check_sec_ext.setToolTip("Extended Security")
        seguranca_layout.addRow("", self.check_sec_ext)
        
        self.check_sec_aad = QCheckBox("AAD")
        self.check_sec_aad.setToolTip("Azure Active Directory")
        seguranca_layout.addRow("", self.check_sec_aad)
        
        parent_layout.addLayout(seguranca_layout)
    
    def _init_aba_servidores(self):
        """Inicializa aba de gerenciamento de servidores"""
        self.tab_servidores = QWidget()
        self.tabs.addTab(self.tab_servidores, "Gerenciar Servidores")
        
        layout = QVBoxLayout(self.tab_servidores)
        
        self.gerenciador_servidores = GerenciadorServidoresWidget()
        self.gerenciador_servidores.servidores_atualizados.connect(self._carregar_servidores)
        layout.addWidget(self.gerenciador_servidores)
    
    def _init_botoes_principais(self, parent_layout):
        """Inicializa botões principais"""
        button_layout = QHBoxLayout()
        
        self.btn_conectar = QPushButton("Conectar")
        self.btn_conectar.clicked.connect(self._conectar)
        self.btn_conectar.setDefault(True)
        button_layout.addWidget(self.btn_conectar)
        
        btn_cancelar = QPushButton("Fechar")
        btn_cancelar.clicked.connect(self._ocultar_janela)
        button_layout.addWidget(btn_cancelar)
        
        parent_layout.addLayout(button_layout)
    
    def _init_system_tray(self):
        """Inicializa gerenciador do system tray"""
        self.system_tray = SystemTrayManager(self)
        self.system_tray.conectar_sinais_janela_principal(self)
    
    def _carregar_servidores(self):
        """Carrega servidores do gerenciador e atualiza interface"""
        self.servidores = self.servidor_manager.carregar_servidores()
        
        servidor_atual = self.combo_servidor.currentText()
        
        self.combo_servidor.clear()
        self.combo_servidor.addItems(list(self.servidores.keys()))
        
        if servidor_atual in self.servidores:
            self.combo_servidor.setCurrentText(servidor_atual)
        
        if hasattr(self, 'system_tray'):
            self.system_tray.atualizar_menu_servidores(self.servidores)
        
        logger.info(f"Carregados {len(self.servidores)} servidores")
    
    def _on_servidor_changed(self, servidor_nome: str):
        """Chamado quando servidor é alterado no combo"""
        if servidor_nome == "Manual":
            self.edit_ip_manual.setVisible(True)
            self.edit_usuario.setText("usuario")
            self.edit_senha.setText("")
            self._atualizar_indicador_senha_salva(False)
        else:
            self.edit_ip_manual.setVisible(False)
            
            if servidor_nome in self.servidores:
                _, usuario_padrao = self.servidores[servidor_nome]
                self.edit_usuario.setText(usuario_padrao)
                
                senha_salva = self._obter_senha_criptografada(servidor_nome)
                if senha_salva:
                    self.edit_senha.setText(senha_salva)
                    self._atualizar_indicador_senha_salva(True, senha_salva.startswith("[SENHA TRANCADA"))
                else:
                    self.edit_senha.setText("")
                    self._atualizar_indicador_senha_salva(False)
    
    def _atualizar_indicador_senha_salva(self, tem_senha_salva: bool, esta_trancada: bool = False):
        """Atualiza indicador visual de senha salva"""
        if tem_senha_salva:
            if esta_trancada:
                self.label_senha_salva.setText("🔒")
                self.label_senha_salva.setToolTip("Senha salva mas trancada - desbloqueie no menu Senhas")
            else:
                status = self.crypto_manager.get_status_info()
                if status['has_custom_password']:
                    self.label_senha_salva.setText("🔐")
                    self.label_senha_salva.setToolTip("Senha criptografada (Master Password personalizada)")
                else:
                    self.label_senha_salva.setText("🔑")
                    self.label_senha_salva.setToolTip("Senha criptografada (chave padrão)")
            self.label_senha_salva.setVisible(True)
        else:
            self.label_senha_salva.setVisible(False)
    
    def _obter_senha_criptografada(self, nome_servidor: str) -> Optional[str]:
        """Obtém senha criptografada para o servidor"""
        status = self.crypto_manager.get_status_info()
        
        if status['has_custom_password'] and not self.crypto_manager.is_unlocked():
            if self.servidor_manager.servidor_tem_senha_salva(nome_servidor):
                return "[SENHA TRANCADA - Clique em Senhas > Destrancar]"
            return None
        
        try:
            senha = self.servidor_manager.obter_senha(nome_servidor)
            if senha:
                logger.debug(f"Senha criptografada obtida para: {nome_servidor}")
                return senha
        except Exception as e:
            logger.warning(f"Erro ao obter senha criptografada para {nome_servidor}: {str(e)}")
        
        return None
    
    def _salvar_senha_automatica(self, servidor_nome: str, senha: str):
        """Salva senha automaticamente se habilitado"""
        if not self.check_salvar_senha.isChecked():
            return
        
        if servidor_nome == "Manual" or servidor_nome not in self.servidores:
            return
        
        try:
            if self.servidor_manager.salvar_senha(servidor_nome, senha):
                status = self.crypto_manager.get_status_info()
                tipo_chave = "personalizada" if status['has_custom_password'] else "padrão"
                logger.info(f"Senha salva automaticamente para: {servidor_nome} (chave {tipo_chave})")
                self._atualizar_indicador_senha_salva(True)
        except Exception as e:
            logger.exception("Erro ao salvar senha automaticamente")
    
    def _obter_opcoes_conexao(self, servidor_nome: str = None) -> Dict:
        """
        Obtém opções de conexão da interface.
        Se servidor_nome for informado e tiver 'sec' configurado,
        usa o sec do servidor; caso contrário, usa as opções globais da aba Opções.
        """
        # Verificar se o servidor tem sec específico configurado
        sec_value = None
        if servidor_nome and servidor_nome != "Manual":
            dados = self.servidor_manager.obter_servidor(servidor_nome)
            if dados and len(dados) >= 3 and dados[2]:  # (ip, usuario, sec)
                sec_value = dados[2]
                logger.debug(f"Usando sec do servidor '{servidor_nome}': {sec_value}")
        
        # Fallback para opções globais se servidor não tem sec definido
        if not sec_value:
            protocolos_sec = []
            if self.check_sec_rdp.isChecked():
                protocolos_sec.append('rdp')
            if self.check_sec_tls.isChecked():
                protocolos_sec.append('tls')
            if self.check_sec_nla.isChecked():
                protocolos_sec.append('nla')
            if self.check_sec_ext.isChecked():
                protocolos_sec.append('ext')
            if self.check_sec_aad.isChecked():
                protocolos_sec.append('aad')
            
            sec_value = ';'.join(protocolos_sec) if protocolos_sec else None
        
        return {
            'clipboard': self.check_clipboard.isChecked(),
            'montar_home': self.check_home.isChecked(),
            'som': SOM_MAP.get(self.combo_som.currentText(), 'local'),
            'impressoras': self.check_impressoras.isChecked(),
            'multimonitor': self.check_multimonitor.isChecked(),
            'resolucao': RESOLUCAO_MAP.get(self.combo_resolucao.currentText(), 'auto'),
            'qualidade': QUALIDADE_MAP.get(self.combo_qualidade.currentText(), 'broadband'),
            'ignorar_cert': self.check_ignorar_cert.isChecked(),
            'sec': sec_value
        }
    
    def _validar_entrada(self) -> Tuple[bool, str]:
        """Valida dados de entrada"""
        servidor = self.combo_servidor.currentText()
        
        if servidor == "Manual":
            host = self.edit_ip_manual.text().strip()
            if not host:
                return False, "Digite o IP para conexão manual"
            
            if not validar_ip_porta(host):
                return False, "IP/hostname inválido. Use: 192.168.1.100 ou 192.168.1.100:3389"
            
            host_normalizado = normalizar_ip_porta(host)
            self.edit_ip_manual.setText(host_normalizado)
            
        else:
            if servidor not in self.servidores:
                return False, "Servidor inválido"
        
        usuario = self.edit_usuario.text().strip()
        if not usuario:
            return False, "Digite o nome de usuário"
        
        senha = self.edit_senha.text()
        if not senha:
            return False, "Digite a senha"
        
        if senha.startswith("[SENHA TRANCADA"):
            return False, "Desbloqueie as senhas primeiro (Menu Senhas > Destrancar)"
        
        return True, ""
    
    def _conectar(self):
        """Inicia conexão RDP"""
        if not verificar_comando_disponivel("xfreerdp3"):
            QMessageBox.critical(self, "Dependências", 
                               "xfreerdp não encontrado. Instale o pacote freerdp.")
            return
        
        valido, erro = self._validar_entrada()
        if not valido:
            QMessageBox.warning(self, "Erro de Validação", erro)
            return
        
        servidor = self.combo_servidor.currentText()
        if servidor == "Manual":
            host = self.edit_ip_manual.text().strip()
        else:
            host, _ = self.servidores[servidor]
        
        usuario = self.edit_usuario.text().strip()
        senha = self.edit_senha.text()
        opcoes = self._obter_opcoes_conexao(servidor)
        
        self._salvar_senha_automatica(servidor, senha)
        self._salvar_configuracoes()
        self.config_app.adicionar_ao_historico(servidor, usuario)
        
        self._iniciar_conexao(host, usuario, senha, opcoes)
    
    def _conectar_rapido(self, servidor: str):
        """Conexão rápida via system tray"""
        if servidor not in self.servidores:
            return
        
        host, usuario_padrao = self.servidores[servidor]
        
        senha = self._obter_senha_criptografada(servidor)
        if not senha or senha.startswith("[SENHA TRANCADA"):
            self.show()
            self.raise_()
            self.activateWindow()
            if senha and senha.startswith("[SENHA TRANCADA"):
                self._notificar("FreeRDP-GUI", f"Desbloqueie as senhas primeiro")
            else:
                self._notificar("FreeRDP-GUI", f"Configure a senha para {servidor}")
            return
        
        opcoes = self._obter_opcoes_conexao(servidor)
        self._iniciar_conexao(host, usuario_padrao, senha, opcoes)
    
    def _iniciar_conexao(self, host: str, usuario: str, senha: str, opcoes: Dict):
        """Inicia conexão RDP com parâmetros fornecidos"""
        logger.info(f"Iniciando conexão RDP para {host} com usuário {usuario}")
        
        self.incrementar_conexoes()
        self.hide()
        
        thread_id = host
        rdp_thread = RDPThread(host, usuario, senha, opcoes)
        self.rdp_threads[thread_id] = rdp_thread
        rdp_thread.finished.connect(lambda sucesso, mensagem: self._on_conexao_finalizada(thread_id, sucesso, mensagem))
        rdp_thread.start()
    
    def _on_conexao_finalizada(self, thread_id: str, sucesso: bool, mensagem: str):
        """Chamado quando conexão RDP termina"""
        self.decrementar_conexoes()

        if thread_id in self.rdp_threads:
            thread = self.rdp_threads.pop(thread_id)
            thread.deleteLater()

        self.btn_conectar.setEnabled(True)
        self.btn_conectar.setText("Conectar")
        
        if sucesso:
            self._notificar("FreeRDP-GUI", mensagem)
            logger.info(mensagem)
        else:
            self._notificar("FreeRDP-GUI", f"Erro: {mensagem}", "error")
            logger.error(f"Erro na conexão: {mensagem}")
        
        self._limpar_thread_rdp()
    
    def _notificar(self, titulo: str, mensagem: str, tipo: str = "information"):
        """Envia notificação (desktop ou tray)"""
        if not notificar_desktop(titulo, mensagem, tipo):
            if hasattr(self, 'system_tray'):
                self.system_tray.notificar(titulo, mensagem, tipo)
    
    def _salvar_configuracoes(self):
        """Salva configurações atuais"""
        sec_protocols = []
        if self.check_sec_rdp.isChecked():
            sec_protocols.append('rdp')
        if self.check_sec_tls.isChecked():
            sec_protocols.append('tls')
        if self.check_sec_nla.isChecked():
            sec_protocols.append('nla')
        if self.check_sec_ext.isChecked():
            sec_protocols.append('ext')
        if self.check_sec_aad.isChecked():
            sec_protocols.append('aad')
        
        config = {
            'servidor': self.combo_servidor.currentText(),
            'usuario': self.edit_usuario.text(),
            'clipboard': self.check_clipboard.isChecked(),
            'montar_home': self.check_home.isChecked(),
            'som': self.combo_som.currentText(),
            'impressoras': self.check_impressoras.isChecked(),
            'multimonitor': self.check_multimonitor.isChecked(),
            'resolucao': self.combo_resolucao.currentText(),
            'qualidade': self.combo_qualidade.currentText(),
            'salvar_senha': self.check_salvar_senha.isChecked(),
            'ignorar_cert': self.check_ignorar_cert.isChecked(),
            'sec_protocols': sec_protocols,
        }
        
        self.settings_manager.salvar_configuracao_interface(config)
        logger.debug("Configurações salvas")
    
    def _restaurar_configuracoes(self):
        """Restaura configurações salvas"""
        config = self.settings_manager.carregar_configuracao_interface()
        
        if config.get('servidor') and config['servidor'] in self.servidores:
            self.combo_servidor.setCurrentText(config['servidor'])
        
        if config.get('usuario'):
            self.edit_usuario.setText(config['usuario'])
        
        self.check_clipboard.setChecked(config.get('clipboard', True))
        self.check_home.setChecked(config.get('montar_home', False))
        self.check_impressoras.setChecked(config.get('impressoras', False))
        self.check_multimonitor.setChecked(config.get('multimonitor', False))
        self.check_salvar_senha.setChecked(config.get('salvar_senha', True))
        self.check_ignorar_cert.setChecked(config.get('ignorar_cert', True))
        
        sec_protocols = config.get('sec_protocols', ['tls'])
        self.check_sec_rdp.setChecked('rdp' in sec_protocols)
        self.check_sec_tls.setChecked('tls' in sec_protocols)
        self.check_sec_nla.setChecked('nla' in sec_protocols)
        self.check_sec_ext.setChecked('ext' in sec_protocols)
        self.check_sec_aad.setChecked('aad' in sec_protocols)
        
        if config.get('som'):
            self.combo_som.setCurrentText(config['som'])
        
        if config.get('resolucao'):
            self.combo_resolucao.setCurrentText(config['resolucao'])
        
        if config.get('qualidade'):
            self.combo_qualidade.setCurrentText(config['qualidade'])
        
        logger.debug("Configurações restauradas")
    
    def mostrar_logs(self):
        """Mostra janela de logs"""
        if self.logs_window is None:
            self.logs_window = LogsWindow(self)
        
        self.logs_window.show()
        self.logs_window.raise_()
        self.logs_window.activateWindow()
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        if self._fechar_de_verdade:
            if not self._limpar_thread_rdp():
                logger.warning("Forçando saída mesmo com thread ativa")
            self._salvar_configuracoes()
            event.accept()
            return

        if self.conexoes_ativas > 0:
            resposta = QMessageBox.question(
                self, "Conexão Ativa", 
                "Há uma conexão RDP ativa. Deseja realmente sair?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if resposta == QMessageBox.StandardButton.Yes:
                self._limpar_thread_rdp()
                self.sair_aplicacao()
                event.accept()
            else:
                event.ignore()
                return
        
        if hasattr(self, 'system_tray') and self.system_tray.is_available():
            self.hide()
            event.ignore()
            self.verificar_saida_completa()
        else:
            self.sair_aplicacao()
            event.accept()

    def changeEvent(self, event):
        """Gerencia mudanças de estado da janela"""
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowMinimized:
                if hasattr(self, 'system_tray') and self.system_tray.is_available():
                    self.hide()
                    event.ignore()
        super().changeEvent(event)
    
    def show_window(self):
        """Mostra e foca a janela"""
        self.show()
        self.raise_()
        self.activateWindow()

    def _ocultar_janela(self):
        """Oculta a janela (minimiza para tray sem sair)"""
        logger.info("Ocultando janela para system tray")
        self.hide()

    def close(self):
        """Sair da aplicação explicitamente"""
        logger.info("Sinal sair_aplicacao recebido → encerrando de verdade")
        self._fechar_de_verdade = True
        super().close()
        QApplication.quit()

# Manter compatibilidade com o nome antigo
RDPConnectorWindow = FreeRDPGUIWindow
