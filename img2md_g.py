import os
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
from typing import Dict, Optional

from google import genai
from google.genai import types

# --- START: API KEY INSERTION ---
API_KEY = "YOUR_API_KEY_HERE"  # <--- INSERT YOUR API KEY HERE
# --- END: API KEY INSERTION ---

# Supported image formats
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

# Gemini Model Options
MODEL_OPTIONS: Dict[int, tuple] = {
    1: ("flash", "gemini-3-flash-preview", "Gemini 3 Flash (Recommended)"),
    2: ("pro", "gemini-3-pro-preview", "Gemini 3 Pro"),
}

# Generation Settings
TEMPERATURE = 1.0  # 1.0 is default and recommended for Gemini 3 models
THINKING_LEVEL = "HIGH"  # Options (FLASH): "MINIMAL", "LOW", "MEDIUM", "HIGH" Options (PRO): "LOW", "HIGH"


def display_models() -> None:
    """Display available models with their descriptions."""
    print("\nDostupné modely:")
    print("-" * 50)
    for num, (name, model_id, description) in MODEL_OPTIONS.items():
        print(f"{num}. {name:<10} - {description}")
    print("-" * 50)


def get_model_choice() -> Optional[str]:
    """Get and validate user's model choice."""
    while True:
        display_models()
        try:
            choice = int(input(f"\nVyberte číslo modelu (1-{len(MODEL_OPTIONS)}): "))
            if choice in MODEL_OPTIONS:
                return MODEL_OPTIONS[choice][1]
            print(f"Neplatná volba. Prosím vyberte číslo mezi 1 a {len(MODEL_OPTIONS)}.")
        except ValueError:
            print("Prosím zadejte platné číslo.")
        except KeyboardInterrupt:
            print("\nOperace zrušena uživatelem.")
            return None


def image_to_markdown(image_path: str, model_name: str) -> Optional[str]:
    """Convert image to markdown description using Gemini API."""
    try:
        print(f"Zpracování: {image_path}")
        print(f"Používám model: {model_name}")
        print(f"Temperature: {TEMPERATURE}, Thinking: {THINKING_LEVEL}")

        # Create client
        client = genai.Client(api_key=API_KEY)

        # Read image file
        with open(image_path, "rb") as image_file:
            image_content = image_file.read()

        # Detect mime type based on extension
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        # --- START: SYSTEM PROMPT ---
        prompt = """
    Analyze the image content and convert it into a structured markdown representation optimized for RAG (Retrieval-Augmented Generation). Focus on preserving data relationships, spatial context, and machine readability.

    Content Analysis and Conversion Guidelines:

   1. Content Type Identification:
   - Identify primary content: table, graph, chart, formula, flowchart, diagram, process flow, technical schematic, or combination
   - For mixed content, process each section separately with clear headers
   - Note the overall context and purpose of the image

   2. For Tables:
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

   3. For Graphs and Charts:
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

   4. For Mathematical Formulas:
   - Convert to LaTeX format within markdown delimiters:
     - Inline: `$formula$`
     - Block: `$$formula$$`
   - Example: `$$E = mc^2$$`
   - Include variable definitions and units
   - Provide context about the formula's application
   - Note any conditions or constraints mentioned

   5. For Flowcharts and Diagrams:
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

   6. For Process Flows and Procedures:
   - Create numbered sequential steps
   - Include decision points and branching logic
   - Note any parallel processes or dependencies
   - Preserve timing information if present

   7. For Technical Diagrams and Schematics:
   - Use hierarchical markdown headers (##, ###, ####)
   - List components with their specifications
   - Document connections and relationships
   - Preserve measurements, tolerances, and technical specifications
   - Create tables for component lists or specifications

   8. For Text-Heavy Content and Long Text Fields:
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

   Output Structure Requirements:

   Metadata Header:
```markdown
---
content_type: [primary content type]
complexity: [simple/moderate/complex]
source_quality: [clear/moderate/poor]
extraction_confidence: [high/medium/low]
---
```

   Content Organization:
1. **Title/Description**: Brief overview of the content
2. **Main Content**: Structured representation using appropriate format
3. **Key Insights**: Summary of important findings or relationships
4. **Additional Notes**: Any unclear elements or assumptions made

   Critical Guidelines for RAG Optimization:

- **Preserve exact numerical values**: Maintain precision as shown
- **Include contextual keywords**: Add relevant technical terms for searchability
- **Structure for querying**: Use consistent headers and formatting
- **Handle uncertainty**: Clearly mark unclear or partially visible content with `[unclear]` or `[partially visible]`
- **Maintain relationships**: Preserve spatial and logical connections between elements
- **Include units and scales**: Always specify measurements and units
- **Cross-reference elements**: Link related sections when applicable

   Quality Assurance:
- Double-check numerical accuracy
- Verify all text transcription
- Ensure markdown syntax is correct
- Test that Mermaid diagrams would render properly
- Confirm LaTeX formulas are properly formatted
        """
        # --- END: SYSTEM PROMPT ---

        # Create content structure
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_content, mime_type=mime_type),
                ],
            ),
        ]

        # Generation config with temperature and thinking level
        generate_content_config = types.GenerateContentConfig(
            temperature=TEMPERATURE,
            thinking_config=types.ThinkingConfig(
                thinking_level=THINKING_LEVEL,
            ),
        )

        # Generate content
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )

        markdown_content = response.text

        if not markdown_content or not markdown_content.strip():
            print(f"Varování: Žádný popis nebyl vygenerován pro: {image_path}")
            return None

        return markdown_content

    except Exception as e:
        print(f"Chyba při zpracování {image_path}: {str(e)}")
        return None


