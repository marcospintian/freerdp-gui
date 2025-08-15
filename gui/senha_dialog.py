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