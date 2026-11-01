"""
╔══════════════════════════════════════════════════════════════════════════╗
║       OSIRIS · mistral_context.py  ·  Gestor de Contexto Inteligente   ║
║                                                                          ║
║  Sistema de gestión de contexto para Mistral AI con:                    ║
║  - Serialización estructurada de fragmentos (inspirado en dyncontext)   ║
║  - Anclaje de instrucciones CRO al principio del contexto               ║
║  - Marcado de respuestas de sistema CRO (filtrado de irrelevantes)      ║
║  - Compresión automática por bucle de inferencias cuando se acerca       ║
║    al límite de tokens (con barra de progreso)                           ║
║  - Integración directa con mistral2.py                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import datetime
import re
import sys
import os

# ─── Tipos de fragmento ──────────────────────────────────────────────────────
FRAG_USER        = "user_turn"
FRAG_AI          = "ai_response"
FRAG_CRO_INST    = "cro_instruction"   # instrucciones CRO → siempre al principio
FRAG_CRO_OUTPUT  = "cro_system_output" # salidas de ejecución CRO
FRAG_CRO_ERROR   = "cro_error"
FRAG_SYSTEM      = "system_instruction"
FRAG_LOG         = "system_log"
FRAG_COMPRESSED  = "compressed_summary"

# ─── Flags ───────────────────────────────────────────────────────────────────
FLAG_ESSENTIAL   = "ESSENTIAL_CORE"
FLAG_HIGH_REL    = "HIGH_RELEVANCE"
FLAG_CRO_ACTIVE  = "CRO_ACTIVE_INSTRUCTION"
FLAG_OBSOLETE    = "OBSOLETE"
FLAG_PINNED      = "TEMPORARY_PIN"
FLAG_CRO_RESULT  = "CRO_RESULT"
FLAG_IRRELEVANT  = "CRO_IRRELEVANT"

# ─── Límites ──────────────────────────────────────────────────────────────────
DEFAULT_TOKEN_LIMIT        = 32_000   # tokens hasta los que Mistral funciona bien
COMPRESSION_TRIGGER_RATIO  = 0.75    # inicia compresión al 75% del límite
CHARS_PER_TOKEN            = 4       # estimación aproximada


# ══════════════════════════════════════════════════════════════════════════════
#  CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class MistralContextManager:
    """
    Gestor de contexto estructurado para Osiris + Mistral.

    Ciclo de vida de un fragmento:
      1. Se añade via add_fragment()
      2. Se ordena: CRO_INST al principio, luego HIGH_REL, luego el resto cronológico
      3. Se verifica el peso de tokens en cada adición
      4. Si supera el COMPRESSION_TRIGGER_RATIO se lanza compress_context()
         → bucle de inferencias Mistral con barra de progreso
      5. build_messages() devuelve la lista lista para client.chat.complete()
    """

    def __init__(
        self,
        mistral_client=None,
        mistral_model: str = "mistral-small-latest",
        token_limit: int = DEFAULT_TOKEN_LIMIT,
        compression_trigger_ratio: float = COMPRESSION_TRIGGER_RATIO,
        verbose: bool = True
    ):
        self.client              = mistral_client
        self.model               = mistral_model
        self.token_limit         = token_limit
        self.trigger_tokens      = int(token_limit * compression_trigger_ratio)
        self.verbose             = verbose

        # Lista principal de fragmentos
        self._fragments: list[dict] = []

        # Contador interno
        self._id_counter = 0

        # Stats
        self.stats = {
            "total_added": 0,
            "total_compressed": 0,
            "compression_runs": 0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  Utilidades internas
    # ─────────────────────────────────────────────────────────────────────────
    def _new_id(self, prefix: str) -> str:
        self._id_counter += 1
        ts = datetime.datetime.now().strftime("%H%M%S%f")
        return f"{prefix}_{ts}_{self._id_counter:04d}"

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // CHARS_PER_TOKEN)

    def _fragment_tokens(self, frag: dict) -> int:
        return self._estimate_tokens(frag.get("content", ""))

    def _total_tokens(self) -> int:
        return sum(self._fragment_tokens(f) for f in self._fragments
                   if FLAG_OBSOLETE not in f.get("flags", []))

    def _progress_bar(self, current: int, total: int, width: int = 40, label: str = "") -> str:
        pct = min(current / max(total, 1), 1.0)
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)
        return f"\r  [{bar}] {pct*100:.1f}%  {label}    "

    def _log(self, msg: str):
        if self.verbose:
            print(f"  [CTX] {msg}")

    # ─────────────────────────────────────────────────────────────────────────
    #  API pública: añadir fragmentos
    # ─────────────────────────────────────────────────────────────────────────
    def add_user(self, text: str, key_ideas: list = None) -> dict:
        """Añade un turno de usuario."""
        return self.add_fragment(
            source_type=FRAG_USER,
            content=text,
            key_ideas=key_ideas or [],
            relevance=1.0
        )

    def add_ai(self, text: str, has_cro: bool = False) -> dict:
        """Añade una respuesta del modelo. Si contiene CRO, eleva la relevancia."""
        flags = [FLAG_HIGH_REL] if has_cro else []
        return self.add_fragment(
            source_type=FRAG_AI,
            content=text,
            flags=flags,
            relevance=1.0 if has_cro else 0.85
        )

    def add_cro_instruction(self, text: str) -> dict:
        """
        Añade una instrucción CRO.  Siempre se ancla al principio del contexto
        (FLAG_ESSENTIAL + FLAG_CRO_ACTIVE).
        """
        return self.add_fragment(
            source_type=FRAG_CRO_INST,
            content=text,
            flags=[FLAG_ESSENTIAL, FLAG_CRO_ACTIVE, FLAG_PINNED],
            relevance=1.0
        )

    def add_cro_output(self, text: str, relevant: bool = True) -> dict:
        """
        Añade la salida de una ejecución CRO.
        Si relevant=False se marca como IRRELEVANT (candidata a eliminar).
        """
        flags = [FLAG_CRO_RESULT]
        if not relevant:
            flags.append(FLAG_IRRELEVANT)
        return self.add_fragment(
            source_type=FRAG_CRO_OUTPUT,
            content=text,
            flags=flags,
            relevance=0.9 if relevant else 0.2
        )

    def add_cro_error(self, text: str) -> dict:
        return self.add_fragment(
            source_type=FRAG_CRO_ERROR,
            content=text,
            flags=[FLAG_CRO_RESULT],
            relevance=0.7
        )

    def add_system(self, text: str, essential: bool = True) -> dict:
        flags = [FLAG_ESSENTIAL] if essential else [FLAG_HIGH_REL]
        return self.add_fragment(
            source_type=FRAG_SYSTEM,
            content=text,
            flags=flags,
            relevance=1.0
        )

    def mark_irrelevant(self, frag_id: str):
        """Marca un fragmento como irrelevante (candidato a purga)."""
        for f in self._fragments:
            if f["id"] == frag_id:
                if FLAG_IRRELEVANT not in f["flags"]:
                    f["flags"].append(FLAG_IRRELEVANT)
                f["relevance"] = 0.1
                self._log(f"Marcado como irrelevante: {frag_id}")
                return
        self._log(f"[WARN] mark_irrelevant: ID no encontrado: {frag_id}")

    def mark_obsolete(self, frag_id: str):
        """Marca un fragmento como obsoleto (excluido del contexto enviado)."""
        for f in self._fragments:
            if f["id"] == frag_id:
                if FLAG_OBSOLETE not in f["flags"]:
                    f["flags"].append(FLAG_OBSOLETE)
                self._log(f"Marcado como obsoleto: {frag_id}")
                return

    # ─────────────────────────────────────────────────────────────────────────
    #  Núcleo: add_fragment + auto-compresión
    # ─────────────────────────────────────────────────────────────────────────
    def add_fragment(
        self,
        source_type: str,
        content: str,
        key_ideas: list = None,
        flags: list = None,
        relevance: float = 0.5
    ) -> dict:
        """Añade un fragmento genérico y dispara compresión si es necesario."""
        frag = {
            "id":        self._new_id(source_type[:6].upper()),
            "type":      source_type,
            "content":   content,
            "timestamp": datetime.datetime.now().isoformat(),
            "key_ideas": key_ideas or [],
            "flags":     sorted(list(set(flags or []))),
            "relevance": relevance,
            "tokens_est": self._estimate_tokens(content)
        }
        self._fragments.append(frag)
        self.stats["total_added"] += 1

        # ── Auto-compresión ──────────────────────────────────────────────────
        total = self._total_tokens()
        if total >= self.trigger_tokens:
            self._log(
                f"⚡ Tokens estimados ({total:,}) ≥ umbral ({self.trigger_tokens:,}). "
                f"Iniciando compresión…"
            )
            self.compress_context()

        return frag

    # ─────────────────────────────────────────────────────────────────────────
    #  Ordenación
    # ─────────────────────────────────────────────────────────────────────────
    def _ordered_active_fragments(self) -> list:
        """
        Devuelve fragmentos activos respetando el orden cronológico de insercion.

        REGLA FUNDAMENTAL: los fragmentos de conversacion (user_turn, ai_response,
        cro_output, cro_error, compressed) NUNCA se reordenan entre si. Deben
        mantenerse en el orden de insercion para preservar la alternancia
        user -> assistant que exige la API de Mistral.

        Los anchor (ESSENTIAL/CRO_INST/SYSTEM) se devuelven al principio para
        que build_messages los identifique y los mueva al system prompt.
        El bloque de conversacion mantiene orden cronologico estricto.

        Se excluyen: OBSOLETE y IRRELEVANT con relevance < 0.3.
        """
        active = [
            f for f in self._fragments          # orden de insercion = cronologico
            if FLAG_OBSOLETE not in f.get("flags", [])
            and not (
                FLAG_IRRELEVANT in f.get("flags", [])
                and f.get("relevance", 1) < 0.3
            )
        ]

        anchor = [
            f for f in active
            if (FLAG_ESSENTIAL in f.get("flags", [])
                or FLAG_CRO_ACTIVE in f.get("flags", [])
                or f["type"] in (FRAG_CRO_INST, FRAG_SYSTEM))
        ]
        conv = [f for f in active if f not in anchor]
        # conv mantiene orden cronologico de self._fragments (sin sort)
        return anchor + conv

    # ─────────────────────────────────────────────────────────────────────────
    #  Construcción de mensajes para la API
    # ─────────────────────────────────────────────────────────────────────────
    def build_messages(self, system_prompt: str = None) -> list:
        """
        Devuelve la lista de mensajes lista para client.chat.complete(messages=...).

        Estructura:
          • system  → system_prompt + instrucciones CRO ancladas
          • user/assistant → fragmentos de conversación ordenados
        """
        ordered = self._ordered_active_fragments()

        # ── Construir bloque system ───────────────────────────────────────────
        system_parts = []
        if system_prompt:
            system_parts.append(system_prompt)

        cro_instructions = [
            f for f in ordered
            if f["type"] == FRAG_CRO_INST
        ]
        if cro_instructions:
            system_parts.append("\n\n── INSTRUCCIONES CRO ACTIVAS (ancla) ──")
            for ci in cro_instructions:
                system_parts.append(ci["content"])

        system_parts.append("\n── CONTEXTO DEL SISTEMA ──")
        system_parts.append(
            f"Tokens estimados en contexto: {self._total_tokens():,} / {self.token_limit:,}"
        )

        messages = []
        if system_parts:
            messages.append({
                "role":    "system",
                "content": "\n".join(system_parts)
            })

        # ── Fragmentos de conversación (no CRO_INST, no SYSTEM) ──────────────
        conv_frags = [
            f for f in ordered
            if f["type"] not in (FRAG_CRO_INST, FRAG_SYSTEM)
        ]

        # Convertir a user/assistant alternando según el tipo
        for frag in conv_frags:
            ftype = frag["type"]
            if ftype == FRAG_USER:
                role = "user"
                content = frag["content"]
            elif ftype == FRAG_AI:
                role = "assistant"
                content = frag["content"]
            elif ftype in (FRAG_CRO_OUTPUT, FRAG_CRO_ERROR):
                # Las salidas CRO se inyectan como mensajes de usuario con etiqueta
                role = "user"
                tag = "🖥️ SALIDA_CRO" if ftype == FRAG_CRO_OUTPUT else "❌ ERROR_CRO"
                content = f"[{tag}]\n{frag['content']}\n[/{tag}]"
            elif ftype == FRAG_COMPRESSED:
                role = "user"
                content = f"[📦 CONTEXTO_COMPRIMIDO]\n{frag['content']}\n[/CONTEXTO_COMPRIMIDO]"
            elif ftype == FRAG_LOG:
                role = "user"
                content = f"[🗒️ LOG_SISTEMA]\n{frag['content']}\n[/LOG_SISTEMA]"
            else:
                role = "user"
                content = frag["content"]

            # Evitar mensajes vacíos
            if content.strip():
                messages.append({"role": role, "content": content})

        # Mistral requiere que el último mensaje sea "user" si no hay respuesta pendiente
        # y que no haya dos mensajes consecutivos del mismo rol
        messages = self._fix_message_alternation(messages)

        return messages

    def _fix_message_alternation(self, messages: list) -> list:
        """
        Mistral API requiere roles alternados (user/assistant).
        Fusiona mensajes consecutivos del mismo rol.
        Nunca toca el mensaje system (índice 0 si lo hay).
        """
        if not messages:
            return messages

        start = 1 if messages[0]["role"] == "system" else 0
        fixed = messages[:start]

        for msg in messages[start:]:
            if fixed[start:] and fixed[-1]["role"] == msg["role"]:
                # Fusionar: mismo rol → concatenar contenido
                fixed[-1]["content"] += "\n\n" + msg["content"]
            else:
                fixed.append(msg)

        return fixed

    # ─────────────────────────────────────────────────────────────────────────
    #  COMPRESIÓN  (bucle de inferencias con barra de progreso)
    # ─────────────────────────────────────────────────────────────────────────
    def compress_context(self, target_ratio: float = 0.5) -> bool:
        """
        Comprime el contexto en un bucle de inferencias Mistral.

        Estrategia por pasos:
          Paso 1 → Purgar fragmentos IRRELEVANT/OBSOLETE
          Paso 2 → Inferencia Mistral para resumir fragmentos de baja relevancia
          Paso 3 → Reemplazar fragmentos resumidos por un COMPRESSED_SUMMARY
          Paso 4 → Si aún supera el objetivo, purgar CRO_OUTPUTs no esenciales
          Paso 5 → Verificación final

        target_ratio: fracción del token_limit que queremos alcanzar.
        """
        if self.client is None:
            self._log("⚠️  Sin cliente Mistral: compresión sin inferencia (solo purga).")
            self._purge_irrelevant()
            return False

        target_tokens = int(self.token_limit * target_ratio)
        self._log(f"🗜️  Objetivo de compresión: {target_tokens:,} tokens ({target_ratio*100:.0f}% del límite)")

        self.stats["compression_runs"] += 1
        MAX_STEPS = 5
        step = 0
        success = False

        print()  # línea vacía para la barra

        while step < MAX_STEPS:
            step += 1
            current = self._total_tokens()
            progress_label = f"Paso {step}/{MAX_STEPS} — {current:,} tokens"
            sys.stdout.write(self._progress_bar(current, self.token_limit, label=progress_label))
            sys.stdout.flush()
            time.sleep(0.1)  # pequeña pausa visual

            if current <= target_tokens:
                success = True
                break

            if step == 1:
                # ── Paso 1: purga simple ─────────────────────────────────────
                removed = self._purge_irrelevant()
                self._log(f"  Paso 1: {removed} fragmentos irrelevantes/obsoletos purgados.")

            elif step == 2:
                # ── Paso 2: inferencia de resumen sobre fragmentos de bajo score ─
                candidates = self._get_compression_candidates(n=8)
                if not candidates:
                    self._log("  Paso 2: No hay candidatos para resumir.")
                    continue
                self._log(f"  Paso 2: Resumiendo {len(candidates)} fragmentos con Mistral…")
                summary = self._infer_summary(candidates)
                if summary:
                    # Marcar candidatos como obsoletos
                    for c in candidates:
                        self.mark_obsolete(c["id"])
                    # Insertar el resumen comprimido
                    self.add_fragment(
                        source_type=FRAG_COMPRESSED,
                        content=summary,
                        flags=[FLAG_HIGH_REL],
                        relevance=0.9
                    )
                    self.stats["total_compressed"] += len(candidates)
                    self._log(f"  Paso 2: {len(candidates)} fragmentos → 1 resumen comprimido.")

            elif step == 3:
                # ── Paso 3: purgar CRO_OUTPUTs marcados irrelevantes ─────────
                removed = self._purge_cro_outputs()
                self._log(f"  Paso 3: {removed} salidas CRO de baja relevancia eliminadas.")

            elif step == 4:
                # ── Paso 4: resumen agresivo (mayor número de candidatos) ────
                candidates = self._get_compression_candidates(n=20, min_relevance=0.0)
                if candidates:
                    summary = self._infer_summary(candidates, aggressive=True)
                    if summary:
                        for c in candidates:
                            self.mark_obsolete(c["id"])
                        self.add_fragment(
                            source_type=FRAG_COMPRESSED,
                            content=summary,
                            flags=[FLAG_HIGH_REL],
                            relevance=0.95
                        )
                        self.stats["total_compressed"] += len(candidates)
                        self._log(f"  Paso 4: resumen agresivo de {len(candidates)} fragmentos.")

            elif step == 5:
                # ── Paso 5: fuerza bruta — purgar todo lo no esencial ────────
                removed = self._force_purge_non_essential()
                self._log(f"  Paso 5: purga forzosa de {removed} fragmentos no esenciales.")

        # Línea final de la barra
        final_tokens = self._total_tokens()
        sys.stdout.write(
            self._progress_bar(final_tokens, self.token_limit,
                               label=f"✅ Finalizado — {final_tokens:,} tokens") + "\n"
        )
        sys.stdout.flush()

        if not success and final_tokens > target_tokens:
            self._log(
                f"⚠️  Compresión incompleta: {final_tokens:,} tokens "
                f"(objetivo era {target_tokens:,}). Se recomienda --cc para reiniciar contexto."
            )

        return success

    # ─────────────────────────────────────────────────────────────────────────
    #  Helpers de compresión
    # ─────────────────────────────────────────────────────────────────────────
    def _purge_irrelevant(self) -> int:
        """Marca como OBSOLETE todos los fragmentos IRRELEVANT o con relevance < 0.25."""
        count = 0
        for f in self._fragments:
            if FLAG_OBSOLETE in f.get("flags", []):
                continue
            if FLAG_IRRELEVANT in f.get("flags", []) or f.get("relevance", 1) < 0.25:
                if FLAG_ESSENTIAL not in f.get("flags", []):
                    f["flags"].append(FLAG_OBSOLETE)
                    count += 1
        return count

    def _purge_cro_outputs(self) -> int:
        """Purga salidas CRO que no sean esenciales."""
        count = 0
        for f in self._fragments:
            if FLAG_OBSOLETE in f.get("flags", []):
                continue
            if f["type"] in (FRAG_CRO_OUTPUT, FRAG_CRO_ERROR):
                if FLAG_ESSENTIAL not in f.get("flags", []) and FLAG_PINNED not in f.get("flags", []):
                    if f.get("relevance", 1) < 0.8:
                        f["flags"].append(FLAG_OBSOLETE)
                        count += 1
        return count

    def _force_purge_non_essential(self) -> int:
        """Purga todo lo que no sea ESSENTIAL o los ultimos 4 fragmentos de conv."""
        count = 0
        conv_frags = [
            f for f in self._fragments   # orden cronologico
            if f["type"] in (FRAG_USER, FRAG_AI)
            and FLAG_OBSOLETE not in f.get("flags", [])
        ]
        keep_ids = {f["id"] for f in conv_frags[-4:]}   # los 4 mas recientes

        for f in self._fragments:
            if FLAG_OBSOLETE in f.get("flags", []):
                continue
            if FLAG_ESSENTIAL in f.get("flags", []):
                continue
            if f["id"] in keep_ids:
                continue
            f["flags"].append(FLAG_OBSOLETE)
            count += 1
        return count

    def _get_compression_candidates(self, n: int = 8, min_relevance: float = 0.0) -> list:
        """
        Devuelve hasta n fragmentos comprimibles.
        Los mas recientes (al final de self._fragments) se excluyen.
        Excluye: ESSENTIAL, CRO_INST, SYSTEM, los ultimos 4 turnos de conv.
        """
        active = [
            f for f in self._fragments          # orden cronologico
            if FLAG_OBSOLETE not in f.get("flags", [])
            and FLAG_ESSENTIAL not in f.get("flags", [])
            and FLAG_CRO_ACTIVE not in f.get("flags", [])
            and f["type"] not in (FRAG_CRO_INST, FRAG_SYSTEM)
            and f.get("relevance", 1) >= min_relevance
        ]
        # Excluir los ultimos 4 fragmentos de conversacion (los mas recientes)
        recent_ids = {f["id"] for f in active[-4:]}
        candidates = [f for f in active if f["id"] not in recent_ids]
        # Comprimir primero los de menor relevancia
        candidates.sort(key=lambda x: x.get("relevance", 0))
        return candidates[:n]

    def _infer_summary(self, fragments: list, aggressive: bool = False) -> str | None:
        """
        Llama a Mistral para resumir una lista de fragmentos.
        Devuelve el texto del resumen o None si falla.
        """
        if not self.client:
            return None

        # Construir el texto a comprimir
        raw_text = ""
        for i, f in enumerate(fragments):
            raw_text += f"\n[{i+1}] [{f['type']}] {f['content'][:800]}\n"

        instruction = (
            "Eres un sistema de compresión de contexto para una IA conversacional.\n"
            "Tu tarea es resumir los siguientes fragmentos de conversación/sistema "
            "conservando TODA la información esencial: hechos, comandos ejecutados, "
            "resultados relevantes, preferencias del usuario y estado del sistema.\n"
            "El resumen debe ser denso en información y en español.\n"
        )
        if aggressive:
            instruction += (
                "Modo AGRESIVO: comprime al máximo. Mantén solo lo imprescindible. "
                "Omite logs repetitivos, errores menores y conversación social.\n"
            )

        try:
            resp = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user",   "content": f"Fragmentos a comprimir:\n{raw_text}"}
                ]
            )
            return resp.choices[0].message.content
        except Exception as e:
            self._log(f"Error en inferencia de compresión: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    #  Estadísticas e introspección
    # ─────────────────────────────────────────────────────────────────────────
    def status(self) -> dict:
        """Devuelve un dict con el estado actual del gestor."""
        active = [f for f in self._fragments if FLAG_OBSOLETE not in f.get("flags", [])]
        obsolete_count = len(self._fragments) - len(active)
        return {
            "total_fragments":      len(self._fragments),
            "active_fragments":     len(active),
            "obsolete_fragments":   obsolete_count,
            "estimated_tokens":     self._total_tokens(),
            "token_limit":          self.token_limit,
            "trigger_tokens":       self.trigger_tokens,
            "usage_pct":            round(self._total_tokens() / max(self.token_limit, 1) * 100, 1),
            "cro_instructions":     sum(1 for f in active if f["type"] == FRAG_CRO_INST),
            "cro_outputs":          sum(1 for f in active if f["type"] == FRAG_CRO_OUTPUT),
            "compression_runs":     self.stats["compression_runs"],
            "total_compressed":     self.stats["total_compressed"],
            "model":                self.model,
        }

    def print_status(self):
        """Imprime el estado en formato legible."""
        s = self.status()
        sep = "─" * 55
        bar_filled = int(40 * s["usage_pct"] / 100)
        bar = "█" * bar_filled + "░" * (40 - bar_filled)
        color_warn = s["usage_pct"] >= 75

        print(f"""
  {sep}
  OSIRIS · Gestor de Contexto Mistral
  {sep}
  Modelo          : {s['model']}
  Fragmentos      : {s['active_fragments']} activos  |  {s['obsolete_fragments']} obsoletos
  Instrucciones CRO ancladas : {s['cro_instructions']}
  Salidas CRO     : {s['cro_outputs']}
  Tokens est.     : {s['estimated_tokens']:,} / {s['token_limit']:,}  ({s['usage_pct']}%)
  [{bar}]
  {'⚠️  Cerca del límite — compresión próxima' if color_warn else '✅  Uso normal'}
  Compresiones    : {s['compression_runs']} veces  |  {s['total_compressed']} fragmentos comprimidos
  {sep}
