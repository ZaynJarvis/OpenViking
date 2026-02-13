#!/bin/bash
set -e

# OpenViking CLI Installer
# Usage: curl -sSL https://raw.githubusercontent.com/volcengine/OpenViking/main/install.sh | bash

REPO="volcengine/OpenViking"
BINARY_NAME="openviking-cli"
INSTALL_DIR="/usr/local/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Detect platform and architecture
detect_platform() {
    case "$(uname -s)" in
        Linux*)
            OS="linux"
            ;;
        Darwin*)
            OS="macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="windows"
            ;;
        *)
            error "Unsupported operating system: $(uname -s)"
            ;;
    esac

    case "$(uname -m)" in
        x86_64|amd64)
            ARCH="x86_64"
            ;;
        arm64|aarch64)
            ARCH="aarch64"
            ;;
        *)
            error "Unsupported architecture: $(uname -m)"
            ;;
    esac

    ARTIFACT_NAME="${BINARY_NAME}-${OS}-${ARCH}"
    if [[ "$OS" == "windows" ]]; then
        ARTIFACT_NAME="${ARTIFACT_NAME}.exe"
    fi
}

# Get latest release info
get_latest_release() {
    info "Getting latest release information..."
    LATEST_RELEASE=$(curl -s "https://api.github.com/repos/${REPO}/releases/latest")
    TAG_NAME=$(echo "$LATEST_RELEASE" | grep '"tag_name"' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    
    if [[ -z "$TAG_NAME" ]]; then
        error "Could not determine latest release version"
    fi
    
    info "Latest version: $TAG_NAME"
    DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${TAG_NAME}/${ARTIFACT_NAME}"
    CHECKSUM_URL="https://github.com/${REPO}/releases/download/${TAG_NAME}/${ARTIFACT_NAME}.sha256"
}

# Download binary
download_binary() {
    info "Downloading $ARTIFACT_NAME..."
    TEMP_DIR=$(mktemp -d)
    TEMP_FILE="$TEMP_DIR/$ARTIFACT_NAME"
    CHECKSUM_FILE="$TEMP_DIR/$ARTIFACT_NAME.sha256"
    
    # Download binary
    if ! curl -sSL -o "$TEMP_FILE" "$DOWNLOAD_URL"; then
        error "Failed to download binary from $DOWNLOAD_URL"
    fi
    
    # Download checksum
    if ! curl -sSL -o "$CHECKSUM_FILE" "$CHECKSUM_URL"; then
        warn "Could not download checksum file, skipping verification"
    else
        info "Verifying checksum..."
        if command -v sha256sum >/dev/null; then
            (cd "$TEMP_DIR" && sha256sum -c "$ARTIFACT_NAME.sha256") || error "Checksum verification failed"
        elif command -v shasum >/dev/null; then
            (cd "$TEMP_DIR" && shasum -a 256 -c "$ARTIFACT_NAME.sha256") || error "Checksum verification failed"
        else
            warn "No checksum utility found, skipping verification"
        fi
    fi
    
    info "Download successful"
}

# Install binary
install_binary() {
    info "Installing to $INSTALL_DIR/$BINARY_NAME..."
    
    # Check if install directory exists and is writable
    if [[ ! -d "$INSTALL_DIR" ]]; then
        error "Install directory $INSTALL_DIR does not exist"
    fi
    
    # Try to install
    if [[ -w "$INSTALL_DIR" ]]; then
        cp "$TEMP_FILE" "$INSTALL_DIR/$BINARY_NAME"
    else
        info "Requesting sudo privileges for installation..."
        sudo cp "$TEMP_FILE" "$INSTALL_DIR/$BINARY_NAME"
        sudo chmod +x "$INSTALL_DIR/$BINARY_NAME"
    fi
    
    # Make executable
    chmod +x "$INSTALL_DIR/$BINARY_NAME" 2>/dev/null || sudo chmod +x "$INSTALL_DIR/$BINARY_NAME"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
}

# Verify installation
verify_installation() {
    info "Verifying installation..."
    if command -v "$BINARY_NAME" >/dev/null; then
        VERSION=$($BINARY_NAME --version)
        info "Successfully installed: $VERSION"
        info "Run '$BINARY_NAME --help' to get started"
    else
        error "Installation failed - $BINARY_NAME not found in PATH"
    fi
}

main() {
    info "OpenViking CLI Installer"
    detect_platform
    info "Detected platform: $OS ($ARCH)"
    get_latest_release
    download_binary
    install_binary
    verify_installation
    info "Installation complete! 🎉"
}

# Run main function
main "$@"