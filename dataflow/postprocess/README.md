# 📊 PostProcess

> A tool for converting UFO execution logs into structured datasets

---

## ✨ Features

- 📂 **Batch Processing**: Automatically scan and process multiple log directories
- 🔄 **Data Standardization**: Convert raw logs into unified JSONL format
- 🖼️ **Image Handling**: Support both Base64 encoding and path reference for image storage
- ✅ **Smart Classification**: Automatically categorize data into success/failure cases based on evaluation results
- 📈 **Statistical Reports**: Generate detailed processing statistics
- 🛡️ **Error Handling**: Gracefully handle missing files and parsing errors

---

## 🚀 Usage

### Basic Command

```bash
python postprocess.py \
  --prefill_path <path_to_prefill_log> \
  --log_path <path_to_log_folder> \
  --output_path <path_to_output_folder> \
  --encode_type <base64|path> \
  --image_output_path <path_to_image_output>
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--prefill_path` | ✅ | Path to the prefill log file (JSON format) |
| `--log_path` | ✅ | Path to the folder containing execution logs |
| `--output_path` | ✅ | Path for the processed dataset output |
| `--encode_type` | ❌ | Image encoding method: `base64` or `path` (default: `path`) |
| `--image_output_path` | ⚠️ | Path for storing image files (required when `encode_type=path`) |

---

## 📖 Examples

### Example 1: Using Base64 Encoding

```bash
python postprocess.py \
  --prefill_path ./logs/prefill.json \
  --log_path ./logs/chunk_0 \
  --output_path ./dataset \
  --encode_type base64
```

### Example 2: Using Path Reference

```bash
python postprocess.py \
  --prefill_path ./logs/prefill.json \
  --log_path ./logs/chunk_0 \
  --output_path ./dataset \
  --encode_type path \
  --image_output_path ./dataset/images
```

---

## ⚙️ Python API

You can also use PostProcess directly in your Python code:

```python
from dataflow.postprocess.postprocess import PostProcess

# Create instance
processor = PostProcess(
    encode_type="path",
    image_output_path="./images"
)

# Process logs
processor.process(
    prefill_log_path="./prefill.json",
    log_folder_path="./logs",
    output_folder_path="./output"
)
```

---

## 📁 Output Structure

```
output_path/
├── success/              # Successful cases
│   ├── <execution_id_1>.jsonl
│   └── ...
└── fail/                 # Failed cases
    ├── <execution_id_2>.jsonl
    └── ...

image_output_path/        # Image files (when encode_type=path)
├── success/
│   ├── <execution_id_1>/
│   └── ...
└── fail/
    └── ...
```
