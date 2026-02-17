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
    config_dir = Path(os.path.expanduser('~/.config/freerdp-gui'))
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Se o arquivo não existe no diretório de config mas existe no diretório do programa,
    # copia o arquivo do programa para o diretório de config
    config_file = config_dir / "servidores.ini"
    if not config_file.exists():
        try:
            # Tenta copiar do diretório do programa primeiro
            program_ini = get_project_root() / "servidores.ini"
            if program_ini.exists():
                import shutil
                shutil.copy2(program_ini, config_file)
        except Exception:
            pass
    
    return config_file

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
    """
    Validação de IP/hostname com porta opcional
    Aceita: 192.168.1.100, 192.168.1.100:3389, servidor.com, servidor.com:3389
    """
    if not ip_porta or not ip_porta.strip():
        return False
    
    ip_porta = ip_porta.strip()
    
    # Padrão com porta especificada
    if ':' in ip_porta:
        try:
            host, porta_str = ip_porta.rsplit(':', 1)
            porta = int(porta_str)
            # Validar se porta está em range válido
            if not (1 <= porta <= 65535):
                return False
        except (ValueError, IndexError):
            return False
    else:
        # Sem porta especificada - usar padrão 3389
        host = ip_porta
    
    # Validar hostname/IP (básico)
    # Aceita letras, números, pontos, hífens
    import re
    pattern = r'^[a-zA-Z0-9.-]+$'
    if not re.match(pattern, host):
        return False
    
    # Não pode começar ou terminar com ponto ou hífen
    if host.startswith('.') or host.endswith('.') or host.startswith('-') or host.endswith('-'):
        return False
    
    return True

def normalizar_ip_porta(ip_porta: str) -> str:
    """
    Normaliza IP/porta adicionando :3389 se não especificado
    
    Args:
        ip_porta: IP ou hostname com ou sem porta
        
    Returns:
        IP/hostname com porta (sempre no formato host:porta)
    """
    if not ip_porta:
        return ip_porta
    
    ip_porta = ip_porta.strip()
    
    # Se já tem porta, retornar como está
    if ':' in ip_porta:
        return ip_porta
    
    # Adicionar porta padrão
    return f"{ip_porta}:3389"

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