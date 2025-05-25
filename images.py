import base64
from typing import List, Optional
import anthropic
from pathlib import Path
import logging
from datetime import datetime
import os

class ImageProcessor:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the image processor.
        
        Args:
            model: Model to be used for analysis (default is claude-sonnet-4-20250514)
        """
        self.client = anthropic.Anthropic(api_key="Insert_API_Key_Here")  
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
        Create system prompt for structured data analysis and conversion of images to markdown for RAG optimized pipeline.
        
        Returns:
            System prompt
        """
        return """Analyze the image content and convert it into a structured markdown representation optimized for RAG (Retrieval-Augmented Generation). Focus on preserving data relationships, spatial context, and machine readability.

## Content Analysis and Conversion Guidelines:

### 1. Content Type Identification:
   - Identify primary content: table, graph, chart, formula, flowchart, diagram, process flow, technical schematic, or combination
   - For mixed content, process each section separately with clear headers
   - Note the overall context and purpose of the image

### 2. For Tables:
   - Create exact markdown table using proper syntax:
     ```
     | Column 1 | Column 2 | Column 3 |
     |----------|----------|----------|
     | Value 1  | Value 2  | Value 3  |
     ```
   - Preserve all values exactly as shown (including units, decimals, formatting)
   - For complex tables with merged cells, use descriptive text to indicate structure
   - Handle multi-level headers by creating separate description sections
   - After the table, include:
     - Brief description of each column's meaning
     - Key insights, trends, or notable values
     - Any totals, calculations, or summary rows

### 3. For Graphs and Charts:
   - Start with chart type identification (bar, line, pie, scatter, histogram, etc.)
   - Document axes information:
     - X-axis: label, units, range, scale type (linear/log)
     - Y-axis: label, units, range, scale type
   - Extract data points systematically (especially key values)
   - Identify and describe:
     - Trends (increasing, decreasing, cyclical, etc.)
     - Outliers and significant points
     - Relationships between variables
     - Any annotations or callouts on the chart

### 4. For Mathematical Formulas:
   - Convert to LaTeX format within markdown delimiters:
     - Inline: `$formula$`
     - Block: `$$formula$$`
   - Example: `$$E = mc^2$$`
   - Include variable definitions and units
   - Provide context about the formula's application
   - Note any conditions or constraints mentioned

### 5. For Flowcharts and Diagrams:
   - Convert to Mermaid syntax:
   ```mermaid
   flowchart TD
       A[Start] --> B{Decision}
       B -->|Yes| C[Process]
       B -->|No| D[End]
       C --> D
   ```
   
   **Essential syntax rules:**
   - Use `flowchart TD` (Top Down) or `flowchart LR` (Left Right) - NOT `graph`
   - Node shapes: `A[Rectangle]`, `B{Diamond}`, `C((Circle))`, `D[/Parallelogram/]`
   - Connections: `A --> B` (arrow), `A -->|Label| B` (labeled arrow)
   - Quote labels with spaces: `A["Multi word label"]`
   - Keep node IDs simple (A, B, C or descriptive single words)
   
   **For new Mermaid versions:**
   - Always use `flowchart` instead of deprecated `graph`
   - Quote labels containing spaces, parentheses, or special characters
   - Escape special characters when needed

### 6. For Process Flows and Procedures:
   - Create numbered sequential steps
   - Include decision points and branching logic
   - Note any parallel processes or dependencies
   - Preserve timing information if present

### 7. For Technical Diagrams and Schematics:
   - Use hierarchical markdown headers (##, ###, ####)
   - List components with their specifications
   - Document connections and relationships
   - Preserve measurements, tolerances, and technical specifications
   - Create tables for component lists or specifications

### 8. For Text-Heavy Content and Long Text Fields:
   - **Identify text regions**: Distinguish between structured data and pure text content
   - **Preserve exact transcription**: Maintain original wording, punctuation, and spacing
   - **Handle different text types**:
     - **Paragraphs**: Transcribe as markdown paragraphs with proper line breaks
     - **Lists**: Convert to markdown lists (- or 1.) while preserving hierarchy
     - **Headers/Titles**: Use appropriate markdown headers (##, ###, ####)
     - **Quotes/Citations**: Use blockquote format (>) for quoted material
     - **Code/Technical text**: Use code blocks (```) for technical content
   
   - **Formatting preservation**:
     - Maintain paragraph breaks and logical text flow
     - Preserve emphasis (bold/italic) using **bold** and *italic* markdown
     - Keep original capitalization and punctuation exactly
     - Note any unclear or partially visible text with [unclear] markers
   
   - **Structure long text**:
     ```markdown
     ## [Document Title/Section Name]
     
     [First paragraph of text exactly as shown...]
     
     [Second paragraph...]
     
     ### [Subsection if applicable]
     
     [Continued text...]
     ```
   
   - **Special considerations**:
     - For multi-column text, clearly indicate column breaks
     - Preserve any numbering or bullet point systems
     - Maintain original language (don't translate)
     - Keep any technical terminology or jargon exactly as written
     - For handwritten text, transcribe as accurately as possible and note uncertainty

## Output Structure Requirements:

### Metadata Header:
```markdown
---
content_type: [primary content type]
complexity: [simple/moderate/complex]
source_quality: [clear/moderate/poor]
extraction_confidence: [high/medium/low]
---
```

### Content Organization:
1. **Title/Description**: Brief overview of the content
2. **Main Content**: Structured representation using appropriate format
3. **Key Insights**: Summary of important findings or relationships
4. **Additional Notes**: Any unclear elements or assumptions made

## Critical Guidelines for RAG Optimization:

- **Preserve exact numerical values**: Maintain precision as shown
- **Include contextual keywords**: Add relevant technical terms for searchability
- **Structure for querying**: Use consistent headers and formatting
- **Handle uncertainty**: Clearly mark unclear or partially visible content with `[unclear]` or `[partially visible]`
- **Maintain relationships**: Preserve spatial and logical connections between elements
- **Include units and scales**: Always specify measurements and units
- **Cross-reference elements**: Link related sections when applicable

## Quality Assurance:
- Double-check numerical accuracy
- Verify all text transcription
- Ensure markdown syntax is correct
- Test that Mermaid diagrams would render properly
- Confirm LaTeX formulas are properly formatted"""

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
        "claude-sonnet-4-20250514",
        "claude-opus-4-20250514",
        "claude-3-5-haiku-latest"
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
