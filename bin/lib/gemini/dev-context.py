# dyncontext.py
# Módulo para la gestión del contexto dinámico de Osiris

import json
import os
import time
from enum import Enum

# Asumiendo que las definiciones del sistema están accesibles
# from osiris_definitions import osiris_definitions # Si estuvieran en un archivo separado

# Definiciones internas para este módulo
# En una implementación real, estas definiciones podrían venir de una configuración externa
# o ser cargadas dinámicamente.
class ContextScope(Enum):
    SESSION = "session"
    PERMANENT = "permanent"
    GLOBAL = "global" # Para datos del sistema que no cambian

class DynamicContextManager:
    def __init__(self, context_data_path="/var/osiris2/bin/com/datas/ai", context_file="session_context.json"):
        self.context_data_path = context_data_path
        self.context_file = context_file
        self.session_context = {}
        self.permanent_context = {}
        self.global_context = {} # Para datos del sistema como modo de operación, etc.

        # Asegurar que el directorio de datos del contexto exista
        os.makedirs(self.context_data_path, exist_ok=True)

        # Cargar contexto permanente y de sesión al inicio
        self._load_permanent_context()
        self._load_session_context()
        self._load_global_context()

    def _get_context_filepath(self, scope):
        if scope == ContextScope.PERMANENT:
            return os.path.join(self.context_data_path, f"permanent_context.json")
        elif scope == ContextScope.SESSION:
            return os.path.join(self.context_data_path, self.context_file)
        elif scope == ContextScope.GLOBAL:
            return os.path.join(self.context_data_path, "global_context.json")
        else:
            raise ValueError("Ámbito de contexto inválido")

    def _load_context_from_file(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Advertencia: No se pudo decodificar el archivo de contexto: {filepath}")
                return {}
            except Exception as e:
                print(f"Error al cargar contexto desde {filepath}: {e}")
                return {}
        return {}

    def _save_context_to_file(self, filepath, context_data):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar contexto en {filepath}: {e}")

    def _load_session_context(self):
        self.session_context = self._load_context_from_file(self._get_context_filepath(ContextScope.SESSION))

    def _save_session_context(self):
        self._save_context_to_file(self._get_context_filepath(ContextScope.SESSION), self.session_context)

    def _load_permanent_context(self):
        self.permanent_context = self._load_context_from_file(self._get_context_filepath(ContextScope.PERMANENT))

    def _save_permanent_context(self):
        self._save_context_to_file(self._get_context_filepath(ContextScope.PERMANENT), self.permanent_context)

    def _load_global_context(self):
        # El contexto global podría ser más estático o cargado de otra fuente
        self.global_context = self._load_context_from_file(self._get_context_filepath(ContextScope.GLOBAL))
        # Asegurar que el modo de operación esté presente
        if "operation_mode" not in self.global_context:
            self.global_context["operation_mode"] = "CLI" # Por defecto

    def _save_global_context(self):
        self._save_context_to_file(self._get_context_filepath(ContextScope.GLOBAL), self.global_context)

    def update_context(self, key, value, scope=ContextScope.SESSION, ttl=None):
        """
        Actualiza o añade un valor al contexto.
        :param key: La clave del dato a almacenar.
        :param value: El valor a almacenar.
        :param scope: El ámbito del contexto (SESSION, PERMANENT, GLOBAL).
        :param ttl: Time-to-live en segundos para datos de sesión (no implementado completamente aún).
        """
        if scope == ContextScope.SESSION:
            self.session_context[key] = value
            # Aquí iría lógica para manejar TTL si fuera necesario
            self.context_file = f"session_context_{int(time.time())}.json" # Para persistencia simple de sesión
            self._save_session_context()
        elif scope == ContextScope.PERMANENT:
            self.permanent_context[key] = value
            self._save_permanent_context()
        elif scope == ContextScope.GLOBAL:
            self.global_context[key] = value
            self._save_global_context()
        else:
            raise ValueError("Ámbito de contexto inválido para actualización")

    def get_context(self, key, default=None, scope=ContextScope.SESSION):
        """
        Recupera un valor del contexto.
        :param key: La clave del dato a recuperar.
        :param default: Valor por defecto si la clave no se encuentra.
        :param scope: El ámbito de contexto desde donde buscar (SESSION, PERMANENT, GLOBAL).
                      Busca en SESSION -> PERMANENT -> GLOBAL si no se especifica ámbito.
        """
        # Implementar lógica de búsqueda priorizada si no se especifica scope
        if scope == ContextScope.SESSION:
            return self.session_context.get(key, default)
        elif scope == ContextScope.PERMANENT:
            return self.permanent_context.get(key, default)
        elif scope == ContextScope.GLOBAL:
            return self.global_context.get(key, default)
        else:
            # Búsqueda priorizada si no se especifica scope explícitamente
            value = self.session_context.get(key)
            if value is not None:
                return value
            value = self.permanent_context.get(key)
            if value is not None:
                return value
            return self.global_context.get(key, default)

    def delete_context(self, key, scope=ContextScope.SESSION):
        """
        Elimina un dato del contexto.
        """
        if scope == ContextScope.SESSION:
            if key in self.session_context:
                del self.session_context[key]
                self._save_session_context()
        elif scope == ContextScope.PERMANENT:
            if key in self.permanent_context:
                del self.permanent_context[key]
                self._save_permanent_context()
        elif scope == ContextScope.GLOBAL:
            if key in self.global_context:
                del self.global_context[key]
                self._save_global_context()
        else:
            raise ValueError("Ámbito de contexto inválido para eliminación")

    def clear_all_session_context(self):
        """
        Limpia todos los datos de contexto de la sesión actual.
        """
        self.session_context = {}
        self._save_session_context()

    def get_operation_mode(self):
        """
        Devuelve el modo de operación actual del sistema (CLI, WEB, DESKTOP).
        """
        return self.global_context.get("operation_mode", "CLI") # Default a CLI

    def set_operation_mode(self, mode):
        """
        Establece el modo de operación del sistema.
        """
        if mode in ["CLI", "WEB", "DESKTOP"]:
            self.update_context("operation_mode", mode, scope=ContextScope.GLOBAL)
        else:
            print(f"Advertencia: Modo de operación inválido '{mode}'. Use CLI, WEB o DESKTOP.")

    def get_all_context_keys(self, scope=None):
        """
        Devuelve una lista de todas las claves de contexto disponibles.
        Si se especifica un ámbito, solo devuelve las claves de ese ámbito.
        """
        if scope == ContextScope.SESSION:
            return list(self.session_context.keys())
        elif scope == ContextScope.PERMANENT:
            return list(self.permanent_context.keys())
        elif scope == ContextScope.GLOBAL:
            return list(self.global_context.keys())
        elif scope is None:
            all_keys = set(self.session_context.keys())
            all_keys.update(self.permanent_context.keys())
            all_keys.update(self.global_context.keys())
            return list(all_keys)
        else:
            raise ValueError("Ámbito de contexto inválido para obtener claves")

# --- Simulación de uso ---
# if __name__ == "__main__":
#     # Crear una instancia del gestor de contexto
#     context_manager = DynamicContextManager()
#
#     # Actualizar contexto de sesión
#     context_manager.update_context("user_query_summary", "Ejemplo de consulta resumida")
#     context_manager.update_context("last_action_result", "Comando CRO ejecutado con éxito.")
#
#     # Actualizar contexto permanente
#     context_manager.update_context("user_preferences", {"theme": "dark", "language": "es"}, scope=ContextScope.PERMANENT)
#
#     # Actualizar contexto global
#     context_manager.set_operation_mode("WEB")
#     context_manager.update_context("ai_model_version", "gemini-2.5-flash-lite-preview-06-17", scope=ContextScope.GLOBAL)
#
#     # Recuperar valores
#     print(f"Modo de operación: {context_manager.get_operation_mode()}")
#     print(f"Resumen de consulta: {context_manager.get_context('user_query_summary')}")
#     print(f"Preferencias de usuario: {context_manager.get_context('user_preferences', scope=ContextScope.PERMANENT)}")
#     print(f"Versión del modelo AI: {context_manager.get_context('ai_model_version', scope=ContextScope.GLOBAL)}")
#     print(f"Clave desconocida (sesión): {context_manager.get_context('unknown_key', default='N/A', scope=ContextScope.SESSION)}")
#
#     # Listar claves
#     print(f"Claves de sesión: {context_manager.get_all_context_keys(scope=ContextScope.SESSION)}")
#     print(f"Claves permanentes: {context_manager.get_all_context_keys(scope=ContextScope.PERMANENT)}")
#     print(f"Claves globales: {context_manager.get_all_context_keys(scope=ContextScope.GLOBAL)}")
#
#     # Eliminar un dato de sesión
#     context_manager.delete_context("last_action_result", scope=ContextScope.SESSION)
#     print(f"Claves de sesión después de eliminar: {context_manager.get_all_context_keys(scope=ContextScope.SESSION)}")
#
#     # Limpiar contexto de sesión
#     # context_manager.clear_all_session_context()
#     # print(f"Claves de sesión después de limpiar: {context_manager.get_all_context_keys(scope=ContextScope.SESSION)}")