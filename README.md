# 🛡️ BreakMyAgent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Break your AI before attackers do.** BreakMyAgent is an open-source sandbox designed to stress-test your LLM system prompts against prompt injections, jailbreaks, and adversarial attacks. 

Test 12 standard exploits, or fire your own zero-day payloads against multiple models simultaneously.

![BreakMyAgent Demo](https://github.com/user-attachments/assets/aaa26214-1005-4cf7-8ac4-a44b5a2def3c)

---

## 🚀 Live Demo & Pro API

Try the free hosted version right now:
👉 **[breakmyagent.dev](https://breakmyagent.dev)**

**Building Enterprise AI?**
The Open-Source version includes 12 basic public exploits. Real attackers use multi-step agentic payloads, context window overflows, and tool spoofing. 

Join the **BreakMyAgent Pro** waitlist to get:
* 🔌 **CI/CD API Access:** Automate red-teaming in your GitHub Actions.
* 🗄️ **50+ Enterprise Attack Vectors:** Continuously updated payload database.
* 🧠 **Smart Fuzzer:** Adaptive attack sorting based on target model vulnerabilities.
* 📊 **Exportable Compliance Reports.**

[**Request Pro API Access ↗**](https://breakmyagent.dev)

---

## 🌟 Core Features

* 🤖 **Auto Test Suite:** Run a concurrent barrage of 12 curated jailbreaks against your system prompt in seconds.
* ⚔️ **Multi-Model Playground:** Have a new jailbreak idea? Test your custom payload against up to 3 LLMs (e.g., GPT-4.1, Llama 3, Claude) side-by-side to compare their native alignment.
* ⚖️ **LLM-as-a-Judge:** A hardcoded, strictly aligned `gpt-4.1-mini` model analyzes the Target's responses using Prompt Caching to accurately detect instruction leaks and unauthorized tool usage.
* 🔌 **Plug-and-Play UI:** The model selector dynamically populates based on the API keys you provide. No broken interfaces, no missing dependencies.

---

## 💻 Local Installation

We strictly use [`uv`]([https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)) for lightning-fast, reproducible dependency management. Do not use standard `pip`.

### 1. Clone the repository
```bash
git clone https://github.com/BreakMyAgent/breakmyagent-os.git
cd breakmyagent-os
```

### 2. Set up the environment
```bash
uv venv
uv pip install -r requirements.txt
```

### 3. Configure API Keys (Zero-Friction Setup)
Create a `.env` file in the root directory. **The UI will automatically detect your keys and populate the available model list accordingly.**

To get started immediately, you only need one key (OpenAI is used for the Judge and basic Targets):
```env
OPENAI_API_KEY=sk-proj-...
```

*Optional:* Add more keys to unlock additional target models (Claude, Llama, etc.) in the sandbox:
```env
OPENROUTER_API_KEY=sk-or-v1-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Run the Sandbox (Requires two terminal tabs)

**Terminal 1 (Backend API):**
```bash
uv run uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend UI):**
```bash
uv run streamlit run frontend/app.py --server.port 8501
```
Open `http://localhost:8501` in your browser.

---

## 🤝 Contributing (Bring Your Own Payload)
Found a new Prompt Injection vector? We'd love to add it to the open-source payload database (`data/attacks.json`)! 

**How to submit a payload:**
1. Open the UI and go to the **⚔️ Custom Payload** tab.
2. Test your injection against a target model to prove it works.
3. Click the **"Copy Markdown for PR"** button under the results.
4. Open a Pull Request in this repository and paste the Markdown report to validate your attack!

## 📄 License
This open-source core is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.