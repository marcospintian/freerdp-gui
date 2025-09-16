"""
Módulo para conexões RDP
"""

import os
import subprocess
import logging
from typing import Dict, Optional

try:
    from PySide6.QtCore import QThread, Signal
except ImportError:
    QThread = None
    Signal = None

from .utils import obter_pasta_home

logger = logging.getLogger(__name__)

class RDPConnectionError(Exception):
    """Exceção específica para erros de conexão RDP"""
    pass

class RDPThread(QThread):
    """Thread para executar conexão RDP sem travar a interface"""
    
    finished = Signal(bool, str)
    started = Signal()
    
    def __init__(self, host: str, usuario: str, senha: str, opcoes: Dict):
        super().__init__()
        self.host = host
        self.usuario = usuario
        self.senha = senha
        self.opcoes = opcoes or {}
    
    def run(self):
        """Executa conexão RDP"""
        try:
            self.started.emit()
            self._conectar_rdp()
            self.finished.emit(True, "Conexão RDP finalizada")
        except RDPConnectionError as e:
            logger.error(f"Erro RDP: {str(e)}")
            self.finished.emit(False, str(e))
        except Exception as e:
            logger.exception("Erro durante conexão RDP")
            self.finished.emit(False, f"Erro inesperado: {str(e)}")
    
    def _conectar_rdp(self):
        """Estabelece conexão RDP com opções avançadas"""
        cmd = self._construir_comando_rdp()
        
        logger.info(f"Iniciando conexão RDP para {self.host} com usuário {self.usuario}")
        logger.debug(f"Comando RDP: {' '.join(cmd[:10])}...")  # Log parcial por segurança
        
        try:
            resultado = subprocess.run(cmd, capture_output=True, text=True)
            
            if resultado.returncode != 0:
                error_msg = resultado.stderr.strip() if resultado.stderr else "Código de erro desconhecido"
                raise RDPConnectionError(f"Conexão RDP falhou (código {resultado.returncode}): {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise RDPConnectionError("Timeout na conexão RDP")
        except FileNotFoundError:
            raise RDPConnectionError("xfreerdp não encontrado. Instale o pacote freerdp.")
        except Exception as e:
            raise RDPConnectionError(f"Erro ao executar xfreerdp: {str(e)}")
    
    def _construir_comando_rdp(self) -> list:
        """Constrói comando xfreerdp com todas as opções"""
        cmd = [
            "xfreerdp3",
            f"/u:{self.usuario}",
            f"/p:{self.senha}",
            f"/v:{self.host}",
            "/cert:ignore",
            "/dynamic-resolution",
            "/compression",
            "/auto-reconnect"
        ]
        
        # Opções básicas
        if self.opcoes.get('clipboard', False):
            cmd.append("/clipboard")
            
        if self.opcoes.get('montar_home', False):
            home = obter_pasta_home()
            if os.path.exists(home):
                cmd.append(f"/drive:c,{home}")
        
        # Opções de som
        som = self.opcoes.get('som', 'local')
        if som == 'remoto':
            cmd.append("/audio-mode:1")
        elif som == 'ambos':
            cmd.append("/audio-mode:2")
        elif som == 'desabilitado':
            cmd.append("/audio-mode:0")
        else:  # local (padrão)
            cmd.append("/audio-mode:0")
        
        # Impressoras
        if self.opcoes.get('impressoras', False):
            cmd.append("/printer")
        
        # Múltiplos monitores
        if self.opcoes.get('multimonitor', False):
            cmd.append("/multimon")
            cmd.append("/span")
        
        # Resolução customizada
        resolucao = self.opcoes.get('resolucao', 'auto')
        if resolucao != 'auto':
            cmd.append(f"/size:{resolucao}")
        
        # Qualidade de conexão
        qualidade = self.opcoes.get('qualidade', 'broadband')
        if qualidade == 'modem':
            cmd.extend(["/bpp:8", "/compression-level:2"])
        elif qualidade == 'broadband':
            cmd.extend(["/bpp:16", "/compression-level:1"])
        elif qualidade == 'lan':
            cmd.extend(["/bpp:32", "/compression-level:0"])
        
        return cmd

def criar_opcoes_padrao() -> Dict:
    """Cria dicionário com opções padrão de conexão RDP"""
    return {
        'clipboard': True,
        'montar_home': False,
        'som': 'local',
        'impressoras': False,
        'multimonitor': False,
        'resolucao': 'auto',
        'qualidade': 'broadband'
    }