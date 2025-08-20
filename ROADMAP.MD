## 🔒 Segurança de Senhas (Implementado na v2.0)

- As senhas agora são armazenadas de forma criptografada (AES-256) diretamente no arquivo servidores.ini.
- Não há mais dependência de keyring, facilitando portabilidade e manutenção.
- O campo de senha nunca é salvo em texto claro.

# 🗺️ ROADMAP - RDP Connector Pro

## 📋 Visão Geral

Este roadmap define as próximas funcionalidades e melhorias planejadas para o RDP Connector Pro, organizadas por prioridade e complexidade.

---

## 🚀 Versão 2.1.0 - Melhorias de Usabilidade (Q4 2025)

### 🚀 Empacotamento e Distribuição

#### 📦 Sistema de Empacotamento Multiplataforma
- **Descrição**: Simplificar distribuição com pacotes nativos
- **Formatos de Destino**:
  - **AppImage** (Universal Linux) - 🎯
  - **Flatpak** (Linux moderno) - 🎯 

#### 🤖 Pipeline de Build Automático
- **Descrição**: CI/CD para builds automatizados
- **Implementação**:
  - GitHub Actions para multiple targets
  - Build matrix para diferentes distribuições
  - Releases automáticos com changelogs
  - Testes automatizados antes do empacotamento
  - Assinatura digital dos pacotes

#### 📋 Ferramentas de Empacotamento
- **AppImage**: PyInstaller + AppImageKit
- **Flatpak**: Flatpak Builder + runtime Python
- **Auto-updater**: Implementar verificação de versão

#### ✅ Separação de IP e Porta
- **Descrição**: Campos separados para IP e porta na interface
- **Benefício**: Interface mais intuitiva e validação individual
- **Implementação**: 
  - Modificar `gerenciador.py` com campos separados
  - Atualizar validação em `utils.py`
  - Manter compatibilidade com formato atual `ip:porta`
  - Usar porta padrão 3389 quando não especificada

#### 🔧 Configurações Avançadas de Conexão
- **Descrição**: Mais opções de personalização do xfreerdp
- **Funcionalidades**:
  - Timeout de conexão configurável
  - Opções de certificado (strict/ignore/warn)
  - Configuração de codecs de áudio/vídeo
  - Redirecionamento de USB devices

#### 🔍 Sistema de Busca e Filtros
- **Descrição**: Localizar servidores rapidamente
- **Funcionalidades**:
  - Busca por nome, IP ou usuário
  - Filtros por tags/categorias
  - Ordenação customizada
  - Favoritos com acesso rápido

---

## 🚀 Versão 2.2.0 - Recursos Avançados (Q1 2026)

#### 📁 Grupos e Categorização
- **Descrição**: Organizar servidores em grupos/pastas
- **Funcionalidades**:
  - Criação de grupos/pastas
  - Arrastar e soltar servidores
  - Menu do system tray hierárquico
  - Cores/ícones por grupo

#### 📂 Import/Export de Configurações
- **Descrição**: Portabilidade de configurações
- **Formatos**:
  - JSON para backup completo
  - CSV para lista de servidores
  - RDP files do Windows (import)
  - Sync com cloud storage (opcional)

#### 🔐 Gerenciador de Sessões
- **Descrição**: Controle avançado de sessões RDP
- **Funcionalidades**:
  - Lista de sessões ativas
  - Log de sessões com duração
  - Alertas de sessões longas

#### 🌐 Monitoramento de Conectividade
- **Descrição**: Verificar status dos servidores
- **Funcionalidades**:
  - Ping automático dos servidores
  - Indicadores de status (online/offline)
  - Notificações de mudança de status
  - Health check agendado

## 🚀 Versão 2.3.0 - Automação e Integração (Q2 2026)

#### ⚡ Scripts Pré/Pós Conexão
- **Descrição**: Automação de tarefas na conexão
- **Funcionalidades**:
  - Scripts Python ou shell executáveis
  - Hooks para pré-conexão e pós-desconexão
  - Variáveis de ambiente disponíveis
  - Logs de execução de scripts

#### 🔗 Integração com Ferramentas Externas
- **Descrição**: Conectividade com outras ferramentas
- **Integrações**:
  - SSH tunneling automático
  - VPN connection checks
  - Integração com password managers externos

