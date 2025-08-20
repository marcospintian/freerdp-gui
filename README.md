# FreeRDP-GUI v2.0 🚀

Interface gráfica moderna e intuitiva para conexões RDP usando FreeRDP. Agora com **criptografia local de senhas** e preparado para distribuição via Flatpak, AppImage, DEB e RPM.

## ✨ Novidades da v2.0

- 🔐 **Sistema próprio de criptografia** - Senhas seguras sem depender do keyring
- 🏷️ **Novo nome**: FreeRDP-GUI (mais descritivo)
- 📦 **Preparado para distribuição** moderna (Flatpak/AppImage/DEB/RPM)
- 🔄 **Migração automática** do keyring para criptografia local
- 🛡️ **Master password** para proteger todas as senhas
- 💾 **Portabilidade total** - um arquivo INI com tudo

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

### Master Password
- **Primeira execução**: Configure uma master password para proteger suas senhas RDP
- **Segurança**: Usa PBKDF2 com 100.000 iterações + AES-256
- **Portabilidade**: Funciona em qualquer distribuição Linux

### Como Funciona
1. **Master password** protege todas as senhas RDP
2. **Criptografia local** - senhas ficam no arquivo `servidores.ini`
3. **Sem dependências** de keyring/kwallet
4. **Backup simples** - copie `servidores.ini` + `.master_salt`

### Migração do Keyring
Se você usava a versão anterior com keyring:

```bash
python migrate_to_crypto.py
```

## 📱 Interface

### Abas Principais
- **Conexão**: Configure servidor, usuário e senha
- **Opções**: Resolução, som, clipboard, impressoras, etc.
- **Gerenciar Servidores**: CRUD completo de servidores

### Menu Senhas
- **Configurar Master Password**: Primeira configuração
- **Alterar Master Password**: Trocar senha existente
- **Trancar/Destrancar**: Controle de acesso às senhas
- **Status das Senhas**: Ver quais servidores têm senha salva

### System Tray
- **Conexão rápida** para servidores salvos
- **Acesso aos logs**
- **Controle da janela principal**

## 🏗️ Estrutura do Projeto

```
freerdp-gui/
├── main.py                    # Ponto de entrada
├── core/                      # Lógica de negócio
│   ├── crypto.py             # 🆕 Sistema de criptografia
│   ├── rdp.py                # Conexões RDP
│   ├── servidores.py         # 🔄 Gerenciamento (com crypto)
│   ├── settings.py           # Configurações da aplicação
│   └── utils.py              # Funções utilitárias
├── gui/                      # Interface gráfica
│   ├── main_window.py        # 🔄 Janela principal (FreeRDP-GUI)
│   ├── master_password_dialog.py # 🆕 Dialogs de master password
│   ├── gerenciador.py        # Widget de gerenciamento
│   ├── senha_dialog.py       # Dialogs de senha
│   ├── logs_window.py        # Visualização de logs
│   └── system_tray.py        # System tray
├── assets/                   # Recursos
│   └── icons/                # Ícones da aplicação
├── migrate_to_crypto.py      # 🆕 Script de migração
├── servidores.ini            # Configuração de servidores
└── requirements.txt          # 🔄 Dependências (+ cryptography)
```

## 📁 Arquivos de Configuração

### `servidores.ini`
```ini
[Servidor1]
ip = 192.168.1.100:3389
usuario = administrador
senha_encrypted = eyJ2ZXJzaW9uIjoxLCJkYXRhIjoi...  # 🆕 Criptografada

[Servidor2]
ip = 10.0.0.50:3389
usuario = user
senha_encrypted = eyJ2ZXJzaW9uIjoxLCJkYXRhIjoi...
```

### `.master_salt` (oculto)
- Salt da master password
- **Importante**: Faça backup junto com `servidores.ini`

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
- 🔍 Validação de IP:porta

## 🛠️ Desenvolvimento

### Testando
```bash
# Executar em modo debug
python main.py

# Ver logs em tempo real
tail -f ~/.config/freerdp-gui.log
```

### Contribuindo
1. Fork o projeto
2. Crie uma branch para sua feature
3. Teste com diferentes distribuições
4. Envie um PR

## 📦 Distribuição

O projeto está preparado para distribuição moderna:

- **Flatpak**: Sandbox seguro
- **AppImage**: Portabilidade máxima  
- **DEB/RPM**: Instalação tradicional

### Building
```bash
# Em breve - scripts de build automático
./packaging/build_all.sh
```

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

### Erro: "Master password incorreta"
1. Verifique se digitou corretamente
2. Se esqueceu: delete `.master_salt` (⚠️ perde todas as senhas)
3. Use `migrate_to_crypto.py` para reconfigurar

### Senhas não aparecem
1. Verifique se crypto está desbloqueado (Menu → Senhas → Status)
2. Configure master password se for primeira vez
3. Check logs: Menu → Ver Logs

## 📋 Changelog

### v2.0.0 (Nova Major Version)
- 🔐 Sistema próprio de criptografia de senhas
- 🏷️ Rename para FreeRDP-GUI
- 📦 Preparação para distribuição moderna
- 🔄 Migração automática do keyring
- 🛡️ Master password com AES-256
- 💾 Portabilidade total dos dados
- 🎨 Interface aprimorada com indicadores de senha
- 🔧 Menu dedicado para gerenciamento de senhas

### v1.x (Legacy)
- Sistema baseado em keyring
- Nome: RDP Connector Pro

## 📄 Licença

GPL v3 - Veja LICENSE para detalhes.

## 🙋‍♂️ Suporte

- **Issues**: Use o GitHub Issues
- **Logs**: `~/.config/freerdp-gui.log`
- **Config**: `~/.config/freerdp-gui/`

---

**FreeRDP-GUI v2.0** - Interface moderna para conexões RDP seguras 🛡️