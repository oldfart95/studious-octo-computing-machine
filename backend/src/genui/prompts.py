from __future__ import annotations

from .models import GenerationParameters, GenerationRequest
from .storage import get_preset, get_style_block


def _merge_parameters(request_params: GenerationParameters, preset_params: GenerationParameters) -> GenerationParameters:
    if request_params.model_dump() == GenerationParameters().model_dump():
        return preset_params
    return request_params


def merge_request_with_preset(request: GenerationRequest) -> GenerationRequest:
    if not request.preset:
        return request

    preset = get_preset(request.preset)
    if not preset:
        return request

    merged = request.model_copy(deep=True)
    merged.workflow_mode = request.workflow_mode or preset.workflow_mode
    merged.checkpoint = request.checkpoint or preset.checkpoint
    merged.negative_prompt = request.negative_prompt or preset.negative_prompt
    merged.style_prompt = "\n".join(filter(None, [preset.style_prompt, request.style_prompt]))
    merged.locked_style_blocks = list(
        dict.fromkeys([*preset.locked_style_blocks, *request.locked_style_blocks])
    )
    merged.parameters = _merge_parameters(request.parameters, preset.parameters)
    merged.metadata = {**preset.model_dump(mode="json"), **request.metadata}
    merged.metadata["positive_prefix"] = preset.positive_prefix
    merged.loras = request.loras or [
        item if not isinstance(item, str) else {"name": item}
        for item in preset.loras
    ]
    return merged


def compile_prompts(request: GenerationRequest) -> tuple[str, str]:
    working = merge_request_with_preset(request)
    positive_parts = []
    preset_prefix = working.metadata.get("positive_prefix", "")
    if preset_prefix:
        positive_parts.append(str(preset_prefix).strip())
    if working.prompt:
        positive_parts.append(working.prompt.strip())
    if working.style_prompt:
        positive_parts.append(working.style_prompt.strip())
    for block_name in working.locked_style_blocks:
        block = get_style_block(block_name)
        if block:
            positive_parts.append(block.prompt.strip())
    negative_parts = [working.negative_prompt.strip()] if working.negative_prompt else []
    return ", ".join([part for part in positive_parts if part]), ", ".join(
        [part for part in negative_parts if part]
    )
