import replicate


class Client:
    def __init__(self) -> None:
        self.api_key = api_key

    def get_prompt(input):
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={"prompt": "make a chields coloring drawing of" + input},
        )

        print(output)
