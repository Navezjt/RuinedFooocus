import torch
from clip_interrogator import Config, Interrogator
from PIL import Image
import json
from shared import state, path_manager
from transformers import AutoProcessor, AutoModelForCausalLM 
from modules.util import TimeIt

import os
from transformers.dynamic_module_utils import get_imports
from unittest.mock import patch

def look(image, prompt, gr):
    if prompt.strip() == "clip:":
        text = clip_look(image, prompt, gr)
    elif prompt.strip() == "florence:":
        text = florence_look(image, prompt, gr)
    else:
        if prompt != "":
            return prompt

        try:
            info = image.info
            params = info.get("parameters", "")
            text = json.dumps(json.loads(params))
        except:
            # Default interrogator
            text = florence_look(image, prompt, gr)

    return text

def clip_look(image, prompt, gr):
    text = "Lets interrogate"

    # Unload models, if needed?
    #state["pipeline"] = None
    gr.Info("Clip is reating Your Prompt")

    conf = Config(
        device=torch.device("cuda"),
        clip_model_name="ViT-L-14/openai",
        cache_path=path_manager.model_paths["clip_path"],
    )
    conf.apply_low_vram_defaults()

    i = Interrogator(conf)
    text = i.interrogate(image)

    return text

def florence_look(image, prompt, gr):
    def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
        """Work around for https://huggingface.co/microsoft/Florence-2-large-ft/discussions/4 ."""
        if os.path.basename(filename) != "modeling_florence2.py":
            return get_imports(filename)
        imports = get_imports(filename)
        imports.remove("flash_attn")
        return imports

    text = "Lets interrogate"
    print(f"Looking...")
    image = image.convert('RGB')

    #state["pipeline"] = None
    gr.Info("Florence is creating Your Prompt")

    with TimeIt(""):
        device = "cpu"
        torch_dtype = torch.float32

        prompt = "<MORE_DETAILED_CAPTION>"

        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            model = AutoModelForCausalLM.from_pretrained(
                "microsoft/Florence-2-large",
                torch_dtype=torch_dtype,
                trust_remote_code=True
            ).to(device)
            processor = AutoProcessor.from_pretrained("microsoft/Florence-2-large", trust_remote_code=True)

        inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch_dtype)
        print(f"Judging...")
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=2048,
            num_beams=6,
            do_sample=False
        )
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        result = processor.post_process_generation(generated_text, task=prompt, image_size=(image.width, image.height))
        text = result[prompt]

    return text

# Add flash_attflash_attn-2.6.3