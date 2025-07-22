import asyncio
import requests
import os
from random import randint
from PIL import Image
from time import sleep

def open_images(prompt):
    """Open generated images from the Data/Images folder."""
    folder_path = os.path.join("Data", "Images")
    prompt_formatted = prompt.replace(" ", "_")
    files = [f"{prompt_formatted}_{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            # Use PIL Image open once and close immediately after show to free resources
            with Image.open(image_path) as img:
                print(f"Opening Image: {image_path}")
                msg="Oening Images"
                img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")
            msg="Unabel to open Image"

async def query(prompt, width=1024, height=1024, model="flux"):
    """Send a request to Pollinations AI and get the image content."""
    seed = randint(0, 1000000)
    formatted_prompt = prompt.replace(" ", "%20")
    url = f"https://pollinations.ai/p/{formatted_prompt}?width={width}&height={height}&seed={seed}&model={model}"
    print(f"Requesting image from: {url}")
    msg="Image Genrartion is Under Process........"
    # Use asyncio.to_thread to run blocking requests.get without blocking event loop
    response = await asyncio.to_thread(requests.get, url)
    response.raise_for_status()  # Raise error for bad response to catch in caller if needed
    return response.content

async def generate_image(prompt: str, width=1024, height=1024, model="flux"):
    """Generate and save 4 images asynchronously."""
    # Create tasks concurrently
    tasks = [asyncio.create_task(query(prompt, width, height, model)) for _ in range(4)]
    image_bytes_list = await asyncio.gather(*tasks)

    images_dir = os.path.join("Data", "Images")
    os.makedirs(images_dir, exist_ok=True)

    prompt_formatted = prompt.replace(' ', '_')
    for i, image_bytes in enumerate(image_bytes_list, start=1):
        image_path = os.path.join(images_dir, f"{prompt_formatted}_{i}.jpg")
        # Use 'with' to ensure file closure
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        print(f"Saved image: {image_path}")
        msg = "Image Was Saved."

def generate_images(prompt: str, width=1024, height=1024, model="flux"):
    """Main function to generate and open images."""
    asyncio.run(generate_image(prompt, width, height, model))
    open_images(prompt)

if __name__ == "__main__":
    n=input("Enter Image Name:")
    generate_images(n)