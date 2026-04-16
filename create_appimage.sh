#!/bin/bash
# Script para criar AppImage do FreeRDP-GUI

set -e

echo "🚀 Criando AppImage do FreeRDP-GUI..."

# Verificar se appimagetool está instalado
if command -v appimagetool &> /dev/null; then
    APPIMAGETOOL="appimagetool"
elif [ -f "./appimagetool" ]; then
    APPIMAGETOOL="./appimagetool"
else
    echo "❌ appimagetool não encontrado. Instale com:"
    echo "   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "   chmod +x appimagetool-x86_64.AppImage"
    echo "   sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool"
    exit 1
fi

# Criar estrutura do AppDir
APPDIR="FreeRDP-GUI.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR"

# Copiar executável
cp dist/freerdp-gui "$APPDIR/FreeRDP-GUI"

# Criar estrutura básica do AppImage
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copiar executável para usr/bin
cp dist/freerdp-gui "$APPDIR/usr/bin/freerdp-gui"

# Criar desktop file
cat > "$APPDIR/freerdp-gui.desktop" << 'EOF'
[Desktop Entry]
Name=FreeRDP-GUI
Exec=FreeRDP-GUI
Icon=freerdp-gui
Type=Application
Categories=Network;RemoteAccess;
Comment=Interface gráfica moderna para conexões RDP
Terminal=false
EOF

# Copiar desktop file
cp "$APPDIR/freerdp-gui.desktop" "$APPDIR/usr/share/applications/"

# Copiar ícone (se existir)
if [ -f "assets/rdp-icon.png" ]; then
    cp assets/rdp-icon.png "$APPDIR/freerdp-gui.png"
    cp assets/rdp-icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/freerdp-gui.png"
fi

# Criar AppRun
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="$HERE/usr/bin:$PATH"
export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"
exec "$HERE/usr/bin/freerdp-gui" "$@"
EOF

chmod +x "$APPDIR/AppRun"

# Criar AppImage
echo "📦 Gerando AppImage..."
$APPIMAGETOOL "$APPDIR" "FreeRDP-GUI-x86_64.AppImage"

# Limpar
rm -rf "$APPDIR"

echo "✅ AppImage criado: FreeRDP-GUI-x86_64.AppImage"
echo "📏 Tamanho: $(ls -lh FreeRDP-GUI-x86_64.AppImage | awk '{print $5}')"
echo ""
echo "🎯 Para testar: ./FreeRDP-GUI-x86_64.AppImage"