def save_markdown(markdown_content: str, output_path: str) -> bool:
    """Save Markdown content to file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✓ Uloženo: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Chyba při ukládání {output_path}: {str(e)}")
        return False


def process_image(image_path: str, model_name: str, output_dir: str) -> bool:
    """Process a single image file."""
    try:
        markdown_content = image_to_markdown(image_path, model_name)
        if markdown_content:
            output_filename = Path(image_path).stem + "_popis.md"
            output_path = os.path.join(output_dir, output_filename)
            return save_markdown(markdown_content, output_path)
        return False
    except Exception as e:
        print(f"Chyba při zpracování {image_path}: {str(e)}")
        return False


def main() -> None:
    """Main function to run the Image to Markdown converter."""
    print("Převodník obrázků na popis v Markdownu")
    print(f"Python: {sys.executable}")
    print("-" * 50)

    # Setup directories
    input_dir = os.getcwd()
    output_dir = os.path.join(input_dir, "vystupy")

    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as error:
        print(f"Chyba při vytváření výstupního adresáře: {error}")
        return

    # Get model choice
    model_name = get_model_choice()
    if not model_name:
        return

    # Find image files
    image_files = []
    for ext in SUPPORTED_FORMATS:
        image_files.extend(glob.glob(os.path.join(input_dir, f"*{ext}")))

    if not image_files:
        print("Nebyly nalezeny žádné podporované obrázky v aktuálním adresáři.")
        print(f"Podporované formáty: {', '.join(SUPPORTED_FORMATS)}")
        return

    print(f"\nNalezeno {len(image_files)} obrázků.")

    # Process files
    start_time = time.time()
    successful_conversions = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_image, image_path, model_name, output_dir)
            for image_path in image_files
        ]

        for future in as_completed(futures):
            if future.result():
                successful_conversions += 1

    end_time = time.time()
    duration = end_time - start_time

    # Print summary
    print("\nShrnutí konverze:")
    print("-" * 50)
    print(f"Celkem zpracováno souborů: {len(image_files)}")
    print(f"Úspěšné konverze: {successful_conversions}")
    print(f"Neúspěšné konverze: {len(image_files) - successful_conversions}")
    print(f"Celkový čas: {duration:.2f} sekund")
    print(f"Průměrný čas na soubor: {duration/len(image_files):.2f} sekund")
    print(f"\nVýstupní adresář: {output_dir}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperace zrušena uživatelem.")
    except Exception as e:
        print(f"Nastala neočekávaná chyba: {str(e)}")
