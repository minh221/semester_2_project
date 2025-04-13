from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.crew_docling_source import CrewDoclingSource
import os

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from crewai import Task
from crewai.tasks import TaskOutput

# Define the Pydantic model for the meal planning output
class FoodItem(BaseModel):
	name: str = Field(..., description="Name of the food item")
	portion_size: str = Field(..., description="Portion size of the food item")
	preparation: Optional[str] = Field(None, description="Basic preparation instructions")

class Meal(BaseModel):
    name: str = Field(..., description="Name of the meal (e.g., 'Breakfast', 'Lunch', 'Dinner', 'Snack')")
    foods: List[FoodItem] = Field(..., description="List of foods included in this meal")

class DailyMealPlan(BaseModel):
    day: int = Field(..., description="Day number in the meal plan")
    meals: List[Meal] = Field(..., description="List of meals for this day")
    daily_advice: Optional[str] = Field(None, description="Specific advice for this day")

class MealPlanOutput(BaseModel):
    meal_plan: List[DailyMealPlan] = Field(..., description="Daily meal plans for the requested duration")
    health_condition_considerations: Dict[str, str] = Field(
        ..., 
        description="How the meal plan addresses each health condition"
    )
    dietary_accommodations: Dict[str, str] = Field(
        ..., 
        description="How dietary preferences and allergies were accommodated"
    )
    general_advice: str = Field(..., description="General advice for following the meal plan")


@CrewBase
class MealPlanCrew():
	"""A crew that give you tailored meals for your health can preferences."""
	def __init__(self, knowledge_paths: Optional[List[str]] = None):
		self.knowledge_paths = knowledge_paths # e.g., ['/path/to/knowledge.md']

	gemini_model = LLM(
			model="gemini/gemini-2.0-flash",
			temperature=0.7,
			api_key=os.getenv("GEMINI_API_KEY")
		)
	agents_config = "config/agents.yaml"

	tasks_config = "config/tasks.yaml"

	@agent
	def meal_planner(self) -> Agent:
		return Agent(
			config=self.agents_config['meal_planner'],
			llm=self.gemini_model,
			verbose=True
		)

	@task
	def meal_planning_task(self) -> Task:
		return Task(
			config=self.tasks_config['meal_planning_task'], output_pydantic=MealPlanOutput
		)


	@crew
	def crew(self) -> Crew:
		"""A crew that give you tailored meals for your health can preferences."""
		if self.knowledge_paths is None:
			return Crew(
				agents=self.agents,
				tasks=self.tasks, 
				process=Process.sequential,
				verbose=True,
			)
		else: 
			return Crew(
			agents=self.agents,
			tasks=self.tasks, 
			process=Process.sequential,
			knowledge_sources=[CrewDoclingSource(file_paths=self.knowledge_paths)],
			verbose=True,
		)