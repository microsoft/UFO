import json
import os
import random
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict

from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dataflow.instantiation.agent.template_agent import TemplateAgent

from dataflow.config.config import Config

_configs = Config.get_instance().config_data


class ChooseTemplateFlow:
    """
    Class to select and copy the most relevant template file based on the given task context.
    """

    _SENTENCE_TRANSFORMERS_PREFIX = "sentence-transformers/"

    def __init__(self, app_name: str, task_file_name: str, file_extension: str):
        """
        Initialize the flow with the given task context.
        :param app_name: The name of the application.
        :param file_extension: The file extension of the template.
        :param task_file_name: The name of the task file.
        """

        self._app_name = app_name
        self._file_extension = file_extension
        self._task_file_name = task_file_name
        self.execution_time = None
        self._embedding_model = self._load_embedding_model(
            model_name=_configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]
        )

    def execute(self) -> str:
        """
        Execute the flow and return the copied template path.
        :return: The path to the copied template file.
        """

        start_time = time.time()
        try:
            template_copied_path = self._choose_template_and_copy()
        except Exception as e:
            raise e
        finally:
            self.execution_time = round(time.time() - start_time, 3)
        return template_copied_path

    def _create_copied_file(
        self, copy_from_path: Path, copy_to_folder_path: Path, file_name: str = None
    ) -> str:
        """
        Create a cache file from the specified source.
        :param copy_from_path: The original path of the file.
        :param copy_to_folder_path: The path where the cache file will be created.
        :param file_name: Optional; the name of the task file.
        :return: The path to the newly created cache file.
        """

        os.makedirs(copy_to_folder_path, exist_ok=True)
        copied_template_path = self._generate_copied_file_path(
            copy_to_folder_path, file_name
        )

        with open(copy_from_path, "rb") as f:
            ori_content = f.read()
        with open(copied_template_path, "wb") as f:
            f.write(ori_content)

        return copied_template_path

    def _generate_copied_file_path(self, folder_path: Path, file_name: str) -> str:
        """
        Generate the file path for the copied template.
        :param folder_path: The folder where the file will be created.
        :param file_name: Optional; the name of the task file.
        :return: The path to the newly created file.
        """

        template_extension = self._file_extension
        if file_name:
            return str(folder_path / f"{file_name}{template_extension}")
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return str(folder_path / f"{timestamp}{template_extension}")

    def _get_chosen_file_path(self) -> str:
        """
        Choose the most relevant template file based on the task.
        :return: The path to the most relevant template file.
        """

        templates_description_path = (
            Path(_configs["TEMPLATE_PATH"]) / self._app_name / "description.json"
        )

        try:
            with open(templates_description_path, "r") as f:
                return self._choose_target_template_file(
                    self._task_file_name, json.load(f)
                )
        except FileNotFoundError:
            warnings.warn(
                f"Warning: {templates_description_path} does not exist. Choosing a random template."
            )
            return self._choose_random_template()

    def _choose_random_template(self) -> str:
        """
        Select a random template file from the template folder.
        :return: The path to the randomly selected template file.
        """

        template_folder = Path(_configs["TEMPLATE_PATH"]) / self._app_name
        template_files = [f for f in template_folder.iterdir() if f.is_file()]

        if not template_files:
            raise Exception("No template files found in the specified directory.")

        chosen_template_file = random.choice(template_files)
        print(f"Randomly selected template: {chosen_template_file.name}")
        return str(chosen_template_file)

    def _choose_template_and_copy(self) -> str:
        """
        Choose the template and copy it to the cache folder.
        :return: The path to the copied template file.
        """

        chosen_template_file_path = self._get_chosen_file_path()
        chosen_template_full_path = (
            Path(_configs["TEMPLATE_PATH"]) / self._app_name / chosen_template_file_path
        )

        target_template_folder_path = Path(
            _configs["RESULT_HUB"].format(task_type="saved_document")
        ) / (os.path.dirname(os.path.dirname(self._task_file_name)))

        return self._create_copied_file(
            chosen_template_full_path, target_template_folder_path, self._task_file_name
        )

    def _choose_target_template_file(
        self, given_task: str, doc_files_description: Dict[str, str]
    ) -> str:
        """
        Get the target file based on the semantic similarity of the given task and the template file descriptions.
        :param given_task: The task to be matched.
        :param doc_files_description: A dictionary of template file descriptions.
        :return: The path to the chosen template file.
        """

        if _configs["TEMPLATE_METHOD"] == "SemanticSimilarity":
            return self._choose_target_template_file_semantic(
                given_task, doc_files_description
            )
        elif _configs["TEMPLATE_METHOD"] == "LLM":
            self.template_agent = TemplateAgent(
                "template",
                is_visual=True,
                main_prompt=_configs["TEMPLATE_PROMPT"],
            )
            return self._choose_target_template_file_llm(
                given_task, doc_files_description
            )
        else:
            raise ValueError("Invalid TEMPLATE_METHOD.")

    def _choose_target_template_file_semantic(
        self, given_task: str, doc_files_description: Dict[str, str]
    ) -> str:
        """
        Get the target file based on the semantic similarity of the given task and the template file descriptions.
        :param given_task: The task to be matched.
        :param doc_files_description: A dictionary of template file descriptions.
        :return: The path to the chosen template file.
        """

        file_doc_map = {
            desc: file_name for file_name, desc in doc_files_description.items()
        }
        db = FAISS.from_texts(
            list(doc_files_description.values()), self._embedding_model
        )
        most_similar = db.similarity_search(given_task, k=1)

        if not most_similar:
            raise ValueError("No similar templates found.")
        return file_doc_map[most_similar[0].page_content]

    def _choose_target_template_file_llm(
        self, given_task: str, doc_files_description: Dict[str, str]
    ) -> str:
        """
        Get the target file based on the LLM of the given task and the template file descriptions.
        :param given_task: The task to be matched.
        :param doc_files_description: A dictionary of template file descriptions.
        :return: The path to the chosen template file.
        """

        prompt_message = self.template_agent.message_constructor(
            doc_files_description, given_task
        )
        response_string, _ = self.template_agent.get_response(
            prompt_message, "prefill", use_backup_engine=True, configs=_configs
        )
        if response_string is None:
            raise ValueError("No similar templates found.")
        elif "```json" in response_string:
            response_string = response_string[7:-3]
        response_json = json.loads(response_string)
        file_name = list(response_json.keys())[0]
        if file_name not in doc_files_description:
            print(f"Template {file_name} not found in the description.")
            raise ValueError("No similar templates found.")
        return file_name

    @staticmethod
    def _load_embedding_model(model_name: str) -> CacheBackedEmbeddings:
        """
        Load the embedding model.
        :param model_name: The name of the embedding model to load.
        :return: The loaded embedding model.
        """

        store = LocalFileStore(_configs["CONTROL_EMBEDDING_CACHE_PATH"])
        if not model_name.startswith(ChooseTemplateFlow._SENTENCE_TRANSFORMERS_PREFIX):
            model_name = ChooseTemplateFlow._SENTENCE_TRANSFORMERS_PREFIX + model_name
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        return CacheBackedEmbeddings.from_bytes_store(
            embedding_model, store, namespace=model_name
        )
