"""
Dialog para gerenciamento da master password
"""

import logging
from typing import Optional

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox,
        QGroupBox, QDialogButtonBox
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QPixmap, QIcon
except ImportError as e:
    raise ImportError(f"PySide6 não encontrado: {e}")

from core.crypto import get_crypto_manager
from core.utils import get_project_root, arquivo_existe

logger = logging.getLogger(__name__)

class MasterPasswordDialog(QDialog):
    """Dialog para entrada da master password"""
    
    def __init__(self, parent=None, title: str = "Master Password", 
                 message: str = "Digite a master password:", 
                 is_first_time: bool = False):
        super().__init__(parent)
        
        self.crypto_manager = get_crypto_manager()
        self.password = ""
        self.is_first_time = is_first_time
        
        self._init_ui(title, message)
    
    def _init_ui(self, title: str, message: str):
        """Inicializa interface"""
        self.setWindowTitle(title)
        # Definir ícone do dialog a partir de assets com fallback
        try:
            icon_path = get_project_root() / "assets" / "rdp-icon.png"
            if arquivo_existe(str(icon_path)):
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
            else:
                theme_icon = QIcon.fromTheme("dialog-password")
                if not theme_icon.isNull():
                    self.setWindowIcon(theme_icon)
        except Exception:
            pass
        self.setModal(True)
        self.setFixedSize(400, 250 if not self.is_first_time else 350)
        
        layout = QVBoxLayout(self)
        
        # Ícone e mensagem principal
        self._add_header(layout, message)
        
        # Campos de senha
        self._add_password_fields(layout)
        
        # Opções adicionais para primeira vez
        if self.is_first_time:
            self._add_first_time_options(layout)
        
        # Botões
        self._add_buttons(layout)
        
        # Focar no primeiro campo
        self.password_edit.setFocus()
    
    def _add_header(self, parent_layout, message: str):
        """Adiciona header com ícone e mensagem"""
        header_layout = QHBoxLayout()
        
        # Ícone (tentar usar ícone do sistema)
        icon_label = QLabel()
        try:
            icon = QIcon.fromTheme("dialog-password", QIcon.fromTheme("security-high"))
            if not icon.isNull():
                pixmap = icon.pixmap(48, 48)
                icon_label.setPixmap(pixmap)
        except:
            # Fallback: texto
            icon_label.setText("🔐")
            icon_label.setFont(QFont("Arial", 24))
        
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Mensagem
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(message_label)
        
        parent_layout.addLayout(header_layout)
    
    def _add_password_fields(self, parent_layout):
        """Adiciona campos de senha"""
        form_layout = QFormLayout()
        
        # Campo principal de senha
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self._on_ok_clicked)
        form_layout.addRow("Senha:", self.password_edit)
        
        # Campo de confirmação (só na primeira vez)
        if self.is_first_time:
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_edit.returnPressed.connect(self._on_ok_clicked)
            form_layout.addRow("Confirmar:", self.confirm_edit)
        
        parent_layout.addLayout(form_layout)
    
    def _add_first_time_options(self, parent_layout):
        """Adiciona opções específicas da primeira configuração"""
        group_box = QGroupBox("Dicas de Segurança")
        group_layout = QVBoxLayout(group_box)
        
        # Dicas
        tips = [
            "• Use uma senha forte com pelo menos 12 caracteres",
            "• Misture letras, números e símbolos",
            "• Esta senha protegerá todas as suas senhas RDP",
            "• Não use senhas que você usa em outros lugares"
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setFont(QFont("Arial", 8))
            group_layout.addWidget(tip_label)
        
        parent_layout.addWidget(group_box)
    
    def _add_buttons(self, parent_layout):
        """Adiciona botões do dialog"""
        button_layout = QHBoxLayout()
        
        # Botão Mostrar/Ocultar senha
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(30, 30)
        self.show_password_btn.setToolTip("Mostrar/ocultar senha")
        self.show_password_btn.clicked.connect(self._toggle_password_visibility)
        button_layout.addWidget(self.show_password_btn)
        
        # Espaçador
        button_layout.addStretch()
        
        # Botões principais
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self._on_ok_clicked)
        btn_ok.setDefault(True)
        button_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        parent_layout.addLayout(button_layout)
    
    def _toggle_password_visibility(self):
        """Alterna visibilidade da senha"""
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            if self.is_first_time:
                self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            if self.is_first_time:
                self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁")
    
    def _on_ok_clicked(self):
        """Processa clique em OK"""
        password = self.password_edit.text()
        
        # Validações básicas
        if not password:
            QMessageBox.warning(self, "Erro", "Digite uma senha.")
            self.password_edit.setFocus()
            return
        
        # Validação específica da primeira vez
        if self.is_first_time:
            confirm_password = self.confirm_edit.text()
            
            if password != confirm_password:
                QMessageBox.warning(self, "Erro", "As senhas não conferem.")
                self.confirm_edit.clear()
                self.confirm_edit.setFocus()
                return
            
            if len(password) < 8:
                result = QMessageBox.question(
                    self, "Senha Fraca",
                    "A senha tem menos de 8 caracteres. Recomendamos pelo menos 12.\n\n"
                    "Deseja continuar mesmo assim?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if result != QMessageBox.StandardButton.Yes:
                    self.password_edit.setFocus()
                    return
        
        # Tentar definir a senha
        if self.crypto_manager.set_master_password(password):
            self.password = password
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", 
                               "Senha incorreta." if not self.is_first_time 
                               else "Erro ao definir senha.")
            self.password_edit.clear()
            if self.is_first_time:
                self.confirm_edit.clear()
            self.password_edit.setFocus()
    
    def get_password(self) -> Optional[str]:
        """
        Obtém senha digitada
        
        Returns:
            Senha digitada ou None se cancelado
        """
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.password
        return None

