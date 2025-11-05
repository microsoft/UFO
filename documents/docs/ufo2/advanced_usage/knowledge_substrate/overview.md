# Reinforcing AppAgent

UFO provides versatile mechanisms to reinforce the AppAgent's capabilities through RAG (Retrieval-Augmented Generation) and other techniques. These enhance the AppAgent's understanding of the task, improving the quality of the generated plans, and increasing the efficiency of the AppAgent's interactions with the application.

We currently support the following reinforcement methods:

| Reinforcement Method | Description |
|----------------------|-------------|
| [Learning from Help Documents](./learning_from_help_document.md) | Reinforce the AppAgent by retrieving knowledge from help documents. |
| [Learning from Bing Search](./learning_from_bing_search.md) | Reinforce the AppAgent by searching for information on Bing to obtain up-to-date knowledge. |
| [Learning from Self-Experience](./experience_learning.md) | Reinforce the AppAgent by learning from its own successful experiences. |
| [Learning from User Demonstrations](./learning_from_demonstration.md) | Reinforce the AppAgent by learning from action trajectories demonstrated by users. |

## Knowledge Provision

UFO provides the knowledge to the AppAgent through a `context_provision` method defined in the `AppAgent` class:

```python
def context_provision(self, request: str = "") -> None:
    """
    Provision the context for the app agent.
    :param request: The Bing search query.
    """

    # Load the offline document indexer for the app agent if available.
    if configs["RAG_OFFLINE_DOCS"]:
        utils.print_with_color(
            "Loading offline help document indexer for {app}...".format(
                app=self._process_name
            ),
            "magenta",
        )
        self.build_offline_docs_retriever()

    # Load the online search indexer for the app agent if available.

    if configs["RAG_ONLINE_SEARCH"] and request:
        utils.print_with_color("Creating a Bing search indexer...", "magenta")
        self.build_online_search_retriever(
            request, configs["RAG_ONLINE_SEARCH_TOPK"]
        )

    # Load the experience indexer for the app agent if available.
    if configs["RAG_EXPERIENCE"]:
        utils.print_with_color("Creating an experience indexer...", "magenta")
        experience_path = configs["EXPERIENCE_SAVED_PATH"]
        db_path = os.path.join(experience_path, "experience_db")
        self.build_experience_retriever(db_path)

    # Load the demonstration indexer for the app agent if available.
    if configs["RAG_DEMONSTRATION"]:
        utils.print_with_color("Creating an demonstration indexer...", "magenta")
        demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
        db_path = os.path.join(demonstration_path, "demonstration_db")
        self.build_human_demonstration_retriever(db_path)
```

The `context_provision` method loads the offline document indexer, online search indexer, experience indexer, and demonstration indexer for the AppAgent based on the configuration settings in the `config_dev.yaml` file.

# Reference
UFO employs the `Retriever` class located in the `ufo/rag/retriever.py` file to retrieve knowledge from various sources. The `Retriever` class provides the following methods to retrieve knowledge:

:::rag.retriever.Retriever