""")

    def list_fragments(self, show_obsolete: bool = False):
        """Imprime la lista de fragmentos en forma de tabla compacta."""
        frags = self._fragments if show_obsolete else [
            f for f in self._fragments if FLAG_OBSOLETE not in f.get("flags", [])
        ]
        print(f"\n  {'ID':<32} {'TIPO':<22} {'REL':>5}  {'TOKENS':>6}  {'FLAGS'}")
        print("  " + "─" * 90)
        for f in frags:
            flags_str = ",".join(f.get("flags", []))[:35]
            snippet   = f.get("content", "")[:45].replace("\n", " ")
            print(
                f"  {f['id']:<32} {f['type']:<22} "
                f"{f.get('relevance',0):>5.2f}  {f['tokens_est']:>6}  "
                f"{flags_str}  …{snippet}"
            )
        print()

    def export_json(self, filepath: str):
        """Exporta todos los fragmentos a un JSON."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as fp:
                json.dump(self._fragments, fp, ensure_ascii=False, indent=2)
            print(f"  [CTX] Contexto exportado → {filepath}")
        except Exception as e:
            print(f"  [CTX] Error exportando: {e}")

    def import_json(self, filepath: str) -> bool:
        """Importa fragmentos desde un JSON (se fusionan con los existentes)."""
        try:
            with open(filepath, "r", encoding="utf-8") as fp:
                loaded = json.load(fp)
            self._fragments.extend(loaded)
            print(f"  [CTX] {len(loaded)} fragmentos importados desde {filepath}")
            return True
        except Exception as e:
            print(f"  [CTX] Error importando: {e}")
            return False

    def reset(self, keep_essential: bool = True):
        """
        Resetea el contexto.
        Si keep_essential=True, conserva los fragmentos ESSENTIAL_CORE.
        """
        if keep_essential:
            self._fragments = [
                f for f in self._fragments
                if FLAG_ESSENTIAL in f.get("flags", [])
            ]
            self._log(f"Reset manteniendo {len(self._fragments)} fragmentos esenciales.")
        else:
            self._fragments = []
            self._log("Reset completo.")


