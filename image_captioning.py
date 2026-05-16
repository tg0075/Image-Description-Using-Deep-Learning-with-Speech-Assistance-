from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

# Load the Processor and Model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

def generate_caption(image_path):
    # Load the Image
    raw_image = Image.open(image_path).convert('RGB')

    # Prepare the Inputs
    text = "A photography of"
    inputs = processor(raw_image, text, return_tensors="pt")

    # Generate the Caption
    output = model.generate(**inputs)
    return processor.decode(output[0], skip_special_tokens=True)
