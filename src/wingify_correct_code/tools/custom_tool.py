from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."
    
import os
from dotenv import load_dotenv
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from crewai_tools import SerperDevTool
from pypdf import PdfReader # Replaces the non-existent 'Pdf' class

load_dotenv()

# --- Search Tool ---
# Initializing the standard SerperDevTool for internet research
search_tool = SerperDevTool()

# --- PDF Reader Tool ---

class FinancialDocumentToolInput(BaseModel):
    """Input schema for FinancialDocumentTool."""
    path: str = Field(..., description="The file path of the PDF document to read.")

class FinancialDocumentTool(BaseTool):
    name: str = "read_financial_document"
    description: str = (
        "Reads and extracts text from a PDF financial document. "
        "Useful for verifying document types and analyzing financial data."
    )
    args_schema: Type[BaseModel] = FinancialDocumentToolInput

    def _run(self, path: str) -> str:
        """Implementation to read and clean PDF content."""
        try:
            # Check if file exists to prevent crash 
            if not os.path.exists(path):
                return f"Error: The file at {path} was not found."

            reader = PdfReader(path)
            full_report = ""
            
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    # Clean and format the text content
                    while "\n\n" in content:
                        content = content.replace("\n\n", "\n")
                    full_report += content + "\n"
            
            return full_report if full_report.strip() else "The document appears to be empty."
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

# --- Investment Analysis Tool ---

class InvestmentToolInput(BaseModel):
    """Input schema for InvestmentTool."""
    financial_data: str = Field(..., description="The raw financial text data to analyze.")

class InvestmentTool(BaseTool):
    name: str = "analyze_investments"
    description: str = (
        "Analyzes processed financial data to provide stock picks and "
        "investment strategy recommendations."
    )
    args_schema: Type[BaseModel] = InvestmentToolInput

    def _run(self, financial_data: str) -> str:
        # Implementation for cleaning up double spaces
        processed_data = " ".join(financial_data.split())
        
        # Logic to be handled by LLM agent using this context
        return f"Processed Analysis Data: {processed_data[:500]}..."

# --- Risk Assessment Tool ---

class RiskToolInput(BaseModel):
    """Input schema for RiskTool."""
    financial_data: str = Field(..., description="The raw financial text data to assess for risks.")

class RiskTool(BaseTool):
    name: str = "assess_financial_risk"
    description: str = (
        "Evaluates financial data to identify market, credit, and operational risks."
    )
    args_schema: Type[BaseModel] = RiskToolInput

    def _run(self, financial_data: str) -> str:
        # Placeholder for risk evaluation logic
        return "Risk assessment analysis performed on the provided document data."
