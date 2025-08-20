#!/usr/bin/env python3
"""
Script de migração para FreeRDP-GUI v2.0
Migra senhas do keyring para o novo sistema de criptografia
"""

import sys
import logging
from pathlib import Path

# Adicionar diretório do projeto
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils import setup_logging
from core.servidores import get_servidor_manager
from core.crypto import get_crypto_manager
from gui.master_password_dialog import solicitar_master_password

def main():
    """Função principal de migração"""
    print("=" * 60)
    print("FreeRDP-GUI v2.0 - Script de Migração")
    print("=" * 60)
    print()
    
    # Configurar logging
    logger = setup_logging()
    
    try:
        import keyring
    except ImportError:
        print("❌ Keyring não está disponível. Nada para migrar.")
        return 0
    
    # Inicializar managers
    servidor_manager = get_servidor_manager()
    crypto_manager = get_crypto_manager()
    
    # Verificar se há senhas no keyring para migrar
    servidores = servidor_manager.carregar_servidores()
    senhas_encontradas = []
    
    print("🔍 Procurando senhas no keyring...")
    
    for nome_servidor, (ip, usuario) in servidores.items():
        if nome_servidor == "Manual":
            continue
        
        try:
            senha = keyring.get_password(nome_servidor, usuario)
            if senha:
                senhas_encontradas.append((nome_servidor, usuario, senha))
        except Exception as e:
            print(f"⚠️  Erro ao verificar {nome_servidor}: {e}")
    
    if not senhas_encontradas:
        print("✅ Nenhuma senha encontrada no keyring. Migração não necessária.")
        return 0
    
    print(f"📦 Encontradas {len(senhas_encontradas)} senhas para migrar:")
    for nome, usuario, _ in senhas_encontradas:
        print(f"   • {nome} ({usuario})")
    
    print()
    resposta = input("Deseja continuar com a migração? (s/N): ").lower().strip()
    if resposta != 's':
        print("❌ Migração cancelada.")
        return 0
    
    # Solicitar master password
    print("\n🔐 Configurando master password para o novo sistema...")
    
    # Tentar usar interface gráfica se disponível
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        senha_master = solicitar_master_password(None, is_first_time=True)
        if not senha_master:
            print("❌ Master password é obrigatória para migração.")
            return 1
    except:
        # Fallback para interface de linha de comando
        import getpass
        while True:
            senha_master = getpass.getpass("Digite a nova master password: ")
            if not senha_master:
                print("❌ Senha não pode estar vazia.")
                continue
            
            confirma = getpass.getpass("Confirme a master password: ")
            if senha_master != confirma:
                print("❌ Senhas não conferem.")
                continue
            
            if len(senha_master) < 8:
                resposta = input("⚠️  Senha tem menos de 8 caracteres. Continuar? (s/N): ")
                if resposta.lower().strip() != 's':
                    continue
            
            break
        
        # Configurar master password
        if not crypto_manager.set_master_password(senha_master):
            print("❌ Erro ao configurar master password.")
            return 1
    
    print("✅ Master password configurada com sucesso.")
    
    # Migrar senhas
    print("\n📦 Migrando senhas...")
    migradas = 0
    erros = 0
    
    for nome_servidor, usuario, senha in senhas_encontradas:
        try:
            print(f"   Migrando {nome_servidor}...", end=" ")
            
            # Salvar no novo sistema
            if servidor_manager.salvar_senha(nome_servidor, senha):
                # Remover do keyring
                try:
                    keyring.delete_password(nome_servidor, usuario)
                    print("✅")
                    migradas += 1
                except Exception as e:
                    print(f"⚠️  (salva mas erro ao remover do keyring: {e})")
                    migradas += 1
            else:
                print("❌")
                erros += 1
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            erros += 1
    
    print()
    print("=" * 60)
    print("RESULTADO DA MIGRAÇÃO")
    print("=" * 60)
    print(f"✅ Senhas migradas com sucesso: {migradas}")
    if erros > 0:
        print(f"❌ Erros: {erros}")
    print()
    
    if migradas > 0:
        print("🎉 Migração concluída com sucesso!")
        print("   • Suas senhas agora estão criptografadas localmente")
        print("   • Não dependem mais do keyring do sistema")
        print("   • São portáveis entre diferentes distribuições")
        print()
        print("💡 Dicas:")
        print("   • Faça backup do arquivo 'servidores.ini'")
        print("   • Lembre-se da master password")
        print("   • O arquivo '.master_salt' também é importante")
        
        # Verificar se migração foi bem sucedida
        print("\n🔍 Verificando migração...")
        verificacao_ok = True
        
        for nome_servidor, usuario, senha_original in senhas_encontradas:
            senha_recuperada = servidor_manager.obter_senha(nome_servidor)
            if senha_recuperada != senha_original:
                print(f"❌ Erro na verificação de {nome_servidor}")
                verificacao_ok = False
        
        if verificacao_ok:
            print("✅ Verificação concluída - todas as senhas foram migradas corretamente!")
        else:
            print("⚠️  Algumas senhas podem não ter sido migradas corretamente.")
    else:
        print("❌ Nenhuma senha foi migrada.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Migração interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)