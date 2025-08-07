"""
Funções utilitárias compartilhadas
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# --- Constantes ---
LOG_LEVEL = logging.INFO
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 3

# Mapeamentos de opções
SOM_MAP = {
    "Local (padrão)": "local",
    "Remoto": "remoto", 
    "Ambos": "ambos",
    "Desabilitado": "desabilitado"
}

RESOLUCAO_MAP = {
    "Automática": "auto",
    "1920x1080": "1920x1080",
    "1600x900": "1600x900",
    "1366x768": "1366x768",
    "1280x1024": "1280x1024",
    "1024x768": "1024x768",
    "800x600": "800x600"
}

QUALIDADE_MAP = {
    "LAN (melhor)": "lan",
    "Broadband": "broadband",
    "Modem (menor)": "modem"
}

def setup_logging() -> logging.Logger:
    """Configura sistema de logging com rotação"""
    log_path = os.path.expanduser('~/.config/rdp-connector.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    rotating_handler = RotatingFileHandler(
        log_path, 
        maxBytes=LOG_MAX_SIZE, 
        backupCount=LOG_BACKUP_COUNT
    )

    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[rotating_handler, logging.StreamHandler()]
    )
    
    return logging.getLogger(__name__)

def get_log_path() -> str:
    """Retorna caminho do arquivo de log"""
    return os.path.expanduser('~/.config/rdp-connector.log')

def get_project_root() -> Path:
    """Retorna diretório raiz do projeto"""
    return Path(__file__).parent.parent

def get_ini_path() -> Path:
    """Retorna caminho do arquivo servidores.ini"""
    return get_project_root() / "servidores.ini"

def verificar_comando_disponivel(comando: str) -> bool:
    """Verifica se um comando está disponível no sistema"""
    try:
        subprocess.run([comando, "--help"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def validar_ip_porta(ip_porta: str) -> bool:
    """Validação simples de IP:porta usando regex"""
    # Aceita IPs, hostnames e portas
    pattern = r'^[a-zA-Z0-9.-]+:\d+$'
    return bool(re.match(pattern, ip_porta))

def notificar_desktop(titulo: str, mensagem: str, icone: str = "information") -> bool:
    """
    Envia notificação desktop usando notify-send
    
    Args:
        titulo: Título da notificação
        mensagem: Texto da notificação
        icone: Tipo do ícone (information, error, warning)
        
    Returns:
        True se notificação foi enviada com sucesso
    """
    try:
        if verificar_comando_disponivel("notify-send"):
            icon_name = "krdc" if icone == "information" else "error"
            subprocess.run([
                "notify-send", 
                "-i", icon_name,
                titulo, 
                mensagem
            ], timeout=5)
            return True
    except Exception:
        pass
    
    return False

def expandir_usuario(caminho: str) -> str:
    """Expande ~ para diretório do usuário"""
    return os.path.expanduser(caminho)

def criar_diretorio(caminho: str) -> bool:
    """Cria diretório se não existir"""
    try:
        os.makedirs(caminho, exist_ok=True)
        return True
    except Exception:
        return False

def ler_arquivo_texto(caminho: str, encoding: str = 'utf-8') -> Optional[str]:
    """Lê arquivo de texto com tratamento de erro"""
    try:
        with open(caminho, 'r', encoding=encoding) as f:
            return f.read()
    except Exception:
        return None

def escrever_arquivo_texto(caminho: str, conteudo: str, encoding: str = 'utf-8') -> bool:
    """Escreve arquivo de texto com tratamento de erro"""
    try:
        with open(caminho, 'w', encoding=encoding) as f:
            f.write(conteudo)
        return True
    except Exception:
        return False

def arquivo_existe(caminho: str) -> bool:
    """Verifica se arquivo existe"""
    return os.path.exists(caminho)

def obter_pasta_home() -> str:
    """Obtém pasta home do usuário"""
    return os.path.expanduser("~")