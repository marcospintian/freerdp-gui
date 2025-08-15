"""
Janela principal da aplicação RDP Connector
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
from core.utils import SOM_MAP, RESOLUCAO_MAP, QUALIDADE_MAP, notificar_desktop, verificar_comando_disponivel

from .gerenciador import GerenciadorServidoresWidget
from .logs_window import LogsWindow
from .system_tray import SystemTrayManager

logger = logging.getLogger(__name__)

class RDPConnectorWindow(QMainWindow):
    """Janela principal da aplicação"""
    
    # SINAL ADICIONADO - Indica quando a aplicação deve realmente sair
    aplicacao_deve_sair = Signal()
    
    def __init__(self):
        super().__init__()
        self._fechar_de_verdade = False
        
        # CONTADOR DE CONEXÕES ATIVAS ADICIONADO
        self.conexoes_ativas = 0

        # Managers
        self.servidor_manager = get_servidor_manager()
        self.settings_manager = get_settings_manager()
        self.config_app = get_configuracoes_app()
        
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
        
        logger.info("Janela principal inicializada")
    
    # MÉTODOS ADICIONADOS PARA CONTROLE DE CONEXÕES
    def incrementar_conexoes(self):
        """Incrementa contador de conexões ativas"""
        self.conexoes_ativas += 1
        logger.info(f"Conexões ativas: {self.conexoes_ativas}")
        
    def decrementar_conexoes(self):
        """Decrementa contador de conexões ativas"""
        self.conexoes_ativas = max(0, self.conexoes_ativas - 1)
        logger.info(f"Conexões ativas: {self.conexoes_ativas}")
        
        # Verificar se deve sair após desconexão
        if self.conexoes_ativas == 0:
            self.verificar_saida_completa()
    
    def verificar_saida_completa(self):
        """Verifica se a aplicação deve sair completamente"""
        # Se não há conexões ativas e a janela está oculta
        if self.conexoes_ativas == 0 and not self.isVisible():
            logger.info("Sem conexões ativas e janela oculta - considerando saída")
            # Aguardar um pouco antes de decidir sair (dar tempo para nova conexão)
            QTimer.singleShot(5000, self.considerar_saida)  # 5 segundos
    
    def considerar_saida(self):
        """Considera sair se ainda não há atividade"""
        if self.conexoes_ativas == 0 and not self.isVisible():
            logger.info("Decidindo sair da aplicação")
            self.sair_aplicacao()
    
    def sair_aplicacao(self):
        """Método para sair completamente da aplicação"""
        logger.info("Saindo da aplicação completamente")
        
        # Esconder system tray primeiro
        if hasattr(self, 'system_tray'):
            self.system_tray.hide()
        
        # Fechar todas as conexões RDP ativas
        self.encerrar_todas_conexoes()
        
        # Salvar configurações
        self._salvar_configuracoes()
        
        # Marcar para fechar de verdade
        self._fechar_de_verdade = True
        
        # Emitir sinal de saída
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

            # Remover do dicionário independentemente do sucesso da finalização
            if thread_id in self.rdp_threads:
                del self.rdp_threads[thread_id]

        logger.info("Todas as threads RDP finalizadas com sucesso")
        return True

    def _init_ui(self):
        """Inicializa interface do usuário"""
        self.setWindowTitle("RDP Connector Pro")
        self.setFixedSize(500, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Abas
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Aba Conexão
        self._init_aba_conexao()
        
        # Aba Opções
        self._init_aba_opcoes()
        
        # Aba Gerenciar Servidores
        self._init_aba_servidores()
        
        # Botões principais
        self._init_botoes_principais(layout)
    
    def _init_aba_conexao(self):
        """Inicializa aba de conexão"""
        self.tab_conexao = QWidget()
        self.tabs.addTab(self.tab_conexao, "Conexão")
        
        layout = QVBoxLayout(self.tab_conexao)
        
        # Configurações do Servidor
        servidor_layout = QFormLayout()
        
        self.combo_servidor = QComboBox()
        self.combo_servidor.currentTextChanged.connect(self._on_servidor_changed)
        servidor_layout.addRow("Servidor:", self.combo_servidor)
        
        self.edit_ip_manual = QLineEdit()
        self.edit_ip_manual.setPlaceholderText("Digite IP:porta (ex: 192.168.1.100:3389)")
        self.edit_ip_manual.setVisible(False)
        servidor_layout.addRow("IP Manual:", self.edit_ip_manual)
        
        layout.addLayout(servidor_layout)
        
        # Credenciais
        self._init_credenciais_form(layout)
    
    def _init_credenciais_form(self, parent_layout):
        """Inicializa formulário de credenciais"""
        cred_layout = QFormLayout()
        
        self.edit_usuario = QLineEdit()
        cred_layout.addRow("Usuário:", self.edit_usuario)
        
        # Layout da senha com botão gerenciar
        senha_layout = QHBoxLayout()
        
        self.edit_senha = QLineEdit()
        self.edit_senha.setEchoMode(QLineEdit.EchoMode.Password)
        senha_layout.addWidget(self.edit_senha)
        
        self.btn_gerenciar_senha = QPushButton("Gerenciar")
        self.btn_gerenciar_senha.setMaximumWidth(80)
        self.btn_gerenciar_senha.clicked.connect(self._gerenciar_senha)
        senha_layout.addWidget(self.btn_gerenciar_senha)
        
        senha_widget = QWidget()
        senha_widget.setLayout(senha_layout)
        cred_layout.addRow("Senha:", senha_widget)
        
        parent_layout.addLayout(cred_layout)
    
    def _init_aba_opcoes(self):
        """Inicializa aba de opções"""
        self.tab_opcoes = QWidget()
        self.tabs.addTab(self.tab_opcoes, "Opções")
        
        layout = QVBoxLayout(self.tab_opcoes)
        
        # Opções básicas
        self.check_clipboard = QCheckBox("Compartilhar área de transferência")
        self.check_clipboard.setChecked(True)
        layout.addWidget(self.check_clipboard)
        
        self.check_home = QCheckBox("Montar pasta pessoal como drive C:")
        layout.addWidget(self.check_home)
        
        self.check_salvar_senha = QCheckBox("Salvar senha automaticamente")
        layout.addWidget(self.check_salvar_senha)
        
        # Som
        som_layout = QFormLayout()
        self.combo_som = QComboBox()
        self.combo_som.addItems(list(SOM_MAP.keys()))
        som_layout.addRow("Som:", self.combo_som)
        layout.addLayout(som_layout)
        
        # Dispositivos
        self.check_impressoras = QCheckBox("Compartilhar impressoras")
        layout.addWidget(self.check_impressoras)
        
        # Display
        self._init_opcoes_display(layout)
    
    def _init_opcoes_display(self, parent_layout):
        """Inicializa opções de display"""
        display_layout = QFormLayout()
        
        self.check_multimonitor = QCheckBox("Usar múltiplos monitores")
        parent_layout.addWidget(self.check_multimonitor)
        
        self.combo_resolucao = QComboBox()
        self.combo_resolucao.addItems(list(RESOLUCAO_MAP.keys()))
        display_layout.addRow("Resolução:", self.combo_resolucao)
        
        # Qualidade
        self.combo_qualidade = QComboBox()
        self.combo_qualidade.addItems(list(QUALIDADE_MAP.keys()))
        self.combo_qualidade.setCurrentText("Broadband")  # Padrão
        display_layout.addRow("Qualidade:", self.combo_qualidade)
        
        parent_layout.addLayout(display_layout)
    
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
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.close)
        button_layout.addWidget(btn_cancelar)
        
        parent_layout.addLayout(button_layout)
    
    def _init_system_tray(self):
        """Inicializa gerenciador do system tray"""
        self.system_tray = SystemTrayManager(self)
        self.system_tray.conectar_sinais_janela_principal(self)
    
    def _carregar_servidores(self):
        """Carrega servidores do gerenciador e atualiza interface"""
        self.servidores = self.servidor_manager.carregar_servidores()
        
        # Salvar seleção atual
        servidor_atual = self.combo_servidor.currentText()
        
        # Atualizar combo
        self.combo_servidor.clear()
        self.combo_servidor.addItems(list(self.servidores.keys()))
        
        # Restaurar seleção se ainda existe
        if servidor_atual in self.servidores:
            self.combo_servidor.setCurrentText(servidor_atual)
        
        # Atualizar system tray
        if hasattr(self, 'system_tray'):
            self.system_tray.atualizar_menu_servidores(self.servidores)
        
        logger.info(f"Carregados {len(self.servidores)} servidores")
    
    def _on_servidor_changed(self, servidor_nome: str):
        """Chamado quando servidor é alterado no combo"""
        if servidor_nome == "Manual":
            self.edit_ip_manual.setVisible(True)
            self.edit_usuario.setText("usuario")
            self.edit_senha.setText("")
            self.btn_gerenciar_senha.setEnabled(False)
        else:
            self.edit_ip_manual.setVisible(False)
            self.btn_gerenciar_senha.setEnabled(True)
            
            if servidor_nome in self.servidores:
                _, usuario_padrao = self.servidores[servidor_nome]
                self.edit_usuario.setText(usuario_padrao)
                
                # Tentar carregar senha do keyring
                senha = self._obter_senha_keyring(servidor_nome)
                self.edit_senha.setText(senha)
    
    def _obter_senha_keyring(self, nome_servidor: str) -> str:
        """Obtém senha do keyring para o servidor"""
        try:
            import keyring
            
            if nome_servidor not in self.servidores:
                return ""
            
            _, usuario = self.servidores[nome_servidor]
            senha = keyring.get_password(nome_servidor, usuario)
            
            if senha:
                logger.info(f"Senha obtida do keyring para: {nome_servidor}")
                return senha
            
        except Exception as e:
            logger.warning(f"Erro ao obter senha do keyring para {nome_servidor}: {str(e)}")
        
        return ""
    
    def _salvar_senha_automatica(self, servidor_nome: str, senha: str):
        """Salva senha automaticamente se habilitado"""
        if not self.check_salvar_senha.isChecked():
            return
        
        if servidor_nome == "Manual" or servidor_nome not in self.servidores:
            return
        
        try:
            import keyring
            
            # Verificar se senha já existe
            senha_atual = self._obter_senha_keyring(servidor_nome)
            if senha_atual == senha:
                return
            
            _, usuario = self.servidores[servidor_nome]
            keyring.set_password(servidor_nome, usuario, senha)
            
            logger.info(f"Senha salva automaticamente para: {servidor_nome}")
            self._notificar("RDP Connector", f"Senha salva automaticamente para {servidor_nome}")
                
        except Exception as e:
            logger.exception("Erro ao salvar senha automaticamente")
    
    def _gerenciar_senha(self):
        """Abre dialog para gerenciar senhas"""
        servidor = self.combo_servidor.currentText()
        if servidor == "Manual":
            QMessageBox.information(self, "Info", 
                                  "Gerenciamento de senha não disponível para conexões manuais")
            return
        
        dialog = PasswordManagerDialog(self, servidor)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._on_servidor_changed(servidor)
    
    def _obter_opcoes_conexao(self) -> Dict:
        """Obtém opções de conexão da interface"""
        return {
            'clipboard': self.check_clipboard.isChecked(),
            'montar_home': self.check_home.isChecked(),
            'som': SOM_MAP.get(self.combo_som.currentText(), 'local'),
            'impressoras': self.check_impressoras.isChecked(),
            'multimonitor': self.check_multimonitor.isChecked(),
            'resolucao': RESOLUCAO_MAP.get(self.combo_resolucao.currentText(), 'auto'),
            'qualidade': QUALIDADE_MAP.get(self.combo_qualidade.currentText(), 'broadband')
        }
    
    def _validar_entrada(self) -> Tuple[bool, str]:
        """Valida dados de entrada"""
        servidor = self.combo_servidor.currentText()
        
        if servidor == "Manual":
            host = self.edit_ip_manual.text().strip()
            if not host:
                return False, "Digite o IP para conexão manual"
            
            if ":" not in host:
                host = f"{host}:3389"
                self.edit_ip_manual.setText(host)
        else:
            if servidor not in self.servidores:
                return False, "Servidor inválido"
        
        usuario = self.edit_usuario.text().strip()
        if not usuario:
            return False, "Digite o nome de usuário"
        
        senha = self.edit_senha.text()
        if not senha:
            return False, "Digite a senha"
        
        return True, ""
    
    def _conectar(self):
        """Inicia conexão RDP"""
        # Verificar dependências
        if not verificar_comando_disponivel("xfreerdp"):
            QMessageBox.critical(self, "Dependências", 
                               "xfreerdp não encontrado. Instale o pacote freerdp.")
            return
        
        # Validar entrada
        valido, erro = self._validar_entrada()
        if not valido:
            QMessageBox.warning(self, "Erro de Validação", erro)
            return
        
        # Obter dados
        servidor = self.combo_servidor.currentText()
        if servidor == "Manual":
            host = self.edit_ip_manual.text().strip()
        else:
            host, _ = self.servidores[servidor]
        
        usuario = self.edit_usuario.text().strip()
        senha = self.edit_senha.text()
        opcoes = self._obter_opcoes_conexao()
        
        # Salvar senha se habilitado
        self._salvar_senha_automatica(servidor, senha)
        
        # Salvar configurações atuais
        self._salvar_configuracoes()
        
        # Adicionar ao histórico
        self.config_app.adicionar_ao_historico(servidor, usuario)
        
        # Iniciar conexão
        self._iniciar_conexao(host, usuario, senha, opcoes)
    
    def _conectar_rapido(self, servidor: str):
        """Conexão rápida via system tray"""
        if servidor not in self.servidores:
            return
        
        host, usuario_padrao = self.servidores[servidor]
        
        # Tentar obter senha do keyring
        senha = self._obter_senha_keyring(servidor)
        if not senha:
            self.show()
            self.raise_()
            self.activateWindow()
            self._notificar("RDP Connector", f"Senha necessária para {servidor}")
            return
        
        # Usar opções da interface
        opcoes = self._obter_opcoes_conexao()

        
        # Iniciar conexão
        self._iniciar_conexao(host, usuario_padrao, senha, opcoes)
    
    def _iniciar_conexao(self, host: str, usuario: str, senha: str, opcoes: Dict):
        """Inicia conexão RDP com parâmetros fornecidos"""
        logger.info(f"Iniciando conexão RDP para {host} com usuário {usuario}")
        
        self._notificar("RDP Connector", f"Conectando a {host}...")
        
        # INCREMENTAR CONTADOR DE CONEXÕES
        self.incrementar_conexoes()
        
        # Minimizar janela
        self.hide()
        
        # Criar e iniciar thread
        # Crie uma chave única para a conexão, como o host
        thread_id = host
        # Crie e inicie a nova thread
        rdp_thread = RDPThread(host, usuario, senha, opcoes)
        # Armazene a thread no dicionário
        self.rdp_threads[thread_id] = rdp_thread
        # Conecte o sinal finished a um novo método que gerencie a finalização
        rdp_thread.finished.connect(lambda sucesso, mensagem: self._on_conexao_finalizada(thread_id, sucesso, mensagem))
        rdp_thread.start()
        
        # Desabilitar botão conectar
        #self.btn_conectar.setEnabled(False)
        #self.btn_conectar.setText("Conectando...")
    
    def _on_conexao_finalizada(self, thread_id: str, sucesso: bool, mensagem: str):
        """Chamado quando conexão RDP termina"""
        # DECREMENTAR CONTADOR DE CONEXÕES - AQUI ESTÁ O PONTO CRUCIAL
        self.decrementar_conexoes()

         # Remova a thread do dicionário
        if thread_id in self.rdp_threads:
            thread = self.rdp_threads.pop(thread_id)
            thread.deleteLater() # Limpa o objeto da memória

        # Reabilitar interface
        self.btn_conectar.setEnabled(True)
        self.btn_conectar.setText("Conectar")
        
        # Notificar resultado
        if sucesso:
            self._notificar("RDP Connector", mensagem)
            logger.info(mensagem)
        else:
            self._notificar("RDP Connector", f"Erro: {mensagem}", "error")
            logger.error(f"Erro na conexão: {mensagem}")
        
        # Limpar thread CORRETAMENTE
        self._limpar_thread_rdp()
    
    def _notificar(self, titulo: str, mensagem: str, tipo: str = "information"):
        """Envia notificação (desktop ou tray)"""
        # Tentar notificação desktop primeiro
        if not notificar_desktop(titulo, mensagem, tipo):
            # Fallback para system tray
            if hasattr(self, 'system_tray'):
                self.system_tray.notificar(titulo, mensagem, tipo)
    
    def _salvar_configuracoes(self):
        """Salva configurações atuais"""
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
            #Não quero geometria nem estado da Janela
            #'geometry': self.saveGeometry(),
            #'windowState': self.saveState()
        }
        
        self.settings_manager.salvar_configuracao_interface(config)
        logger.debug("Configurações salvas")
    
    def _restaurar_configuracoes(self):
        """Restaura configurações salvas"""
        config = self.settings_manager.carregar_configuracao_interface()
        
        # Restaurar valores dos controles
        if config.get('servidor') and config['servidor'] in self.servidores:
            self.combo_servidor.setCurrentText(config['servidor'])
        
        if config.get('usuario'):
            self.edit_usuario.setText(config['usuario'])
        
        self.check_clipboard.setChecked(config.get('clipboard', True))
        self.check_home.setChecked(config.get('montar_home', False))
        self.check_impressoras.setChecked(config.get('impressoras', False))
        self.check_multimonitor.setChecked(config.get('multimonitor', False))
        self.check_salvar_senha.setChecked(config.get('salvar_senha', False))
        
        # Combos
        if config.get('som'):
            self.combo_som.setCurrentText(config['som'])
        
        if config.get('resolucao'):
            self.combo_resolucao.setCurrentText(config['resolucao'])
        
        if config.get('qualidade'):
            self.combo_qualidade.setCurrentText(config['qualidade'])
        
        # Geometria da janela
        #if config.get('geometry'):
        #    self.restoreGeometry(config['geometry'])
        #
        #if config.get('windowState'):
        #    self.restoreState(config['windowState'])
        
        logger.debug("Configurações restauradas")
    
    def mostrar_logs(self):
        """Mostra janela de logs"""
        if self.logs_window is None:
            self.logs_window = LogsWindow(self)
        
        self.logs_window.show()
        self.logs_window.raise_()
        self.logs_window.activateWindow()
    
    def closeEvent(self, event):
        """Evento de fechamento da janela - MÉTODO MODIFICADO"""
        if self._fechar_de_verdade:
            # Garantir que threads sejam finalizadas antes de fechar
            if not self._limpar_thread_rdp():
                logger.warning("Forçando saída mesmo com thread ativa")
            self._salvar_configuracoes()
            event.accept()
            return

        # Se há conexão ativa, perguntar se quer sair
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
        
        # Se tiver system tray, minimizar
        if hasattr(self, 'system_tray') and self.system_tray.is_available():
            self.hide()
            self._notificar("RDP Connector", "Aplicativo minimizado para a bandeja")
            event.ignore()
            # Verificar se deve sair completamente
            self.verificar_saida_completa()
        else:
            self.sair_aplicacao()
            event.accept()

    def changeEvent(self, event):
        """Gerencia mudanças de estado da janela"""
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowMinimized:
                # Se tem system tray, esconder quando minimizar
                if hasattr(self, 'system_tray') and self.system_tray.is_available():
                    self.hide()
                    event.ignore()
        super().changeEvent(event)
    
    def show_window(self):
        """Mostra e foca a janela"""
        self.show()
        self.raise_()
        self.activateWindow()

    def close(self):
        """Sair da aplicação explicitamente - MÉTODO MODIFICADO"""
        print("Sinal sair_aplicacao recebido → encerrando de verdade")
        self._fechar_de_verdade = True
        super().close()
        QApplication.quit()