# freerdp-gui
# RDP Connector Pro - Modular

Uma aplicação gráfica em Python para gerenciar e conectar via RDP de forma simples e eficiente.

## Estrutura do Projeto

```
rdp_connector/
│
├── main.py                    # Ponto de entrada da aplicação
├── core/                      # Lógica de negócio
│   ├── rdp.py                 # Conexões RDP (RDPThread, RDPConnector)
│   ├── servidores.py          # Gerenciamento de servidores (INI)
│   ├── settings.py            # Configurações da aplicação (QSettings)
│   └── utils.py               # Funções utilitárias
│
├── gui/                       # Interface gráfica
│   ├── main_window.py         # Janela principal
│   ├── gerenciador.py         # Widget de gerenciamento de servidores
│   ├── senha_dialog.py        # Dialog de gerenciamento de senhas
│   ├── logs_window.py         # Janela de visualização de logs
│   └── system_tray.py         # Gerenciador do system tray
│
├── assets/                    # Recursos da aplicação
│   └── rdp-icon.png           # Ícone da aplicação (opcional)
│
├── servidores.ini             # Arquivo de configuração dos servidores
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

## Características

### Funcionalidades Principais

- **Interface gráfica moderna** com abas organizadas
- **Gerenciamento de servidores** via arquivo INI
- **Armazenamento seguro de senhas** usando keyring do sistema
- **System tray** com conexões rápidas
- **Logs detalhados** com visualizador integrado
- **Configurações persistentes** 
- **Conexões RDP avançadas** com múltiplas opções

### Arquitetura Modular

- **Separação de responsabilidades** entre módulos
- **Core isolado** da interface gráfica
- **Fácil manutenção** e extensão
- **Testes unitários** facilitados
- **Reutilização de código** entre componentes

## Instalação

### Pré-requisitos

- Python 3.8+
- xfreerdp (Linux) - para conexões RDP
- Sistema com keyring suportado

### Dependências Python

```bash
pip install -r requirements.txt
```

### Instalação do xfreerdp (Linux)

```bash
# Ubuntu/Debian
sudo apt install freerdp2-x11

# Fedora
sudo dnf install freerdp

# Arch Linux  
sudo pacman -S freerdp
```

## Uso

### Executar aplicação

```bash
python main.py
```

### Configuração inicial

1. A aplicação criará automaticamente um arquivo `servidores.ini` com exemplos
2. Use a aba "Gerenciar Servidores" para adicionar seus servidores
3. Configure as opções de conexão na aba "Opções"

### Conexão rápida via System Tray

- Clique direito no ícone da bandeja
- Selecione "Conectar a [Servidor]"
- A conexão será iniciada automaticamente se a senha estiver salva

## Módulos

### Core (`core/`)

#### `utils.py`
- Funções utilitárias compartilhadas
- Configuração de logging
- Validações e helpers

#### `servidores.py`
- Classe `ServidorManager` para gerenciar arquivo INI
- CRUD completo de servidores
- Validação de dados

#### `rdp.py`  
- Classe `RDPThread` para conexões assíncronas
- Classe `RDPConnector` para conexões síncronas
- Construção de comandos xfreerdp com opções avançadas

#### `settings.py`
- Classe `SettingsManager` usando QSettings
- Persistência de configurações da interface
- Histórico de conexões

### GUI (`gui/`)

#### `main_window.py`
- Janela principal da aplicação
- Coordenação entre componentes
- Gerenciamento de estado da aplicação

#### `gerenciador.py`
- Widget para gerenciar servidores
- Interface CRUD completa
- Integração com keyring

#### `senha_dialog.py`
- Dialog para gerenciar senhas no keyring
- Entrada segura de senhas
- Validações de entrada

#### `logs_window.py`
- Visualizador de logs em tempo real
- Filtros e exportação
- Auto-atualização

#### `system_tray.py`
- Gerenciamento do ícone da bandeja
- Menu contextual dinâmico
- Notificações do sistema

## Configuração

### Arquivo `servidores.ini`

```ini
[Servidor1]
ip = 192.168.1.100:3389
usuario = administrador

[Servidor2]  
ip = 10.0.0.50:3389
usuario = user
```

### Opções de Conexão RDP

- **Área de transferência**: Compartilhamento entre sistemas
- **Drives locais**: Montar pasta home como drive
- **Som**: Local, remoto, ambos ou desabilitado
- **Impressoras**: Compartilhar impressoras locais
- **Multi-monitor**: Usar múltiplos monitores
- **Resolução**: Automática ou personalizada
- **Qualidade**: LAN, Broadband ou Modem

## Logging

Os logs são armazenados em `~/.config/rdp-connector.log` com rotação automática:

- Tamanho máximo: 5MB por arquivo
- Backup: 3 arquivos
- Formato: timestamp, nível, mensagem

## Segurança

- **Senhas não são armazenadas** em texto plano
- **Keyring do sistema** usado para credenciais
- **Logs não contêm** senhas ou dados sensíveis
- **Validação de entrada** em todos os campos

## Desenvolvimento

### Estrutura para novos recursos

1. **Lógica de negócio**: adicionar em `core/`
2. **Interface**: adicionar em `gui/`
3. **Testes**: criar arquivos de teste paralelos
4. **Documentação**: atualizar README e docstrings

### Padrões de código

- **Type hints** em todas as funções
- **Docstrings** detalhadas
- **Logging** adequado em todos os módulos
- **Tratamento de exceções** robusto
- **Separação clara** entre GUI e lógica

### Testes

```bash
# Exemplo de estrutura para testes futuros
tests/
├── test_core/
│   ├── test_servidores.py
│   ├── test_rdp.py
│   └── test_utils.py
└── test_gui/
    ├── test_main_window.py
    └── test_gerenciador.py
```

## Contribuição

1. Fork do projeto
2. Criar branch para feature (`git checkout -b feature/nova-feature`)
3. Commit das mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Criar Pull Request

## Licença

Este projeto está sob licença MIT. Veja arquivo `LICENSE` para detalhes.

## Problemas Conhecidos

- System tray pode não funcionar em alguns ambientes Linux
- xfreerdp requer configurações específicas em alguns sistemas
- Keyring pode precisar de configuração manual em headless systems

## Roadmap

- [ ] Interface web opcional
- [ ] Suporte a múltiplos protocolos (VNC, SSH)
- [ ] Temas personalizáveis
- [ ] Plugins de extensão
- [ ] Sincronização de configurações
- [ ] Túneis SSH automáticos