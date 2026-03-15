import asyncio
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from postable_ia.agent import root_agent
from postable_ia.tools import generate_image, resolve_image_ref, _IMG_REF_PREFIX
from schema.request import GenerateRequest

logger = logging.getLogger(__name__)
router = APIRouter()

_TOOL_STEPS = {
    "fetch_trends": ("fetching_trends", "Buscando tendências..."),
    "generate_image": ("generating_image", "Gerando imagem..."),
}


def _step_for_tool(name: str) -> tuple[str, str] | None:
    if name in _TOOL_STEPS:
        return _TOOL_STEPS[name]
    if "search" in name.lower():
        return ("analyzing_competitors", "Analisando concorrentes...")
    return None


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/generate")
async def generate(request: GenerateRequest):
    async def stream():
        try:
            session_service = InMemorySessionService()
            session = await session_service.create_session(
                app_name="postable_ia", user_id="api"
            )
            runner = Runner(
                agent=root_agent,
                app_name="postable_ia",
                session_service=session_service,
            )
            user_message = Content(
                role="user",
                parts=[Part(text=request.model_dump_json())],
            )

            emitted_steps: set[str] = set()
            final_response = None

            async for event in runner.run_async(
                user_id="api",
                session_id=session.id,
                new_message=user_message,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        fc = getattr(part, "function_call", None)
                        if fc:
                            mapped = _step_for_tool(fc.name)
                            if mapped and mapped[0] not in emitted_steps:
                                emitted_steps.add(mapped[0])
                                yield _sse({"event": "status", "step": mapped[0], "message": mapped[1]})

                if event.is_final_response():
                    if event.content and event.content.parts and event.content.parts[0].text:
                        final_response = event.content.parts[0].text
                    break

            if not final_response:
                yield _sse({"event": "error", "message": "Agent produced no response"})
                yield _sse({"event": "done"})
                return

            text = final_response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            # Extract the JSON object by finding its boundaries
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]
            if not text:
                yield _sse({"event": "error", "message": "Agent produced empty JSON response"})
                yield _sse({"event": "done"})
                return
            try:
                data = json.loads(text)
            except json.JSONDecodeError as parse_err:
                logger.warning("json.loads failed (%s), attempting json_repair", parse_err)
                try:
                    from json_repair import repair_json
                    repaired = repair_json(text)
                    if not repaired:
                        raise ValueError("json_repair returned empty string")
                    data = json.loads(repaired)
                except Exception as repair_err:
                    logger.error("json_repair also failed: %s | original text: %.200s", repair_err, text)
                    yield _sse({"event": "error", "message": f"Could not parse agent response: {parse_err}"})
                    yield _sse({"event": "done"})
                    return
            # Resolve image ref — the tool stored the real base64 out-of-band
            # so the LLM never had to repeat a ~1 MB string in its text output.
            ref = data.get("image_base64", "")
            if ref.startswith(_IMG_REF_PREFIX):
                stored = resolve_image_ref(ref)
                if stored:
                    data["image_base64"] = stored["image_base64"]
                    data["image_mime_type"] = stored["image_mime_type"]
                    logger.info("Resolved image ref %s: mime=%s b64_len=%d", ref, stored["image_mime_type"], len(stored["image_base64"]))
                else:
                    logger.error("Image ref %s not found in store", ref)
            else:
                # Agent skipped the generate_image tool — call it directly.
                logger.info("Agent did not call generate_image; triggering fallback image generation")
                yield _sse({"event": "status", "step": "generating_image", "message": "Gerando imagem..."})
                bp = request.business_profile
                post_text = data.get("post_text", "")
                image_prompt = (
                    f"{bp.niche} in {bp.city}, {bp.state}. "
                    f"Brand: {bp.brand_identity}. "
                    f"Post theme: {post_text[:200]}"
                )
                loop = asyncio.get_event_loop()
                img_result = await loop.run_in_executor(
                    None, lambda: generate_image(image_prompt)
                )
                img_ref = img_result.get("image_base64", "")
                if img_ref.startswith(_IMG_REF_PREFIX):
                    stored = resolve_image_ref(img_ref)
                    if stored:
                        data["image_base64"] = stored["image_base64"]
                        data["image_mime_type"] = stored["image_mime_type"]
                        logger.info("Fallback image generated: mime=%s b64_len=%d", stored["image_mime_type"], len(stored["image_base64"]))

            yield _sse({"event": "result", **data})
            yield _sse({"event": "done"})

        except Exception as e:
            yield _sse({"event": "error", "message": str(e)})
            yield _sse({"event": "done"})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
