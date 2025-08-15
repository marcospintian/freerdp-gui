"""
Módulo para gerenciamento de configurações da aplicação
"""

import logging
from typing import Any, Optional, Dict

try:
    from PySide6.QtCore import QSettings
except ImportError:
    QSettings = None

from .utils import SOM_MAP, RESOLUCAO_MAP, QUALIDADE_MAP

logger = logging.getLogger(__name__)

class SettingsManager:
    """Gerenciador de configurações da aplicação"""
    
    def __init__(self, organization: str = "RDPConnector", application: str = "Settings"):
        if QSettings is None:
            raise ImportError("PySide6.QtCore.QSettings não disponível")
        
        self.settings = QSettings(organization, application)
        logger.debug(f"Configurações carregadas de: {self.settings.fileName()}")
    
    def salvar_configuracao_interface(self, dados: Dict[str, Any]):
        """
        Salva configurações da interface
        
        Args:
            dados: Dicionário com dados da interface
        """
        try:
            # Configurações básicas
            if 'servidor' in dados:
                self.settings.setValue("servidor", dados['servidor'])
            
            if 'usuario' in dados:
                self.settings.setValue("usuario", dados['usuario'])
            
            # Opções de conexão
            opcoes_conexao = [
                'clipboard', 'montar_home', 'impressoras', 
                'multimonitor', 'salvar_senha'
            ]
            
            for opcao in opcoes_conexao:
                if opcao in dados:
                    self.settings.setValue(opcao, dados[opcao])
            
            # Opções com texto
            opcoes_texto = ['som', 'resolucao', 'qualidade']
            
            for opcao in opcoes_texto:
                if opcao in dados:
                    self.settings.setValue(opcao, dados[opcao])
            
            # Geometria da janela
            #if 'geometry' in dados:
            #    self.settings.setValue("geometry", dados['geometry'])
            #
            #if 'windowState' in dados:
            #    self.settings.setValue("windowState", dados['windowState'])
            
            logger.debug("Configurações da interface salvas")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {str(e)}")
    
    def carregar_configuracao_interface(self) -> Dict[str, Any]:
        """
        Carrega configurações da interface
        
        Returns:
            Dicionário com configurações
        """
        config = {}
        
        try:
            # Configurações básicas
            config['servidor'] = self.settings.value("servidor", "")
            config['usuario'] = self.settings.value("usuario", "")
            
            # Opções booleanas com valores padrão
            config['clipboard'] = self.settings.value("clipboard", True, type=bool)
            config['montar_home'] = self.settings.value("montar_home", False, type=bool)
            config['impressoras'] = self.settings.value("impressoras", False, type=bool)
            config['multimonitor'] = self.settings.value("multimonitor", False, type=bool)
            config['salvar_senha'] = self.settings.value("salvar_senha", False, type=bool)
            
            # Opções com texto
            config['som'] = self.settings.value("som", "Local (padrão)")
            config['resolucao'] = self.settings.value("resolucao", "Automática")
            config['qualidade'] = self.settings.value("qualidade", "Broadband")
            
            # Geometria da janela
            #config['geometry'] = self.settings.value("geometry")
            #config['windowState'] = self.settings.value("windowState")
            
            logger.debug("Configurações da interface carregadas")
            
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {str(e)}")
        
        return config
    
    def obter_opcoes_conexao_de_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte configurações da interface para opções de conexão RDP
        
        Args:
            config: Configurações da interface
            
        Returns:
            Dicionário com opções de conexão RDP
        """
        return {
            'clipboard': config.get('clipboard', True),
            'montar_home': config.get('montar_home', False),
            'som': SOM_MAP.get(config.get('som', 'Local (padrão)'), 'local'),
            'impressoras': config.get('impressoras', False),
            'multimonitor': config.get('multimonitor', False),
            'resolucao': RESOLUCAO_MAP.get(config.get('resolucao', 'Automática'), 'auto'),
            'qualidade': QUALIDADE_MAP.get(config.get('qualidade', 'Broadband'), 'broadband')
        }
    
    def limpar_configuracoes(self):
        """Remove todas as configurações salvas"""
        try:
            self.settings.clear()
            logger.info("Configurações limpas")
        except Exception as e:
            logger.error(f"Erro ao limpar configurações: {str(e)}")
    
    def salvar_valor(self, chave: str, valor: Any):
        """
        Salva valor individual
        
        Args:
            chave: Chave da configuração
            valor: Valor a salvar
        """
        try:
            self.settings.setValue(chave, valor)
            logger.debug(f"Valor salvo: {chave}")
        except Exception as e:
            logger.error(f"Erro ao salvar valor {chave}: {str(e)}")
    
    def obter_valor(self, chave: str, padrao: Any = None, tipo: type = None) -> Any:
        """
        Obtém valor individual
        
        Args:
            chave: Chave da configuração
            padrao: Valor padrão se não encontrado
            tipo: Tipo do valor (int, bool, str, etc.)
            
        Returns:
            Valor da configuração
        """
        try:
            if tipo is not None:
                return self.settings.value(chave, padrao, type=tipo)
            else:
                return self.settings.value(chave, padrao)
        except Exception as e:
            logger.error(f"Erro ao obter valor {chave}: {str(e)}")
            return padrao
    
    def obter_caminho_arquivo(self) -> str:
        """
        Obtém caminho do arquivo de configurações
        
        Returns:
            Caminho completo do arquivo
        """
        return self.settings.fileName()
    
    def sincronizar(self):
        """Força sincronização das configurações com o disco"""
        try:
            self.settings.sync()
            logger.debug("Configurações sincronizadas")
        except Exception as e:
            logger.error(f"Erro ao sincronizar configurações: {str(e)}")

class ConfiguracoesAplicacao:
    """Configurações específicas da aplicação"""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings = settings_manager
    
    def salvar_ultima_conexao(self, servidor: str, usuario: str):
        """Salva dados da última conexão"""
        self.settings.salvar_valor("ultima_conexao_servidor", servidor)
        self.settings.salvar_valor("ultima_conexao_usuario", usuario)
    
    def obter_ultima_conexao(self) -> tuple:
        """Obtém dados da última conexão"""
        servidor = self.settings.obter_valor("ultima_conexao_servidor", "")
        usuario = self.settings.obter_valor("ultima_conexao_usuario", "")
        return servidor, usuario
    
    def salvar_preferencias_interface(self, mostrar_system_tray: bool = True, 
                                    minimizar_para_tray: bool = True,
                                    iniciar_minimizado: bool = False):
        """Salva preferências da interface"""
        self.settings.salvar_valor("mostrar_system_tray", mostrar_system_tray)
        self.settings.salvar_valor("minimizar_para_tray", minimizar_para_tray)
        self.settings.salvar_valor("iniciar_minimizado", iniciar_minimizado)
    
    def obter_preferencias_interface(self) -> Dict[str, bool]:
        """Obtém preferências da interface"""
        return {
            'mostrar_system_tray': self.settings.obter_valor("mostrar_system_tray", True, bool),
            'minimizar_para_tray': self.settings.obter_valor("minimizar_para_tray", True, bool),
            'iniciar_minimizado': self.settings.obter_valor("iniciar_minimizado", False, bool)
        }
    
    def salvar_historico_conexoes(self, historico: list, max_itens: int = 10):
        """
        Salva histórico de conexões
        
        Args:
            historico: Lista com histórico
            max_itens: Máximo de itens no histórico
        """
        # Limitar tamanho do histórico
        if len(historico) > max_itens:
            historico = historico[:max_itens]
        
        historico_str = ';'.join(historico)
        self.settings.salvar_valor("historico_conexoes", historico_str)
    
    def obter_historico_conexoes(self) -> list:
        """Obtém histórico de conexões"""
        historico_str = self.settings.obter_valor("historico_conexoes", "")
        if historico_str and isinstance(historico_str, str):
            return historico_str.split(';')
        return []
    
    def adicionar_ao_historico(self, servidor: str, usuario: str, max_itens: int = 10):
        """Adiciona entrada ao histórico"""
        entrada = f"{servidor.replace(';', '-')}|{usuario.replace(';', '-')}"

        historico = self.obter_historico_conexoes()
        
        # Se por algum motivo não for lista, converter
        if not isinstance(historico, list):
            logger.warning("Histórico não era lista, convertendo")
            if isinstance(historico, str):
                historico = [historico] if historico else []
            else:
                historico = []

        # Remover entrada duplicada se existir
        if entrada in historico:
            historico.remove(entrada)
        
        # Adicionar no início
        historico.insert(0, entrada)
        
        # Salvar histórico atualizado
        self.salvar_historico_conexoes(historico, max_itens)

# Instância global do gerenciador de configurações
_settings_manager = None
_configuracoes_app = None

def get_settings_manager() -> SettingsManager:
    """Obtém instância singleton do gerenciador de configurações"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

def get_configuracoes_app() -> ConfiguracoesAplicacao:
    """Obtém instância das configurações da aplicação"""
    global _configuracoes_app
    if _configuracoes_app is None:
        _configuracoes_app = ConfiguracoesAplicacao(get_settings_manager())
    return _configuracoes_app