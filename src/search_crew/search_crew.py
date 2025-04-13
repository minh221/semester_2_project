from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
import os

@CrewBase
class SearchCrew():
	"""A crew that helps you with nutrition research and report generation."""
	gemini_model = LLM(
			model="gemini/gemini-2.0-flash",
			temperature=0.7,
			api_key=os.getenv("GEMINI_API_KEY")
		)
	agents_config = "config/agents.yaml"

	tasks_config = "config/tasks.yaml"


	@agent
	def nutrition_advisor(self) -> Agent:
		return Agent(
			config=self.agents_config['nutrition_advisor'],
			llm=self.gemini_model,
			tools=[SerperDevTool(), ScrapeWebsiteTool()],
			verbose=True
		)

	@agent
	def nutrition_report_creator(self) -> Agent:
		return Agent(
			config=self.agents_config['nutrition_report_creator'],
			llm=self.gemini_model,
			verbose=True
		)

	@task
	def nutrition_research_task(self) -> Task:
		return Task(
			config=self.tasks_config['nutrition_research_task'],
		)

	@task
	def nutrition_reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['nutrition_reporting_task']
		)

	@crew
	def crew(self) -> Crew:
		"""A crew that helps you with nutrition research and report generation."""
		return Crew(
			agents=self.agents,
			tasks=self.tasks, 
			process=Process.sequential,
			verbose=True,
		)