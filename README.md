# FreeRDP-GUI v2.0 🚀

Interface gráfica moderna e intuitiva para conexões RDP usando FreeRDP. Agora com **sistema híbrido de criptografia de senhas** e preparado para distribuição via Flatpak, AppImage, DEB e RPM.

## ✨ Novidades da v2.0

- 🔐 **Sistema híbrido de criptografia** - Funciona com chave padrão automática ou master password personalizada
- 🏷️ **Novo nome**: FreeRDP-GUI (mais descritivo)
- 🛡️ **Master password opcional** para controle total sobre as senhas
- 💾 **Portabilidade total** - um arquivo INI com tudo
- 🔒 **Instância Única**: Prevenção de múltiplas instâncias executando simultaneamente
- 🎯 **Controle Inteligente de Conexões**: Sistema avançado de gerenciamento de conexões ativas
- 🔧 **Sistema de Limpeza Automática**: Gerenciamento seguro de threads e recursos
- 🌟 **System Tray Inteligente**: Comportamento aprimorado para minimização e restauração
- 📱 **Notificações Desktop**: Integração com sistema de notificações do Linux
- ⚡ **Conexões Rápidas**: Conectar diretamente pelo system tray com senhas salvas
- 📊 **Logging Avançado**: Sistema de logs com rotação automática e visualizador integrado
- 🔄 **Auto-salvamento**: Configurações salvas automaticamente a cada conexão
- 📈 **Histórico de Conexões**: Rastreamento das últimas conexões realizadas

## 🔧 Instalação

### Dependências do Sistema

**Ubuntu/Debian:**
```bash
sudo apt install freerdp2-x11 libnotify-bin python3-pip
```

**Fedora:**
```bash
sudo dnf install freerdp libnotify python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S freerdp libnotify python-pip
```

### Dependências Python

```bash
pip install -r requirements.txt
```

### Executar

```bash
python main.py
```

## 🔐 Sistema de Senhas

### Sistema Híbrido - Duas Opções:

#### 1. **Chave Padrão (Automática)** 🔑
- **Pronto para usar**: Funciona imediatamente, sem configuração
- **Automático**: Senhas criptografadas automaticamente com chave baseada no sistema
- **Simples**: Não precisa lembrar de senhas extras
- **Seguro**: Usa PBKDF2 + AES-256, única por instalação/usuário

#### 2. **Master Password Personalizada** 🔐
- **Controle total**: Você define uma senha mestre
- **Trancar/Destrancar**: Pode bloquear temporariamente o acesso às senhas
- **Mais seguro**: Proteção adicional com sua senha personalizada
- **Migração**: Converte automaticamente da chave padrão

### Como Funciona
1. **Primeira execução**: Sistema usa chave padrão automaticamente
2. **Opcional**: Configure master password personalizada para mais controle
3. **Criptografia local** - senhas ficam no arquivo `servidores.ini`
4. **Sem dependências** de keyring/kwallet
5. **Backup simples** - copie `servidores.ini` + arquivos de configuração

### Configuração da Master Password
1. **Menu Senhas** → **Configurar Master Password**
2. Define sua senha personalizada
3. Sistema migra automaticamente todas as senhas existentes
4. Agora você pode trancar/destrancar quando quiser

## 📱 Interface

### Abas Principais
- **Conexão**: Configure servidor, usuário e senha
- **Opções**: Resolução, som, clipboard, impressoras, etc.
- **Gerenciar Servidores**: CRUD completo de servidores

### Menu Senhas
- **Configurar Master Password**: Primeira configuração da senha personalizada
- **Alterar Master Password**: Trocar senha existente
- **Remover Master Password**: Voltar para chave padrão
- **Trancar/Destrancar**: Controle de acesso às senhas (só com master password)
- **Status do Sistema**: Ver tipo de criptografia e senhas salvas

### System Tray
- **Conexão rápida** para servidores salvos
- **Acesso aos logs**
- **Controle da janela principal**

### Indicadores Visuais
- 🔑 **Chave padrão**: Senha criptografada automaticamente
- 🔐 **Master password**: Senha protegida por master password personalizada
- 🔒 **Trancado**: Senhas temporariamente bloqueadas

## 🏗️ Estrutura do Projeto

```
freerdp-gui/
├── main.py                    # Ponto de entrada
├── core/                      # Lógica de negócio
│   ├── crypto.py             # 🆕 Sistema híbrido de criptografia
│   ├── rdp.py                # Conexões RDP
│   ├── servidores.py         # 🔄 Gerenciamento (com crypto integrado)
│   ├── settings.py           # Configurações da aplicação
│   └── utils.py              # Funções utilitárias
├── gui/                      # Interface gráfica
│   ├── main_window.py        # 🔄 Janela principal (FreeRDP-GUI)
│   ├── master_password_dialog.py # 🆕 Dialogs de master password
│   ├── gerenciador.py        # Widget de gerenciamento
│   ├── logs_window.py        # Visualização de logs
│   └── system_tray.py        # System tray
├── assets/                   # Recursos
│   └── icons/                # Ícones da aplicação
├── servidores.ini            # Configuração de servidores
└── requirements.txt          # 🔄 Dependências (+ cryptography)
```

