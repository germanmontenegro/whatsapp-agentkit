# agent/tools.py — Herramientas del agente
# Generado por AgentKit

"""
Herramientas específicas del negocio Lavadero PITA.
Estas funciones extienden las capacidades del agente más allá de responder texto.
Casos de uso: FAQ, agendar turnos, leads/ventas, informar cierres por mal tiempo.
"""

import os
import yaml
import json
import logging
from datetime import datetime

logger = logging.getLogger("agentkit")

# Archivos de datos locales (se crean automáticamente)
TURNOS_FILE = "config/turnos.json"
LEADS_FILE = "config/leads.json"
ESTADO_FILE = "config/estado_negocio.json"


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_horario() -> dict:
    """Retorna el horario de atención del negocio."""
    info = cargar_info_negocio()
    return {
        "horario": info.get("negocio", {}).get("horario", "No disponible"),
        "esta_abierto": True,  # TODO: calcular según hora actual y horario
    }


def buscar_en_knowledge(consulta: str) -> str:
    """
    Busca información relevante en los archivos de /knowledge.
    Retorna el contenido más relevante encontrado.
    """
    resultados = []
    knowledge_dir = "knowledge"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                # Búsqueda simple por coincidencia de texto
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."


# ════════════════════════════════════════════════════════════
# Utilidad interna para leer/escribir archivos JSON simples
# ════════════════════════════════════════════════════════════

def _leer_json(ruta: str, default):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _escribir_json(ruta: str, data):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════
# AGENDAR TURNOS
# ════════════════════════════════════════════════════════════

def reservar_turno(telefono: str, fecha: str, hora: str, vehiculo: str, servicio: str) -> dict:
    """
    Registra un turno de atención.

    Args:
        telefono: Número del cliente
        fecha: Fecha del turno (ej: "2026-07-01")
        hora: Hora del turno (ej: "10:00")
        vehiculo: Tipo de vehículo (moto / auto / camioneta)
        servicio: Servicio solicitado (lavado simple, encerado, gomería, etc.)

    Returns:
        dict con los datos del turno registrado
    """
    turnos = _leer_json(TURNOS_FILE, [])
    turno = {
        "id": len(turnos) + 1,
        "telefono": telefono,
        "fecha": fecha,
        "hora": hora,
        "vehiculo": vehiculo,
        "servicio": servicio,
        "estado": "confirmado",
        "creado": datetime.utcnow().isoformat(),
    }
    turnos.append(turno)
    _escribir_json(TURNOS_FILE, turnos)
    logger.info(f"Turno reservado: {turno}")
    return turno


def listar_turnos(telefono: str) -> list[dict]:
    """Lista los turnos de un cliente."""
    turnos = _leer_json(TURNOS_FILE, [])
    return [t for t in turnos if t.get("telefono") == telefono]


def cancelar_turno(turno_id: int) -> bool:
    """Cancela un turno por su ID."""
    turnos = _leer_json(TURNOS_FILE, [])
    for t in turnos:
        if t.get("id") == turno_id:
            t["estado"] = "cancelado"
            _escribir_json(TURNOS_FILE, turnos)
            return True
    return False


# ════════════════════════════════════════════════════════════
# LEADS / VENTAS
# ════════════════════════════════════════════════════════════

def registrar_lead(telefono: str, nombre: str = "", interes: str = "") -> dict:
    """
    Registra un lead/interesado (ej: consulta por cubiertas o servicios).

    Args:
        telefono: Número del cliente
        nombre: Nombre del cliente (si lo dio)
        interes: Qué le interesa (ej: "cubiertas para camioneta", "encerado")
    """
    leads = _leer_json(LEADS_FILE, [])
    lead = {
        "id": len(leads) + 1,
        "telefono": telefono,
        "nombre": nombre,
        "interes": interes,
        "creado": datetime.utcnow().isoformat(),
    }
    leads.append(lead)
    _escribir_json(LEADS_FILE, leads)
    logger.info(f"Lead registrado: {lead}")
    return lead


# ════════════════════════════════════════════════════════════
# CIERRE POR MAL TIEMPO
# ════════════════════════════════════════════════════════════

def marcar_cierre_por_clima(activo: bool, motivo: str = "Cerrado por mal tiempo") -> dict:
    """
    Activa o desactiva el aviso de cierre por mal tiempo.
    El equipo del negocio usa esto para informar a los clientes.
    """
    estado = {"cerrado_por_clima": activo, "motivo": motivo,
              "actualizado": datetime.utcnow().isoformat()}
    _escribir_json(ESTADO_FILE, estado)
    return estado


def estado_negocio() -> dict:
    """Retorna el estado actual del negocio (abierto / cerrado por clima)."""
    return _leer_json(ESTADO_FILE, {"cerrado_por_clima": False, "motivo": ""})
