"""Coleta de métricas simples de sistema e GPU para exibição no frontend."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

try:
    import psutil
except Exception:  # pragma: no cover - fallback quando psutil não estiver disponível.
    psutil = None


def _format_bytes(total_bytes: int | float | None) -> str:
    if total_bytes is None:
        return "indisponível"

    value = float(total_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    return f"{value:.1f} {unit}"


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"n/a", "not supported", "unknown", "[not supported]"}:
        return None
    try:
        return round(float(text), 1)
    except (TypeError, ValueError):
        return None


def _to_int(value: str | None) -> int | None:
    number = _to_float(value)
    return int(number) if number is not None else None


def _read_gpu_metrics() -> dict[str, Any]:
    visible_devices = os.getenv("CUDA_VISIBLE_DEVICES") or os.getenv("NVIDIA_VISIBLE_DEVICES")
    smi_cmd = shutil.which("nvidia-smi")

    if smi_cmd:
        try:
            result = subprocess.run(
                [
                    smi_cmd,
                    "--query-gpu=name,utilization.gpu,memory.total,memory.used,temperature.gpu,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                first_line = next((line for line in result.stdout.splitlines() if line.strip()), "")
                if first_line:
                    parts = [part.strip() for part in first_line.split(",")]
                    name = parts[0] if len(parts) > 0 else "GPU NVIDIA"
                    usage_percent = _to_float(parts[1] if len(parts) > 1 else None)
                    mem_total_mib = _to_float(parts[2] if len(parts) > 2 else None)
                    mem_used_mib = _to_float(parts[3] if len(parts) > 3 else None)
                    temp_c = _to_float(parts[4] if len(parts) > 4 else None)
                    driver = parts[5] if len(parts) > 5 else "indisponível"
                    return {
                        "disponivel": True,
                        "nome": name,
                        "uso_percentual": usage_percent,
                        "memoria_total": _format_bytes((mem_total_mib or 0) * 1024 * 1024),
                        "memoria_usada": _format_bytes((mem_used_mib or 0) * 1024 * 1024),
                        "temperatura_c": temp_c,
                        "driver": driver,
                        "mensagem": "GPU detectada e pronta para acelerar a IA.",
                    }
        except Exception:
            pass

    fallback_name = os.getenv("ROSITA_GPU_NAME")
    if visible_devices and str(visible_devices).strip().lower() not in {"none", "void", ""}:
        return {
            "disponivel": True,
            "nome": fallback_name or f"GPU exposta ao container ({visible_devices})",
            "uso_percentual": None,
            "memoria_total": "indisponível",
            "memoria_usada": "indisponível",
            "temperatura_c": None,
            "driver": "indisponível",
            "mensagem": "GPU visível para a aplicação, mas sem leitura detalhada do driver.",
        }

    return {
        "disponivel": False,
        "nome": fallback_name or "não detectada",
        "uso_percentual": None,
        "memoria_total": "indisponível",
        "memoria_usada": "indisponível",
        "temperatura_c": None,
        "driver": "indisponível",
        "mensagem": "GPU não detectada para uso com o modelo; o Ollama tende a usar CPU neste host.",
    }


def get_system_snapshot() -> dict[str, Any]:
    cpu_model = platform.processor() or platform.machine() or "indisponível"
    hostname = socket.gethostname()
    platform_name = f"{platform.system()} {platform.release()}".strip()

    cpu_usage = None
    logical_cores = os.cpu_count() or 0
    physical_cores = None
    memory_total = None
    memory_used = None
    memory_available = None
    memory_percent = None
    disk_total = None
    disk_used = None
    disk_free = None
    disk_percent = None

    if psutil is not None:
        try:
            cpu_usage = round(psutil.cpu_percent(interval=0.1), 1)
        except Exception:
            cpu_usage = None

        try:
            physical_cores = psutil.cpu_count(logical=False)
        except Exception:
            physical_cores = None

        try:
            memory = psutil.virtual_memory()
            memory_total = memory.total
            memory_used = memory.used
            memory_available = memory.available
            memory_percent = round(memory.percent, 1)
        except Exception:
            pass

        try:
            disk = psutil.disk_usage(str(Path.cwd().anchor or "/"))
            disk_total = disk.total
            disk_used = disk.used
            disk_free = disk.free
            disk_percent = round(disk.percent, 1)
        except Exception:
            pass

    gpu = _read_gpu_metrics()

    return {
        "hostname": hostname,
        "plataforma": platform_name,
        "cpu": {
            "modelo": cpu_model,
            "nucleos_logicos": logical_cores,
            "nucleos_fisicos": physical_cores,
            "uso_percentual": cpu_usage,
        },
        "memoria": {
            "total": _format_bytes(memory_total),
            "usada": _format_bytes(memory_used),
            "disponivel": _format_bytes(memory_available),
            "percentual": memory_percent,
        },
        "disco": {
            "total": _format_bytes(disk_total),
            "usado": _format_bytes(disk_used),
            "livre": _format_bytes(disk_free),
            "percentual": disk_percent,
        },
        "gpu": gpu,
        "ia": {
            "usa_gpu": bool(gpu.get("disponivel")),
            "mensagem": gpu.get("mensagem"),
        },
    }
