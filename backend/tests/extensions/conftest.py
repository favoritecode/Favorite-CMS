from collections.abc import Mapping


def manifest_data(**overrides: object) -> Mapping[str, object]:
    data: dict[str, object] = {
        "id": "favorite.plugin.example",
        "type": "plugin",
        "name": "Example",
        "version": "1.0.0",
        "description": "A generic test extension",
        "author": "Favorite CMS",
        "license": "Test only",
        "homepage": "https://example.invalid",
        "repository": "https://example.invalid/repository",
        "minimumCoreVersion": "0.1.0",
        "maximumCoreVersion": "1.0.0",
    }
    data.update(overrides)
    return data

