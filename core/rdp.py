"""
Módulo para conexões RDP
"""

import os
import subprocess
import logging
from typing import Dict, Optional

try:
    from PySide6.QtCore import QThread, Signal
    PYSIDE6_AVAILABLE = True
except ImportError:
    QThread = None
    Signal = None
    PYSIDE6_AVAILABLE = False

from .utils import obter_pasta_home

logger = logging.getLogger(__name__)

def get_rdp_command() -> list:
    """
    Retorna o comando RDP apropriado baseado no ambiente.
    
    - Sempre tenta usar o FreeRDP do Flathub primeiro
    - Se não estiver disponível, usa xfreerdp3 do sistema
    """
    # Verificar se FreeRDP do Flathub está disponível
    try:
        result = subprocess.run(
            ["flatpak", "run", "com.freerdp.FreeRDP", "/help"],
            capture_output=True, timeout=5
        )
        # Se o app responder, ele está instalado e disponível
        if result.returncode != 127:
            return ["flatpak", "run", "com.freerdp.FreeRDP"]
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Fallback para versão do sistema
    return ["xfreerdp3"]

class RDPConnectionError(Exception):
    """Exceção específica para erros de conexão RDP"""
    pass

if PYSIDE6_AVAILABLE:
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
                    stderr = resultado.stderr.strip() if resultado.stderr else ""
                    
                    # Mensagens que indicam encerramento NORMAL (não erro real)
                    mensagens_normais = [
                        "LOGOFF_BY_USER",           # Usuário fez logoff
                        "STATE_RUN_QUIT_SESSION",   # Sessão encerrada normalmente
                        "CONNECTION_STATE_",        # Diferentes estados de desconexão normal
                        "ERRCONNECT_CONNECT_CANCELLED",  # Fechamento pelo usuário no FreeRDP 3.x
                        "freerdp_abort_connect_context",  # cancelamento de conexão
                        "handleShow"                # aviso do SDL quando fecha a tela
                    ]
                    
                    # Se há [ERROR] e não é um dos encerramento normais, é erro real
                    if "[ERROR]" in stderr:
                        # Verificar se é um erro normal ou cancelamento pelo usuário
                        eh_normal = any(msg in stderr for msg in mensagens_normais)
                        
                        if eh_normal:
                            logger.info("Conexão RDP encerrada normalmente (cancelada pelo usuário)")
                        else:
                            # É um erro real
                            error_lines = [line for line in stderr.split('\n') if "[ERROR]" in line]
                            error_msg = " ".join(error_lines[:2]) if error_lines else stderr  # Limitar a 2 linhas
                            raise RDPConnectionError(f"Conexão RDP falhou: {error_msg}")
                    else:
                        # Apenas warnings ou sem mensagens = encerramento normal
                        logger.info(f"Conexão RDP encerrada normalmente (código {resultado.returncode})")
                    
            except subprocess.TimeoutExpired:
                raise RDPConnectionError("Timeout na conexão RDP")
            except FileNotFoundError:
                raise RDPConnectionError("FreeRDP não encontrado. Instale o pacote freerdp ou verifique o Flatpak.")
            except RDPConnectionError:
                raise  # Re-raise RDPConnectionError
            except Exception as e:
                raise RDPConnectionError(f"Erro ao executar FreeRDP: {str(e)}")
        
        def _construir_comando_rdp(self) -> list:
            """Constrói comando xfreerdp com todas as opções"""
            cmd = []
            cmd.extend(get_rdp_command())
            cmd.extend([
                f"/u:{self.usuario}",
                f"/p:{self.senha}",
                f"/v:{self.host}",
                "/dynamic-resolution",
                "/compression",
                "/auto-reconnect"
            ])
            
            # Certificado SSL/TLS
            if self.opcoes.get('ignorar_cert', True):
                cmd.append("/cert:ignore")
            
            # Opções de segurança
            sec_options = self.opcoes.get('sec', None)
            if sec_options:
                cmd.append(f"/sec:{sec_options}")
            
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
else:
    # Stub class quando PySide6 não está disponível
    class RDPThread:
        """Stub class quando PySide6 não está disponível"""
        def __init__(self, *args, **kwargs):
            raise ImportError("PySide6 não está disponível para usar RDPThread")

def criar_opcoes_padrao() -> Dict:
    """Cria dicionário com opções padrão de conexão RDP"""
    return {
        'clipboard': True,
        'montar_home': False,
        'som': 'local',
        'impressoras': False,
        'multimonitor': False,
        'resolucao': 'auto',
        'qualidade': 'broadband',
        'ignorar_cert': True,
        'sec': None  # Exemplos: 'rdp', 'tls', 'nla', 'rdp:on;tls:off', etc
    }