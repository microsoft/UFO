# OpenAI CUA (Operator)

The [Opeartor](https://openai.com/index/computer-using-agent/) is a specialized agentic model tailored for Computer-Using Agents (CUA). We now support calling via the Azure OpenAI API (AOAI). The following sections provide a comprehensive guide on how to set up and use the AOAI API with UFO. Note that now AOAI only supports the [Response API](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/responses?tabs=python-secure) to invoke the model.



## Step 1
To use the Azure OpenAI API, you need to create an account on the [Azure OpenAI website](https://azure.microsoft.com/en-us/products/ai-services/openai-service). After creating an account, you can deploy the AOAI API and access the API key.

## Step 2
After obtaining the API key, you can configure the `OPERATOR` in the `config.yaml` file (rename the `config_template.yaml` file to `config.yaml`) to use the Azure OpenAI API. The following is an example configuration for the Azure OpenAI API:

```yaml
OPERATOR: {
  SCALER: [1024, 768], # The scaler for the visual input in a list format, [width, height]
  API_TYPE: "azure_ad" , # The API type, "openai" for the OpenAI API, "aoai" for the AOAI API, 'azure_ad' for the ad authority of the AOAI API.  
  API_MODEL: "computer-use-preview-20250311",  #"gpt-4o-mini-20240718", #"gpt-4o-20240513",  # The only OpenAI model by now that accepts visual input
  API_VERSION: "2025-03-01-preview", # "2024-02-15-preview" by default
  API_BASE: "<YOUR_ENDPOINT>", # The the OpenAI API endpoint, "https://api.openai.com/v1/chat/completions" for the OpenAI API. As for the AAD, it should be your endpoints.
}
```

If you want to use AAD for authentication, you should additionally set the following configuration:

```yaml
    AAD_TENANT_ID: "YOUR_TENANT_ID", # Set the value to your tenant id for the llm model
    AAD_API_SCOPE: "YOUR_SCOPE", # Set the value to your scope for the llm model
    AAD_API_SCOPE_BASE: "YOUR_SCOPE_BASE" # Set the value to your scope base for the llm model, whose format is API://YOUR_SCOPE_BASE, and the only need is the YOUR_SCOPE_BASE
```

## Step 3

Now UFO only support to run Operator as a single agent, or as a separate `AppAgent` that can be called by the `HostAgent`. Please refer to the [documents](../advanced_usage/operator_as_app_agent.md) for how to run Operator within UFO. 

!!!note
    The Opeartor is a visual-only model and use different workflow from the other models. Currently, it does not support reuse the `AppAgent` workflow. Please refer to the documents for how to run Operator within UFO.

