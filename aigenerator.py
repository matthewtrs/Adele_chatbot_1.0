import requests
import base64

def generate_and_save_image(prompt, output_path="output.png"):
    """
    Generates an image using the Stable Diffusion API and saves it to a file.
    
    Parameters:
        prompt (str): The text prompt for image generation.
        output_path (str): The file path where the image will be saved.
    
    Returns:
        bool: True if the image was saved successfully, False otherwise.
    """
    url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

    payload = {
        "prompt": prompt,
        "negative_prompt": "nsfw, nudity, explicit, gore, violence, low quality, worst quality",
        "steps": 20,
        "cfg_scale": 7,
        "width": 512,
        "height": 512,
        "sampler_name": "Euler a"
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

# Example usage
if __name__ == "__main__":
    generate_and_save_image("A futuristic city at sunset", "generated_image.png")
