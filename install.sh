#!/bin/bash
#
# thenvoi-cli installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/bacedia/thenvoi-cli/main/install.sh | bash
#
# Options (via environment variables):
#   THENVOI_VERSION   - Version to install (default: latest)
#   THENVOI_INSTALL_DIR - Installation directory (default: /usr/local/bin or ~/.local/bin)
#   THENVOI_NO_MODIFY_PATH - Don't modify shell profile
#

set -e

# Colors (disabled if NO_COLOR is set)
if [ -z "$NO_COLOR" ] && [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

info() {
    echo -e "${BLUE}==>${NC} $1"
}

success() {
    echo -e "${GREEN}==>${NC} $1"
}

warn() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

error() {
    echo -e "${RED}Error:${NC} $1" >&2
}

# Detect architecture
detect_arch() {
    local arch=$(uname -m)
    case "$arch" in
        x86_64|amd64)
            echo "x86_64"
            ;;
        aarch64|arm64)
            echo "aarch64"
            ;;
        *)
            error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

# Detect OS
detect_os() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    case "$os" in
        linux)
            echo "linux"
            ;;
        darwin)
            echo "darwin"
            ;;
        *)
            error "Unsupported OS: $os"
            exit 1
            ;;
    esac
}

# Check if command exists
has_command() {
    command -v "$1" &> /dev/null
}

# Get latest version from GitHub
get_latest_version() {
    if has_command curl; then
        curl -fsSL "https://api.github.com/repos/bacedia/thenvoi-cli/releases/latest" | \
            grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/'
    elif has_command wget; then
        wget -qO- "https://api.github.com/repos/bacedia/thenvoi-cli/releases/latest" | \
            grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/'
    else
        error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
}

# Download file
download() {
    local url="$1"
    local dest="$2"

    info "Downloading from $url"

    if has_command curl; then
        curl -fsSL "$url" -o "$dest"
    elif has_command wget; then
        wget -q "$url" -O "$dest"
    else
        error "Neither curl nor wget found."
        exit 1
    fi
}

# Add to PATH in shell profile
add_to_path() {
    local dir="$1"
    local profile=""

    # Detect shell and profile
    if [ -n "$BASH_VERSION" ]; then
        if [ -f "$HOME/.bashrc" ]; then
            profile="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            profile="$HOME/.bash_profile"
        fi
    elif [ -n "$ZSH_VERSION" ]; then
        profile="$HOME/.zshrc"
    fi

    if [ -z "$profile" ]; then
        # Try common profiles
        if [ -f "$HOME/.bashrc" ]; then
            profile="$HOME/.bashrc"
        elif [ -f "$HOME/.zshrc" ]; then
            profile="$HOME/.zshrc"
        elif [ -f "$HOME/.profile" ]; then
            profile="$HOME/.profile"
        fi
    fi

    if [ -n "$profile" ]; then
        # Check if already in PATH config
        if ! grep -q "thenvoi-cli" "$profile" 2>/dev/null; then
            echo "" >> "$profile"
            echo "# Added by thenvoi-cli installer" >> "$profile"
            echo "export PATH=\"$dir:\$PATH\"" >> "$profile"
            info "Added $dir to PATH in $profile"
            info "Run 'source $profile' or restart your shell"
        fi
    fi
}

# Main installation
main() {
    echo ""
    echo "  thenvoi-cli installer"
    echo ""

    local version="${THENVOI_VERSION:-latest}"
    local os=$(detect_os)
    local arch=$(detect_arch)
    local install_dir="${THENVOI_INSTALL_DIR:-}"

    # Determine install directory
    if [ -z "$install_dir" ]; then
        if [ -w "/usr/local/bin" ]; then
            install_dir="/usr/local/bin"
        else
            install_dir="$HOME/.local/bin"
            mkdir -p "$install_dir"
        fi
    fi

    info "OS: $os, Arch: $arch"
    info "Install directory: $install_dir"

    # Get version
    if [ "$version" = "latest" ]; then
        info "Fetching latest version..."
        version=$(get_latest_version)
        if [ -z "$version" ]; then
            error "Could not determine latest version"
            exit 1
        fi
    fi

    info "Version: $version"

    # Build download URL
    local binary_name="thenvoi-cli-${os}-${arch}"
    local download_url="https://github.com/bacedia/thenvoi-cli/releases/download/${version}/${binary_name}"

    # Download binary
    local tmp_file=$(mktemp)
    download "$download_url" "$tmp_file"

    # Make executable
    chmod +x "$tmp_file"

    # Move to install directory
    local final_path="$install_dir/thenvoi-cli"

    if [ -w "$install_dir" ]; then
        mv "$tmp_file" "$final_path"
    else
        info "Need sudo to install to $install_dir"
        sudo mv "$tmp_file" "$final_path"
    fi

    # Verify installation
    if [ -x "$final_path" ]; then
        success "Installed thenvoi-cli to $final_path"
    else
        error "Installation failed"
        exit 1
    fi

    # Add to PATH if needed
    if [ -z "$THENVOI_NO_MODIFY_PATH" ]; then
        if [[ ":$PATH:" != *":$install_dir:"* ]]; then
            add_to_path "$install_dir"
        fi
    fi

    # Verify it works
    if has_command thenvoi-cli; then
        echo ""
        success "Installation complete!"
        thenvoi-cli --version
    else
        echo ""
        success "Installation complete!"
        info "Run: $final_path --version"
        info "Or add $install_dir to your PATH"
    fi

    echo ""
    echo "Get started:"
    echo "  thenvoi-cli config set my-agent --agent-id <uuid> --api-key <key>"
    echo "  thenvoi-cli run my-agent"
    echo ""
}

# Handle installation via pip/pipx as fallback
install_via_pip() {
    info "Binary not available for your platform. Installing via pip..."

    if has_command pipx; then
        info "Installing with pipx (recommended)..."
        pipx install thenvoi-cli
    elif has_command pip3; then
        info "Installing with pip3..."
        pip3 install --user thenvoi-cli
    elif has_command pip; then
        info "Installing with pip..."
        pip install --user thenvoi-cli
    else
        error "No pip/pipx found. Please install Python 3.11+ and pip."
        exit 1
    fi

    success "Installed via pip!"
}

# Run main
main "$@"
