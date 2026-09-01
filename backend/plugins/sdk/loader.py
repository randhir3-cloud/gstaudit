"""Discover and load GAIS plugins from the repository plugins/ directory."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from plugins.sdk.context import PluginContext
from plugins.sdk.manifest import PluginManifest
from plugins.sdk.registry import plugin_registry

_LOADED = False
_PLUGINS_ROOT: Optional[Path] = None


def plugins_root() -> Path:
    global _PLUGINS_ROOT
    if _PLUGINS_ROOT is None:
        # backend/plugins/sdk/loader.py → repo root is parents[3]
        _PLUGINS_ROOT = Path(__file__).resolve().parents[3] / "plugins"
    return _PLUGINS_ROOT


def _load_manifest(plugin_dir: Path) -> PluginManifest:
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Plugin missing manifest.json: {plugin_dir.name}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return PluginManifest.model_validate(data)


def _import_plugin_module(plugin_dir: Path):
    module_path = plugin_dir / "plugin.py"
    if not module_path.exists():
        return None
    module_name = f"gais_plugin_{plugin_dir.name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin module: {plugin_dir}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _register_plugin(plugin_dir: Path, app: Optional[FastAPI] = None) -> None:
    if not plugin_dir.is_dir():
        return
    if plugin_dir.name.startswith("_") or plugin_dir.name == "future":
        return
    manifest = _load_manifest(plugin_dir)
    plugin_registry.register_manifest(manifest)
    module = _import_plugin_module(plugin_dir)
    if module and hasattr(module, "register"):
        ctx = PluginContext(app=app)
        module.register(plugin_registry, ctx)


def ensure_plugins_loaded(app: Optional[FastAPI] = None) -> None:
    """Load plugin manifests and registrations once per process."""
    global _LOADED
    if _LOADED:
        return
    root = plugins_root()
    if not root.exists():
        _LOADED = True
        return
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry / "manifest.json").exists():
            _register_plugin(entry, app=app)
    _LOADED = True


def load_plugins(app: FastAPI) -> None:
    """Discover plugins and mount their routers on the FastAPI app."""
    ensure_plugins_loaded(app=app)
    for router in plugin_registry.routers:
        app.include_router(router)


def reset_plugins_for_tests() -> None:
    global _LOADED
    _LOADED = False
