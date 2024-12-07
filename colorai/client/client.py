import os

import environ
import replicate
from dotenv import load_dotenv
from replicate.exceptions import ModelError

load_dotenv()
print("hi")
API_KEY = os.getenv("REPLICATE_API_TOKEN")


replicate = replicate.Client(api_token=API_KEY)


class Client:
    def __init__(self) -> None:
        self.hi = "HI"

    def get_prompt(input):
        try:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={"prompt": "Make a chields coloring drawing of" + input},
            )

            print(output)
            return output
        except ModelError as e:
            return e
