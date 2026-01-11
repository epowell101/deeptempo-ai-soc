# Building Your First AI-Powered SOC: A Step-by-Step Guide

Security Operations Centers (SOCs) are the nerve center of modern cybersecurity. But what if we could build a SOC that was not just reactive, but predictive and intuitive? What if we could replace complex dashboards with intelligent conversations? 

This project, the **AI SOC Experimentation Framework**, is an open-source initiative to do just that. It’s a hands-on guide to building your own AI-native SOC, leveraging the power of large language models (LLMs) for both detection and orchestration. Whether you’re a seasoned security pro or just starting out, this project is designed to be your launchpad into the future of AI-driven security.

## The Vision: A Conversational SOC

Imagine a SOC where you can simply ask questions and get immediate, context-aware answers. No more endless clicking through dashboards. No more manually correlating alerts. Just a conversation with an AI analyst that understands your intent and can take action on your behalf.

This is the vision behind this project. It’s a SOC built for the age of AI, where human analysts are augmented, not replaced, by intelligent systems.

## The Architecture: A Modular, AI-First Approach

Our AI SOC is built on a simple yet powerful architecture:

- **Detection Engine**: Choose between traditional Sigma-like rules or an embeddings-first model like DeepTempo's LogLM.
- **Orchestration Engine**: Use Claude as the primary analyst interface, leveraging its natural language understanding to interpret commands and orchestrate investigations.
- **Model Context Protocol (MCP)**: The bridge between Claude and the SOC tools. MCP allows Claude to securely invoke tools and access data from the underlying security systems.
- **Streamlit**: The visualization layer. A rich, interactive dashboard provides a visual representation of the attack flow, from initial compromise to data exfiltration.

## What We’ve Built So Far: A Functional AI SOC

In just a few short steps, we’ve built a functional AI SOC with the following capabilities:

### 1. A Tale of Two SOCs: Rules vs. Embeddings

At the core of our SOC is a side-by-side comparison that allows you to evaluate two different detection philosophies:

- **Rules-Based Detection**: Using a set of Sigma-like rules, this approach generates alerts based on specific, predefined patterns.
- **Embeddings-First Detection**: Using a model like DeepTempo's LogLM, this approach generates high-fidelity security embeddings from raw log data. These embeddings capture the semantic meaning of security events, allowing for powerful similarity searches and the identification of complex attack patterns.

### 2. Conversational Orchestration with Claude

We’ve integrated Claude as our primary analyst interface, allowing us to have natural conversations with our SOC. Using the Model Context Protocol (MCP), we’ve exposed a set of SOC tools that Claude can invoke, including:

- **`list_alerts` / `list_findings`**: List security events from either the rules engine or the LogLM model.
- **`nearest_neighbors`**: Find similar findings using embeddings (LogLM mode only).
- **`get_attack_narrative`**: Get a human-readable summary of a correlated attack (LogLM mode only).

This allows you to perform complex investigations with simple, natural language commands and directly compare the experience between the two modes.

### 3. Interactive Attack Flow Visualization

To provide a visual representation of the attack flow, we’ve built an interactive dashboard with Streamlit. The dashboard includes:

- **Attack Graph**: A network graph of all entities involved in the attack, showing the difference in visibility between the two detection methods.
- **MTTD Analysis**: A quantitative comparison of the Mean Time to Detect for each attack phase.
- **Confusion Matrix**: A visualization of the precision and recall for both the rules-based and LogLM approaches.

This provides a clear, intuitive way to understand the full scope of an attack and the effectiveness of each detection method.

## Getting Started: Build Your Own AI SOC

Ready to dive in? You can get started with the AI SOC Experimentation Framework in just a few simple steps:

1.  **Clone the repo:**

    ```bash
    git clone https://github.com/epowell101/deeptempo-ai-soc.git
    cd deeptempo-ai-soc
    ```

2.  **Set up the environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r streamlit_app/requirements.txt
    ```

3.  **Run the data pipelines and launch the dashboard:**

    ```bash
    python scripts/generate_scenario.py
    python scripts/rules_detection.py
    python scripts/loglm_detection.py
    python scripts/evaluate.py
    streamlit run streamlit_app/tale_of_two_socs.py
    ```

That’s it! You now have a fully functional AI SOC comparison environment running on your local machine.

## Related Open-Source Projects

This project is a great starting point, but it's just one piece of the puzzle. For practitioners looking to build out a more comprehensive open-source security stack, we recommend exploring:

*   **Wazuh**: An open-source XDR and SIEM platform that provides a solid foundation for security monitoring.
*   **Security Onion**: A full-featured SIEM with a focus on network security monitoring, great for deep-diving into network traffic.
*   **Sigma**: A vendor-agnostic format for detection rules. Our rules-based approach is built on Sigma-like rules, and the public repository is a great resource.
*   **Timesketch**: A collaborative forensic timeline analysis tool, which is already integrated into this project.
*   **DFIR-IRIS**: An open-source incident response platform for case management, which could be a great next integration for this project.

## Join the Revolution

The future of security is AI-native. This project is your opportunity to be a part of that future. We invite you to clone the repo, experiment with the code, and contribute your own ideas. Together, we can build the next generation of intelligent security operations.

**Get involved:**

- **GitHub Repo**: [https://github.com/epowell101/deeptempo-ai-soc](https://github.com/epowell101/deeptempo-ai-soc)
