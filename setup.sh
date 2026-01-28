#!/usr/bin/env bash
set -euo pipefail

# Proxmox MCP Server Setup Script
# Streamlines installation and agent configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check for uv
command -v uv >/dev/null 2>&1 || error "uv is required. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

# Setup virtual environment and install dependencies
setup_venv() {
    info "Setting up virtual environment..."
    if [[ ! -d ".venv" ]]; then
        uv venv
    fi

    info "Installing dependencies..."
    uv pip install -e ".[dev]"
}

# Create .env file if it doesn't exist
setup_env() {
    if [[ ! -f ".env" ]]; then
        info "Creating .env file..."
        cat > .env << 'EOF'
# Proxmox API Token
# Format: user@realm!token_name
PROXMOX_TOKEN_ID=root@pam!mcp
PROXMOX_TOKEN_SECRET=your-token-secret-here
EOF
        warn ".env file created - please edit with your Proxmox credentials"
    else
        info ".env file already exists"
    fi
}

# Create config.json if it doesn't exist
setup_config() {
    mkdir -p proxmox-config
    if [[ ! -f "proxmox-config/config.json" ]]; then
        info "Creating config.json..."
        cat > proxmox-config/config.json << 'EOF'
{
    "proxmox": {
        "host": "your-proxmox-host",
        "port": 8006,
        "verify_ssl": false,
        "service": "PVE"
    },
    "auth": {},
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}
EOF
        warn "proxmox-config/config.json created - please edit with your Proxmox host"
    else
        info "config.json already exists"
    fi
}

# Generate Claude Code MCP server config
generate_claude_config() {
    info "Generating Claude Code MCP server configuration..."

    local config_json
    config_json=$(cat << EOF
{
  "mcpServers": {
    "proxmox": {
      "command": "${SCRIPT_DIR}/.venv/bin/python",
      "args": ["-m", "proxmox_mcp.server"],
      "env": {
        "PYTHONPATH": "${SCRIPT_DIR}/src",
        "PROXMOX_MCP_CONFIG": "${SCRIPT_DIR}/proxmox-config/config.json"
      }
    }
  }
}
EOF
)

    echo ""
    echo "Add this to your Claude Code settings (~/.claude/settings.json):"
    echo ""
    echo "$config_json"
    echo ""

    # Check if settings.json exists and offer to update
    local settings_file="$HOME/.claude/settings.json"
    if [[ -f "$settings_file" ]] && [[ -t 0 ]]; then
        read -p "Would you like to automatically add this to your Claude settings? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Use jq if available, otherwise manual merge
            if command -v jq >/dev/null 2>&1; then
                local merged
                merged=$(jq --argjson new "$config_json" '. * $new' "$settings_file")
                echo "$merged" > "$settings_file"
                info "Updated $settings_file"
            else
                warn "jq not installed - please manually add the config above to $settings_file"
            fi
        fi
    fi
}

# Verify installation
verify() {
    info "Verifying installation..."
    if .venv/bin/python -c "import proxmox_mcp; print('OK')" 2>/dev/null; then
        info "Installation verified successfully"
    else
        error "Installation verification failed"
    fi
}

# Main
main() {
    echo "=================================="
    echo "  Proxmox MCP Server Setup"
    echo "=================================="
    echo ""

    setup_venv
    setup_env
    setup_config
    verify
    generate_claude_config

    echo ""
    info "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env with your Proxmox API token"
    echo "  2. Edit proxmox-config/config.json with your Proxmox host"
    echo "  3. Restart Claude Code to load the MCP server"
    echo ""
    echo "To test manually:"
    echo "  PROXMOX_MCP_CONFIG=proxmox-config/config.json .venv/bin/python -m proxmox_mcp.server"
}

main "$@"
