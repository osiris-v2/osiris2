# osiris2/__init__.py

from .multiprocess import info, man, ProcessHandler, ProcessManager, multiprocess, fixed_pid

# Inicializa el ProcessManager para poder acceder a sus métodos
process_manager = ProcessManager()

__all__ = ["info", "man", "ProcessHandler", "ProcessManager", "multiprocess", "process_manager","fixed_pid"]

