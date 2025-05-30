# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from typing import List

from azure.core.paging import ItemPaged
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.storage.blob import BlobServiceClient, BlobProperties
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
        credential = AzureCliCredential()
        blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=credential
        )

        self.container_client = blob_service_client.get_container_client(self.container_name)
        if not self.container_client.exists():
            utils.print_with_color(f"Container {self.container_name} not exist in blob {self.account_url}", "red")

    def list_blobs(self, prefix: str = None) -> ItemPaged[BlobProperties]:
        """
        List blobs in the container
        :return:
        """
        if prefix is None:
            return self.container_client.list_blobs()
        else:
            return self.container_client.list_blobs(name_starts_with=prefix)

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

    def delete(self, blob_name: str) -> None:
        """
        Delete a file from Azure Blob Storage
        :param blob_name: file name in blob
        :return:
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        utils.print_with_color(f"Delete {blob_name} in {self.account_url}/{self.container_name}", "green")

    def delete_folder(self, folder_name: str):
        """
        Delete a folder from Azure Blob Storage
        :param folder_name:
        :return:
        """
        blobs = self.container_client.list_blobs(name_starts_with=folder_name)
        total_blobs = sum(1 for _ in self.container_client.list_blobs(name_starts_with=folder_name))

        # delete all blob under folder
        for blob in tqdm(blobs, desc="delete", total=total_blobs):
            blob_name = blob.name
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
        utils.print_with_color(f"Delete {folder_name} in {self.account_url}/{self.container_name}", "green")

    def upload_folder(self, log_path: str, data_source: str = "", blob_prefix: str = "", overwrite: bool = True, retry: int = 0) -> None:
        """
        Upload folder to Azure Blob Storage
        :param retry: retry count
        :param log_path: relative path of folder
        :param data_source: data source
        :param blob_prefix: prefix of blob
        :param overwrite: overwrite existing file
        """
        absolute_log_path = os.path.abspath(log_path)

        log_prefix = blob_prefix
        if log_prefix == "":
            log_prefix = os.path.join(data_source, log_path).replace("\\", "/")

        try:
            # If log_prefix exist
            if list(self.list_blobs(log_prefix)):
                if overwrite is False:
                    pass
                else:
                    # clear old folder
                    self.delete_folder(log_prefix)

            total_files = sum([len(files) for _, _, files in os.walk(absolute_log_path)])
            with tqdm(total=total_files, desc=f"upload {log_prefix}") as pbar:
                for root, dirs, files in os.walk(absolute_log_path):
                    for file in files:
                        log_file_path = os.path.join(root, file)
                        blob_name = os.path.join(log_prefix, os.path.relpath(log_file_path, absolute_log_path)).replace(
                            "\\", "/")
                        self.upload_file(blob_name, log_file_path, overwrite)
                        pbar.update(1)
            utils.print_with_color(f"Upload log: {log_path} --> {log_prefix}", "green")
        except Exception as e:
            utils.print_with_color(f"Upload log: {log_path} --> {log_prefix} failed: {e}\n Retry {retry}", "red")
            self.upload_folder(log_path, data_source, blob_prefix, overwrite, retry + 1)

    def download_folder(self, folder_prefix: str, output_folder: str) -> None:
        """
        Download folder from Azure Blob Storage
        :param folder_prefix: folder name
        :param output_folder: output folder path
        """
        # list all files in this folder
        blob_list = list(self.container_client.list_blobs(name_starts_with=folder_prefix))
        total_files = len(blob_list)
        print(f"Download Start...")
        with tqdm(total=total_files, desc=f"download {folder_prefix}", unit="file") as total_progress_bar:
            for blob in blob_list:
                blob_name = blob.name
                relative_path = os.path.relpath(blob_name, folder_prefix)
                local_file_path = os.path.join(output_folder, relative_path)

                if os.path.exists(local_file_path):
                    # update tqdm
                    total_progress_bar.update(1)
                    continue

                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                # download files
                self.download(blob_name, local_file_path)

                # update tqdm
                total_progress_bar.update(1)

        utils.print_with_color(f"Download {folder_prefix} -> {output_folder}")

