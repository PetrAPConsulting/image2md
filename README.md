# image2md

## Structured Images to Markdown Converter

This tool automatically converts batch of images containing structured data (tables, formulas, graphs, diagrams, flowcharts, etc.) into markdown format. Markdown files are suitable for RAG pipeline. Tool uses either top tier Anthropic's models or free Mistral AI's vision Pixtral model via API to analyze images and create detailed markdown descriptions based on included robust system prompt. 

## Prerequisites

Before you start, you need to have:
1. Python installed on your computer (version 3.7 or higher)
2. An Anthropic API key (get it from [Anthropic's console](https://console.anthropic.com/dashboard))
3. An Mistral API key when using Pixtral model (get it from [Mistral's console](https://console.mistral.ai/api-keys/))

## Installation Steps

### 1. Install Python
If you don't have Python installed:
1. Go to [Python's official website](https://www.python.org/downloads/)
2. Download the latest version for your operating system
3. Run the installer
   - On Windows: Make sure to check "Add Python to PATH" during installation
   - On Mac: Follow the standard installation process

### 2. Get the Code

#### Using Git (Option 1):
1. Open Terminal (Mac) or Command Prompt (Windows)
2. Navigate to where you want to save the project:
```bash
cd Documents
```
3. Clone the repository:
```bash
git clone https://github.com/PetrAPConsulting/image2md.git
```
4. It creates folder image2md with cloned files

#### Manual Download (Option 2):
1. Click the green "Code" button on this page
2. Click on the sheet "Local"
3. Select "Download ZIP"
4. Extract the ZIP file to your desired location

### 3. Install Required Library
Open Terminal (Mac) or Command Prompt (Windows) in the project folder and run:
```bash
pip install anthropic
```

If that doesn't work, try:
```bash
pip3 install anthropic
```
You do not need to install anything for using Mistral AI models.

### Script configuration for Anthropic 

1. Open the `images.py` file in a text editor
2. Find this line:
```python
self.client = anthropic.Anthropic(api_key="insert_api_key_here")
```
3. Replace `"insert_api_key_here"` with your Anthropic API key
4. Follow development of Anthropic models and make adjustments in the script when new version is realised. Only models with vision capabilities are supported. 
```python
def __init__(self, model: str = "claude-3-5-sonnet-20241022")
```
```python
def main():
    available_models = [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307"
    ]  
```
### Script configuration for Mistral AI

1. Open the `img2md_m.py` file in a text editor
2. Find this line:
```python
API_KEY = "API_key_here"
```
3. Replace `"API_key_here"` with your Mistral API key
4. Follow development of Mistral AI models and make adjustments in the script when new version is realised. Only models with vision capabilities are supported and only Pixtral is free. If you would like to use top tier Pixtral Large you need to charge your account with credit. 
```python
class MistralModel(str, Enum):
    PIXTRAL = "pixtral-12b-2409"
    PIXTRAL_LARGE = "pixtral-large-latest"
```

### Usage

1. Copy your images (.jpg, .jpeg, or .png) to the same folder as the script. Keep images around 1000 x 1000px for token consumption optimalization. You can download simple batch image downscaler for downscaling jpeg, jpg, png, webp files.
2. Open Terminal (Mac) or Command Prompt (Windows)
3. Navigate to the script's folder:
```bash
cd path/to/your/folder
```
4. Run the script:
```bash
python images.py
```
or
```bash
python img2md_m.py
```
5. Select a model when prompted (1-3)
6. The script will create markdown (.md) files for each image in the same folder

### Supported File Types
- `.jpg`
- `.jpeg`
- `.png`

### Features
- Automatically detects tables, formulas, graphs, flowcharts, etc.
- Creates markdown tables from image tables
- Converts mathematical formulas to LaTeX format
- Provides detailed analysis of graphs with key values
- Creates nice clear markdown mermaid from flowcharts and process diagrams
- Preserves anotations and tables with measurements 
- Generates log files for troubleshooting
- IMPORTANT: If you need output in different language than ENG you need to translate system prompt in python script. Even though Anthropic and Mistral models are multilingual, language of sytem prompt determinates language of output except, data is directly extracted from source, like content of tables.  

### Troubleshooting

### Common Issues:

1. **"No module named 'anthropic'"**
   - Run `pip install anthropic` again
   - Make sure you're using the correct Python version

2. **"Invalid API key"**
   - Check if you've correctly inserted your API key in the script
   - Verify your API key is active on Anthropic's or Mistral's website

3. **"Python not found"**
   - Make sure Python is installed
   - Try using `python3` instead of `python`

### Still Having Problems?
First, try your good friend ChatGPT, Claude or Gemini. All three of them are able to help you if you give them occured errors.
Or create an issue in this repository with:
- The error message you're seeing
- Your operating system
- Steps you've tried

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Uses Anthropic's API or Mistral AI API for image analysis
- Inspired by Petr's need for automated structured data extraction from images
