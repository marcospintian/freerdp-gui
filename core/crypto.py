"""
Módulo de criptografia para senhas do FreeRDP-GUI
"""

import os
import base64
import hashlib
import logging
from typing import Optional, Tuple
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class CryptoManager:
    """Gerenciador de criptografia para senhas"""
    
    def __init__(self, config_dir: Path = None):
        """
        Inicializa o gerenciador de criptografia
        
        Args:
            config_dir: Diretório de configuração (opcional)
        """
        if config_dir is None:
            config_dir = Path.home() / '.config' / 'freerdp-gui'
        
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo para armazenar salt da master password
        self.master_salt_file = self.config_dir / '.master_salt'
        
        # Cache da chave durante a sessão
        self._cached_key = None
        self._session_timeout = None
        
        logger.debug(f"CryptoManager inicializado em: {self.config_dir}")
    
    def _get_or_create_master_salt(self) -> bytes:
        """
        Obtém ou cria salt para a master password
        
        Returns:
            Salt de 32 bytes
        """
        if self.master_salt_file.exists():
            try:
                with open(self.master_salt_file, 'rb') as f:
                    salt = f.read()
                if len(salt) == 32:
                    return salt
                logger.warning("Salt inválido encontrado, criando novo")
            except Exception as e:
                logger.warning(f"Erro ao ler salt: {e}, criando novo")
        
        # Criar novo salt
        salt = os.urandom(32)
        try:
            with open(self.master_salt_file, 'wb') as f:
                f.write(salt)
            # Definir permissões restritas (só o usuário pode ler)
            os.chmod(self.master_salt_file, 0o600)
            logger.info("Novo salt da master password criado")
        except Exception as e:
            logger.error(f"Erro ao salvar salt: {e}")
            raise
        
        return salt
    
    def _derive_key_from_password(self, password: str) -> bytes:
        """
        Deriva chave criptográfica da master password
        
        Args:
            password: Master password
            
        Returns:
            Chave de 32 bytes para Fernet
        """
        salt = self._get_or_create_master_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # Recomendado pelo OWASP (2024)
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        return key
    
    def set_master_password(self, password: str) -> bool:
        """
        Define a master password para a sessão
        
        Args:
            password: Master password
            
        Returns:
            True se senha foi aceita
        """
        try:
            key = self._derive_key_from_password(password)
            
            # Testar se a chave funciona com dados existentes
            if self._validate_master_password(key):
                self._cached_key = key
                logger.info("Master password definida para a sessão")
                return True
            else:
                # Se não há dados criptografados ainda, aceitar qualquer senha
                # (primeira execução)
                if not self._has_encrypted_data():
                    self._cached_key = key
                    logger.info("Master password definida (primeira execução)")
                    return True
                else:
                    logger.warning("Master password incorreta")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao definir master password: {e}")
            return False
    
    def _validate_master_password(self, key: bytes) -> bool:
        """
        Valida master password tentando descriptografar dados existentes
        
        Args:
            key: Chave derivada da senha
            
        Returns:
            True se senha está correta
        """
        try:
            # Procurar por dados criptografados no INI para validar
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            
            # Carregar configuração
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            # Procurar primeira senha criptografada para testar
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    encrypted_data = servidor_manager.config[section_name]['senha_encrypted']
                    try:
                        # Tentar descriptografar
                        self._decrypt_data(encrypted_data, key)
                        return True
                    except:
                        return False
            
            # Se não há dados criptografados, não pode validar
            return True
            
        except Exception as e:
            logger.debug(f"Erro na validação da master password: {e}")
            return True  # Assumir válida se não pode verificar
    
    def _has_encrypted_data(self) -> bool:
        """
        Verifica se existem dados criptografados no sistema
        
        Returns:
            True se há dados criptografados
        """
        try:
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    return True
            
            return False
        except:
            return False
    
    def is_unlocked(self) -> bool:
        """
        Verifica se o crypto está desbloqueado (master password definida)
        
        Returns:
            True se está desbloqueado
        """
        return self._cached_key is not None
    
    def lock(self):
        """Remove chave da memória (trava o crypto)"""
        self._cached_key = None
        logger.info("CryptoManager travado")
    
    def encrypt_password(self, password: str, server_name: str) -> Optional[str]:
        """
        Criptografa uma senha
        
        Args:
            password: Senha em texto claro
            server_name: Nome do servidor (usado como contexto adicional)
            
        Returns:
            Senha criptografada em base64 ou None se erro
        """
        if not self.is_unlocked():
            logger.error("CryptoManager não está desbloqueado")
            return None
        
        try:
            # Criar salt único para esta senha
            salt = os.urandom(16)
            
            # Criar dados para criptografar (senha + contexto)
            data_to_encrypt = {
                'password': password,
                'server': server_name,
                'version': 1
            }
            
            import json
            plain_data = json.dumps(data_to_encrypt).encode('utf-8')
            
            # Criptografar
            fernet = Fernet(self._cached_key)
            encrypted_data = fernet.encrypt(plain_data)
            
            # Combinar salt + dados criptografados
            combined = salt + encrypted_data
            
            # Retornar como base64
            result = base64.b64encode(combined).decode('utf-8')
            
            logger.debug(f"Senha criptografada para servidor: {server_name}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao criptografar senha: {e}")
            return None
    
    def decrypt_password(self, encrypted_data: str, server_name: str) -> Optional[str]:
        """
        Descriptografa uma senha
        
        Args:
            encrypted_data: Dados criptografados em base64
            server_name: Nome do servidor (para validação)
            
        Returns:
            Senha em texto claro ou None se erro
        """
        if not self.is_unlocked():
            logger.error("CryptoManager não está desbloqueado")
            return None
        
        try:
            return self._decrypt_data(encrypted_data, self._cached_key, server_name)
        except Exception as e:
            logger.error(f"Erro ao descriptografar senha para {server_name}: {e}")
            return None
    
    def _decrypt_data(self, encrypted_data: str, key: bytes, server_name: str = None) -> str:
        """
        Descriptografa dados (método interno)
        
        Args:
            encrypted_data: Dados criptografados em base64
            key: Chave de descriptografia  
            server_name: Nome do servidor para validação (opcional)
            
        Returns:
            Senha em texto claro
            
        Raises:
            Exception: Se não conseguir descriptografar
        """
        # Decodificar base64
        combined = base64.b64decode(encrypted_data.encode('utf-8'))
        
        # Separar salt e dados criptografados
        salt = combined[:16]
        encrypted = combined[16:]
        
        # Descriptografar
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted)
        
        # Parse JSON
        import json
        data = json.loads(decrypted_data.decode('utf-8'))
        
        # Validar contexto se fornecido
        if server_name and data.get('server') != server_name:
            logger.warning(f"Contexto do servidor não confere: esperado={server_name}, encontrado={data.get('server')}")
        
        return data['password']
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        Altera a master password, re-criptografando todos os dados
        
        Args:
            old_password: Senha atual
            new_password: Nova senha
            
        Returns:
            True se alteração foi bem sucedida
        """
        try:
            # Validar senha atual
            old_key = self._derive_key_from_password(old_password)
            if not self._validate_master_password(old_key):
                logger.error("Senha atual incorreta")
                return False
            
            # Coletar todos os dados criptografados
            encrypted_passwords = {}
            
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            # Descriptografar todas as senhas com chave antiga
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    encrypted_data = servidor_manager.config[section_name]['senha_encrypted']
                    try:
                        plain_password = self._decrypt_data(encrypted_data, old_key, section_name)
                        encrypted_passwords[section_name] = plain_password
                    except Exception as e:
                        logger.error(f"Erro ao descriptografar senha de {section_name}: {e}")
                        return False
            
            # Gerar nova chave
            new_key = self._derive_key_from_password(new_password)
            
            # Re-criptografar todas as senhas com nova chave
            self._cached_key = new_key  # Temporariamente usar nova chave
            
            for section_name, password in encrypted_passwords.items():
                new_encrypted = self.encrypt_password(password, section_name)
                if new_encrypted:
                    servidor_manager.config[section_name]['senha_encrypted'] = new_encrypted
                else:
                    logger.error(f"Erro ao re-criptografar senha de {section_name}")
                    return False
            
            # Salvar configuração
            servidor_manager._salvar_config()
            
            # Remover salt antigo e criar novo (força derivação de nova chave)
            if self.master_salt_file.exists():
                self.master_salt_file.unlink()
            
            # Gerar novo salt e re-derivar chave
            self._cached_key = None
            self.set_master_password(new_password)
            
            logger.info("Master password alterada com sucesso")
            return True
            
        except Exception as e:
            logger.exception("Erro ao alterar master password")
            return False
    
    def export_encrypted_passwords(self) -> dict:
        """
        Exporta todas as senhas criptografadas (para backup)
        
        Returns:
            Dicionário com senhas criptografadas
        """
        try:
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            exported = {}
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    exported[section_name] = servidor_manager.config[section_name]['senha_encrypted']
            
            return exported
        except Exception as e:
            logger.error(f"Erro ao exportar senhas: {e}")
            return {}

# Instância global do gerenciador
_crypto_manager = None

def get_crypto_manager() -> CryptoManager:
    """Obtém instância singleton do gerenciador de criptografia"""
    global _crypto_manager
    if _crypto_manager is None:
        _crypto_manager = CryptoManager()
    return _crypto_manager