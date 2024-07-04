# Learning from Help Documents

User or applications can provide help documents to the AppAgent to reinforce its capabilities. The AppAgent can retrieve knowledge from these documents to improve its understanding of the task, generate high-quality plans, and interact more efficiently with the application. You can find how to provide help documents to the AppAgent in the [Help Document Provision](../../creating_app_agent/help_document_provision.md) section.


## Mechanism
The help documents are provided in a format of **task-solution pairs**. Upon receiving a request, the AppAgent retrieves the relevant help documents by matching the request with the task descriptions in the help documents and generates a plan based on the retrieved solutions.

!!! note
    Since the retrieved help documents may not be relevant to the request, the `AppAgent` will only take them as references to generate the plan. 

## Activate the Learning from Help Documents

Follow the steps below to activate the learning from help documents:

### Step 1: Provide Help Documents
Please follow the steps in the [Help Document Provision](../../creating_app_agent/help_document_provision.md) document to provide help documents to the AppAgent.

### Step 2: Configure the AppAgent

Configure the following parameters in the `config.yaml` file to activate the learning from help documents:

| Configuration Option | Description | Type | Default Value |
|----------------------|-------------|------|---------------|
| `RAG_OFFLINE_DOCS` | Whether to use the offline RAG | Boolean | False |
| `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` | The topk for the offline retrieved documents | Integer | 1 |


# Reference

:::rag.retriever.OfflineDocRetriever