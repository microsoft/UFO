# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.utils import get_hugginface_embedding
from . import xml_loader, json_loader, basic
from .utils import load_json_file, save_json_file, print_with_color
from langchain_community.vectorstores import FAISS
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


class DocumentsIndexer:
    """
    The class for the documents indexer.
    """

    _doc_loader_mapper = {
        "xml": xml_loader.XMLLoader,
        "json": json_loader.JsonLoader,
    }

    @staticmethod
    def create_indexer(
        app: str, docs: str, format: str, incremental: bool, save_path: str
    ):
        """
        Create an indexer for the given application.
        :param app: The name of the application to create an indexer for.
        :param docs: The help documents dir for the application.
        :param format: The format of the help documents.
        :param incremental: Whether to enable incremental updates.
        :param save_path: The path to save the indexer to.
        :return: The created indexer.
        """

        if os.path.exists("./learner/records.json"):
            records = load_json_file("./learner/records.json")
        else:
            records = {}

        print_with_color("Loading documents from {docs}...".format(docs=docs), "cyan")

        if format not in DocumentsIndexer._doc_loader_mapper.keys():
            raise ValueError("Invalid format: " + format)

        loader: basic.BasicDocumentLoader = DocumentsIndexer._doc_loader_mapper[format](
            docs
        )
        documents = loader.construct_document()

        print_with_color(
            "Creating indexer for {num} documents for {app}...".format(
                num=len(documents), app=app
            ),
            "yellow",
        )

        embeddings = get_hugginface_embedding()

        db = FAISS.from_documents(documents, embeddings)

        if incremental:
            if app in records:
                print_with_color("Merging with previous indexer...", "yellow")
                prev_db = FAISS.load_local(
                    records[app], embeddings, allow_dangerous_deserialization=True
                )
                db.merge_from(prev_db)

        db_file_path = os.path.join(save_path, app)
        db_file_path = os.path.abspath(db_file_path)
        db.save_local(db_file_path)

        records[app] = db_file_path

        save_json_file("./learner/records.json", records)

        print_with_color(
            "Indexer for {app} created successfully. Save in {path}.".format(
                app=app, path=db_file_path
            ),
            "green",
        )

        return db_file_path
