from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel
# Importing the tool classes as defined in the previous step
from tools.custom_tool import search_tool, FinancialDocumentTool, InvestmentTool, RiskTool

# Define a schema for the verification result to ensure deterministic output
class VerificationResult(BaseModel):
    is_financial_doc: bool
    reason: str

@CrewBase
class WingifyCorrectCode():
    """WingifyCorrectCode crew for high-fidelity financial analysis"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # --- Agents ---

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_analyst'],
            # Using instantiated tools as per refactored tools.py
            tools=[FinancialDocumentTool(), search_tool],
            verbose=True
        )

    @agent
    def verifier(self) -> Agent:
        return Agent(
            config=self.agents_config['verifier'],
            # Verifier only needs the PDF reader to check validity
            tools=[FinancialDocumentTool()],
            verbose=True
        )

    @agent
    def investment_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['investment_advisor'],
            # Investment advisor can now use the specialized investment tool
            tools=[InvestmentTool()],
            verbose=True
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_assessor'],
            # Risk assessor uses the specialized risk tool
            tools=[RiskTool()],
            verbose=True
        )

    # --- Tasks ---

    @task
    def verification(self) -> Task:
        return Task(
            config=self.tasks_config['verification'],
            agent=self.verifier(),
            output_json=VerificationResult
        )

    @task
    def analyze_financial_document(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_financial_document'],
            agent=self.financial_analyst(),
            context=[self.verification()] 
        )

    @task
    def investment_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['investment_analysis'],
            agent=self.investment_advisor(),
            context=[self.analyze_financial_document()]
        )

    @task
    def risk_assessment(self) -> Task:
        return Task(
            config=self.tasks_config['risk_assessment'],
            agent=self.risk_assessor(),
            context=[self.analyze_financial_document()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the WingifyCorrectCode crew"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )