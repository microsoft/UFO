import json
import os
import random
import warnings
from datetime import datetime
from typing import Dict

from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from instantiation.config.config import Config
from instantiation.instantiation import TaskObject

configs = Config.get_instance().config_data


class ChooseTemplateFlow:
    _SENTENCE_TRANSFORMERS_PREFIX = "sentence-transformers/"

    def __init__(self, task_object: TaskObject):
        """
        Initialize the flow with the given task object.
        :param task_object: An instance of TaskObject, representing the task context.
        """
        self.task_object = task_object
        self._embedding_model = self._load_embedding_model(
            model_name=configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]
        )

    def execute(self) -> str:
        """
        Execute the flow and return the copied template path.
        :return: The path to the copied template file.
        """
        template_copied_path=self._choose_template_and_copy()

        return template_copied_path

    def _create_copied_file(
        self, copy_from_path: str, copy_to_folder_path: str, file_name: str = None
    ) -> str:
        """
        Create a cache file from the specified source.
        :param copy_from_path: The original path of the file.
        :param copy_to_folder_path: The path where the cache file will be created.
        :param file_name: Optional; the name of the task file.
        :return: The path to the newly created cache file.
        """
        os.makedirs(copy_to_folder_path, exist_ok=True)
        time_start = datetime.now()
        template_extension = self.task_object.app_object.file_extension

        if not file_name:
            copied_template_path = os.path.join(
                copy_to_folder_path,
                time_start.strftime("%Y-%m-%d-%H-%M-%S") + template_extension,
            )
        else:
            copied_template_path = os.path.join(
                copy_to_folder_path, file_name + template_extension
            )
            with open(copy_from_path, "rb") as f:
                ori_content = f.read()
            with open(copied_template_path, "wb") as f:
                f.write(ori_content)
                
        return copied_template_path

    def _get_chosen_file_path(self) -> str:
        """
        Choose the most relevant template file based on the task.
        :return: The path to the most relevant template file.
        """
        templates_description_path = os.path.join(
            configs["TEMPLATE_PATH"],
            self.task_object.app_object.description.lower(),
            "description.json",
        )

        try:
            with open(templates_description_path, "r") as f:
                templates_file_description = json.load(f)
        except FileNotFoundError:
            warnings.warn(
                f"Warning: {templates_description_path} does not exist. Choosing a random template."
            )
            template_folder = os.path.join(
                configs["TEMPLATE_PATH"],
                self.task_object.app_object.description.lower(),
            )
            template_files = [
                f
                for f in os.listdir(template_folder)
                if os.path.isfile(os.path.join(template_folder, f))
            ]

            if not template_files:
                raise Exception("No template files found in the specified directory.")

            chosen_template_file = random.choice(template_files)
            print(f"Randomly selected template: {chosen_template_file}")
            return chosen_template_file

        chosen_file_path = self._choose_target_template_file(
            self.task_object.task, templates_file_description
        )
        print(f"Chosen template file: {chosen_file_path}")
        return chosen_file_path

    def _choose_template_and_copy(self) -> str:
        """
        Choose the template and copy it to the cache folder.
        :return: The path to the copied template file.
        """
        chosen_template_file_path = self._get_chosen_file_path()
        chosen_template_full_path = os.path.join(
            configs["TEMPLATE_PATH"],
            self.task_object.app_object.description.lower(),
            chosen_template_file_path,
        )

        target_template_folder_path = os.path.join(
            configs["TASKS_HUB"], self.task_object.task_dir_name + "_templates"
        )

        template_copied_path = self._create_copied_file(
            chosen_template_full_path,
            target_template_folder_path,
            self.task_object.task_file_name,
        )
        self.task_object.instantial_template_path = template_copied_path

        return template_copied_path

    def _choose_target_template_file(
        self, given_task: str, doc_files_description: Dict[str, str]
    ) -> str:
        """
        Get the target file based on the semantic similarity of the given task and the template file descriptions.
        :param given_task: The task to be matched.
        :param doc_files_description: A dictionary of template file descriptions.
        :return: The path to the chosen template file.
        """
        candidates = list(doc_files_description.values())
        file_doc_descriptions = {
            doc_file_description: doc
            for doc, doc_file_description in doc_files_description.items()
        }

        db = FAISS.from_texts(candidates, self._embedding_model)
        doc_descriptions = db.similarity_search(given_task, k=1)

        if not doc_descriptions:
            raise Exception("No similar templates found.")

        doc_description = doc_descriptions[0].page_content
        doc = file_doc_descriptions[doc_description]
        return doc

    @staticmethod
    def _load_embedding_model(model_name: str):
        """
        Load the embedding model.
        :param model_name: The name of the embedding model to load.
        :return: The loaded embedding model.
        """
        store = LocalFileStore(configs["CONTROL_EMBEDDING_CACHE_PATH"])
        if not model_name.startswith(ChooseTemplateFlow._SENTENCE_TRANSFORMERS_PREFIX):
            model_name = ChooseTemplateFlow._SENTENCE_TRANSFORMERS_PREFIX + model_name
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        cached_embedder = CacheBackedEmbeddings.from_bytes_store(
            embedding_model, store, namespace=model_name
        )
        return cached_embedder