#### 📡 Sincronização Multi-dispositivo
- **Descrição**: Sync de configurações entre máquinas
- **Funcionalidades**:
  - Sync via cloud storage (Google Drive, Dropbox)
  - Sync via repositório Git
  - Resolução de conflitos automática
  - Backup incremental

#### 🔒 Políticas de Segurança
- **Descrição**: Controles de segurança avançados
- **Funcionalidades**:
  - Timeout de sessão automático
  - Rotação de senhas programada
  - Audit log de todas as ações
  - Bloqueio após tentativas falhas

---

## 🚀 Versão 3.0.0 - Multiplataforma e Enterprise (Q3 2026)

#### 🖥️ Suporte Multiplataforma
- **Descrição**: Expandir para Windows e macOS
- **Implementação**:
  - Adaptação para mstsc no Windows
  - Suporte para Microsoft Remote Desktop no macOS
  - Instaladores nativos para cada plataforma
  - CI/CD para builds multiplataforma

#### 🏢 Recursos Enterprise
- **Descrição**: Funcionalidades para empresas
- **Funcionalidades**:
  - Gerenciamento centralizado de configurações
  - Políticas de grupo
  - Active Directory integration
  - Multi-tenant support

#### 🗄️ Database Backend
- **Descrição**: Migração para banco de dados
- **Benefícios**:
  - Performance melhorada para muitos servidores
  - Histórico detalhado de conexões
  - Backup e recovery robustos
  - Suporte a SQLite, PostgreSQL, MySQL

---

## 🔍 Versão 3.1.0+ - Inovação e IA (2027+)

### 🤖 Funcionalidades Futuras

#### 🧠 AI-Powered Features
- **Descrição**: Inteligência artificial integrada
- **Funcionalidades**:
  - Detecção automática de servidores na rede
  - Otimização inteligente de configurações
  - Predição de problemas de conectividade
  - Assistente virtual para troubleshooting

#### 🔮 Análise Preditiva
- **Descrição**: Machine learning para insights
- **Funcionalidades**:
  - Predição de falhas de servidor
  - Otimização automática de performance
  - Detecção de anomalias de segurança
  - Recomendações personalizadas

## 📊 Priorização de Desenvolvimento

### 🎯 Critérios de Priorização

1. **Impacto no usuário** (Alto/Médio/Baixo)
2. **Complexidade técnica** (Simples/Moderada/Complexa)
3. **Recursos necessários** (Horas estimadas)
4. **Dependências** (Internas/Externas)
5. **Feedback da comunidade** (Demanda)

### 📈 Métricas de Sucesso

- **Adoção**: Número de usuários ativos
- **Satisfação**: Ratings e feedback
- **Estabilidade**: Crash reports e bugs
- **Performance**: Tempo de inicialização e responsividade
- **Segurança**: Vulnerabilidades reportadas

---

## 🤝 Como Contribuir

### 💡 Sugestões de Funcionalidades
- Abra uma **Issue** com label `enhancement`
- Descreva o caso de uso detalhadamente
- Inclua mockups ou exemplos se possível

### 🐛 Reporte de Bugs
- Use template específico de bug report
- Inclua logs e informações do sistema
- Passos detalhados para reproduzir

### 💻 Contribuições de Código
- Verifique roadmap atual antes de começar
- Discuta grandes mudanças em Issues primeiro
- Siga guia de contribuição do projeto

---

## 📅 Timeline Estimado

| Versão | Período | Funcionalidades Chave | 
|--------|---------|------------------------|
| 2.0.1 | **SET 2025** | 📦 **AppImage** | 
| 2.0.2 | **OUT 2025** | 📦 **Flatpak** | 
| 2.1.0 | **NOV 2025** | Separação IP/Porta |
| 2.2.0 | Q1 2026 | Grupos, Profiles | 
| 2.3.0 | Q2 2026 | Scripts, Sync | 
| 3.0.0 | Q3 2026 | Multiplataforma | 

### 🎯 **ROADMAP DE EMPACOTAMENTO DETALHADO**

#### **Fase 1: Release Imediato** (Setembro 2025)
- [ ] **AppImage** - Máxima compatibilidade Linux
- [ ] **Auto-updater básico** - Notificação de versões
- [ ] **Instalador shell script** - Setup automatizado

#### **Fase 2: Stores Oficiais** (Outubro 2025)  
- [ ] **Flatpak** - Flathub submission
- [ ] **Documentação** - Guias de instalação

---

*Este roadmap é um documento vivo e será atualizado conforme evolução do projeto e feedback da comunidade.*