## 📁 Arquivos de Configuração

### `servidores.ini`
```ini
[Servidor1]
ip = 192.168.1.100              # Porta 3389 automática
usuario = administrador
senha_encrypted = eyJ2ZXJzaW9uIjoxLCJkYXRhIjoi...  # 🆕 Criptografada

[Servidor2]
ip = 10.0.0.50:3389            # Porta específica
usuario = user
senha_encrypted = eyJ2ZXJzaW9uIjoxLCJkYXRhIjoi...

[ServidorEmpresa]
ip = rdp.empresa.com           # Hostname sem porta
usuario = funcionario
senha_encrypted = eyJ2ZXJzaW9uIjoxLCJkYXRhIjoi...
```

### `~/.config/freerdp-gui/`
- `.master_salt`: Salt da master password (se configurada)
- `.has_custom_password`: Marca presença de master password personalizada
- **Importante**: Faça backup da pasta completa

## 🚀 Recursos Avançados

### System Tray
- **Conexão rápida**: Clique no servidor → conecta automaticamente
- **Logs em tempo real**: Acesso rápido aos logs
- **Controles**: Mostrar/ocultar janela principal

### Opções de Conexão
- ✅ Área de transferência compartilhada
- 📁 Montar pasta home como drive
- 🔊 Redirecionamento de som (local/remoto/ambos/off)
- 🖨️ Compartilhamento de impressoras
- 🖥️ Múltiplos monitores
- 📏 Resoluções personalizadas
- 🌐 Qualidade de conexão (LAN/Broadband/Modem)

### Gerenciamento de Servidores
- ➕ Criar/editar/remover servidores
- 🔄 Renomear servidores (preserva senhas)
- 💾 Senhas criptografadas automaticamente
- 🔍 Validação de IP/hostname (porta 3389 opcional)
- 🌐 Suporte a hostnames e IPs

### Gerenciamento de Threads e Conexões
- 🧵 **Threads RDP seguras**: Cada conexão roda em thread separada
- 🔄 **Cleanup automático**: Finalização segura de todas as threads
- 📊 **Contador de conexões**: Controle de conexões ativas
- 🚪 **Saída inteligente**: Aguarda conexões terminarem antes de sair

## 🛠️ Desenvolvimento

### Testando
```bash
# Executar em modo debug
python main.py

# Ver logs em tempo real
tail -f ~/.config/rdp-connector.log
```

### Contribuindo
1. Fork o projeto
2. Crie uma branch para sua feature
3. Teste com diferentes distribuições
4. Envie um PR

## 🔧 Troubleshooting

### Erro: "xfreerdp não encontrado"
```bash
# Ubuntu/Debian
sudo apt install freerdp2-x11

# Fedora
sudo dnf install freerdp

# Arch
sudo pacman -S freerdp
```

### Problemas com Master Password
1. **Esqueceu a master password**: 
   - Menu Senhas → Remover Master Password
   - Volta para chave padrão (preserva todas as senhas)
2. **Senhas trancadas**: Menu Senhas → Destrancar Senhas
3. **Migração**: Sistema migra automaticamente ao configurar master password

### Senhas não aparecem
1. Verifique se crypto está desbloqueado (Menu → Senhas → Status do Sistema)
2. Para master password: Menu → Senhas → Destrancar Senhas
3. Check logs: Menu → Ver Logs

### Problemas de Threads/Conexões
1. **Aplicação não fecha**: Aguarde threads RDP terminarem ou force Ctrl+C
2. **Conexões ativas**: System tray mostra conexões em andamento
3. **Cleanup automático**: Aplicação finaliza threads automaticamente

## 📋 Changelog

### v2.0.0 (Nova Major Version)
- 🔐 Sistema híbrido de criptografia (chave padrão + master password opcional)
- 🏷️ Rename para FreeRDP-GUI
- 📦 Preparação para distribuição moderna
- 🛡️ Master password opcional com AES-256
- 💾 Portabilidade total dos dados
- 🎨 Interface aprimorada com indicadores de senha
- 🔧 Menu dedicado para gerenciamento de senhas
- 🧵 Gerenciamento avançado de threads RDP
- 🔒 Controle de instância única
- 📊 Sistema de logging com rotação
- 🌟 System tray inteligente com conexões rápidas
- 📱 Notificações desktop integradas
- 🌐 Porta RDP opcional (3389 padrão automático)

### v1.x (Legacy)
- Sistema baseado em keyring
- Nome: RDP Connector Pro

## 📄 Licença

GPL v3 - Veja LICENSE para detalhes.

## 🙋‍♂️ Suporte

- **Issues**: Use o GitHub Issues
- **Logs**: `~/.config/rdp-connector.log`
- **Config**: `~/.config/freerdp-gui/`

---

**FreeRDP-GUI v2.0** - *Desenvolvido com ❤️ e ☕ para simplificar conexões RDP no Linux*