class ChangeMasterPasswordDialog(QDialog):
    """Dialog para alteração da master password"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.crypto_manager = get_crypto_manager()
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa interface"""
        self.setWindowTitle("Alterar Master Password")
        # Definir ícone do dialog de alteração a partir de assets com fallback
        try:
            icon_path = get_project_root() / "assets" / "rdp-icon.png"
            if arquivo_existe(str(icon_path)):
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
            else:
                theme_icon = QIcon.fromTheme("dialog-password")
                if not theme_icon.isNull():
                    self.setWindowIcon(theme_icon)
        except Exception:
            pass
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Aviso
        warning_label = QLabel(
            "⚠️ Alterar a master password irá re-criptografar todas as senhas salvas.\n"
            "Este processo pode demorar alguns segundos."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #FF8C00; padding: 10px; background-color: #FFF8DC; border-radius: 5px;")
        layout.addWidget(warning_label)
        
        # Campos
        form_layout = QFormLayout()
        
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Senha Atual:", self.current_password_edit)
        
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Nova Senha:", self.new_password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Confirmar:", self.confirm_password_edit)
        
        layout.addLayout(form_layout)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._change_password)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Focar no primeiro campo
        self.current_password_edit.setFocus()
    
    def _change_password(self):
        """Executa alteração da senha"""
        current = self.current_password_edit.text()
        new = self.new_password_edit.text()
        confirm = self.confirm_password_edit.text()
        
        # Validações
        if not current or not new or not confirm:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return
        
        if new != confirm:
            QMessageBox.warning(self, "Erro", "Nova senha e confirmação não conferem.")
            self.new_password_edit.clear()
            self.confirm_password_edit.clear()
            self.new_password_edit.setFocus()
            return
        
        if len(new) < 8:
            result = QMessageBox.question(
                self, "Senha Fraca",
                "A nova senha tem menos de 8 caracteres.\n\nDeseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return
        
        # Tentar alterar
        try:
            # Mostrar progresso
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            if self.crypto_manager.change_master_password(current, new):
                QApplication.restoreOverrideCursor()
                QMessageBox.information(self, "Sucesso", 
                                      "Master password alterada com sucesso!")
                self.accept()
            else:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Erro", 
                                   "Erro ao alterar master password. Verifique a senha atual.")
                self.current_password_edit.clear()
                self.current_password_edit.setFocus()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Erro", f"Erro inesperado: {str(e)}")
            logger.exception("Erro ao alterar master password")

# Funções de conveniência

def solicitar_master_password(parent=None, is_first_time: bool = False) -> Optional[str]:
    """
    Solicita master password do usuário
    
    Args:
        parent: Widget pai
        is_first_time: Se é a primeira vez definindo a senha
        
    Returns:
        Senha digitada ou None se cancelado
    """
    title = "Configurar Master Password" if is_first_time else "Master Password"
    message = ("Defina uma master password para proteger suas senhas RDP:" 
              if is_first_time 
              else "Digite sua master password:")
    
    dialog = MasterPasswordDialog(parent, title, message, is_first_time)
    return dialog.get_password()

def alterar_master_password(parent=None) -> bool:
    """
    Mostra dialog para alterar master password
    
    Args:
        parent: Widget pai
        
    Returns:
        True se senha foi alterada
    """
    dialog = ChangeMasterPasswordDialog(parent)
    return dialog.exec() == QDialog.DialogCode.Accepted