#!/bin/bash
# Install Node.js locally for yt-dlp
NODE_VERSION="v18.19.1"
DISTRO="linux-x64"
URL="https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-${DISTRO}.tar.xz"
INSTALL_DIR="$(pwd)/bin/node"

echo "📥 Downloading Node.js ${NODE_VERSION}..."
mkdir -p "$INSTALL_DIR"
curl -L "$URL" | tar -xJ -C "$INSTALL_DIR" --strip-components=1

echo "✅ Node.js installed to $INSTALL_DIR"
echo "👉 Path: $INSTALL_DIR/bin/node"
"$INSTALL_DIR/bin/node" -v
