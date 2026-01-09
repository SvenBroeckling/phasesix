import json
import logging
import re
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from openai import OpenAI

from plots.models import PlotElement, Handout, Location

logger = logging.getLogger(__name__)


class PlotOpenAIService:
    def __init__(self, plot):
        self.plot = plot

    @staticmethod
    def _parse_json_response(text):
        def extract_json_payload(raw_text):
            fenced_match = re.search(r"```(?:json)?\s*(.*?)```", raw_text, re.DOTALL)
            if fenced_match:
                raw_text = fenced_match.group(1)
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            return raw_text[start : end + 1]

        def remove_trailing_commas(raw_text):
            return re.sub(r",\s*([}\]])", r"\1", raw_text)

        payload = extract_json_payload(text)
        if not payload:
            raise ValueError("Invalid JSON response")

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            cleaned = remove_trailing_commas(payload)
            return json.loads(cleaned)

    def _client(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured.")
        return OpenAI(api_key=settings.OPENAI_API_KEY)

    def _model(self):
        return getattr(settings, "OPENAI_PLOT_MODEL", settings.OPENAI_TRANSLATION_MODEL)

    def _plot_context(self, language=None):
        extensions = [ext.name for ext in self.plot.extensions.all()]
        return {
            "name": self.plot.name,
            "language": language or self.plot.language,
            "epoch": getattr(self.plot.epoch_extension, "name", None),
            "world": getattr(self.plot.world_extension, "name", None),
            "extensions": extensions,
        }

    def _language_hint(self, language):
        if language == "de":
            return "German (de)"
        return "English (en)"

    def _structure_prompt(self, description, language=None):
        context = json.dumps(self._plot_context(language=language), ensure_ascii=False)
        language_hint = self._language_hint(language)
        return (
            "You are an RPG plot assistant. Split the provided plot description into a structured outline. "
            "Return ONLY a JSON object. Create all content in the requested language.\n"
            f"Requested language: {language_hint}.\n"
            "No code fences, no comments, no trailing commas.\n\n"
            "Requirements:\n"
            "- Create meaningful plot elements with clear names.\n"
            "- Provide a stable ref for each element (e.g., e1, e2) and use parent_ref for hierarchy.\n"
            "- Include handouts and locations per element when appropriate; each must have name and description.\n"
            "- Keep handouts/locations concise and text-only (no images).\n"
            "- Target 5-15 elements unless the input is very small.\n\n"
            "Return JSON with this schema:\n"
            "{\n"
            '  "elements": [\n'
            "    {\n"
            '      "ref": "e1",\n'
            '      "name": "Element name",\n'
            '      "parent_ref": null,\n'
            '      "summary": "short purpose/role",\n'
            '      "handouts": [{"name": "...", "description": "..."}],\n'
            '      "locations": [{"name": "...", "description": "..."}]\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Plot context:\n"
            f"{context}\n\n"
            "Plot description:\n"
            f"{description}"
        )

    def _element_descriptions_prompt(self, description, elements, language=None):
        context = json.dumps(self._plot_context(language=language), ensure_ascii=False)
        language_hint = self._language_hint(language)
        elements_payload = [
            {
                "ref": element.get("ref"),
                "name": element.get("name"),
                "parent_ref": element.get("parent_ref"),
                "summary": element.get("summary"),
            }
            for element in elements
        ]
        return (
            "You are an RPG plot assistant. Write GM notes and player summaries for each element. "
            "Return ONLY a JSON object. Create all content in the requested language.\n"
            f"Requested language: {language_hint}.\n"
            "No code fences, no comments, no trailing commas.\n\n"
            "Guidelines:\n"
            "- gm_notes: detailed, for the game master (secrets allowed).\n"
            "- player_summary: an introduction to the scene for players, which a gm could read out loudly. Atmospheric and engaging.\n"
            "- Keep each to a few short paragraphs.\n\n"
            "Return JSON with this schema:\n"
            "{\n"
            '  "elements": [\n'
            "    {\n"
            '      "ref": "e1",\n'
            '      "gm_notes": "...",\n'
            '      "player_summary": "..."\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Plot context:\n"
            f"{context}\n\n"
            "Plot description:\n"
            f"{description}\n\n"
            "Elements:\n"
            f"{json.dumps(elements_payload, ensure_ascii=False)}"
        )

    def _openai_json(self, prompt, attempt_repair=True):
        client = self._client()
        model = self._model()
        logger.info("OpenAI plot request model=%s prompt_length=%s", model, len(prompt))
        try:
            response = client.responses.create(
                model=model,
                input=prompt,
                response_format={"type": "json_object"},
            )
        except TypeError:
            logger.warning(
                "OpenAI response_format json_object not supported by SDK, retrying plain text"
            )
            response = client.responses.create(
                model=model,
                input=prompt,
            )
        except Exception:
            logger.exception(
                "OpenAI response_format json_object failed, retrying plain text"
            )
            response = client.responses.create(
                model=model,
                input=prompt,
            )
        output_text = getattr(response, "output_text", None)
        if not output_text and getattr(response, "output", None):
            output_text = response.output[0].content[0].text
        logger.info(
            "OpenAI plot response received model=%s output_length=%s",
            model,
            len(output_text or ""),
        )
        try:
            return self._parse_json_response(output_text or "")
        except Exception:
            if not attempt_repair:
                raise
            logger.exception("OpenAI JSON parse failed, attempting single repair")
            repair_prompt = (
                "Fix the JSON so it is valid strict JSON and matches the same structure. "
                "Return ONLY the corrected JSON object. No code fences, no comments.\n\n"
                f"{output_text}"
            )
            return self._openai_json(repair_prompt, attempt_repair=False)

    def _existing_attachment_cache(self, model):
        cache = {}
        if model is Handout:
            qs = Handout.objects.filter(plotelement__plot=self.plot).distinct()
        else:
            qs = Location.objects.filter(plotelement__plot=self.plot).distinct()
        for obj in qs:
            key = (obj.name.strip().lower(), obj.description.strip().lower())
            cache[key] = obj
        return cache

    def _create_or_get_attachment(self, model, cache, payload):
        name = (payload.get("name") or "").strip()
        description = (payload.get("description") or "").strip()
        if not name or not description:
            return None
        key = (name.lower(), description.lower())
        if key in cache:
            return cache[key]
        obj = model.objects.create(name=name, description=description)
        cache[key] = obj
        return obj

    def create_from_description(self, description, language=None):
        structure = self._openai_json(
            self._structure_prompt(description, language=language)
        )
        elements_payload = structure.get("elements", [])
        if not isinstance(elements_payload, list) or not elements_payload:
            raise ValueError("OpenAI did not return any plot elements.")

        handout_cache = self._existing_attachment_cache(Handout)
        location_cache = self._existing_attachment_cache(Location)

        created_elements = {}
        ordering_counter = defaultdict(int)

        def create_element(payload, parent_obj):
            ref = payload.get("ref")
            name = (payload.get("name") or "").strip() or "Untitled"
            ordering = ordering_counter[parent_obj.pk if parent_obj else None]
            ordering_counter[parent_obj.pk if parent_obj else None] += 1
            element = PlotElement.objects.create(
                plot=self.plot,
                parent=parent_obj,
                name=name,
                ordering=ordering,
            )
            if ref:
                created_elements[ref] = element
            return element

        pending = list(elements_payload)
        with transaction.atomic():
            while pending:
                progressed = False
                for payload in pending[:]:
                    parent_ref = payload.get("parent_ref")
                    if parent_ref:
                        parent_obj = created_elements.get(parent_ref)
                        if not parent_obj:
                            continue
                    else:
                        parent_obj = None
                    element = create_element(payload, parent_obj)
                    pending.remove(payload)
                    progressed = True

                    for handout_payload in payload.get("handouts", []) or []:
                        handout = self._create_or_get_attachment(
                            Handout, handout_cache, handout_payload
                        )
                        if handout:
                            element.handouts.add(handout)

                    for location_payload in payload.get("locations", []) or []:
                        location = self._create_or_get_attachment(
                            Location, location_cache, location_payload
                        )
                        if location:
                            element.locations.add(location)

                if not progressed:
                    for payload in pending:
                        element = create_element(payload, None)
                        for handout_payload in payload.get("handouts", []) or []:
                            handout = self._create_or_get_attachment(
                                Handout, handout_cache, handout_payload
                            )
                            if handout:
                                element.handouts.add(handout)
                        for location_payload in payload.get("locations", []) or []:
                            location = self._create_or_get_attachment(
                                Location, location_cache, location_payload
                            )
                            if location:
                                element.locations.add(location)
                    break

        try:
            descriptions = self._openai_json(
                self._element_descriptions_prompt(
                    description, elements_payload, language=language
                )
            )
        except Exception:
            logger.exception("OpenAI plot description generation failed")
            return created_elements

        updates = descriptions.get("elements", [])
        if not isinstance(updates, list):
            return created_elements

        for update in updates:
            ref = update.get("ref")
            element = created_elements.get(ref)
            if not element:
                continue
            gm_notes = (update.get("gm_notes") or "").strip()
            player_summary = (update.get("player_summary") or "").strip()
            if gm_notes or player_summary:
                element.gm_notes = gm_notes or element.gm_notes
                element.player_summary = player_summary or element.player_summary
                element.save(update_fields=["gm_notes", "player_summary"])

        return created_elements
