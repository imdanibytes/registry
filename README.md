# Nexus Plugin Registry

The official community registry for [Nexus](https://github.com/imdanibytes/nexus) plugins and extensions.

Packages listed here appear in the Nexus Marketplace for one-click install. The registry uses a Homebrew-style format: each package is a standalone YAML file validated against JSON schemas and compiled into `index.json` by CI.

## Repository Structure

```
registry.yaml              # Registry metadata
plugins/                    # One YAML file per plugin
  com.nexus.cookie-jar.yaml
extensions/                 # One YAML file per extension
schema/                     # JSON Schema definitions
  plugin.schema.json
  extension.schema.json
  registry.schema.json
scripts/
  build-index.py            # Compiles YAML sources into index.json
index.json                  # Auto-generated — do not edit
```

## Package Format

### Plugin YAML

```yaml
id: com.yourname.plugin-name
name: My Plugin
version: "1.0.0"
description: >
  A short description of what your plugin does
author: yourname
license: MIT
homepage: https://github.com/yourname/nexus-plugin-name
image: ghcr.io/yourname/nexus-plugin-name:1.0.0
manifest_url: https://raw.githubusercontent.com/yourname/nexus-plugin-name/main/plugin.json
categories:
  - productivity
status: active
```

Plugins are Docker containers that run as MCP servers inside Nexus. The `image` field points to a published OCI image, and `manifest_url` points to a `plugin.json` that describes the plugin's tools and configuration.

### Extension YAML

```yaml
id: com.yourname.extension-name
name: My Extension
version: "1.0.0"
description: >
  A short description of what your extension does
author: yourname
license: MIT
homepage: https://github.com/yourname/nexus-extension-name
author_public_key: "base64-encoded-public-key"
manifest_url: https://raw.githubusercontent.com/yourname/nexus-extension-name/main/manifest.json
platforms:
  - windows
  - macos
  - linux
categories:
  - themes
status: active
```

Extensions are signed native packages that extend the Nexus UI. The `author_public_key` is used to verify the extension signature.

### Status Values

| Status | Behavior |
|--------|----------|
| `active` | Listed in marketplace and index.json |
| `deprecated` | Listed with deprecation notice |
| `unlisted` | Excluded from index.json entirely |

### Plugin ID Convention

Use reverse-domain notation: `com.yourname.plugin-name`

The filename **must** match the ID (e.g., `com.yourname.plugin-name.yaml`).

## Submitting a Package

### Using the CLI (recommended)

The `nexus-registry` CLI automates the entire submission flow — generates the YAML, validates it, creates a PR, and enables auto-merge:

```bash
# Install (from the Nexus repo)
cd nexus/src-tauri && cargo install --path crates/nexus-registry

# Add a plugin to your local registry clone
nexus-registry add plugin \
  --id com.yourname.my-plugin \
  --name "My Plugin" \
  --version 1.0.0 \
  --author yourname \
  --image ghcr.io/yourname/nexus-plugin-name:1.0.0 \
  --manifest-url https://raw.githubusercontent.com/yourname/nexus-plugin-name/main/plugin.json \
  --categories "productivity,ai-tools"

# Publish to the community registry (branches, validates, pushes, opens PR)
nexus-registry publish \
  --registry https://github.com/imdanibytes/registry.git \
  --package plugins/com.yourname.my-plugin.yaml
```

The `publish` command will:
1. Clone the registry
2. Copy your package YAML into it
3. Run `validate` to check schemas and catch errors
4. Create a branch, commit, and push
5. Open a PR (requires `gh` CLI) with auto-merge enabled

### Manual submission

1. Create your plugin/extension repo with a manifest and Dockerfile
2. Fork this repository
3. Add a YAML file to `plugins/` or `extensions/` following the format above
4. Open a pull request

CI will validate your entry automatically:
- YAML syntax check
- Schema validation against `schema/plugin.schema.json` or `schema/extension.schema.json`
- Duplicate ID detection
- Manifest URL reachability

On merge, `index.json` is rebuilt and committed automatically.

See [nexus-cookie-jar](https://github.com/imdanibytes/nexus-cookie-jar) for a complete plugin example.

## Creating Your Own Registry

Nexus supports custom registries. To create one:

1. **Scaffold the structure:**
   ```
   mkdir my-registry && cd my-registry
   mkdir plugins extensions schema scripts
   ```

2. **Copy the schemas** from `schema/` — they define the contract.

3. **Create `registry.yaml`:**
   ```yaml
   name: "My Organization"
   description: "Internal plugin registry"
   homepage: "https://github.com/myorg/registry"
   maintainer: "myorg"
   ```

4. **Add the build script** — copy `scripts/build-index.py`.

5. **Set up CI** — use the workflows in `.github/workflows/` as templates.

6. **Point Nexus at your registry:**
   ```
   nexus registry add myorg https://raw.githubusercontent.com/myorg/registry/main/index.json
   ```

## Registry CLI

The `nexus registry` commands manage registry sources:

```
nexus registry list              # Show configured registries
nexus registry add <name> <url>  # Add a custom registry
nexus registry remove <name>     # Remove a registry
nexus registry sync              # Refresh all registry indexes
```

## Building Locally

```bash
pip install pyyaml jsonschema
python3 scripts/build-index.py
```

This validates all YAML files and generates `index.json`.

## License

MIT
