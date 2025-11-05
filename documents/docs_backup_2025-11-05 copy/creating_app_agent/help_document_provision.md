# Providing Help Documents to the AppAgent

Help documents provide guidance to the `AppAgent` in executing specific tasks. The `AppAgent` uses these documents to understand the context of the task and the steps required to execute it, effectively becoming an expert in the application.

## How to Provide Help Documents to the AppAgent?

### Step 1: Prepare Help Documents and Metadata

UFO currently supports processing help documents in `json` format. More formats will be supported in the future.

An example of a help document in `json` format is as follows:

```json
{
    "application": "chrome",
    "request": "How to change the username in chrome profiles?",
    "guidance": [
        "Click the profile icon in the upper-right corner of the Chrome window.",
        "Click the gear icon labeled 'Manage Chrome Profiles' in the profile menu.",
        "In the list of profiles, locate the profile whose name you want to change.",
        "Hover over the desired profile and click the three-dot menu icon on that profile card.",
        "Select 'Edit' from the dropdown menu.",
        "In the Edit Profile dialog, click inside the name field.",
        "Delete the current name and type your new desired username.",
        "Click 'Save' to confirm the changes.",
        "Verify that the profile name is updated in the profile list and in the top-right corner of Chrome."
    ]
}
```

Save each help document in a `json` file of your target folder.

### Step 2: Place Help Documents in the AppAgent Directory

Once you have prepared all help documents and their metadata, place them into a folder. Sub-folders for the help documents are allowed, but ensure that each help document and its corresponding metadata are placed in the same directory.

### Step 3: Create a Help Document Indexer

After organizing your documents in a folder named `path_of_the_docs`, you can create an offline indexer to support RAG for UFO. Follow these steps:

```bash
# Assume you are in the cloned UFO folder
python -m learner --app <app_name> --docs <path_of_the_docs>
```

- Replace `<app_name>` with the **Exact Process Name** of the application, such as `WINWORD.EXE` for Microsoft Word or `POWERPNT.EXE` for PowerPoint. 
- Replace `<path_of_the_docs>` with the full path to the folder containing all your documents.

This command will create an offline indexer for all documents in the `path_of_the_docs` folder using Faiss and embedding with sentence transformer (additional embeddings will be supported soon). By default, the created index will be placed [here](https://github.com/microsoft/UFO/tree/main/vectordb/docs).

!!! note
    Ensure the `app_name` is accurately defined, as it is used to match the offline indexer in online RAG.


### How to Use Help Documents to Enhance the AppAgent?

After creating the offline indexer, you can find the guidance on how to use the help documents to enhance the `AppAgent` in the [Learning from Help Documents](../advanced_usage/reinforce_appagent/learning_from_help_document.md) section.