"""Gemini service — genera recomendaciones clínicas vía Google Gemini API REST."""

import json
import time
from typing import Optional

import httpx

from app.core.config import settings

_SLUGS_DISPONIBLES = [
    "control_prenatal_rutinario",
    "seguimiento_estrecho_lc",
    "progesterona_vaginal",
    "tratar_infeccion",
    "vigilancia_hta_multiple",
    "derivacion_alto_riesgo",
]

_PROMPT_TEMPLATE = """Eres un obstetra experto en prevención de parto prematuro.
Basado en los siguientes datos clínicos de una paciente gestante, genera UNA recomendación clínica específica y personalizada.

DATOS DE LA PACIENTE:
- Probabilidad de parto prematuro (consenso): {prob_prematuro}%
- Nivel de urgencia (triaje): {nivel_urgencia}
- Parto prematuro previo: {parto_prematuro_previo}
- Número de condiciones crónicas: {num_condiciones_cronicas}
- IMC (BMI): {bmi}
- Longitud cervical: {longitud_cervical_mm} mm
- Infecciones activas: {infeccion_activa}
- Embarazo múltiple: {embarazo_multiple}

CRITERIOS ESTRICTOS PARA ELEGIR EL SLUG (usa el PRIMERO que coincida):
1. "derivacion_alto_riesgo" → SOLO si prob_prematuro >= 60% O nivel_urgencia es ROJO
2. "tratar_infeccion" → SOLO si infeccion_activa = Sí
3. "progesterona_vaginal" → SOLO si parto_prematuro_previo = Sí Y longitud_cervical < 25mm
4. "seguimiento_estrecho_lc" → SOLO si longitud_cervical < 25mm O (longitud_cervical < 30mm Y prob_prematuro >= 30%)
5. "vigilancia_hta_multiple" → SOLO si hipertensión gestacional O embarazo múltiple O condiciones_cronicas >= 3 O nivel_urgencia NARANJA
6. "control_prenatal_rutinario" → para cualquier otro caso (bajo riesgo)

Responde ÚNICAMENTE con un JSON válido (sin markdown, sin bloques ```) con esta estructura:
{{"recomendacion": "<slug>", "titulo": "<título corto>", "descripcion": "<explicación detallada, máximo 3 párrafos>"}}"""


class GeminiService:

    @staticmethod
    def _reintentar(
        url: str, body: dict, max_intentos: int = 3, timeout: int = 30
    ) -> dict:
        for intento in range(1, max_intentos + 1):
            try:
                response = httpx.post(url, json=body, timeout=timeout)
                if response.status_code == 429 and intento < max_intentos:
                    espera = 2 ** intento
                    time.sleep(espera)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                if intento < max_intentos:
                    time.sleep(2 ** intento)
                    continue
                raise
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and intento < max_intentos:
                    time.sleep(2 ** intento)
                    continue
                raise
        raise httpx.HTTPStatusError(
            f"Gemini no respondió tras {max_intentos} intentos",
            request=None, response=None,
        )

    @staticmethod
    def generar_recomendacion(
        *,
        prob_prematuro: Optional[float] = None,
        nivel_urgencia: str = "VERDE",
        parto_prematuro_previo: bool = False,
        num_condiciones_cronicas: int = 0,
        bmi: Optional[float] = None,
        longitud_cervical_mm: Optional[float] = None,
        infeccion_activa: bool = False,
        embarazo_multiple: bool = False,
    ) -> dict:
        api_key = settings.GEMINI_APIKEY
        if not api_key:
            raise ValueError(
                "GEMINI_APIKEY no configurada. "
                "Agrega GEMINI_APIKEY=tu_api_key en el archivo .env"
            )

        prompt = _PROMPT_TEMPLATE.format(
            prob_prematuro=round(prob_prematuro * 100, 1) if prob_prematuro is not None else "N/A",
            nivel_urgencia=nivel_urgencia.upper() if nivel_urgencia else "VERDE",
            parto_prematuro_previo="Sí" if parto_prematuro_previo else "No",
            num_condiciones_cronicas=num_condiciones_cronicas,
            bmi=f"{bmi:.1f}" if bmi is not None else "N/A",
            longitud_cervical_mm=f"{longitud_cervical_mm:.1f}" if longitud_cervical_mm is not None else "N/A",
            infeccion_activa="Sí" if infeccion_activa else "No",
            embarazo_multiple="Sí" if embarazo_multiple else "No",
        )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={api_key}"
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            },
        }

        data = GeminiService._reintentar(url, body)

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini no devolvió candidatos en la respuesta.")

        texto = candidates[0]["content"]["parts"][0]["text"].strip()
        if texto.startswith("```"):
            texto = texto.split("\n", 1)[-1]
            if "```" in texto:
                texto = texto.rsplit("```", 1)[0]
        texto = texto.strip()

        try:
            resultado = json.loads(texto)
        except json.JSONDecodeError:
            raise ValueError(
                f"Gemini respondió con JSON inválido: {texto[:200]}"
            )

        slug = resultado.get("recomendacion", "control_prenatal_rutinario")
        if slug not in _SLUGS_DISPONIBLES:
            slug = "control_prenatal_rutinario"

        return {
            "recomendacion": slug,
            "titulo": resultado.get("titulo", "Recomendación clínica"),
            "descripcion": resultado.get("descripcion", ""),
        }
