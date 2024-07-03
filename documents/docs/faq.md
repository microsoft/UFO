# FAQ

We provide answers to some frequently asked questions about the UFO.

## Q1: Why is it called UFO?

A: UFO stands for **U**I **Fo**cused agent. The name is inspired by the concept of an unidentified flying object (UFO) that is mysterious and futuristic.

## Q2: Can I use UFO on Linux or macOS?
A: UFO is currently only supported on Windows OS.

## Q3: Why the latency of UFO is high?
A: The latency of UFO depends on the response time of the LLMs and the network speed. If you are using GPT, it usually takes dozens of seconds to generate a response in one step. The workload of the GPT endpoint may also affect the latency.

## Q4: What models does UFO support?
A: UFO supports various language models, including OpenAI and Azure OpenAI models, QWEN, google Gimini, Ollama, and more. You can find the full list of supported models in the `Supported Models` section of the documentation.

## Q5: Can I use non-vision models in UFO?
A: Yes, you can use non-vision models in UFO. You can set the `VISUAL_MODE` to `False` in the `config.yaml` file to disable the visual mode and use non-vision models. However, UFO is designed to work with vision models, and using non-vision models may affect the performance.

## Q6: Can I host my own LLM endpoint?
A: Yes, you can host your custom LLM endpoint and configure UFO to use it. Check the documentation in the `Supported Models` section for more details.

## Q7: Can I use non-English requests in UFO?
A: It depends on the language model you are using. Most of LLMs support multiple languages, and you can specify the language in the request. However, the performance may vary for different languages.

## Q8: Why it shows the error `Error making API request: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))`?
A: This means the LLM endpoint is not accessible. You can check the network connection (e.g. VPN) and the status of the LLM endpoint. 

!!! info
    To get more support, please submit an issue on the [GitHub Issues](https://github.com/microsoft/UFO/issues), or send an email to [ufo-agent@microsoft.com](mailto:ufo-agent@microsoft.com).