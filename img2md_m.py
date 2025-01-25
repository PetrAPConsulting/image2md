import base64
from typing import List, Optional, Literal
from pathlib import Path
import logging
from datetime import datetime
import requests
from dataclasses import dataclass
from enum import Enum
import os

class MistralModel(str, Enum):
    PIXTRAL = "pixtral-12b-2409"
    PIXTRAL_LARGE = "pixtral-large-latest"

@dataclass
class MistralConfig:
    api_key: str
    model: MistralModel
    api_base: str = "https://api.mistral.ai"
    max_tokens: int = 4096
    temperature: float = 0.0

    API_KEY = "API_key_here"  # Replace with your actual Mistral API key
    
    @classmethod
    def create(cls, model: MistralModel):
        """Create config with built-in API key."""
        return cls(api_key=cls.API_KEY, model=model)

class ImageProcessor:
    def __init__(self, config: MistralConfig):
        """Initialize with configuration."""
        self.config = config
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging configuration."""
        log_filename = f"image_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def create_chat_prompt(self) -> List[dict]:
        """Create chat messages for product image analysis."""
        return [
            {
                "role": "system",
                "content": """Analyze the image content and convert this image into a structured markdown representation with focus on preserving data relationships and machine readability. 
        Follow these conversion guidelines based on content type:

1. Content Type:
   - Identify whether it's a table, graph, chart, formula, flowchart, diagram, process flow, technical diagram or combination
 
2. For Tables:
   - Create exact markdown representation of the table using markdown syntax (|column1|column2|)
   - Create a separator row (|---|---|) after the header
   - Transcribe all values exactly as they appear in the table
   - After the table, add a brief description of column headers and their meaning
   - Identify key trends or important values in the data

3. For Graphs and Charts:
   - Identify the graph type (bar, line, pie, etc.)
   - Describe axes and their units
   - Analyze trends and significant points
   - Record maximums, minimums, and important values
   - Describe the relationship pattern (linear, exponential, etc.) as a markdown header

4. For Formulas:
   - Transcribe the formula into LaTeX format if possible
   - Use LaTeX notation within markdown delimiters. For example: $$ y = mx + b $$
   - Identify variables and their meaning
   - Describe the mathematical context of the formula
   
5. For Flowcharts and Diagrams:
   - Convert to mermaid markdown syntax when possible:
	```mermaid
	graph LR
        A-->B
        B-->C
	```
   
6. For Process Flows:
   - Create a numbered list with clear step progression and any branching conditions

7. For Technical Diagrams:
   - Create a hierarchical structure using markdown headers
   - List components and their relationships
   - Preserve any measurements or specifications in tables   

Additional Guidelines:
- Maintain numerical precision exactly as shown
- Preserve all labels and annotations as markdown text
- Include metadata as key-value pairs at the top
- Transcribe and preserve any explanatory text as markdown text
- Structure the output to prioritize machine readability
- Preserve relationships between data elements using markdown hierarchy"""
            },
            {
                "role": "user",
                "content": "Analyze this product image and create a detailed markdown description."
            }
        ]

    def get_mime_type(self, file_path: str) -> str:
        """Determine MIME type from file extension."""
        extension = Path(file_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        return mime_types.get(extension, 'image/jpeg')

    def process_image(self, image_path: str) -> Optional[str]:
        """Process single image using Mistral API."""
        try:
            base64_image = self.encode_image(image_path)
            mime_type = self.get_mime_type(image_path)
            
            messages = self.create_chat_prompt()
            messages[1]["content"] = [
                {
                    "type": "text",
                    "text": "Analyze this product image and create a detailed markdown description."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            ]
            
            response = requests.post(
                f"{self.config.api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }
            )
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            logging.error(f"Error processing {image_path}: {str(e)}")
            return None
            
    def process_directory(self, directory: Optional[Path] = None):
        """Process all supported images in specified directory or current directory."""
        directory = directory or Path.cwd()
        supported_extensions = {'.jpg', '.jpeg', '.png'}
        
        image_files = [f for f in directory.iterdir() 
                      if f.is_file() and f.suffix.lower() in supported_extensions]
        
        if not image_files:
            print(f"No images found in {directory}")
            return
            
        print(f"Found {len(image_files)} images to process")
        
        for image_file in image_files:
            print(f"Processing {image_file.name}")
            logging.info(f"Processing {image_file.name}")
            
            description = self.process_image(str(image_file))
            if description:
                output_file = image_file.with_suffix('.md')
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(description)
                    print(f"Created file: {output_file.name}")
                    logging.info(f"Markdown saved to {output_file.name}")
                except Exception as e:
                    logging.error(f"Error saving {output_file.name}: {str(e)}")

def main():

    print("\nAvailable models:")
    for i, model in enumerate(MistralModel, 1):
        print(f"{i}. {model.value}")
    
    while True:
        try:
            model_choice = int(input("\nSelect model number (1-2): ")) - 1
            if 0 <= model_choice < len(MistralModel):
                break
            print("Invalid choice, enter 1-2")
        except ValueError:
            print("Invalid input, enter 1-2")
    
    config = MistralConfig.create(list(MistralModel)[model_choice])
    processor = ImageProcessor(config)
    
    directory = input("\nEnter directory path (press Enter for current directory): ").strip()
    process_dir = Path(directory) if directory else None
    
    processor.process_directory(process_dir)

if __name__ == "__main__":
    main()