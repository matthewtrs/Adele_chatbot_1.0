import requests
import base64
import time

# Default global settings
LORA_WEIGHT = 1.0
CURRENT_CHECKPOINT = "hassakuXLIllustrious_v2.safetensors"

def set_checkpoint(checkpoint_name):
    """Set the checkpoint model in the Stable Diffusion API."""
    global CURRENT_CHECKPOINT
    
    url = "http://127.0.0.1:7860/sdapi/v1/options"
    payload = {"sd_model_checkpoint": checkpoint_name}
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        CURRENT_CHECKPOINT = checkpoint_name
        print(f"Checkpoint set to: {checkpoint_name}")
        # Give the system a moment to load the checkpoint
        time.sleep(3)
        return True
    else:
        print(f"Error setting checkpoint: {response.text}")
        return False

def set_lora_weight(weight):
    """Allows setting the LoRA weight globally."""
    global LORA_WEIGHT
    LORA_WEIGHT = weight

def generate_and_save_image(prompt, output_path="output.png", lora_models=None):
    """
    Generates an image using Stable Diffusion API with optional multiple LoRA models.
    Uses the currently loaded checkpoint.
    """
    url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

    # Apply multiple LoRAs if specified
    if lora_models:
        for lora_name in lora_models:
            prompt = f"<lora:{lora_name}:{LORA_WEIGHT}> " + prompt
    
    addon = "masterpiece, best quality, theresa_\(arknights\)"

    payload = {
        "prompt": addon + prompt,
        "negative_prompt": "nsfw, nudity, explicit, gore, violence, low quality, worst quality",
        "steps": 20,
        "cfg_scale": 7,
        "width": 512,
        "height": 512,
        "sampler_name": "Euler a",
        "denoising_strength": 0.7
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        image_data = response.json().get("images", [None])[0]

        if image_data:
            try:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image_data))
                print(f"Image saved as {output_path}")
                return True
            except Exception as e:
                print(f"Error saving image: {e}")
                return False
        else:
            print("Error: No image data received.")
            return False
    else:
        print(f"Error: {response.text}")
        return False

# Example usage with improved workflow
if __name__ == "__main__":
    # Set checkpoint once at the beginning
    set_checkpoint("hassakuXLIllustrious_v2.safetensors")
    
    # Set global LoRA weight
    set_lora_weight(0.8)

    # Generate multiple images without needing to set checkpoint each time
    generate_and_save_image(
        prompt="eating cookies",
        output_path="city_sunset.png",
        lora_models=["theresa_arknights_v2.0_for_IL-000012"]
    )
    
    # Generate another image using the same checkpoint
    generate_and_save_image(
        prompt="in crystal cave with glowing minerals",
        output_path="crystal_cave.png",
        lora_models=["theresa_arknights_v2.0_for_IL-000012"]
    )