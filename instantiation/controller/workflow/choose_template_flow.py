# from instantiation.controller.agent.agent import FilterAgent
import json
import os
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
    def __init__(self, task_object: TaskObject):
        """
        :param task_dir_name: Folder name of the task, specific for one process.
        :param task_json_object: Json object, which is the json file of the task.
        :param task_path_object: Path object, which is related to the path of the task.
        """

        self.task_object = task_object
        self.embedding_model = ChooseTemplateFlow.load_embedding_model(
            model_name=configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]
        )

    def execute(self):
        """
        Execute the flow.
        """

        self.chose_template_and_copy()

    def create_cache_file(
        self, copy_from_path: str, copy_to_folder_path: str, file_name: str = None
    ) -> str:
        """
        According to the original path, create a cache file.
        :param copy_from_path: The original path of the file.
        :param copy_to_folder_path: The path of the cache file.
        :param file_name: The name of the task file.
        :return: The template path string as a new created file.
        """

        # Create the folder if not exists.
        if not os.path.exists(copy_to_folder_path):
            os.makedirs(copy_to_folder_path)
        time_start = datetime.now()
        template_extension = self.task_object.app_object.file_extension
        if not file_name:
            cached_template_path = os.path.join(
                # current_path,
                copy_to_folder_path,
                time_start.strftime("%Y-%m-%d-%H-%M-%S") + template_extension,
            )
        else:
            cached_template_path = os.path.join(
                copy_to_folder_path, file_name + template_extension
            )
            with open(copy_from_path, "rb") as f:
                ori_content = f.read()
            with open(cached_template_path, "wb") as f:
                f.write(ori_content)
        return cached_template_path

    def get_chosen_file_path(self) -> str:
        """
        Choose the most relative template file.
        :return: The most relative template file path string.
        """

        # get the description of the templates
        templates_description_path = os.path.join(
            configs["TEMPLATE_PATH"],
            self.task_object.app_object.description.lower(),
            "description.json",
        )

        # Check if the description.json file exists
        try:
            with open(templates_description_path, "r") as f:
                templates_file_description = json.load(f)
        except FileNotFoundError:
            print(
                f"Warning: {templates_description_path} does not exist. Choosing a random template."
            )

            # List all available template files
            template_files = [
                f
                for f in os.listdir(
                    os.path.join(
                        configs["TEMPLATE_PATH"],
                        self.task_object.app_object.description.lower(),
                    )
                )
                if os.path.isfile(
                    os.path.join(
                        configs["TEMPLATE_PATH"],
                        self.task_object.app_object.description.lower(),
                        f,
                    )
                )
            ]

            # If no templates are found, raise an exception
            if not template_files:
                raise Exception("No template files found in the specified directory.")

            # Randomly select one of the available template files
            chosen_template_file = random.choice(template_files)
            print(f"Randomly selected template: {chosen_template_file}")
            return chosen_template_file

        templates_file_description = json.load(open(templates_description_path, "r"))

        # get the chosen file path
        chosen_file_path = self.chose_target_template_file(
            self.task_object.task, templates_file_description
        )

        # Print the chosen template for the user
        print(f"Chosen template file: {chosen_file_path}")
        return chosen_file_path

    def chose_template_and_copy(self) -> str:
        """
        Choose the template and copy it to the cache folder.
        """

        # Get the chosen template file path.
        chosen_template_file_path = self.get_chosen_file_path()
        chosen_template_full_path = os.path.join(
            configs["TEMPLATE_PATH"],
            self.task_object.app_object.description.lower(),
            chosen_template_file_path,
        )

        # Get the target template folder path.
        target_template_folder_path = os.path.join(
            configs["TASKS_HUB"], self.task_object.task_dir_name + "_templates"
        )

        # Copy the template to the cache folder.
        template_cached_path = self.create_cache_file(
            chosen_template_full_path,
            target_template_folder_path,
            self.task_object.task_file_name,
        )
        self.task_object.instantial_template_path = template_cached_path

        return template_cached_path

    def chose_target_template_file(
        self, given_task: str, doc_files_description: Dict[str, str]
    ):
        """
        Get the target file based on the semantic similarity of given task and the template file decription.
        :param given_task: The given task.
        :param doc_files_description: The description of the template files.
        :return: The target file path.
        """

        candidates = [
            doc_file_description
            for doc, doc_file_description in doc_files_description.items()
        ]
        file_doc_descriptions = {
            doc_file_description: doc
            for doc, doc_file_description in doc_files_description.items()
        }
        # use FAISS to get the top k control items texts
        db = FAISS.from_texts(candidates, self.embedding_model)
        doc_descriptions = db.similarity_search(given_task, k=1)
        doc_description = doc_descriptions[0].page_content
        doc = file_doc_descriptions[doc_description]
        return doc

    @staticmethod
    def load_embedding_model(model_name: str):
        store = LocalFileStore(configs["CONTROL_EMBEDDING_CACHE_PATH"])
        if not model_name.startswith("sentence-transformers"):
            model_name = "sentence-transformers/" + model_name
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        cached_embedder = CacheBackedEmbeddings.from_bytes_store(
            embedding_model, store, namespace=model_name
        )
        return cached_embedder
