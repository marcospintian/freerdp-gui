"""
Dialog para gerenciamento de senhas no keyring
"""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QMessageBox
    )
    from PySide6.QtGui import QFont
except ImportError as e:
    raise ImportError(f"PySide6 não encontrado: {e}")

from core.servidores import get_servidor_manager

logger = logging.getLogger(__name__)

class PasswordManagerDialog(QDialog):
    """Dialog para gerenciar senhas de servidores no keyring"""
    
    def __init__(self, parent, servidor_nome: str):
        super().__init__(parent)
        
        self.servidor_nome = servidor_nome
        self.servidor_manager = get_servidor_manager()
        
        self._init_ui()
        self._carregar_estado_atual()
    
    def _init_ui(self):
        """Inicializa interface do usuário"""
        self.setWindowTitle(f"Gerenciar Senha - {self.servidor_nome}")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel(f"Gerenciar senha para: {self.servidor_nome}")
        titulo.setFont(QFont("", 10, QFont.Weight.Bold))
        layout.addWidget(titulo)
        
        # Status atual
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # Campo de senha
        form_layout = QFormLayout()
        
        self.senha_edit = QLineEdit()
        self.senha_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Senha:", self.senha_edit)
        
        layout.addLayout(form_layout)
        
        # Botões
        self._init_botoes(layout)
    
    def _init_botoes(self, parent_layout):
        """Inicializa botões do dialog"""
        button_layout = QHBoxLayout()
        
        self.btn_salvar = QPushButton("Salvar Senha")
        self.btn_salvar.clicked.connect(self._salvar_senha)
        button_layout.addWidget(self.btn_salvar)
        
        self.btn_remover = QPushButton("Remover Senha")
        self.btn_remover.clicked.connect(self._remover_senha)
        button_layout.addWidget(self.btn_remover)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancelar)
        
        parent_layout.addLayout(button_layout)
    
    def _carregar_estado_atual(self):
        """Carrega estado atual da senha"""
        senha_atual = self._obter_senha_keyring()
        
        if senha_atual:
            self.status_label.setText("✓ Senha salva no Keyring")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.senha_edit.setText(senha_atual)
            self.btn_remover.setEnabled(True)
        else:
            self.status_label.setText("✗ Nenhuma senha salva")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.btn_remover.setEnabled(False)
    
    def _obter_senha_keyring(self) -> str:
        """Obtém senha atual do keyring"""
        try:
            import keyring
            
            # Obter dados do servidor
            dados = self.servidor_manager.obter_servidor(self.servidor_nome)
            if not dados:
                logger.warning(f"Servidor '{self.servidor_nome}' não encontrado")
                return ""
            
            _, usuario = dados
            
            # Obter senha do keyring
            senha = keyring.get_password(self.servidor_nome, usuario)
            return senha if senha else ""
            
        except ImportError:
            logger.error("Keyring não disponível")
            return ""
        except Exception as e:
            logger.exception(f"Erro ao obter senha do keyring para {self.servidor_nome}")
            return ""
    
    def _salvar_senha(self):
        """Salva senha no keyring"""
        senha = self.senha_edit.text().strip()
        if not senha:
            QMessageBox.warning(self, "Erro", "Digite uma senha válida")
            return
        
        try:
            import keyring
            
            # Obter dados do servidor
            dados = self.servidor_manager.obter_servidor(self.servidor_nome)
            if not dados:
                QMessageBox.critical(self, "Erro", 
                                   f"Servidor '{self.servidor_nome}' não encontrado")
                return
            
            _, usuario = dados
            
            # Salvar senha no keyring
            keyring.set_password(self.servidor_nome, usuario, senha)
            
            logger.info(f"Senha salva no keyring para: {self.servidor_nome}")
            QMessageBox.information(self, "Sucesso", "Senha salva no keyring com sucesso!")
            
            self.accept()
            
        except ImportError:
            QMessageBox.critical(self, "Erro", "Keyring não disponível")
        except Exception as e:
            error_msg = f"Erro ao salvar senha: {str(e)}"
            logger.exception("Erro ao salvar senha no keyring")
            QMessageBox.critical(self, "Erro", error_msg)
    
    def _remover_senha(self):
        """Remove senha do keyring"""
        resposta = QMessageBox.question(
            self, "Confirmar", 
            f"Deseja remover a senha salva para {self.servidor_nome}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        try:
            import keyring
            
            # Obter dados do servidor
            dados = self.servidor_manager.obter_servidor(self.servidor_nome)
            if not dados:
                QMessageBox.critical(self, "Erro", 
                                   f"Servidor '{self.servidor_nome}' não encontrado")
                return
            
            _, usuario = dados
            
            # Remover senha do keyring
            keyring.delete_password(self.servidor_nome, usuario)
            
            logger.info(f"Senha removida do keyring para: {self.servidor_nome}")
            QMessageBox.information(self, "Sucesso", "Senha removida do keyring!")
            
            self.accept()
            
        except ImportError:
            QMessageBox.critical(self, "Erro", "Keyring não disponível")
        except Exception as e:
            error_msg = f"Erro ao remover senha: {str(e)}"
            logger.exception("Erro ao remover senha do keyring")
            QMessageBox.critical(self, "Erro", error_msg)

class PasswordInputDialog(QDialog):
    """Dialog simples para entrada de senha"""
    
    def __init__(self, parent, titulo: str = "Digite a Senha", 
                 mensagem: str = "Senha:", servidor_nome: str = ""):
        super().__init__(parent)
        
        self.senha = ""
        self.servidor_nome = servidor_nome
        
        self._init_ui(titulo, mensagem)
    
    def _init_ui(self, titulo: str, mensagem: str):
        """Inicializa interface"""
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        
        # Mensagem
        if self.servidor_nome:
            label_text = f"{mensagem}\nServidor: {self.servidor_name}"
        else:
            label_text = mensagem
        
        label = QLabel(label_text)
        layout.addWidget(label)
        
        # Campo de senha
        self.senha_edit = QLineEdit()
        self.senha_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.senha_edit.returnPressed.connect(self.accept)
        layout.addWidget(self.senha_edit)
        
        # Botões
        button_layout = QHBoxLayout()
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self._on_ok_clicked)
        btn_ok.setDefault(True)
        button_layout.addWidget(btn_ok)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancelar)
        
        layout.addLayout(button_layout)
        
        # Focar no campo de senha
        self.senha_edit.setFocus()
    
    def _on_ok_clicked(self):
        """Processa clique em OK"""
        self.senha = self.senha_edit.text()
        if self.senha.strip():
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Digite uma senha válida")
            self.senha_edit.setFocus()
    
    def get_password(self) -> Optional[str]:
        """
        Obtém senha digitada
        
        Returns:
            Senha digitada ou None se cancelado
        """
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.senha
        return None

def solicitar_senha(parent, servidor_nome: str) -> Optional[str]:
    """
    Função helper para solicitar senha
    
    Args:
        parent: Widget pai
        servidor_nome: Nome do servidor
        
    Returns:
        Senha digitada ou None se cancelado
    """
    dialog = PasswordInputDialog(
        parent, 
        f"Senha - {servidor_nome}",
        "Digite a senha:",
        servidor_nome
    )
    return dialog.get_password()