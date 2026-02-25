from crew import WingifyCorrectCode

import os
from dotenv import load_dotenv

# Loading environment variables (OpenAI key, etc.)
load_dotenv()

def run_test():
    # Defining the path to your specific PDF
    file_path = "D:\\Wingify\\financial-document-analyzer-debug\\data\\TSLA-Q2-2025-Update.pdf"

    
    # Validating file existence before kickoff to avoid deterministic errors
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    # Preparing inputs for the YAML templates
    inputs = {
        'query': 'Analyze the revenue growth and major risk factors for Tesla in Q2 2025.',
        'file_path': file_path
    }

    print("### Starting Financial Analysis Crew ###\n")

    try:
        # Initializing the crew and kicking off the sequential process
        crew_instance = WingifyCorrectCode().crew()
        result = crew_instance.kickoff(inputs=inputs)

        print("\n### Final Analysis Result ###\n")
        print(result.raw)

    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    run_test()