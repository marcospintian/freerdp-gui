"""
Módulo de criptografia para senhas do FreeRDP-GUI
Com master password opcional - usa chave padrão quando não configurada
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
    """Gerenciador de criptografia para senhas com master password opcional"""
    
    # Senha padrão para quando usuário não configura master password
    # Baseada em características do sistema para ser única por instalação
    DEFAULT_PASSWORD_BASE = "FreeRDP-GUI-2024-Default-Key"
    
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
        
        # Arquivo que indica se usuário configurou master password personalizada
        self.has_custom_password_file = self.config_dir / '.has_custom_password'
        
        # Cache da chave durante a sessão
        self._cached_key = None
        self._is_using_default_key = False
        
        # Auto-inicializar com chave apropriada
        self._auto_initialize()
        
        logger.debug(f"CryptoManager inicializado em: {self.config_dir}")
    
    def _auto_initialize(self):
        """Inicializa automaticamente com chave padrão ou personalizada"""
        if self.has_custom_master_password():
            # Usuário tem master password personalizada - precisa desbloquear manualmente
            logger.info("Master password personalizada detectada - aguardando desbloqueio")
        else:
            # Usar chave padrão automaticamente
            self._use_default_key()
            logger.info("Usando chave padrão (master password não configurada)")
    
    def has_custom_master_password(self) -> bool:
        """
        Verifica se usuário configurou master password personalizada
        
        Returns:
            True se tem master password personalizada
        """
        return self.has_custom_password_file.exists()
    
    def _use_default_key(self):
        """Usa chave padrão baseada no sistema"""
        try:
            # Criar senha padrão única para este sistema/usuário
            import platform
            import getpass
            
            system_info = f"{platform.node()}-{getpass.getuser()}-{self.DEFAULT_PASSWORD_BASE}"
            default_password = hashlib.sha256(system_info.encode()).hexdigest()[:32]
            
            # Derivar chave da senha padrão
            self._cached_key = self._derive_key_from_password(default_password, use_default_salt=True)
            self._is_using_default_key = True
            
            logger.debug("Chave padrão ativada")
        except Exception as e:
            logger.error(f"Erro ao usar chave padrão: {e}")
            self._cached_key = None
            self._is_using_default_key = False
    
    def _get_or_create_master_salt(self, use_default_salt: bool = False) -> bytes:
        """
        Obtém ou cria salt para a master password
        
        Args:
            use_default_salt: Se True, usa salt fixo para chave padrão
        
        Returns:
            Salt de 32 bytes
        """
        if use_default_salt:
            # Salt fixo para chave padrão (baseado no sistema)
            import platform
            salt_base = f"{self.DEFAULT_PASSWORD_BASE}-{platform.system()}"
            return hashlib.sha256(salt_base.encode()).digest()
        
        # Salt personalizado para master password do usuário
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
    
    def _derive_key_from_password(self, password: str, use_default_salt: bool = False) -> bytes:
        """
        Deriva chave criptográfica da password
        
        Args:
            password: Password para derivar a chave
            use_default_salt: Se usar salt padrão ou personalizado
            
        Returns:
            Chave de 32 bytes para Fernet
        """
        salt = self._get_or_create_master_salt(use_default_salt)
        
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
        Define a master password personalizada para a sessão
        
        Args:
            password: Master password personalizada
            
        Returns:
            True se senha foi aceita
        """
        try:
            key = self._derive_key_from_password(password, use_default_salt=False)
            
            # Se já existem dados criptografados, validar senha
            if self.has_custom_master_password():
                if not self._validate_master_password(key):
                    logger.warning("Master password incorreta")
                    return False
            
            # Marcar que agora tem password personalizada
            try:
                self.has_custom_password_file.touch()
                os.chmod(self.has_custom_password_file, 0o600)
            except Exception as e:
                logger.warning(f"Erro ao criar arquivo de marcação: {e}")
            
            # Se estava usando chave padrão e tem dados, migrar
            if self._is_using_default_key and self._has_encrypted_data():
                if not self._migrate_from_default_to_custom(key):
                    logger.error("Erro ao migrar dados da chave padrão para personalizada")
                    return False
            
            self._cached_key = key
            self._is_using_default_key = False
            logger.info("Master password personalizada definida")
            return True
                    
        except Exception as e:
            logger.error(f"Erro ao definir master password: {e}")
            return False
    
    def _migrate_from_default_to_custom(self, new_custom_key: bytes) -> bool:
        """
        Migra dados criptografados da chave padrão para chave personalizada
        
        Args:
            new_custom_key: Nova chave personalizada
            
        Returns:
            True se migração foi bem sucedida
        """
        try:
            # Salvar chave padrão atual
            old_default_key = self._cached_key
            
            # Obter todos os dados criptografados
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            # Descriptografar com chave padrão e re-criptografar com chave personalizada
            migrated_count = 0
            
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    encrypted_data = servidor_manager.config[section_name]['senha_encrypted']
                    
                    try:
                        # Descriptografar com chave padrão
                        plain_password = self._decrypt_data(encrypted_data, old_default_key, section_name)
                        
                        # Re-criptografar com chave personalizada
                        self._cached_key = new_custom_key  # Temporariamente
                        new_encrypted = self.encrypt_password(plain_password, section_name)
                        
                        if new_encrypted:
                            servidor_manager.config[section_name]['senha_encrypted'] = new_encrypted
                            migrated_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Erro ao migrar senha de {section_name}: {e}")
                        continue
            
            # Salvar configuração migrada
            if migrated_count > 0:
                servidor_manager._salvar_config()
                logger.info(f"Migração concluída: {migrated_count} senhas migradas para chave personalizada")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante migração: {e}")
            return False
    
    def remove_master_password(self) -> bool:
        """
        Remove master password personalizada e volta para chave padrão
        
        Returns:
            True se operação foi bem sucedida
        """
        if not self.has_custom_master_password():
            logger.info("Master password personalizada não estava configurada")
            return True
        
        try:
            # Obter dados criptografados atuais
            encrypted_data = {}
            
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            # Descriptografar todos com chave atual
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    encrypted = servidor_manager.config[section_name]['senha_encrypted']
                    try:
                        plain = self._decrypt_data(encrypted, self._cached_key, section_name)
                        encrypted_data[section_name] = plain
                    except Exception as e:
                        logger.warning(f"Erro ao descriptografar {section_name} durante remoção: {e}")
            
            # Remover arquivos de configuração personalizada
            try:
                if self.master_salt_file.exists():
                    self.master_salt_file.unlink()
                if self.has_custom_password_file.exists():
                    self.has_custom_password_file.unlink()
            except Exception as e:
                logger.warning(f"Erro ao remover arquivos de configuração: {e}")
            
            # Voltar para chave padrão
            self._use_default_key()
            
            # Re-criptografar dados com chave padrão
            for section_name, plain_password in encrypted_data.items():
                new_encrypted = self.encrypt_password(plain_password, section_name)
                if new_encrypted:
                    servidor_manager.config[section_name]['senha_encrypted'] = new_encrypted
            
            # Salvar
            servidor_manager._salvar_config()
            
            logger.info("Master password personalizada removida, voltando para chave padrão")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover master password: {e}")
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
            from .servidores import get_servidor_manager
            servidor_manager = get_servidor_manager()
            
            servidor_manager.config.read(servidor_manager.ini_path, encoding='utf-8')
            
            # Procurar primeira senha criptografada para testar
            for section_name in servidor_manager.config.sections():
                if servidor_manager.config.has_option(section_name, 'senha_encrypted'):
                    encrypted_data = servidor_manager.config[section_name]['senha_encrypted']
                    try:
                        self._decrypt_data(encrypted_data, key)
                        return True
                    except:
                        return False
            
            # Se não há dados criptografados, assumir válida
            return True
            
        except Exception as e:
            logger.debug(f"Erro na validação da master password: {e}")
            return True
    
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
        Verifica se o crypto está desbloqueado
        
        Returns:
            True se está desbloqueado (sempre True neste sistema)
        """
        return self._cached_key is not None
    
    def is_using_default_key(self) -> bool:
        """
        Verifica se está usando chave padrão
        
        Returns:
            True se usando chave padrão
        """
        return self._is_using_default_key
    
    def lock(self):
        """Trava apenas se estiver usando master password personalizada"""
        if not self._is_using_default_key:
            self._cached_key = None
            logger.info("CryptoManager travado (master password personalizada)")
        else:
            logger.info("Não é possível travar - usando chave padrão")
    
    def unlock_with_default_key(self):
        """Força uso da chave padrão (para recuperação)"""
        self._use_default_key()
    
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
            
            # Criar dados para criptografar (senha + contexto + tipo de chave)
            data_to_encrypt = {
                'password': password,
                'server': server_name,
                'version': 1,
                'key_type': 'default' if self._is_using_default_key else 'custom'
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
            # Se não tem master password personalizada, old_password será ignorada
            if not self.has_custom_master_password():
                logger.info("Definindo primeira master password personalizada")
                return self.set_master_password(new_password)
            
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
            self._cached_key = new_key
            self._is_using_default_key = False
            
            for section_name, password in encrypted_passwords.items():
                new_encrypted = self.encrypt_password(password, section_name)
                if new_encrypted:
                    servidor_manager.config[section_name]['senha_encrypted'] = new_encrypted
                else:
                    logger.error(f"Erro ao re-criptografar senha de {section_name}")
                    return False
            
            # Salvar configuração
            servidor_manager._salvar_config()
            
            # Remover salt antigo e criar novo
            if self.master_salt_file.exists():
                self.master_salt_file.unlink()
            
            logger.info("Master password alterada com sucesso")
            return True
            
        except Exception as e:
            logger.exception("Erro ao alterar master password")
            return False
    
    def get_status_info(self) -> dict:
        """
        Obtém informações de status do sistema de criptografia
        
        Returns:
            Dicionário com informações de status
        """
        return {
            'is_unlocked': self.is_unlocked(),
            'has_custom_password': self.has_custom_master_password(),
            'is_using_default_key': self.is_using_default_key(),
            'has_encrypted_data': self._has_encrypted_data(),
            'config_dir': str(self.config_dir)
        }
    
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