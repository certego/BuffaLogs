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

## 📜 **Configuration for BuffaCLI**

BuffaCLI allows users to configure various settings to tailor the tool to their environment and preferences. The configuration can be customized via a **configuration file**, **environment variables**, **buffacli show command** or **default settings**. Below are the primary configurable options in BuffaCLI:


#### 1. **`config_path`** (Custom Configuration File)

* **Purpose**: Allows users to define a custom configuration file that overrides the default configuration for specific fields.
* **Usage**: By setting the `config_path` option, BuffaCLI will load the configuration from the specified file, allowing users to define custom settings.
* **Default**: `~/buffalogs.conf` (i.e., the file `buffalogs.conf` in the user's home directory).

##### Example:

To specify a custom configuration file:

```bash
buffa setup --config-path /path/to/custom/config.conf
```

The config file must be in the **`config format`** (such as `.ini`, `.conf`, etc.), and any field defined in this file will override the default configuration.


#### 2. **`buffalogs_url`** (API Endpoint for BuffaLogs)

* **Purpose**: Sets the endpoint to which BuffaCLI will send requests. This can be set in the configuration file or as an **environment variable**.
* **Default**: `http://127.0.0.1:8000`

  * If no value is specified in the configuration or environment variable, this is the default endpoint.

##### **Configuration File**:

You can define the **`buffalogs_url`** in the configuration file (either the default `buffalogs.conf` or a custom file defined via `config_path`):

```ini
buffalogs_url = https://api.buffalogs.com/v1
```

##### **Environment Variable**:

You can also specify the endpoint using an environment variable. This will **override the setting in the configuration file**.

```bash
export BUFFALOGS_URL="https://api.buffalogs.com/v1"
```

**Note**: When both the configuration file and environment variable are set, the environment variable takes precedence, ensuring the most recent setting is applied.

---

#### Configuration Hierarchy:

1. **Environment Variable (`BUFFALOGS_URL`)**: Highest priority. Overrides both the default and the setting in the configuration file.
2. **Configuration File (`buffalogs.conf` or custom `config_path`)**: The settings in the configuration file override the default values.
3. **Default Settings**: The fallback values used when no custom configuration is provided.


### Example of Loading BuffaCLI Configuration:

1. **Default Behavior** (with no custom config):

   * BuffaCLI will use `https://127.0.0.1:8000` as the endpoint.

2. **Using a Custom Config Path**:

   * If a user specifies a custom `config_path`, the settings in that file will override the defaults for the fields defined in the configuration.

3. **Using Environment Variables**:

   * If the environment variable `BUFFALOGS_URL` is set, it will override the value defined in the configuration file.

---

## Commands

### setup 🔧
Configure BuffaCLI-specific setups, such as user preferences, default settings, and integration parameters.

This command allows you to customize BuffaCLI to better match your environment and use case by setting up various configurations.

### Usage:
buffacli setup [OPTIONS]

### Options:
* **--buffalogs-url**
    * _data type:_ TEXT
    * _default:_ `http://127.0.0.1:8000`
    * Sets the base URL for communicating with BuffaLogs API. 

 * **--config-file** 
    * _data type:_ PATH
    * _default:_ `~/.buffacli.conf`
    * Path to the configuration file (e.g., buffacli.conf) that contains setup parameters.

### Example:
- Set the BuffaLogs URL:
  ```bash
    buffacli setup --buffalogs-url http://buffalogs.local/api`
  ```
  
- Use a configuration file:
  ```bash
    buffa setup --config-file /path/to/config.json
  ```
  

Run `buffa --help` for a full list of available commands and options.
