import datetime  # For getting the current time

from dotenv import load_dotenv  # For loading environment variables

load_dotenv()  # Load environment variables from a .env file

from langchain_core.messages import HumanMessage  # For creating human messages
from langchain_core.output_parsers.openai_tools import (
    JsonOutputToolsParser,  # For parsing JSON outputs from LLM tools
    PydanticToolsParser,  # For parsing outputs into Pydantic models
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)  # For prompt templates
from langchain_openai import ChatOpenAI  # For OpenAI chat model integration

from schemas import AnswerQuestion, ReviseAnswer  # Import custom Pydantic schemas
import os

# Initialize the language model with a specific model name
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-nano"))

# Output parsers for handling LLM tool outputs
parser = JsonOutputToolsParser(return_id=True)
parser_pydantic = PydanticToolsParser(tools=[AnswerQuestion])

# Template for the actor's prompt, including system instructions and message placeholders
actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are expert researcher.
            Current time: {time}

            1. {first_instruction}
            2. Reflect and critique your answer. Be severe to maximize improvement.
            3. Recommend search queries to research information and improve your answer.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above using the required format."),
    ]
).partial(
    time=lambda: datetime.datetime.now().isoformat(),  # Inject current time into the prompt
)

# Prompt template for the first responder, instructing to provide a detailed answer
first_responder_prompt_template = actor_prompt_template.partial(
    first_instruction="Provide a detailed ~500 word answer."
)

# Chain for the first responder: prompt -> LLM with tool binding
first_responder = first_responder_prompt_template | llm.bind_tools(
    tools=[AnswerQuestion], tool_choice="AnswerQuestion"
)

# Instructions for revising an answer, including requirements for citations and references
revise_instructions = """Revise your previous answer using the new information.
        - You should use the previous critique to add important information to your answer.
        - You MUST include numerical citations in your revised answer to ensure it can be verified.
        - You should use the previous critique to remove superfluous information from your answer and make SURE it is not more than 500 words.
"""
# 
# Chain for the revisor: prompt with revision instructions -> LLM with tool binding
revisor = actor_prompt_template.partial(
    first_instruction=revise_instructions
) | llm.bind_tools(tools=[ReviseAnswer], tool_choice="ReviseAnswer")

# Example usage: run the chain if this script is executed directly
if __name__ == "__main__":
    # Create a human message with a specific content prompt
    human_message = HumanMessage(
        content="Write about AI-Powered SOC / autonomous soc  problem domain,"
        " list startups that do that and raised capital."
    )
    # Build the chain: prompt -> LLM tool -> parse output into Pydantic model
    chain = (
        first_responder_prompt_template
        | llm.bind_tools(tools=[AnswerQuestion], tool_choice="AnswerQuestion")
        | parser_pydantic
    )

    # Invoke the chain with the human message as input
    res = chain.invoke(input={"messages": [human_message]})
    print(res)  # Print the result
