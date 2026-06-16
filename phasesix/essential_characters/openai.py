import json
import logging

from django.conf import settings
from openai import OpenAI

from plots.openai import PlotOpenAIService

logger = logging.getLogger(__name__)


def translate_custom_mark(values):
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not configured.")

    prompt = (
        "You are translating custom tabletop RPG content. Detect whether "
        "the supplied values are German or English, then return every value in both "
        "languages. Preserve meaning, tone, comma-separated skill lists, and empty "
        "values. Return ONLY strict JSON with this schema: "
        '{"de": {"field": "..."}, "en": {"field": "..."}}. '
        "Use exactly the supplied field keys in both language objects.\n\n"
        f"{json.dumps(values, ensure_ascii=False)}"
    )
    logger.info(
        "OpenAI essential mark translation request model=%s fields=%s",
        settings.OPENAI_TRANSLATION_MODEL,
        list(values),
    )
    response = OpenAI(api_key=settings.OPENAI_API_KEY).responses.create(
        model=settings.OPENAI_TRANSLATION_MODEL,
        input=prompt,
    )
    output_text = getattr(response, "output_text", None)
    if not output_text and getattr(response, "output", None):
        output_text = response.output[0].content[0].text
    result = PlotOpenAIService._parse_json_response(output_text or "")
    if not isinstance(result.get("de"), dict) or not isinstance(result.get("en"), dict):
        raise ValueError("OpenAI did not return both languages.")
    return result


def translate_skill_names(names):
    def fallback():
        return [{"de": name[:160], "en": name[:160]} for name in names]

    if not settings.OPENAI_API_KEY:
        return fallback()

    prompt = (
        "Translate these tabletop RPG skill names. Detect whether each name is German "
        "or English and return every name in both languages. Keep names short and "
        "preserve their order. Return ONLY strict JSON with this schema: "
        '{"skills": [{"de": "...", "en": "..."}]}.\n\n'
        f"{json.dumps(names, ensure_ascii=False)}"
    )
    logger.info(
        "OpenAI essential skill translation request model=%s count=%s",
        settings.OPENAI_TRANSLATION_MODEL,
        len(names),
    )
    try:
        response = OpenAI(api_key=settings.OPENAI_API_KEY).responses.create(
            model=settings.OPENAI_TRANSLATION_MODEL,
            input=prompt,
        )
        output_text = getattr(response, "output_text", None)
        if not output_text and getattr(response, "output", None):
            output_text = response.output[0].content[0].text
        result = PlotOpenAIService._parse_json_response(output_text or "")
        skills = result.get("skills")
        if not isinstance(skills, list) or len(skills) != len(names):
            raise ValueError("OpenAI returned an invalid skill translation count.")
        translated = [
            {
                "de": (skill.get("de") or name)[:160],
                "en": (skill.get("en") or name)[:160],
            }
            for name, skill in zip(names, skills)
        ]
        for language in ("de", "en"):
            localized_names = [skill[language].casefold() for skill in translated]
            if len(set(localized_names)) != len(localized_names):
                for skill, name in zip(translated, names):
                    skill[language] = name[:160]
        return translated
    except Exception:
        logger.exception("OpenAI essential skill translation failed")
        return fallback()
