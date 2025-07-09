
# AI Medical Document Summarizer & Highlighter

An AI-powered desktop tool to automatically summarize and highlight key terms in clinical documents. It generates a structured summary, extracts important keywords, and uses a color-coded legend to highlight them in both the original text and the summary.

![Application Screenshot](screenshot.jpg)

## Features

-   **AI Summarization & Keyword Extraction**: Generates a structured HEDP (History, Examination, Diagnosis, Plan) summary and identifies key clinical terms using the OpenAI API.
-   **Dual-Pane Highlighting**: Highlights keywords in both the source document and the generated summary for easy cross-referencing.
-   **Dynamic Color Legend**: Automatically creates a legend mapping keywords to their highlight color.
-   **Simple Desktop UI**: A clean, straightforward interface built with Python's native Tkinter.

## How It Works

The application sends the content of a loaded text file to the OpenAI API. It requests a JSON object containing a structured `summary` and a list of `keywords`. The application then renders this data in the UI, creating the legend and highlighting the keywords in both panes.

## Getting Started

### Prerequisites

-   Python 3.7+
-   An OpenAI API Key

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/osotsia/SummarizeApp.git
    cd SummarizeApp
    ```

2.  **Install the dependency:**
    ```bash
    pip install openai
    ```
    *(On some Linux systems, you may also need to install Tkinter: `sudo apt-get install python3-tk`)*

3.  **Set your API Key:**
    The application reads your key from an environment variable for security.

    **macOS / Linux:**
    ```bash
    export OPENAI_API_KEY="sk-your_key_here"
    ```

    **Windows (Command Prompt):**
    ```cmd
    setx OPENAI_API_KEY "sk-your_key_here"
    ```
    *(You may need to restart your terminal after setting the key.)*

## Usage

1.  Run the application:
    ```bash
    python main.py
    ```

2.  Click **"Load Document"** to select a text file (SampleNeph.txt).
3.  Click **"Summarize & Highlight"** to process the document.