# ══════════════════════════════════════════════════════════════════════════════
#  INTEGRACIÓN CON mistral2.py
#  Estas funciones son los puntos de enganche con el código existente
# ══════════════════════════════════════════════════════════════════════════════

# Instancia global (se inicializa desde mistral2.py)
_ctx_manager: MistralContextManager | None = None


def init_context_manager(
    mistral_client,
    mistral_model: str,
    token_limit: int = DEFAULT_TOKEN_LIMIT,
    verbose: bool = True
) -> MistralContextManager:
    """
    Llamar desde mistral2.py justo después de crear el cliente Mistral:

        import mistral_context as mctx
        mctx.init_context_manager(client, mistral_model)
    """
    global _ctx_manager
    _ctx_manager = MistralContextManager(
        mistral_client=mistral_client,
        mistral_model=mistral_model,
        token_limit=token_limit,
        verbose=verbose
    )
    print(f"  [CTX] MistralContextManager inicializado. Límite: {token_limit:,} tokens.")
    return _ctx_manager


def get_manager() -> MistralContextManager | None:
    return _ctx_manager


def ctx_add_user(text: str, key_ideas: list = None):
    if _ctx_manager:
        return _ctx_manager.add_user(text, key_ideas)

def ctx_add_ai(text: str, has_cro: bool = False):
    if _ctx_manager:
        return _ctx_manager.add_ai(text, has_cro)

