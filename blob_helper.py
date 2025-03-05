import argparse

from ufo.utils.azure_storage import AzureBlobStorage

azure_blob = AzureBlobStorage()

def upload(path: str, data_source: str):
    azure_blob.upload_folder(path, data_source)

def download(path: str, folder_prefix: str):
    azure_blob.download_folder(folder_prefix, path)

def delete(path: str):
    azure_blob.delete_folder(path)

def list_blob(path: str):
    if path == '*':
        blobs = azure_blob.list_blobs()
    else:
        blobs = azure_blob.list_blobs(path)

    for blob in blobs:
        print(blob.name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True, choices=['upload', 'download', 'list', 'delete'])
    parser.add_argument('--path', required=True, type=str)
    parser.add_argument('--source', required=False, type=str)
    parser.add_argument('--folder_prefix', required=False, type=str)

    args = parser.parse_args()
    if args.mode == 'upload':
        upload(args.path, args.source)
    elif args.mode == 'download':
        download(args.path, args.folder_prefix)
    elif args.mode == 'list':
        list_blob(args.path)
    elif args.mode == 'delete':
        delete(args.path)

if __name__ == '__main__':
    main()