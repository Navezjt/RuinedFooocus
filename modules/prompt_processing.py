import os
import re
import random

from modules.sdxl_styles import apply_style

def process_metadata(gen_data)
    try:
        meta = json.loads(gen_data["prompt"])
        meta = dict((k.lower(), v) for k, v in meta.items())
        gen_data.update(meta)
        if "prompt" in meta:
            gen_data["style_selection"] = None
        if "loras" in meta:
            idx = 1
            for lora in re.findall(r"<(.*?):(.*?)>", meta["loras"]):
                l, w = lora
                gen_data[f"l{idx}"] = l
                gen_data[f"w{idx}"] = float(w)
                idx += 1
    except ValueError as e:
        pass
    return(gen_data)


def process_wildcards(wildcard_text, directory="wildcards"):
    placeholders = re.findall(r"__(\w+)__", wildcard_text)
    for placeholder in placeholders:
        try:
            with open(os.path.join(directory, f"{placeholder}.txt")) as f:
                words = f.read().splitlines()
            wildcard_text = re.sub(rf"__{placeholder}__", random.choice(words), wildcard_text)
        except IOError:
            print(f"Error: Could not open file {placeholder}.txt. Please ensure the file exists and is readable.")
            raise
    return wildcard_text


def process_prompt(style, prompt, negative):
    p_txt, n_txt = apply_style(style, prompt, negative)
    p_txt = process_wildcards(p_txt)
    return p_txt, n_txt


def parse_loras(prompt, negative):
    pattern = re.compile(r"<lora:([^>]+):(\d+)>")
    loras = []
    for match in re.finditer(pattern, prompt):
        loras.append((f"{match.group(1)}.safetensors", float(match.group(2))))
    for match in re.finditer(pattern, negative):
        loras.append((f"{match.group(1)}.safetensors", float(match.group(2))))
    return loras, re.sub(pattern, "", prompt), re.sub(pattern, "", negative)