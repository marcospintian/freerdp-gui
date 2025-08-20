"""
Módulo para gerenciamento de servidores via arquivo INI
"""

import logging
import configparser
from typing import Dict, Tuple, Optional
from pathlib import Path

from .utils import get_ini_path, validar_ip_porta

logger = logging.getLogger(__name__)

class ServidorManager:
    """Gerenciador de servidores"""
    
    def __init__(self):
        self.ini_path = get_ini_path()
        self.config = configparser.ConfigParser()
        self._criar_arquivo_exemplo_se_necessario()
    
    def _criar_arquivo_exemplo_se_necessario(self):
        """Cria arquivo INI de exemplo se não existir"""
        if not self.ini_path.exists():
            self.config['Servidor1'] = {
                'ip': '192.168.1.100:3389',
                'usuario': 'administrador'
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
    
    def salvar_servidor(self, nome: str, ip: str, usuario: str) -> bool:
        """
        Salva servidor no arquivo INI
        
        Args:
            nome: Nome do servidor
            ip: Endereço IP:porta
            usuario: Nome do usuário
            
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
            # Preserva senha criptografada, se existir
            senha = self.config[nome].get('senha') if nome in self.config else None
            self.config[nome] = {"ip": ip, "usuario": usuario}
            if senha:
                self.config[nome]['senha'] = senha
            self._salvar_config()
            logger.info(f"Servidor '{nome}' salvo com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar servidor '{nome}': {str(e)}")
            return False
    
    def remover_servidor(self, nome: str) -> bool:
        """
        Remove servidor do arquivo INI
        
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
        Renomeia um servidor
        
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
            # Obter dados do servidor atual
            dados = self.obter_servidor(nome_atual)
            if not dados:
                return False
            ip, usuario = dados
            # Preservar senha criptografada, se existir
            senha = self.config[nome_atual].get('senha') if nome_atual in self.config else None
            # Criar nova seção
            self.config[nome_novo] = {"ip": ip, "usuario": usuario}
            if senha:
                self.config[nome_novo]['senha'] = senha
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
        with open(self.ini_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
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