import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import json

# Third-party libraries
from openai import OpenAI, APIError

# ==============================================================================
# CONSTANTS
# ==============================================================================

# A predefined list of distinct, readable highlight colors.
# Using modulo allows us to handle if the LLM gives more keywords than we have colors.
HIGHLIGHT_COLORS = ['#FFADAD', '#FFD6A5', '#FDFFB6', '#CAFFBF', '#9BF6FF', '#BDB2FF']

# The base prompt now includes a clear instruction for JSON output.
SUMMARY_PROMPT_MESSAGES = [
    {"role": "system",
     "content": "You are an expert medical assistant. Your response MUST be a single, valid JSON object."},
    {"role": "user",
     "content": "Patient is a 65yo male with a hx of HTN and DM2, presenting with chest pain. "
                "EKG shows no ST elevation. Troponins are negative. The plan is to admit for"
                " observation and serial troponins, and to consult cardiology."},
    {"role": "assistant", "content": json.dumps({
        "summary": """
        BriefSummary: 65-year-old male with hypertension and type 2 diabetes admitted for 
        observation due to chest pain. Key action items are serial troponins and a cardiology consultation.

        History:
        - 65-year-old male
        - History of Hypertension (HTN)
        - History of Type 2 Diabetes (DM2)
        - Presenting with chest pain
        
        Examination:
        - EKG: No ST elevation
        - Labs: Negative troponins
        
        Diagnosis:
        - Atypical chest pain, rule out Acute Coronary Syndrome (ACS)
        
        Plan:
        - Admit for observation
        - Perform serial troponin tests
        - Consult Cardiology service""",
        "keywords": ["chest pain", "hypertension", "diabetes", "troponins", "cardiology"]
    })}
]


def generate_summary_and_keywords(document: str) -> dict:
    """
    Generates a summary and keywords using the OpenAI API, returning a dictionary.

    Returns:
        A dictionary with 'summary' and 'keywords' keys, or an error message.
    """
    try:
        # On your system, run: export OPENAI_API_KEY='your_key_here'
        client = OpenAI()
        final_instruction = (
            "From the following document, create a medical summary with bullet points, but with the sections as "
            "History, Examination, Diagnosis, and Plan. "
            "Make sure to add all key reminders to the Plan section."
            "At the beginning add a 1-3 sentence summary (BriefSummary) of the key points (esp action points) in the case. "
            "Also, identify exactly 4-5 of the most clinically important keywords from the text. "
            "Respond with a single JSON object containing two keys: 'summary' (a string containing the medical summary above) and 'keywords' (a list of strings)."
            f"\n\nDOCUMENT:\n{document}"
        )

        messages = SUMMARY_PROMPT_MESSAGES + [{"role": "user", "content": final_instruction}]

        completion = client.chat.completions.create(model="gpt-4-turbo", messages=messages,
                                                    response_format={"type": "json_object"})

        response_content = completion.choices[0].message.content
        return json.loads(response_content)

    except json.JSONDecodeError:
        return {'error': "Failed to parse LLM response. The model did not return valid JSON."}
    except APIError as e:
        return {'error': f"The OpenAI API returned an error: {e}"}
    except Exception as e:
        return {'error': f"An unexpected error occurred: {e}"}


# ==============================================================================
# MAIN APPLICATION CLASS
# ==============================================================================

