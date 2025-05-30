import os

import environ
import replicate
from dotenv import load_dotenv
from replicate.exceptions import ModelError

load_dotenv()

API_KEY = os.getenv("REPLICATE_API_TOKEN")

replicate = replicate.Client(api_token=API_KEY)


class RepliateClient:
    def __init__(self) -> None:
        self.hi = "HI"

    def get_prompt(input):
        try:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": "Make a black and white drawing that is ment to be colored by children of"
                    + input,
                    "aspect_ratio": "3:2",
                    "output_format": "jpg",
                },
            )

            return output
        except ModelError as e:
            return e
