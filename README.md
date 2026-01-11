# AI SOC Experimentation Framework

An open-source framework for comparing threat detection methods, including traditional rules-based approaches and modern embeddings-first techniques using LogLM.

## Overview

This project provides a hands-on environment for security practitioners to:

1.  **Compare Detection Methods**: Run a side-by-side comparison of a traditional rules-based SOC vs. an AI-enhanced SOC using the same log data.
2.  **Evaluate Performance**: Quantify the performance of each approach using metrics like precision, recall, and Mean Time to Detect (MTTD).
3.  **Experiment with AI**: Explore how embeddings-first models like DeepTempo's LogLM can augment security operations.
4.  **Integrate with Your Tools**: Use the provided MCP servers to connect with Claude for conversational investigation.

This framework is designed to be educational and vendor-neutral, allowing you to form your own conclusions about the best approach for your environment.

## Tale of Two SOCs: A Comparison Framework

The core of this project is the "Tale of Two SOCs" comparison, which lets you analyze the same attack scenario through two different lenses.

| | **Rules-Only SOC** | **LogLM-Enhanced SOC** |
|---|---|---|
| **Detection Engine** | Sigma-like rules | Embeddings-first model |
| **Output** | Discrete alerts | Correlated findings |
| **Analyst Experience** | Manual triage and correlation | Automated correlation and narrative |

### Run the Comparison

```bash
# 1. Generate the attack scenario with ground truth
python scripts/generate_scenario.py

# 2. Run both detection pipelines
python scripts/rules_detection.py
python scripts/loglm_detection.py

# 3. Evaluate the results
python scripts/evaluate.py

# 4. Launch the comparison dashboard
streamlit run streamlit_app/tale_of_two_socs.py
```

### The Dashboard

The Streamlit dashboard provides a comprehensive view of the results, including:

*   **Side-by-side metrics**: Precision, recall, and false positive rates.
*   **MTTD Analysis**: See how quickly each approach detects different attack phases.
*   **Attack Graph**: Visualize the attack flow as seen by each system.
*   **Rule Analysis**: Inspect the rules used in the rules-only approach.

## Quick Start

### Prerequisites

*   **Python 3.10+**
*   **Claude Desktop** (Optional, for conversational investigation)
*   **Docker** (Optional, for Timesketch visualization)

### Step 1: Clone and Set Up

```bash
git clone https://github.com/epowell101/deeptempo-ai-soc.git
cd deeptempo-ai-soc

python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Install streamlit app dependencies
pip install -r streamlit_app/requirements.txt
```

### Step 2: Generate Data and Run Pipelines

```bash
python scripts/generate_scenario.py
python scripts/rules_detection.py
python scripts/loglm_detection.py
python scripts/evaluate.py
```

### Step 3: Launch Dashboard

```bash
streamlit run streamlit_app/tale_of_two_socs.py
```

## Extending the Framework

This project is designed to be a starting point. Here are some ways you can extend it:

*   **Add Your Own Rules**: Modify `scripts/rules_detection.py` to add your own Sigma rules.
*   **Use Your Own Logs**: Place your own log files in `data/scenarios/custom/` and adapt the scripts to parse them.
*   **Integrate Other Tools**: Use the MCP server framework to connect other security tools to Claude.

## Project Structure

```
deeptempo-ai-soc/
├── streamlit_app/         # Streamlit dashboards
├── mcp_servers/           # MCP servers for Claude integration
├── scripts/               # Data generation and detection pipelines
├── data/                  # Attack scenarios and ground truth
└── ...
```

## Related Open-Source Projects

For practitioners looking to build out a more comprehensive open-source security stack, we recommend exploring:

*   **Wazuh**: An open-source XDR and SIEM platform.
*   **Security Onion**: A full-featured SIEM with a focus on network security monitoring.
*   **Sigma**: A vendor-agnostic format for detection rules, with a large community repository.
*   **Timesketch**: A collaborative forensic timeline analysis tool (already integrated here).
*   **DFIR-IRIS**: An open-source incident response platform for case management.

## License

Apache 2.0
