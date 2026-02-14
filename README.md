# Nexus Plugin Registry

The official community registry for [Nexus](https://github.com/imdanibytes/nexus) plugins and extensions.

This registry is automatically fetched by the Nexus marketplace. Plugins listed here appear in the in-app Marketplace for one-click install.

## Registry Format

`registry.json` contains:

```json
{
  "version": 1,
  "updated_at": "2025-02-14T00:00:00Z",
  "plugins": [
    {
      "id": "com.author.plugin-name",
      "name": "Plugin Name",
      "version": "1.0.0",
      "description": "What it does",
      "image": "docker-image-name:latest",
      "manifest_url": "https://raw.githubusercontent.com/.../plugin.json",
      "categories": ["category"],
      "downloads": 0
    }
  ],
  "extensions": []
}
```

## Submitting a Plugin

1. Create your plugin repo with a `plugin.json` manifest and `Dockerfile`
2. Fork this repository
3. Add your plugin entry to the `plugins` array in `registry.json`
4. Update `updated_at` to the current timestamp
5. Open a pull request

CI will validate your entry (JSON syntax, schema, reachable manifest URL, no duplicate IDs).

See [nexus-cookie-jar](https://github.com/imdanibytes/nexus-cookie-jar) for an example plugin.

## Plugin ID Convention

Use reverse-domain notation: `com.yourname.plugin-name`

## Validation

The registry is validated on every push and PR via the `validate.yml` workflow:
- JSON syntax check
- Schema validation against `schema.json`
- Duplicate ID detection
- Manifest URL reachability check

## License

MIT
