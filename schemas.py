from typing import List

# Import BaseModel and Field from langchain_core's pydantic_v1 module
from langchain_core.pydantic_v1 import BaseModel, Field


# Define a Pydantic model for reflection critiques
class Reflection(BaseModel):
    # Field for critique about missing information
    missing: str = Field(description="Critique of what is missing.")
    # Field for critique about superfluous or unnecessary information
    superfluous: str = Field(description="Critique of what is superfluous.")


# Define a Pydantic model for answering a question and providing a reflection
class AnswerQuestion(BaseModel):
    # The main answer to the question, expected to be a detailed response (~250 words)
    answer: str = Field(description="~500 word detailed answer to the question.")
    # A reflection on the answer, using the Reflection model to critique the response
    reflection: Reflection = Field(description="Reflection on the answer")
    search_queries: List[str] = Field(
        description="1-3 search queries for researching improvements to address the critique of your current answer."
    )


class ReviseAnswer(AnswerQuestion):
    """
    Pydantic model for revising an answer to a question.

    Inherits from AnswerQuestion, and adds a list of references (citations)
    that support or motivate the updated answer.
    """
    references: List[str] = Field(
        description="Citations (as URLs or references) that support your revised answer."
    )