class SearchSummarizeApp:
    """A Tkinter GUI for summarizing and highlighting medical documents."""

    def __init__(self):
        # GUI setup
        self.root = self.create_main_window()
        self.legend_frame, self.summary_pane, self.right_pane = self.create_panes(self.root)
        self.widgets = self.create_buttons(self.root)
        self.is_document_loaded = False

    def run(self):
        self.root.mainloop()

    ### --------------------------------------------------------------------
    ### GUI Setup Methods
    ### --------------------------------------------------------------------

    def create_main_window(self):
        root = tk.Tk()
        root.title("Medical Document Summarizer & Highlighter")
        root.geometry("1200x700")
        return root

    def create_panes(self, root):
        paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned_window.pack(fill=tk.BOTH, expand=1, padx=10, pady=5)

        # --- GUI STRUCTURE CHANGE: Create a master frame for the left side ---
        left_master_frame = tk.Frame(paned_window)

        # 1. The legend will live in its own frame at the top.
        legend_frame = tk.Frame(left_master_frame, relief=tk.GROOVE, borderwidth=1)
        legend_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # 2. The summary text pane will live below the legend.
        summary_pane = tk.Text(left_master_frame, wrap=tk.WORD, font=("Helvetica", 11), padx=5)
        summary_pane.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # The right pane remains a single Text widget.
        right_pane = tk.Text(paned_window, wrap=tk.WORD, font=("Helvetica", 11), padx=5)

        paned_window.add(left_master_frame, width=500)
        paned_window.add(right_pane)

        return legend_frame, summary_pane, right_pane

    def create_buttons(self, root):
        button_frame = tk.Frame(root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        widgets = {
            'load': tk.Button(button_frame, text="Load Document", command=self.load_document),
            'summarize': tk.Button(button_frame, text="Summarize & Highlight", command=self.start_summarize_thread,
                                   state=tk.DISABLED),
        }
        widgets['load'].pack(side=tk.LEFT, padx=5)
        widgets['summarize'].pack(side=tk.LEFT, padx=5)
        return widgets

    ### --------------------------------------------------------------------
    ### Core Application Logic & Threading
    ### --------------------------------------------------------------------

    def set_ui_state(self, is_busy: bool):
        load_state = tk.DISABLED if is_busy else tk.NORMAL
        action_state = tk.DISABLED if is_busy or not self.is_document_loaded else tk.NORMAL
        self.widgets['load'].config(state=load_state)
        self.widgets['summarize'].config(state=action_state)

    def load_document(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        if content:
            self.right_pane.delete(1.0, tk.END)
            self.right_pane.insert(tk.INSERT, content)
            self.summary_pane.delete(1.0, tk.END)
            self._update_legend([])  # Clear legend on new document load
            self.is_document_loaded = True
            self.set_ui_state(is_busy=False)

    def start_summarize_thread(self):
        document = self.right_pane.get(1.0, tk.END)
        if not document.strip():
            messagebox.showwarning("Warning", "Document is empty.")
            return

        self.set_ui_state(is_busy=True)
        self.summary_pane.delete(1.0, tk.END)
        self._update_legend([])  # Clear legend
        self.summary_pane.insert(tk.INSERT, "Generating summary and extracting keywords...")

        threading.Thread(target=self._worker_summarize, args=(document,), daemon=True).start()

    def _worker_summarize(self, document: str):
        result = generate_summary_and_keywords(document)
        self.root.after(0, self._on_summarize_complete, result)

    def _on_summarize_complete(self, result: dict):
        self.summary_pane.delete(1.0, tk.END)

        if 'error' in result:
            self.summary_pane.insert(tk.INSERT, result['error'])
            self.set_ui_state(is_busy=False)
            return

        summary_text = result.get('summary', 'Summary not found in response.')
        keywords = result.get('keywords', [])

        self.summary_pane.insert(tk.INSERT, summary_text)
        self._update_legend(keywords)
        self._highlight_keywords(keywords)

        self.set_ui_state(is_busy=False)

    def _update_legend(self, keywords: list):
        """Clears and rebuilds the color-to-keyword legend frame."""
        # Destroy all previous legend widgets
        for widget in self.legend_frame.winfo_children():
            widget.destroy()

        if not keywords:
            return  # Don't display anything if there are no keywords

        title_label = tk.Label(self.legend_frame, text="Keywords:", font=("Helvetica", 10, "bold"))
        title_label.pack(side=tk.LEFT, padx=5, pady=2)

        for i, keyword in enumerate(keywords):
            color = HIGHLIGHT_COLORS[i % len(HIGHLIGHT_COLORS)]
            label = tk.Label(self.legend_frame, text=keyword, bg=color, fg="black", padx=3, pady=1, relief=tk.RAISED,
                             borderwidth=1)
            label.pack(side=tk.LEFT, padx=3, pady=2)

    def _highlight_keywords(self, keywords: list):
        """Finds and highlights all occurrences of keywords in both text panes."""
        # Define and clear tags for all possible colors
        for i in range(len(HIGHLIGHT_COLORS)):
            tag_name = f"highlight_{i}"
            self.summary_pane.tag_remove(tag_name, "1.0", tk.END)
            self.right_pane.tag_remove(tag_name, "1.0", tk.END)

        for i, keyword in enumerate(keywords):
            color = HIGHLIGHT_COLORS[i % len(HIGHLIGHT_COLORS)]
            tag_name = f"highlight_{i}"

            for pane in [self.summary_pane, self.right_pane]:
                pane.tag_configure(tag_name, background=color, foreground="black")

                start_pos = "1.0"
                while True:
                    pos = pane.search(keyword, start_pos, stopindex=tk.END, nocase=True)
                    if not pos:
                        break

                    end_pos = f"{pos} + {len(keyword)}c"
                    pane.tag_add(tag_name, pos, end_pos)
                    start_pos = end_pos

def main():
    app = SearchSummarizeApp()
    app.run()


if __name__ == "__main__":
    main()