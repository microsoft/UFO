# Providing Help Documents to the AppAgent

Help documents provide guidance to the `AppAgent` in executing specific tasks. The `AppAgent` uses these documents to understand the context of the task and the steps required to execute it, effectively becoming an expert in the application.

## How to Provide Help Documents to the AppAgent?

### Step 1: Prepare Help Documents and Metadata

Currently, UFO supports processing help documents in XML format, which is the default format for official help documents of Microsoft apps. More formats will be supported in the future.

To create a dedicated document for a specific task of an app, save it in a file named, for example, `task.xml`. This document should be accompanied by a metadata file with the same prefix but with the `.meta` extension, such as `task.xml.meta`. The metadata file should include:

- `title`: Describes the task at a high level.
- `Content-Summary`: Summarizes the content of the help document.

These two files are used for similarity search with user requests, so it is important to write them carefully. Examples of a help document and its metadata can be found [here](https://github.com/microsoft/UFO/blob/main/learner/doc_example/ppt-copilot.xml) and [here](https://github.com/microsoft/UFO/blob/main/learner/doc_example/ppt-copilot.xml.meta).

### Step 2: Place Help Documents in the AppAgent Directory

Once you have prepared all help documents and their metadata, place them into a folder. Sub-folders for the help documents are allowed, but ensure that each help document and its corresponding metadata are placed in the same directory.

### Step 3: Create a Help Document Indexer

After organizing your documents in a folder named `path_of_the_docs`, you can create an offline indexer to support RAG for UFO. Follow these steps:

```bash
# Assume you are in the cloned UFO folder
python -m learner --app <app_name> --docs <path_of_the_docs>
```

- Replace `<app_name>` with the name of the application, such as PowerPoint or WeChat.
- Replace `<path_of_the_docs>` with the full path to the folder containing all your documents.

This command will create an offline indexer for all documents in the `path_of_the_docs` folder using Faiss and embedding with sentence transformer (additional embeddings will be supported soon). By default, the created index will be placed [here](https://github.com/microsoft/UFO/tree/main/vectordb/docs).

!!! note
    Ensure the `app_name` is accurately defined, as it is used to match the offline indexer in online RAG.


### How to Use Help Documents to Enhance the AppAgent?

After creating the offline indexer, you can find the guidance on how to use the help documents to enhance the AppAgent in the [Learning from Help Documents](../advanced_usage/reinforce_appagent/learning_from_help_document.md) section.