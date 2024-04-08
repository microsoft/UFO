
# Enhancing UFO with RAG using Offline Help Documents


## How to Prepare Your Help Documents ❓

### Step 1: Prepare Your Help Doc and Metadata

UFO currently supports processing help documents in XML format, as this is the default format for official help documents of Microsoft apps. More formats will be supported in the future.

You can write a dedicated document for a specific task of an app in a file named, for example, `task.xml`. Note that it should be accompanied by a metadata file with the same prefix, but with the `.meta` extension, i.e., `task.xml.meta`. This metadata file should have a `title` describing the task at a high level and a `Content-Summary` field summarizing the content of the help document. These two files are used for similarity search with user requests, so please write them carefully. The [ppt-copilot.xml](./doc_example/ppt-copilot.xml) and [ppt-copilot.xml.meta](./doc_example/ppt-copilot.xml.meta) are examples of a help document and its metadata.

### Step 2: Prepare Your Help Document Set

Once you have all help documents and metadata ready, put all of them into a folder. There can be sub-folders for the help documents, but please ensure that each help document and its corresponding metadata **are placed in the same directory**.


## How to Create an Indexer for Your Help Document Set ❓


Once you have all documents ready in a folder named `path_of_the_docs`, you can easily create an offline indexer to support RAG for UFO. Follow these steps:

```console
# assume you are in the cloned UFO folder
python -m learner --app <app_name> --docs <path_of_the_docs>
```
Replace `app_name` with the name of the application, such as PowerPoint or WeChat.
> Note: Ensure the `app_name` is accurately defined as it is used to match the offline indexer in online RAG.

Replace `path_of_the_docs` with the full path to the folder containing all your documents.

This command will create an offline indexer for all documents in the `path_of_the_docs` folder using Faiss and embedding with sentence transformer (more embeddings will be supported soon). The created index by default will be placed [here](../vectordb/docs/).



## How to Enable RAG from Help Documents during Online Inference ❓
To enable this in online inference, you can set the following configuration in the `ufo/config/config.yaml` file:
```bash
## RAG Configuration for the offline docs
RAG_OFFLINE_DOCS: True  # Whether to use the offline RAG.
RAG_OFFLINE_DOCS_RETRIEVED_TOPK: 1  # The topk for the offline retrieved documents
```
Adjust `RAG_OFFLINE_DOCS_RETRIEVED_TOPK` to optimize performance.
