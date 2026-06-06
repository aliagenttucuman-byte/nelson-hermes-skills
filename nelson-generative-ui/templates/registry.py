"""
Registry multi-proyecto para JARVIS Demo Shell.
Carga automáticamente todos los archivos en tools/ y combina
sus instrucciones en un único system prompt para el agente.

Uso:
- Crear tools/mi_proyecto.py con una clase que herede BaseTool y use @register
- get_system_instructions() retorna el prompt combinado de todos los proyectos
"""
import importlib
import pkgutil
from typing import Dict, Type


_tools: Dict[str, "BaseTool"] = {}
_loaded = False


class BaseTool:
    name: str = "base"
    description: str = ""

    def get_system_instructions(self) -> str:
        return ""


def register(cls: Type[BaseTool]) -> Type[BaseTool]:
    instance = cls()
    _tools[instance.name] = instance
    return cls


def load_all():
    """Importa todos los módulos en tools/ excepto registry y __init__."""
    global _loaded
    if _loaded:
        return
    import tools as tools_pkg
    for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
        if module_name not in ("registry", "__init__"):
            importlib.import_module(f"tools.{module_name}")
    _loaded = True


def get_system_instructions() -> str:
    """Retorna instrucciones combinadas de TODOS los proyectos registrados."""
    load_all()
    if not _tools:
        return "No hay proyectos registrados."

    parts = [
        "Tenés acceso a múltiples fuentes de datos. "
        "Usá la que corresponda según la pregunta del usuario.\n"
    ]
    for tool in _tools.values():
        instructions = tool.get_system_instructions()
        if instructions.strip():
            parts.append(instructions.strip())

    return "\n\n---\n\n".join(parts)


def list_projects() -> list:
    load_all()
    return [{"name": t.name, "description": t.description} for t in _tools.values()]