def ctx_add_cro_instruction(text: str):
    if _ctx_manager:
        return _ctx_manager.add_cro_instruction(text)

def ctx_add_cro_output(text: str, relevant: bool = True):
    if _ctx_manager:
        return _ctx_manager.add_cro_output(text, relevant)

def ctx_add_system(text: str, essential: bool = True):
    if _ctx_manager:
        return _ctx_manager.add_system(text, essential)

def ctx_build_messages(system_prompt: str = None) -> list:
    """Devuelve la lista de mensajes para client.chat.complete()."""
    if _ctx_manager:
        return _ctx_manager.build_messages(system_prompt)
    return []

def ctx_status():
    if _ctx_manager:
        _ctx_manager.print_status()

def ctx_list():
    if _ctx_manager:
        _ctx_manager.list_fragments()

def ctx_compress():
    if _ctx_manager:
        return _ctx_manager.compress_context()

def ctx_reset(keep_essential: bool = True):
    if _ctx_manager:
        _ctx_manager.reset(keep_essential)

def ctx_export(path: str = "com/datas/context_export.json"):
    if _ctx_manager:
        _ctx_manager.export_json(path)

def ctx_import(path: str):
    if _ctx_manager:
        return _ctx_manager.import_json(path)


# ══════════════════════════════════════════════════════════════════════════════
#  PARCHE PARA generate_response en mistral2.py
#  Sustituye la llamada directa a client.chat.complete() usando el gestor
# ══════════════════════════════════════════════════════════════════════════════

