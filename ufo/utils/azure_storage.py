# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from typing import List

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from tqdm import tqdm

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

    def upload_file(self, blob_name: str, input_file_path: str, overwrite: bool = True) -> None:
        """
        Upload a file to Azure Blob Storage
        :param blob_name: the expected name in azure blob
        :param input_file_path: input file path
        :param overwrite: overwrite existing file
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        if overwrite is False:
            if blob_client.exists():
                return
        with open(input_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=overwrite)

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

    def upload_folder(self, log_path: str, data_source: str = "") -> None:
        """
        Upload folder to Azure Blob Storage
        :param log_path: relative path of folder
        :param data_source: data source
        """
        absolute_log_path = os.path.abspath(log_path)
        log_prefix = os.path.join(data_source, log_path).replace("\\", "/")

        total_files = sum([len(files) for _, _, files in os.walk(absolute_log_path)])
        with tqdm(total=total_files, desc=f"upload {data_source}/{log_prefix}") as pbar:
            for root, dirs, files in os.walk(absolute_log_path):
                for file in files:
                    log_file_path = os.path.join(root, file)
                    blob_name = os.path.join(log_prefix, os.path.relpath(log_file_path, absolute_log_path)).replace(
                        "\\", "/")
                    self.upload_file(blob_name, log_file_path)
                    pbar.update(1)
        utils.print_with_color(f"Upload log: {log_path} --> {log_prefix}", "green")

