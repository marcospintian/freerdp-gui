"""
Janela para visualização de logs da aplicação
"""

import logging
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout,
        QTextEdit, QPushButton, QMessageBox
    )
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFont
except ImportError as e:
    raise ImportError(f"PySide6 não encontrado: {e}")

from core.utils import get_log_path, ler_arquivo_texto, arquivo_existe

logger = logging.getLogger(__name__)

class LogsWindow(QDialog):
    """Janela para visualização de logs da aplicação"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.log_path = get_log_path()
        self.last_content = ""
        
        self._init_ui()
        self._load_logs()
        
        # Timer para atualização automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._load_logs)
        self.update_timer.start(2000)  # Atualizar a cada 2 segundos
    
    def _init_ui(self):
        """Inicializa interface do usuário"""
        self.setWindowTitle("Logs - RDP Connector Pro")
        self.setModal(False)  # Permitir interação com janela principal
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Área de texto dos logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))  # Fonte monospace
        
        # Configurar cores para melhor legibilidade
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # Botões de ação
        self._init_buttons(layout)
    
    def _init_buttons(self, parent_layout):
        """Inicializa botões da janela"""
        button_layout = QHBoxLayout()
        
        # Botão atualizar
        btn_refresh = QPushButton("Atualizar")
        btn_refresh.clicked.connect(self._load_logs)
        btn_refresh.setToolTip("Recarregar logs do arquivo")
        button_layout.addWidget(btn_refresh)
        
        # Botão limpar logs
        btn_clear = QPushButton("Limpar Logs")
        btn_clear.clicked.connect(self._clear_logs)
        btn_clear.setToolTip("Limpar arquivo de log")
        button_layout.addWidget(btn_clear)
        
        # Botão salvar logs
        btn_save = QPushButton("Salvar Como...")
        btn_save.clicked.connect(self._save_logs)
        btn_save.setToolTip("Salvar logs em arquivo")
        button_layout.addWidget(btn_save)
        
        # Espaçador
        button_layout.addStretch()
        
        # Botão fechar
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        button_layout.addWidget(btn_close)
        
        parent_layout.addLayout(button_layout)
    
    def _load_logs(self):
        """Carrega logs do arquivo"""
        try:
            if not arquivo_existe(self.log_path):
                self.log_text.setPlainText("Arquivo de log não encontrado.")
                return
            
            # Ler arquivo de log
            content = ler_arquivo_texto(self.log_path)
            if content is None:
                self.log_text.setPlainText("Erro ao ler arquivo de log.")
                return
            
            # Verificar se conteúdo mudou
            if content == self.last_content:
                return
            
            # Limitar número de linhas (últimas 1000 linhas)
            lines = content.splitlines()
            if len(lines) > 1000:
                lines = lines[-1000:]
                content = '\n'.join(lines)
            
            # Atualizar texto
            self.log_text.setPlainText(content)
            self.last_content = content
            
            # Rolar para o final
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            logger.exception("Erro ao carregar logs")
            self.log_text.setPlainText(f"Erro ao carregar logs: {str(e)}")
    
    def _clear_logs(self):
        """Limpa arquivo de log"""
        resposta = QMessageBox.question(
            self, "Confirmar", 
            "Deseja limpar todos os logs?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Limpar arquivo
            with open(self.log_path, 'w', encoding='utf-8') as f:
                f.write('')
            
            # Limpar texto na interface
            self.log_text.clear()
            self.last_content = ""
            
            # Log da ação
            logger.info("Logs limpos pelo usuário")
            
            QMessageBox.information(self, "Sucesso", "Logs limpos com sucesso!")
            
        except Exception as e:
            logger.exception("Erro ao limpar logs")
            QMessageBox.critical(self, "Erro", f"Erro ao limpar logs: {str(e)}")
    
    def _save_logs(self):
        """Salva logs em arquivo"""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            # Dialog para salvar arquivo
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Logs Como...",
                "rdp-connector-logs.txt",
                "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
            )
            
            if not file_path:
                return
            
            # Obter conteúdo atual
            content = self.log_text.toPlainText()
            
            # Salvar arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(self, "Sucesso", 
                                  f"Logs salvos em:\n{file_path}")
            
            logger.info(f"Logs salvos pelo usuário em: {file_path}")
            
        except Exception as e:
            logger.exception("Erro ao salvar logs")
            QMessageBox.critical(self, "Erro", f"Erro ao salvar logs: {str(e)}")
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        # Parar timer de atualização
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Aceitar fechamento
        event.accept()
    
    def showEvent(self, event):
        """Evento de exibição da janela"""
        # Carregar logs quando janela for mostrada
        self._load_logs()
        super().showEvent(event)

class LogViewer:
    """Classe utilitária para visualização de logs"""
    
    @staticmethod
    def show_logs(parent=None) -> LogsWindow:
        """
        Mostra janela de logs
        
        Args:
            parent: Widget pai
            
        Returns:
            Instância da janela de logs
        """
        logs_window = LogsWindow(parent)
        logs_window.show()
        logs_window.raise_()
        logs_window.activateWindow()
        
        return logs_window
    
    @staticmethod
    def clear_logs() -> bool:
        """
        Limpa arquivo de logs
        
        Returns:
            True se limpou com sucesso
        """
        try:
            log_path = get_log_path()
            
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('')
            
            logger.info("Logs limpos programaticamente")
            return True
            
        except Exception as e:
            logger.exception("Erro ao limpar logs")
            return False