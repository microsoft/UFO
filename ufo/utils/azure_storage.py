# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from typing import List

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from ufo.config.config import Config
from ufo import utils

configs = Config.get_instance().config_data

class AzureBlobStorage:
    """
    Azure Blob Storage Service, manage upload and download operations
    """

    def __init__(self):
        self.account_url = configs["ACCOUNT_URL"]
        self.container_name = configs["CONTAINER_NAME"]
        # locad credential from local `az login`
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=credential
        )

        self.container_client = blob_service_client.get_container_client(self.container_name)
        if not self.container_client.exists():
            utils.print_with_color(f"Container {self.container_name} not exist in blob {self.account_url}", "red")

    def list_blobs(self, prefix: str = None) -> List[str]:
        """
        List blobs in the container
        :return:
        """
        if prefix is None:
            return self.container_client.list_blobs()
        else:
            return self.container_client.list_blobs(prefix=prefix)

    def upload_file(self, blob_name, input_file_path: str) -> None:
        """
        Upload a file to Azure Blob Storage
        :param blob_name: the expected name in azure blob
        :param input_file_path: input file path
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        with open(input_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    def download(self, blob_name: str, output_file_path: str):
        """
        Download a file from Azure Blob Storage
        :param blob_name: name in blob
        :param output_file_path: output file path
        :return:
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        with open(output_file_path, "wb") as output_file:
            output_file.write(blob_client.download_blob().readall())

    def delete(self, blob_name: str, is_folder: bool = False) -> None:
        """
        Delete a file from Azure Blob Storage
        :param blob_name: file name in blob
        :param is_folder: file of folder
        :return:
        """
        if is_folder:
            blobs = self.container_client.list_blobs(name_starts_with=blob_name)
            # delete all blob under folder
            for blob in blobs:
                blob_name = blob.name
                blob_client = self.container_client.get_blob_client(blob_name)
                blob_client.delete_blob()
        else:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
        utils.print_with_color(f"Delete {blob_name} in {self.account_url}/{self.container_name}", "green")


    def upload_ufo_logs(self, log_path: str, data_source: str = "") -> None:
        """
        Upload UFO log to Azure Blob Storage
        :param log_path: relative path of UFO log file
        :param data_source: data source
        """
        absolute_log_path = os.path.abspath(log_path)
        log_prefix = os.path.join(data_source, log_path).replace("\\", "/")
        for root, dirs, files in os.walk(absolute_log_path):
            for file in files:
                log_file_path = os.path.join(root, file)
                blob_name = os.path.join(log_prefix, os.path.relpath(log_file_path, absolute_log_path)).replace("\\", "/")
                self.upload_file(blob_name, log_file_path)
        utils.print_with_color(f"Upload log: {log_path} --> {log_prefix}", "green")

    def upload_dataflow_outputs(self, results_hub_path: str, data_source: str = "") -> None:
        """
        Upload dataflow outputs to Azure Blob Storage
        :param results_hub_path: relative path of dataflow outputs
        :param data_source: data source
        """
        absolute_log_path = os.path.abspath(results_hub_path)
        log_prefix = os.path.join(data_source, "outputs").replace("\\", "/")
        for root, dirs, files in os.walk(absolute_log_path):
            for file in files:
                file_path = os.path.join(root, file)
                blob_name = os.path.join(log_prefix, os.path.relpath(file_path, absolute_log_path)).replace("\\", "/")
                self.upload_file(blob_name, file_path)
                print(blob_name)
        utils.print_with_color(f"Upload log: {results_hub_path} --> {log_prefix}", "green")
