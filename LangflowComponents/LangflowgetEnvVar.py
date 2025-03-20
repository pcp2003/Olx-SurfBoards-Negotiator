import os
from dotenv import load_dotenv
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

class GetEnvVar(Component):
    display_name = "Get env var per directory"
    description = "Get env var from a specified directory"
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "code"
    name = "GetEnvVar"

    inputs = [
        MessageTextInput(
            name="env_var_name",
            display_name="Env var name",
            info="Name of the environment variable to get",
            value="",
            tool_mode=True
        ),
        MessageTextInput(
            name="env_dir",
            display_name="Env file directory",
            info="Directory where the .env file is located",
            value="",
            tool_mode=True
        ),
    ]

    outputs = [
        Output(
            display_name="Env var value",
            name="env_var_value",
            method="process_inputs"
        )
    ]

    def process_inputs(self) -> Data:
        # Get directory and env variable name from inputs
        env_var_name = self.env_var_name
        env_dir = self.env_dir
        
        # Load .env file from the specified directory
        dotenv_path = os.path.join(env_dir, ".env")
        load_dotenv(dotenv_path=dotenv_path)
        
        # Check if the environment variable is set
        if env_var_name not in os.environ:
            msg = f"Environment variable {env_var_name} not set"
            raise ValueError(msg)
        
        # Return the environment variable value
        data = Data(value=os.environ[env_var_name])
        self.status = data
        return data 