"""
Widget para gerenciamento de servidores
"""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox
    )
    from PySide6.QtCore import Signal
except ImportError as e:
    raise ImportError(f"PySide6 não encontrado: {e}")

from core.servidores import get_servidor_manager
from core.utils import validar_ip_porta

logger = logging.getLogger(__name__)

class GerenciadorServidoresWidget(QWidget):
    """Widget integrado para gerenciar servidores"""
    
    servidores_atualizados = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Gerenciador de servidores
        self.servidor_manager = get_servidor_manager()
        
        # Estado
        self.modo_edicao = False
        self.nome_sendo_editado = None
        
        self._init_ui()
        self._recarregar_servidores()
    
    def _init_ui(self):
        """Inicializa interface do usuário"""
        layout = QVBoxLayout(self)
        
        # Lista de servidores
        layout.addWidget(QLabel("Servidores:"))
        
        self.lista = QListWidget()
        self.lista.currentTextChanged.connect(self._carregar_detalhes)
        layout.addWidget(self.lista)
        
        # Formulário de detalhes
        self._init_formulario(layout)
        
        # Botões de ação
        self._init_botoes_acao(layout)
        
        # Inicializar no modo leitura
        self._definir_modo_leitura()
    
    def _init_formulario(self, parent_layout):
        """Inicializa formulário de detalhes"""
        form_layout = QFormLayout()
        
        self.input_nome = QLineEdit()
        form_layout.addRow("Nome:", self.input_nome)
        
        self.input_ip = QLineEdit()
        self.input_ip.setPlaceholderText("192.168.1.100:3389")
        form_layout.addRow("IP:Porta:", self.input_ip)
        
        self.input_usuario = QLineEdit()
        form_layout.addRow("Usuário:", self.input_usuario)
        
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Senha:", self.input_senha)
        
        parent_layout.addLayout(form_layout)
    
    def _init_botoes_acao(self, parent_layout):
        """Inicializa botões de ação"""
        botoes_layout = QHBoxLayout()
        
        self.btn_novo = QPushButton("Novo")
        self.btn_novo.clicked.connect(self._novo_servidor)
        botoes_layout.addWidget(self.btn_novo)
        
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self._editar_servidor)
        botoes_layout.addWidget(self.btn_editar)
        
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.clicked.connect(self._salvar_servidor)
        botoes_layout.addWidget(self.btn_salvar)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self._cancelar_edicao)
        botoes_layout.addWidget(self.btn_cancelar)
        
        self.btn_remover = QPushButton("Remover")
        self.btn_remover.clicked.connect(self._remover_servidor)
        botoes_layout.addWidget(self.btn_remover)
        
        parent_layout.addLayout(botoes_layout)
    
    def _definir_modo_leitura(self):
        """Configura interface para modo somente leitura"""
        # Desabilitar campos
        self.input_nome.setEnabled(False)
        self.input_ip.setEnabled(False)
        self.input_usuario.setEnabled(False)
        self.input_senha.setEnabled(False)
        
        # Configurar botões
        self.btn_salvar.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        self.btn_novo.setEnabled(True)
        self.btn_editar.setEnabled(True)
        self.btn_remover.setEnabled(True)
        
        self.modo_edicao = False
    
    def _definir_modo_edicao(self):
        """Configura interface para modo de edição"""
        # Habilitar campos
        self.input_nome.setEnabled(True)
        self.input_ip.setEnabled(True)
        self.input_usuario.setEnabled(True)
        self.input_senha.setEnabled(True)
        
        # Configurar botões
        self.btn_salvar.setEnabled(True)
        self.btn_cancelar.setEnabled(True)
        self.btn_novo.setEnabled(False)
        self.btn_editar.setEnabled(False)
        self.btn_remover.setEnabled(False)
        
        self.modo_edicao = True
    
    def _recarregar_servidores(self):
        """Recarrega lista de servidores"""
        try:
            servidores = self.servidor_manager.listar_servidores()
            
            self.lista.clear()
            for servidor in servidores:
                self.lista.addItem(servidor)
            
            logger.info(f"Lista de servidores recarregada: {len(servidores)} itens")
            
        except Exception as e:
            logger.error(f"Erro ao recarregar servidores: {str(e)}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar servidores: {str(e)}")
    
    def _carregar_detalhes(self, nome: str):
        """Carrega detalhes do servidor selecionado"""
        if not nome:
            self._limpar_campos()
            return
        
        try:
            dados = self.servidor_manager.obter_servidor(nome)
            if dados:
                ip, usuario = dados
                
                self.input_nome.setText(nome)
                self.input_ip.setText(ip)
                self.input_usuario.setText(usuario)
                
                # Tentar carregar senha do keyring
                senha = self._obter_senha_keyring(nome, usuario)
                self.input_senha.setText(senha)
            else:
                self._limpar_campos()
                
        except Exception as e:
            logger.error(f"Erro ao carregar detalhes do servidor '{nome}': {str(e)}")
            self._limpar_campos()
    
    def _obter_senha_keyring(self, nome: str, usuario: str) -> str:
        """Obtém senha do keyring"""
        try:
            import keyring
            senha = keyring.get_password(nome, usuario)
            return senha if senha else ""
        except Exception as e:
            logger.warning(f"Erro ao obter senha do keyring: {str(e)}")
            return ""
    
    def _limpar_campos(self):
        """Limpa todos os campos do formulário"""
        self.input_nome.clear()
        self.input_ip.clear()
        self.input_usuario.clear()
        self.input_senha.clear()
    
    def _novo_servidor(self):
        """Inicia criação de novo servidor"""
        self.lista.clearSelection()
        self._limpar_campos()
        
        self.nome_sendo_editado = None
        self._definir_modo_edicao()
        
        self.input_nome.setFocus()
        logger.debug("Iniciado modo de criação de servidor")
    
    def _editar_servidor(self):
        """Inicia edição do servidor selecionado"""
        item_atual = self.lista.currentItem()
        if not item_atual:
            QMessageBox.warning(self, "Erro", "Selecione um servidor para editar.")
            return
        
        self.nome_sendo_editado = item_atual.text()
        self._definir_modo_edicao()
        
        self.input_nome.setFocus()
        logger.debug(f"Iniciada edição do servidor: {self.nome_sendo_editado}")
    
    def _salvar_servidor(self):
        """Salva servidor (novo ou editado)"""
        # Validar dados
        nome = self.input_nome.text().strip()
        ip = self.input_ip.text().strip()
        usuario = self.input_usuario.text().strip()
        senha = self.input_senha.text()
        
        if not self._validar_dados(nome, ip, usuario):
            return
        
        try:
            # Verificar se é edição ou criação
            if self.nome_sendo_editado:
                success = self._salvar_edicao(nome, ip, usuario, senha)
                acao = "editado"
            else:
                success = self._salvar_novo(nome, ip, usuario, senha)
                acao = "criado"
            
            if success:
                self._finalizar_salvamento(nome, acao)
            
        except Exception as e:
            logger.exception("Erro ao salvar servidor")
            QMessageBox.critical(self, "Erro", f"Erro ao salvar servidor: {str(e)}")
    
    def _validar_dados(self, nome: str, ip: str, usuario: str) -> bool:
        """Valida dados do servidor"""
        if not nome or not ip or not usuario:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios.")
            return False
        
        if not validar_ip_porta(ip):
            QMessageBox.warning(self, "Erro", "IP inválido. Use o formato: 192.168.1.100:3389")
            return False
        
        return True
    
    def _salvar_novo(self, nome: str, ip: str, usuario: str, senha: str) -> bool:
        """Salva novo servidor"""
        if self.servidor_manager.servidor_existe(nome):
            resposta = QMessageBox.question(
                self, "Confirmar",
                f"O servidor '{nome}' já existe. Deseja sobrescrever?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resposta != QMessageBox.StandardButton.Yes:
                return False
        
        # Salvar servidor
        if not self.servidor_manager.salvar_servidor(nome, ip, usuario):
            QMessageBox.critical(self, "Erro", "Erro ao salvar servidor no arquivo INI")
            return False
        
        # Salvar senha se fornecida
        if senha:
            self._salvar_senha_keyring(nome, usuario, senha)
        
        return True
    
    def _salvar_edicao(self, nome: str, ip: str, usuario: str, senha: str) -> bool:
        """Salva edição de servidor existente"""
        # Se nome mudou, verificar se novo nome já existe
        if self.nome_sendo_editado != nome and self.servidor_manager.servidor_existe(nome):
            QMessageBox.warning(self, "Erro", f"Já existe um servidor com o nome '{nome}'.")
            return False
        
        # Se nome mudou, renomear servidor
        if self.nome_sendo_editado != nome:
            if not self.servidor_manager.renomear_servidor(self.nome_sendo_editado, nome):
                QMessageBox.critical(self, "Erro", "Erro ao renomear servidor")
                return False
            
            # Migrar senha no keyring se necessário
            self._migrar_senha_keyring(self.nome_sendo_editado, nome, usuario)
        
        # Atualizar dados do servidor
        if not self.servidor_manager.salvar_servidor(nome, ip, usuario):
            QMessageBox.critical(self, "Erro", "Erro ao salvar servidor")
            return False
        
        # Atualizar senha se fornecida
        if senha:
            self._salvar_senha_keyring(nome, usuario, senha)
        
        return True
    
    def _salvar_senha_keyring(self, nome: str, usuario: str, senha: str):
        """Salva senha no keyring"""
        try:
            import keyring
            keyring.set_password(nome, usuario, senha)
            logger.info(f"Senha salva no keyring para: {nome}")
        except Exception as e:
            logger.warning(f"Erro ao salvar senha no keyring: {str(e)}")
    
    def _migrar_senha_keyring(self, nome_antigo: str, nome_novo: str, usuario: str):
        """Migra senha entre nomes de servidor no keyring"""
        try:
            import keyring
            
            # Obter senha antiga
            senha_antiga = keyring.get_password(nome_antigo, usuario)
            if senha_antiga:
                # Salvar com novo nome
                keyring.set_password(nome_novo, usuario, senha_antiga)
                # Remover senha antiga
                keyring.delete_password(nome_antigo, usuario)
                logger.info(f"Senha migrada de '{nome_antigo}' para '{nome_novo}'")
                
        except Exception as e:
            logger.warning(f"Erro ao migrar senha no keyring: {str(e)}")
    
    def _finalizar_salvamento(self, nome: str, acao: str):
        """Finaliza processo de salvamento"""
        # Recarregar lista
        self._recarregar_servidores()
        
        # Selecionar servidor salvo
        items = self.lista.findItems(nome, self.lista.MatchFlag.MatchExactly)
        if items:
            self.lista.setCurrentItem(items[0])
        
        # Voltar ao modo leitura
        self.nome_sendo_editado = None
        self._definir_modo_leitura()
        
        # Notificar atualização
        self.servidores_atualizados.emit()
        
        # Mostrar sucesso
        QMessageBox.information(self, "Sucesso", f"Servidor '{nome}' {acao} com sucesso!")
        logger.info(f"Servidor '{nome}' {acao}")
    
    def _cancelar_edicao(self):
        """Cancela edição atual"""
        self.nome_sendo_editado = None
        self._definir_modo_leitura()
        
        # Recarregar detalhes do item selecionado
        item_atual = self.lista.currentItem()
        if item_atual:
            self._carregar_detalhes(item_atual.text())
        else:
            self._limpar_campos()
        
        logger.debug("Edição cancelada")
    
    def _remover_servidor(self):
        """Remove servidor selecionado"""
        item_atual = self.lista.currentItem()
        if not item_atual:
            QMessageBox.warning(self, "Erro", "Selecione um servidor para remover.")
            return
        
        nome = item_atual.text()
        
        # Confirmar remoção
        resposta = QMessageBox.question(
            self, "Confirmar",
            f"Tem certeza que deseja remover o servidor '{nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Obter dados do servidor antes de remover
            dados = self.servidor_manager.obter_servidor(nome)
            
            # Remover do arquivo INI
            if not self.servidor_manager.remover_servidor(nome):
                QMessageBox.critical(self, "Erro", "Erro ao remover servidor do arquivo")
                return
            
            # Remover senha do keyring
            if dados:
                _, usuario = dados
                self._remover_senha_keyring(nome, usuario)
            
            # Atualizar interface
            self._recarregar_servidores()
            self._limpar_campos()
            
            # Notificar atualização
            self.servidores_atualizados.emit()
            
            QMessageBox.information(self, "Sucesso", f"Servidor '{nome}' removido com sucesso!")
            logger.info(f"Servidor '{nome}' removido")
            
        except Exception as e:
            logger.exception("Erro ao remover servidor")
            QMessageBox.critical(self, "Erro", f"Erro ao remover servidor: {str(e)}")
    
    def _remover_senha_keyring(self, nome: str, usuario: str):
        """Remove senha do keyring"""
        try:
            import keyring
            keyring.delete_password(nome, usuario)
            logger.info(f"Senha removida do keyring para: {nome}")
        except Exception as e:
            logger.warning(f"Erro ao remover senha do keyring: {str(e)}")
    
    def refresh(self):
        """Atualiza dados do widget"""
        self._recarregar_servidores()
        if not self.modo_edicao:
            item_atual = self.lista.currentItem()
            if item_atual:
                self._carregar_detalhes(item_atual.text())