import base64
from typing import List, Optional
import anthropic
from pathlib import Path
import logging
from datetime import datetime
import os

class ImageProcessor:
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the image processor.
        
        Args:
            model: Model to be used for analysis (default is claude-3-5-sonnet-20241022)
        """
        self.client = anthropic.Anthropic(api_key="insert_api_key_here")  # Insert your API key here
        self.model = model
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging configuration"""
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
        """
        Encode image to base64.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Base64 encoded image
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def create_system_prompt(self) -> str:
        """
        Create system prompt for structured data analysis.
        
        Returns:
            System prompt
        """
        return """Analyze the image content and convert this image into a structured markdown representation that preserves its data and relationships. 
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
- Use markdown quotes for any explanatory text
- Structure the output to prioritize machine readability
- Preserve relationships between data elements using markdown hierarchy"""

    def get_mime_type(self, file_path: str) -> str:
        """
        Determine MIME type based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type of the file
        """
        extension = Path(file_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        return mime_types.get(extension, 'image/jpeg')

    def process_image(self, image_path: str) -> Optional[str]:
        """
        Process a single image using Anthropic API.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Markdown description of the image or None in case of error
        """
        try:
            base64_image = self.encode_image(image_path)
            mime_type = self.get_mime_type(image_path)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0,
                system=self.create_system_prompt(),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image containing structured data and create a detailed markdown description."
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logging.error(f"Error processing {image_path}: {str(e)}")
            return None
            
    def process_current_directory(self):
        """
        Process all supported images in the current directory.
        """
        supported_extensions = {'.jpg', '.jpeg', '.png'}
        current_dir = Path.cwd()  # Get current working directory
        
        # Find all images in current directory
        image_files = [f for f in current_dir.iterdir() 
                      if f.is_file() and f.suffix.lower() in supported_extensions]
        
        if not image_files:
            print("No images found in the current directory.")
            return
            
        print(f"Found {len(image_files)} images to process.")
        
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
    # Available models
    available_models = [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307"
    ]
    
    print("Available models:")
    for i, model in enumerate(available_models, 1):
        print(f"{i}. {model}")
    
    while True:
        try:
            model_choice = int(input("Select model number (1-3): ")) - 1
            if model_choice in range(len(available_models)):
                break
            print("Invalid choice, enter a number 1-3.")
        except ValueError:
            print("Invalid input, enter a number 1-3.")
    
    # Initialize processor
    processor = ImageProcessor(model=available_models[model_choice])
    
    # Process current directory
    processor.process_current_directory()

if __name__ == "__main__":
    main()
