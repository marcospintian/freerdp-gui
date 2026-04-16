#!/bin/bash
# Script principal para empacotar FreeRDP-GUI

set -e

echo "📦 FreeRDP-GUI - Empacotamento para Distribuição"
echo "================================================"
echo ""

# Verificar se build existe
if [ ! -f "dist/freerdp-gui" ]; then
    echo "❌ Executável não encontrado. Execute primeiro:"
    echo "   python3 build.py"
    exit 1
fi

echo "Opções disponíveis:"
echo "1) AppImage (recomendado) - Executável independente, funciona em qualquer distro"
echo "2) .deb - Pacote Debian/Ubuntu"
echo "3) Ambos"
echo ""

read -p "Escolha uma opção (1-3): " choice

case $choice in
    1)
        echo "🚀 Gerando AppImage..."
        ./create_appimage.sh
        ;;
    2)
        echo "📦 Gerando pacote .deb..."
        ./create_deb.sh
        ;;
    3)
        echo "🚀 Gerando AppImage..."
        ./create_appimage.sh
        echo ""
        echo "📦 Gerando pacote .deb..."
        ./create_deb.sh
        ;;
    *)
        echo "❌ Opção inválida"
        exit 1
        ;;
esac

echo ""
echo "✅ Empacotamento concluído!"
echo ""
echo "📋 Resumo dos arquivos gerados:"
echo ""

if [ -f "FreeRDP-GUI-x86_64.AppImage" ]; then
    echo "📱 AppImage: FreeRDP-GUI-x86_64.AppImage ($(ls -lh FreeRDP-GUI-x86_64.AppImage | awk '{print $5}'))"
    echo "   ✅ Vantagens: Executável independente, não requer instalação"
    echo "   ✅ Funciona em: Ubuntu, Fedora, Arch, openSUSE, etc."
    echo "   🎯 Uso: ./FreeRDP-GUI-x86_64.AppImage"
    echo ""
fi

if ls freerdp-gui_*.deb &> /dev/null; then
    DEB_FILE=$(ls freerdp-gui_*.deb)
    echo "📦 .deb: $DEB_FILE ($(ls -lh "$DEB_FILE" | awk '{print $5}'))"
    echo "   ✅ Vantagens: Integração nativa com apt/dpkg"
    echo "   ✅ Funciona em: Ubuntu, Debian, Linux Mint, etc."
    echo "   🎯 Instalação: sudo apt install ./$DEB_FILE"
    echo ""
fi

echo "🎉 Pronto para distribuição!"
echo ""
echo "💡 Recomendações:"
echo "   • AppImage: Melhor para testers casuais e múltiplas distros"
echo "   • .deb: Melhor para usuários Ubuntu/Debian que preferem instalação nativa"
echo "   • Ambos: Cobrem todos os casos de uso"