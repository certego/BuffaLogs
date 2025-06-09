# BuffaCLI

BuffaCLI is a command-line interface (CLI) tool that provides administrators with a lightweight and efficient way to interact with **BuffaLogs**. Designed as a substitute for the web dashboard, BuffaCLI enables direct configuration and log querying capabilities from the terminal.

---

## 🚀 Features

* **🛠 Configuration Management**
  Easily modify BuffaLogs settings such as user risk thresholds.

* **📊 Log Querying**
  Retrieve and filter log data. View summaries, statistics, and historical records right from your terminal.

* **🚨 Alert Management**
  Configure alerters to control how and when alert notifications are triggered.

* **🤖 Automation Support**
  Seamlessly integrate with shell scripts to automate log and configuration tasks.

---

## 🧰 Tech Stack

* **Python** – Core programming language.
* **Typer** – For building the CLI interface.
* **Requests** – Handles HTTP communication with the BuffaLogs backend.
* **Rich** – For beautifully formatted terminal outputs.

---

## 📦 Installation

```bash
pip install buffacli
```

> Ensure Python 3.12 or above is installed on your system.

---

## 📝 Usage

```bash
buffa config set-risk-threshold --user admin --threshold 0.75
buffa logs query --date 2025-06-01 
buffa alert configure --enable webhook
```

Run `buffa --help` for a full list of available commands and options.
