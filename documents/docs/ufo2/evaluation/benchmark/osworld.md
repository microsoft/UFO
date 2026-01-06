# 🧩 Setting up UFO with OSWorld (Windows)


OSWorld is a benchmark suite designed to evaluate the performance of AI agents in real-world scenarios. We select the 49 cases from the original OSWorld benchmark that are compatible with the Windows platform, renamed as OSWorld-W. The tasks cover a wide range of functionalities and interactions that users typically perform on their computers, including Office 365 and browser.

---

## 💻 Deployment Guide (WSL Recommended)

> We strongly recommend reviewing the [original WAA deployment guide](https://github.com/microsoft/WindowsAgentArena) beforehand. The instructions below assume you are familiar with the original setup.

---

### 1. Clone the Repository

```bash
git clone https://github.com/nice-mee/WindowsAgentArena.git
```

> 💡 *To run OSWorld cases, switch to the dedicated development branch:*
```bash
git checkout osworld
```

Create a `config.json` file in the repo root with a placeholder key (UFO will override this):

```json
{
  "OPENAI_API_KEY": "placeholder"
}
```

---

### 2. Build the Docker Image

Navigate to the `scripts` directory and build the Docker image:

```bash
cd scripts
chmod +x build-container-image.sh prepare-agents.sh  # (if needed)
./build-container-image.sh --build-base-image true
```

This will generate the `windowsarena/winarena:latest` image using the latest codebase in `src/`.

---

### 3. Integrate UFO

1. Configure UFO via `ufo/config/config.json` (see [UFO repo](https://github.com/microsoft/UFO) for details).
2. Copy the entire `ufo` folder into the WAA container client directory:

```bash
cp -r src/win-arena-container/vm/setup/mm_agents/UFO/ufo src/win-arena-container/client/
```

> ⚠️ Python 3.9 Compatibility Fix  
> In `ufo/llm/openai.py`, swap the order of `@staticmethod` and `@functools.lru_cache()` to prevent issues due to a known Python 3.9 bug.

---

### 4. Prepare the Windows 11 Virtual Machine

#### 4.1 Download the ISO

1. Go to the [Microsoft Evaluation Center](https://info.microsoft.com/ww-landing-windows-11-enterprise.html)
2. Accept the terms and download **Windows 11 Enterprise Evaluation (English, 90-day trial)** (~6GB)
3. Rename the file to `setup.iso` and place it in:

```
WindowsAgentArena/src/win-arena-container/vm/image
```

#### 4.2 Generate the Golden Image Snapshot

Prepare the Windows VM snapshot (a fully provisioned 30GB image):

```bash
cd ./scripts
./run-local.sh --mode dev --prepare-image true
```

> ⚠️ **Do not interact with the VM during preparation.** It will shut down automatically when complete.

The golden image will be saved in:

```
WindowsAgentArena/src/win-arena-container/vm/storage
```

---

### 5. Initial Run (First Boot Setup)

Launch the environment:

```bash
./run-local.sh --mode dev --json-name "evaluation_examples_windows/test_custom.json" --agent UFO --agent-settings '{"llm_type": "azure", "llm_endpoint": "https://cloudgpt-openai.azure-api.net/openai/deployments/gpt-4o-20240513/chat/completions?api-version=2024-04-01-preview", "llm_auth": {"type": "api-key", "token": ""}}'
```

Once the VM boots:

1. **Do not** enter the device code (this keeps the WAA server alive indefinitely).
2. Visit `http://localhost:8006` and perform the following setup actions:
   - Disable **Windows Firewall**
   - Open **Google Chrome** and complete initial setup
   - Open **VLC** and complete initial setup
   - Activate Office 365 (Word, Excel, PowerPoint, etc.) with a Microsoft account (use a temporary one if needed).

After setup:

- Stop the client
- Backup the golden image from the `storage` folder

---

## 🧪 Running Experiments

Before each experiment:

1. Replace the VM image with your prepared golden snapshot
2. Clear any previous UFO logs

Then run:

```bash
./run-local.sh --mode dev --json-name "evaluation_examples_windows/test_full.json" --agent UFO --agent-settings '{"llm_type": "azure", "llm_endpoint": "https://cloudgpt-openai.azure-api.net/openai/deployments/gpt-4o-20240513/chat/completions?api-version=2024-04-01-preview", "llm_auth": {"type": "api-key", "token": ""}}'
```

!!!note
    > - `test_full.json`: Contains all test cases where UIA is available.  
    > - `test_all.json`: Includes all test cases, even those incompatible with UIA.  
    > - Use `test_full.json` if you're **not** using OmniParser.
---