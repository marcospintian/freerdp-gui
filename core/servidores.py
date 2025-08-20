"""
Módulo para gerenciamento de servidores via arquivo INI com criptografia de senhas
"""

import logging
import configparser
from typing import Dict, Tuple, Optional
from pathlib import Path

from .utils import get_ini_path, validar_ip_porta
from .crypto import get_crypto_manager

logger = logging.getLogger(__name__)

class ServidorManager:
    """Gerenciador de servidores com suporte a senhas criptografadas"""
    
    def __init__(self):
        self.ini_path = get_ini_path()
        self.config = configparser.ConfigParser()
        self.crypto_manager = get_crypto_manager()
        self._criar_arquivo_exemplo_se_necessario()
    
    def _criar_arquivo_exemplo_se_necessario(self):
        """Cria arquivo INI de exemplo se não existir"""
        if not self.ini_path.exists():
            self.config['Servidor1'] = {
                'ip': '192.168.1.100:3389',
                'usuario': 'administrador'
                # Nota: senhas serão criptografadas quando salvas via interface
            }
            self.config['Servidor2'] = {
                'ip': '10.0.0.50:3389', 
                'usuario': 'user'
            }
            
            try:
                self._salvar_config()
                logger.info(f"Arquivo de exemplo criado: {self.ini_path}")
            except Exception as e:
                logger.error(f"Erro ao criar arquivo INI: {str(e)}")
    
    def carregar_servidores(self) -> Dict[str, Tuple[str, str]]:
        """
        Carrega servidores do arquivo INI
        
        Returns:
            Dict com nome_servidor -> (ip:porta, usuario)
        """
        servidores = {}
        
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            
            for secao in self.config.sections():
                try:
                    ip = self.config[secao].get("ip", "manual")
                    usuario = self.config[secao].get("usuario", "usuario")
                    servidores[secao] = (ip, usuario)
                except Exception as e:
                    logger.error(f"Erro ao processar seção '{secao}': {str(e)}")
            
            logger.info(f"Carregados {len(servidores)} servidores do arquivo INI")
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo INI: {str(e)}")
        
        # Sempre adicionar opção Manual
        servidores["Manual"] = ("manual", "usuario")
        
        return servidores
    
    def salvar_servidor(self, nome: str, ip: str, usuario: str, senha: str = None) -> bool:
        """
        Salva servidor no arquivo INI
        
        Args:
            nome: Nome do servidor
            ip: Endereço IP:porta
            usuario: Nome do usuário
            senha: Senha em texto claro (será criptografada automaticamente)
            
        Returns:
            True se salvou com sucesso
        """
        if not nome or not ip or not usuario:
            logger.error("Dados inválidos para salvar servidor")
            return False
        
        if not validar_ip_porta(ip):
            logger.error(f"IP inválido: {ip}")
            return False
        
        try:
            # Criar seção do servidor
            self.config[nome] = {
                "ip": ip, 
                "usuario": usuario
            }
            
            # Criptografar e salvar senha se fornecida
            if senha:
                if not self.salvar_senha(nome, senha):
                    logger.warning(f"Erro ao salvar senha para servidor '{nome}', mas servidor foi salvo")
            
            self._salvar_config()
            logger.info(f"Servidor '{nome}' salvo com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar servidor '{nome}': {str(e)}")
            return False
    
    def salvar_senha(self, nome_servidor: str, senha: str) -> bool:
        """
        Salva senha criptografada para um servidor
        
        Args:
            nome_servidor: Nome do servidor
            senha: Senha em texto claro
            
        Returns:
            True se salvou com sucesso
        """
        if not self.crypto_manager.is_unlocked():
            logger.error("CryptoManager não está desbloqueado para salvar senha")
            return False
        
        try:
            # Criptografar senha
            encrypted_password = self.crypto_manager.encrypt_password(senha, nome_servidor)
            if not encrypted_password:
                logger.error(f"Erro ao criptografar senha para '{nome_servidor}'")
                return False
            
            # Salvar no INI
            if nome_servidor not in self.config:
                logger.error(f"Servidor '{nome_servidor}' não existe")
                return False
            
            self.config[nome_servidor]['senha_encrypted'] = encrypted_password
            self._salvar_config()
            
            logger.info(f"Senha criptografada salva para servidor '{nome_servidor}'")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar senha para '{nome_servidor}': {str(e)}")
            return False
    
    def obter_senha(self, nome_servidor: str) -> Optional[str]:
        """
        Obtém senha descriptografada para um servidor
        
        Args:
            nome_servidor: Nome do servidor
            
        Returns:
            Senha em texto claro ou None se não encontrada/erro
        """
        if not self.crypto_manager.is_unlocked():
            logger.error("CryptoManager não está desbloqueado para obter senha")
            return None
        
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            
            if nome_servidor not in self.config:
                logger.warning(f"Servidor '{nome_servidor}' não encontrado")
                return None
            
            # Verificar se tem senha criptografada
            if not self.config.has_option(nome_servidor, 'senha_encrypted'):
                logger.debug(f"Servidor '{nome_servidor}' não tem senha salva")
                return None
            
            encrypted_password = self.config[nome_servidor]['senha_encrypted']
            
            # Descriptografar
            plain_password = self.crypto_manager.decrypt_password(encrypted_password, nome_servidor)
            
            if plain_password:
                logger.debug(f"Senha obtida para servidor '{nome_servidor}'")
            
            return plain_password
            
        except Exception as e:
            logger.error(f"Erro ao obter senha para '{nome_servidor}': {str(e)}")
            return None
    
    def remover_senha(self, nome_servidor: str) -> bool:
        """
        Remove senha salva de um servidor
        
        Args:
            nome_servidor: Nome do servidor
            
        Returns:
            True se removeu com sucesso
        """
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            
            if nome_servidor not in self.config:
                logger.warning(f"Servidor '{nome_servidor}' não encontrado")
                return False
            
            if self.config.has_option(nome_servidor, 'senha_encrypted'):
                self.config.remove_option(nome_servidor, 'senha_encrypted')
                self._salvar_config()
                logger.info(f"Senha removida do servidor '{nome_servidor}'")
                return True
            else:
                logger.debug(f"Servidor '{nome_servidor}' não tinha senha salva")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao remover senha de '{nome_servidor}': {str(e)}")
            return False
    
    def servidor_tem_senha_salva(self, nome_servidor: str) -> bool:
        """
        Verifica se servidor tem senha salva
        
        Args:
            nome_servidor: Nome do servidor
            
        Returns:
            True se tem senha salva
        """
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            
            return (nome_servidor in self.config and 
                    self.config.has_option(nome_servidor, 'senha_encrypted'))
                    
        except Exception:
            return False
    
    def listar_servidores_com_senha(self) -> list:
        """
        Lista servidores que têm senha salva
        
        Returns:
            Lista com nomes dos servidores que têm senha
        """
        servidores_com_senha = []
        
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            
            for nome_servidor in self.config.sections():
                if self.config.has_option(nome_servidor, 'senha_encrypted'):
                    servidores_com_senha.append(nome_servidor)
                    
        except Exception as e:
            logger.error(f"Erro ao listar servidores com senha: {str(e)}")
        
        return servidores_com_senha
    
    def remover_servidor(self, nome: str) -> bool:
        """
        Remove servidor do arquivo INI (incluindo senha)
        
        Args:
            nome: Nome do servidor a remover
            
        Returns:
            True se removeu com sucesso
        """
        if nome not in self.config:
            logger.warning(f"Servidor '{nome}' não encontrado")
            return False
        
        try:
            self.config.remove_section(nome)
            self._salvar_config()
            logger.info(f"Servidor '{nome}' removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover servidor '{nome}': {str(e)}")
            return False
    
    def obter_servidor(self, nome: str) -> Optional[Tuple[str, str]]:
        """
        Obtém dados de um servidor específico
        
        Args:
            nome: Nome do servidor
            
        Returns:
            Tupla (ip, usuario) ou None se não encontrado
        """
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            
            if nome in self.config:
                ip = self.config[nome].get("ip", "")
                usuario = self.config[nome].get("usuario", "")
                return (ip, usuario)
                
        except Exception as e:
            logger.error(f"Erro ao obter servidor '{nome}': {str(e)}")
        
        return None
    
    def obter_servidor_completo(self, nome: str) -> Optional[Tuple[str, str, str]]:
        """
        Obtém dados completos de um servidor (incluindo senha)
        
        Args:
            nome: Nome do servidor
            
        Returns:
            Tupla (ip, usuario, senha) ou None se não encontrado
            Senha será None se não estiver salva ou crypto não estiver desbloqueado
        """
        dados_basicos = self.obter_servidor(nome)
        if not dados_basicos:
            return None
        
        ip, usuario = dados_basicos
        senha = self.obter_senha(nome)
        
        return (ip, usuario, senha)
    
    def listar_servidores(self) -> list:
        """
        Lista nomes dos servidores disponíveis
        
        Returns:
            Lista com nomes dos servidores
        """
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            return sorted(self.config.sections(), key=str.lower)
        except Exception as e:
            logger.error(f"Erro ao listar servidores: {str(e)}")
            return []
    
    def servidor_existe(self, nome: str) -> bool:
        """
        Verifica se servidor existe
        
        Args:
            nome: Nome do servidor
            
        Returns:
            True se servidor existe
        """
        try:
            self.config.read(self.ini_path, encoding='utf-8')
            return nome in self.config
        except Exception:
            return False
    
    def renomear_servidor(self, nome_atual: str, nome_novo: str) -> bool:
        """
        Renomeia um servidor (preservando senha criptografada)
        
        Args:
            nome_atual: Nome atual do servidor
            nome_novo: Novo nome do servidor
            
        Returns:
            True se renomeou com sucesso
        """
        if not self.servidor_existe(nome_atual):
            logger.error(f"Servidor '{nome_atual}' não existe")
            return False
        
        if self.servidor_existe(nome_novo):
            logger.error(f"Servidor '{nome_novo}' já existe")
            return False
        
        try:
            # Obter todos os dados do servidor atual
            dados_completos = self.obter_servidor_completo(nome_atual)
            if not dados_completos:
                return False
            
            ip, usuario, senha_descriptografada = dados_completos
            
            # Obter senha criptografada (se existir)
            senha_encrypted = None
            if self.config.has_option(nome_atual, 'senha_encrypted'):
                senha_encrypted = self.config[nome_atual]['senha_encrypted']
            
            # Criar nova seção
            self.config[nome_novo] = {
                "ip": ip, 
                "usuario": usuario
            }
            
            # Se tinha senha criptografada, re-criptografar com novo contexto
            if senha_descriptografada and self.crypto_manager.is_unlocked():
                # Re-criptografar com novo nome (para validação de contexto)
                nova_senha_encrypted = self.crypto_manager.encrypt_password(
                    senha_descriptografada, nome_novo
                )
                if nova_senha_encrypted:
                    self.config[nome_novo]['senha_encrypted'] = nova_senha_encrypted
                else:
                    logger.warning(f"Erro ao re-criptografar senha para '{nome_novo}'")
            elif senha_encrypted:
                # Se não conseguiu descriptografar mas tem senha, manter como estava
                # (usuário vai precisar reconfigurar a senha depois)
                logger.warning(f"Senha de '{nome_atual}' não pôde ser migrada para '{nome_novo}' - crypto não desbloqueado")
            
            # Remover seção antiga
            self.config.remove_section(nome_atual)
            
            self._salvar_config()
            logger.info(f"Servidor renomeado de '{nome_atual}' para '{nome_novo}'")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao renomear servidor: {str(e)}")
            return False
    
    def _salvar_config(self):
        """Salva configuração no arquivo INI"""
        try:
            with open(self.ini_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração INI: {str(e)}")
            raise
    
    def recarregar(self):
        """Recarrega configuração do arquivo"""
        try:
            self.config.clear()
            self.config.read(self.ini_path, encoding='utf-8')
            logger.debug("Configuração recarregada do arquivo INI")
        except Exception as e:
            logger.error(f"Erro ao recarregar configuração: {str(e)}")

# Instância global do gerenciador
_servidor_manager = None

def get_servidor_manager() -> ServidorManager:
    """Obtém instância singleton do gerenciador de servidores"""
    global _servidor_manager
    if _servidor_manager is None:
        _servidor_manager = ServidorManager()
    return _servidor_manager