def patched_generate_response(
    user_input: str,
    client,
    mistral_model: str,
    conversation_context_ref: list,   # lista mutable [str] para compatibilidad
    mode: str = ""
) -> str | None:
    """
    Versión mejorada de generate_response() que usa el gestor de contexto.
    
    Uso en mistral2.py — reemplazar el cuerpo de generate_response() con:

        from mistral_context import patched_generate_response
        def generate_response(user_input, mode=""):
            global conversation_context, last_response, client, mistral_model
            result = patched_generate_response(
                user_input, client, mistral_model,
                [conversation_context], mode
            )
            if result and result != "EXIT_LR":
                last_response = result
                conversation_context = conversation_context_ref[0]  # sync
            return result
    """
    global _ctx_manager

    # Detectar si la respuesta contiene CRO
    has_cro = False

    # Añadir input del usuario
    if _ctx_manager:
        _ctx_manager.add_user(user_input)

    # Construir mensajes con el gestor
    if _ctx_manager:
        messages = _ctx_manager.build_messages()
    else:
        messages = [{"role": "user", "content": user_input}]

    try:
        response = client.chat.complete(model=mistral_model, messages=messages)
        response_text = response.choices[0].message.content

        # Detectar CRO en la respuesta
        has_cro = bool(re.search(r"```CRO", response_text))

        # Registrar respuesta
        if _ctx_manager:
            _ctx_manager.add_ai(response_text, has_cro=has_cro)

        # Sincronizar conversation_context legacy (string)
        if conversation_context_ref:
            conversation_context_ref[0] += f"\nUser: {user_input}\nAI: {response_text}\n"

        if mode != "nolastresponse":
            return response_text
        else:
            return "EXIT_LR"

    except Exception as e:
        print(f"Error generando contenido: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n── TEST mistral_context.py (sin cliente real) ──\n")

    mgr = MistralContextManager(mistral_client=None, token_limit=2000, verbose=True)

    # Simular arranque
    mgr.add_system("Sistema OSIRIS v2 iniciado. Idioma: Español.", essential=True)
    mgr.add_cro_instruction("CROMode activo. Parsea bloques ```CRO en tus respuestas.")
    mgr.add_cro_instruction("Regla: siempre confirmar antes de ejecutar WRITE_FILE.")

    # Simular conversación
    mgr.add_user("Lista el contenido de /tmp")
    mgr.add_ai("Claro, voy a listar /tmp:\n```CRO\nLOCAL_FS_* LIST_DIRECTORY\nPATH=\"/tmp\"\n```", has_cro=True)
    mgr.add_cro_output("archivo1.txt  1024B\nscript.sh  2048B\ntemp_data/  DIR", relevant=True)

    mgr.add_user("¿Qué hay en temp_data?")
    mgr.add_ai("Analizando temp_data…\n```CRO\nLOCAL_FS_* LIST_DIRECTORY\nPATH=\"/tmp/temp_data\"\n```", has_cro=True)
    mgr.add_cro_output("cache.bin  512B\nold_log.txt  8192B", relevant=False)  # irrelevante

    # Añadir bastante contenido para simular presión de tokens
    for i in range(10):
        mgr.add_user(f"Pregunta de relleno número {i} sobre el sistema")
        mgr.add_ai(f"Respuesta de relleno número {i}. Todo funciona correctamente en el sistema.")

    print("\n── Estado antes de comprimir ──")
    mgr.print_status()

    print("\n── Lista de fragmentos ──")
    mgr.list_fragments()

    print("\n── Mensajes generados para la API ──")
    msgs = mgr.build_messages(system_prompt="Eres Osiris, asistente AI.")
    for m in msgs:
        role = m["role"]
        snippet = m["content"][:80].replace("\n", " ")
        print(f"  [{role:>9}] {snippet}…")

    print("\n── Comprimir (sin cliente → solo purga) ──")
    mgr.compress_context(target_ratio=0.4)
    mgr.print_status()

    print("\n── Exportar JSON ──")
    mgr.export_json("/tmp/osiris_ctx_test.json")
    print("\nTest completado ✅\n")