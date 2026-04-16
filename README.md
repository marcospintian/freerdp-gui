# FreeRDP-GUI v2.1.0 🚀

Interface gráfica moderna e intuitiva para conexões RDP usando FreeRDP. **Pronto para beta testing!** Suporte completo ao FreeRDP do Flathub, instância única inteligente e notificações otimizadas.

[![Status](https://img.shields.io/badge/Status-Beta%20Ready-brightgreen.svg)](https://github.com/SEU_USERNAME/freerdp-gui/releases)
[![Version](https://img.shields.io/badge/Version-2.1.0-blue.svg)](https://github.com/SEU_USERNAME/freerdp-gui)

## ✨ Novidades da v2.1

- 🏗️ **Suporte Completo ao FreeRDP do Flathub** - Detecção automática e uso prioritário do `com.freerdp.FreeRDP`
- 🔄 **Instância Única Inteligente** - Em vez de bloquear, ativa a janela já em execução
- 🔕 **Notificações Otimizadas** - Menos ruído, foco em erros importantes
- 🛠️ **Tratamento Melhorado de Desconexões** - FreeRDP 3.x não reporta mais fechamentos normais como erro
- ⚡ **Performance Aprimorada** - Menos overhead de notificações e melhor gerenciamento de instâncias

## 🔧 Instalação

### Dependências do Sistema

#### Opção 1: FreeRDP do Flathub (Recomendado) 🏆
```bash
# Instalar Flatpak (se não tiver)
sudo apt install flatpak  # Ubuntu/Debian
sudo dnf install flatpak  # Fedora
sudo pacman -S flatpak    # Arch Linux

# Adicionar Flathub
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Instalar FreeRDP do Flathub
flatpak install flathub com.freerdp.FreeRDP

# Instalar notificações (opcional)
sudo apt install libnotify-bin  # Ubuntu/Debian
```

#### Opção 2: FreeRDP do Sistema
```bash
# Ubuntu/Debian
sudo apt install freerdp3-x11 libnotify-bin

# Fedora
sudo dnf install freerdp libnotify

# Arch Linux
sudo pacman -S freerdp libnotify
```

### Dependências Python

```bash
pip install -r requirements.txt
```

### Executar

```bash
python main.py
```

## 📦 Empacotamento para Distribuição

O FreeRDP-GUI oferece opções de empacotamento para facilitar a distribuição:

### Opção 1: AppImage (Recomendado) 🏆

**Vantagens:**
- ✅ Executável independente (não requer instalação)
- ✅ Funciona em qualquer distribuição Linux
- ✅ Tamanho compacto (~70MB)
- ✅ Fácil de compartilhar

```bash
# 1. Instalar dependências de build
pip install pyinstaller

# 2. Fazer build do executável
python3 build.py

# 3. Criar AppImage
./package.sh
# Escolher opção 1 (AppImage)
```

**Resultado:** `FreeRDP-GUI-x86_64.AppImage`

### Opção 2: Pacote .deb

**Vantagens:**
- ✅ Integração nativa com Ubuntu/Debian
- ✅ Gerenciamento via apt/dpkg
- ✅ Atualizações automáticas possíveis

```bash
# Mesmo processo do AppImage, mas escolher opção 2
./package.sh
# Escolher opção 2 (.deb)
```

**Resultado:** `freerdp-gui_2.1.0_amd64.deb`

### Processo Completo

```bash
# Clonar repositório
git clone https://github.com/SEU_USERNAME/freerdp-gui.git
cd freerdp-gui

# Instalar dependências
pip install -r requirements.txt
pip install pyinstaller

# Build e empacotamento
python3 build.py
./package.sh  # Escolher formato desejado

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

## 🔧 Suporte ao FreeRDP do Flathub

O FreeRDP-GUI detecta automaticamente e prioriza o uso do FreeRDP instalado via Flathub quando disponível, oferecendo a versão mais atualizada do FreeRDP sem conflitos com o sistema.

### Instalação do FreeRDP via Flathub
```bash
# Instalar Flatpak (se não tiver)
sudo apt install flatpak  # Ubuntu/Debian
sudo dnf install flatpak  # Fedora
sudo pacman -S flatpak    # Arch Linux

# Adicionar Flathub
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Instalar FreeRDP do Flathub
flatpak install flathub com.freerdp.FreeRDP
```

### Detecção Automática
- **Prioridade**: FreeRDP do Flathub (`com.freerdp.FreeRDP`) - versão mais atual
- **Fallback**: FreeRDP do sistema (`xfreerdp3`, `xfreerdp`, `freerdp`)
- **Transparente**: Não requer configuração manual do usuário

### Benefícios
- ✅ **Versão mais recente** do FreeRDP (3.x)
- ✅ **Isolado** do sistema (não interfere em outros programas)
- ✅ **Compatibilidade** garantida com recursos mais novos
- ✅ **Tratamento correto** de desconexões normais (fechamento pelo X)
- ✅ **Atualizações** automáticas via Flathub

## 🛠️ Desenvolvimento

### Configuração do Ambiente

```bash
# Clonar repositório
git clone https://github.com/marcospintian/freerdp-gui.git
cd freerdp-gui

# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Testando

```bash
# Executar em modo debug
python main.py

# Ver logs em tempo real
tail -f ~/.config/rdp-connector.log
```

### Build e Empacotamento

```bash
# Build do executável (PyInstaller)
python3 build.py

# Criar pacotes para distribuição
./package.sh  # Menu interativo com opções

# Ou especificamente:
./create_appimage.sh  # AppImage
./create_deb.sh       # Pacote .deb
```

### Scripts Disponíveis

- `build.py` - Build com PyInstaller
- `package.sh` - Menu principal de empacotamento
- `create_appimage.sh` - Gera AppImage
- `create_deb.sh` - Gera pacote Debian
- `freerdp-gui.spec` - Configuração PyInstaller

### Testando os Pacotes

```bash
# Testar AppImage
./FreeRDP-GUI-x86_64.AppImage

# Testar .deb (Ubuntu/Debian)
sudo apt install ./freerdp-gui_2.1.0_amd64.deb
```

### Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça suas mudanças
4. Teste com diferentes distribuições
5. Teste o empacotamento: `./package.sh`
6. Envie um PR

### Estrutura de Release

Para criar uma release:

1. **Teste completo**: Execute em diferentes ambientes
2. **Build limpo**: `rm -rf build dist *.AppImage *.deb && python3 build.py`
3. **Gere pacotes**: `./package.sh` (opção 3 - ambos)
4. **Teste pacotes**: Verifique se funcionam em ambiente limpo
5. **Crie release**: Upload dos arquivos `.AppImage` e `.deb`

## 🔧 Troubleshooting

### Erro: "xfreerdp não encontrado"
```bash
# Opção 1: FreeRDP do Flathub (Recomendado)
flatpak install flathub com.freerdp.FreeRDP

# Opção 2: FreeRDP do sistema
# Ubuntu/Debian
sudo apt install freerdp3-x11

# Fedora
sudo dnf install freerdp

# Arch
sudo pacman -S freerdp
```

### Aplicação não abre uma nova janela
A partir da v2.1, o FreeRDP-GUI usa **instância única inteligente**:
- Se já estiver rodando, tentar abrir novamente **ativa a janela existente**
- Não abre múltiplas instâncias
- Verifique o system tray para a instância em execução

### Muitas notificações / Ruído excessivo
Na v2.1, as notificações foram otimizadas:
- **Removidas**: Notificações de inicialização da aplicação
- **Removidas**: Notificações de conexões bem-sucedidas
- **Mantidas**: Apenas notificações de erro crítico
- Para mais controle: Configure as notificações do sistema

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

### Desconexões reportadas como erro (FreeRDP 3.x)
Na v2.1, o tratamento de desconexões foi melhorado:
- Fechamentos normais pelo usuário (botão X) não são mais erros
- Mensagens como `ERRCONNECT_CONNECT_CANCELLED` são tratadas como desconexões normais
- Verifique os logs para confirmar se foi uma desconexão intencional

#### **Canais de Feedback**
- **Issues no GitHub**: Para bugs e sugestões
- **Logs**: `~/.config/rdp-connector.log`
- **Informações do sistema**: Menu → Ajuda → Sobre


## �📋 Changelog

### v2.1.0 (Atualização de Recursos)
- 🏗️ **Suporte Completo ao FreeRDP do Flathub** - Detecção automática e prioritária do `com.freerdp.FreeRDP`
- 🔄 **Instância Única Inteligente** - Ativação da janela existente em vez de bloqueio
- 🔕 **Notificações Otimizadas** - Redução de ruído, foco em erros críticos
- 🛠️ **Tratamento Melhorado de Desconexões** - FreeRDP 3.x não reporta fechamentos normais como erro
- ⚡ **Performance Aprimorada** - Menos overhead de notificações e melhor gerenciamento de instâncias
- 🔧 **Compatibilidade FreeRDP 3.x** - Tratamento correto de `ERRCONNECT_CONNECT_CANCELLED` e `freerdp_abort_connect_context`

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

## 🙋‍♂️ Suporte

- **Issues**: Use o GitHub Issues
- **Logs**: `~/.config/rdp-connector.log`
- **Config**: `~/.config/freerdp-gui/`

---

**FreeRDP-GUI v2.1** - *Desenvolvido com ❤️ e ☕ para simplificar conexões RDP no Linux*