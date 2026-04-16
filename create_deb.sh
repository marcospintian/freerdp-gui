#!/bin/bash
# Script para criar pacote .deb do FreeRDP-GUI

set -e

echo "📦 Criando pacote .deb do FreeRDP-GUI..."

# Verificar dependências
if ! command -v dpkg-deb &> /dev/null; then
    echo "❌ dpkg-deb não encontrado. Instale com: sudo apt install dpkg-dev"
    exit 1
fi

# Definir versão
VERSION="2.1.0"
ARCH="amd64"
PACKAGE_NAME="freerdp-gui"
DEB_DIR="${PACKAGE_NAME}_${VERSION}_${ARCH}"

# Limpar builds anteriores
rm -rf "$DEB_DIR" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

# Criar estrutura do pacote
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/usr/share/freerdp-gui"
mkdir -p "$DEB_DIR/usr/share/doc/freerdp-gui"

# Copiar executável
cp dist/freerdp-gui "$DEB_DIR/usr/bin/freerdp-gui"
chmod 755 "$DEB_DIR/usr/bin/freerdp-gui"

# Copiar assets
if [ -d "assets" ]; then
    cp -r assets "$DEB_DIR/usr/share/freerdp-gui/"
fi

# Criar desktop file
cat > "$DEB_DIR/usr/share/applications/freerdp-gui.desktop" << 'EOF'
[Desktop Entry]
Name=FreeRDP-GUI
Exec=freerdp-gui
Icon=freerdp-gui
Type=Application
Categories=Network;RemoteAccess;
Comment=Interface gráfica moderna para conexões RDP
Terminal=false
EOF

# Copiar ícone
if [ -f "assets/rdp-icon.png" ]; then
    cp assets/rdp-icon.png "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/freerdp-gui.png"
fi

# Criar control file
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: freerdp-gui
Version: $VERSION
Section: net
Priority: optional
Architecture: $ARCH
Depends: python3 (>= 3.8), python3-pyside6, python3-cryptography, freerdp2-x11 | freerdp, libnotify-bin
Maintainer: FreeRDP-GUI Team <freerdp-gui@example.com>
Description: Interface gráfica moderna para conexões RDP
 FreeRDP-GUI é uma interface gráfica moderna e intuitiva para conexões RDP
 usando FreeRDP. Suporta criptografia de senhas, gerenciamento de servidores
 e múltiplas opções de conexão.
 .
 Recursos:
  * Interface moderna com PySide6
  * Criptografia AES-256 para senhas
  * Suporte ao FreeRDP do Flathub
  * Instância única inteligente
  * System tray
  * Gerenciamento completo de servidores
EOF

# Criar postinst script
cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Atualizar cache de ícones
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi

# Atualizar cache de desktop
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

echo "FreeRDP-GUI instalado com sucesso!"
echo "Execute 'freerdp-gui' no terminal ou procure no menu de aplicações."
EOF

chmod 755 "$DEB_DIR/DEBIAN/postinst"

# Criar prerm script
cat > "$DEB_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

echo "Removendo FreeRDP-GUI..."
EOF

chmod 755 "$DEB_DIR/DEBIAN/prerm"

# Copiar documentação
if [ -f "README.md" ]; then
    cp README.md "$DEB_DIR/usr/share/doc/freerdp-gui/"
fi

# Calcular tamanho instalado
INSTALLED_SIZE=$(du -s "$DEB_DIR" | cut -f1)
INSTALLED_SIZE_MB=$((INSTALLED_SIZE / 1024))

# Atualizar tamanho no control
sed -i "s/^Installed-Size: .*/Installed-Size: $INSTALLED_SIZE/" "$DEB_DIR/DEBIAN/control" 2>/dev/null || true

# Construir pacote
echo "🏗️ Construindo pacote .deb..."
dpkg-deb --build "$DEB_DIR"

# Limpar
rm -rf "$DEB_DIR"

echo "✅ Pacote .deb criado: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "📏 Tamanho: $(ls -lh ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb | awk '{print $5}')"
echo ""
echo "🎯 Para instalar: sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo "   Ou: sudo apt install ./${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"