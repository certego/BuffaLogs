# Splunk Ingestion Documentation

This document outlines a step-by-step guide for configuring Splunk using Docker services. It walks you through deploying Splunk in a containerized environment, then explains how you can ingest data in two ways: locally (by manually adding data via the Splunk web interface) and programmatically (via API calls, like using the HTTP Event Collector). Finally, it describes how Splunk processes the incoming data, parsing and indexing it according to defined configurations.

---

## Pre-requisites

- **Docker & Docker Compose:** Make sure you have Docker and Docker Compose installed.
- **Basic Splunk Knowledge:** Familiarity with Splunk’s interface and basic ingestion concepts.
- **HEC Configuration:** Refer to the [Splunk HEC Documentation](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector) for detailed instructions on setting up the HTTP Event Collector.

---

## Customization of docker-compose.splunk.yaml

In the `docker-compose.splunk.yaml` file, several configurations can be tailored to meet your specific needs:

- **Default Password:**  
  Change the default password to enhance security. Look for the environment variable (e.g., `SPLUNK_PASSWORD`) and update its value.
  
- **Ports and Volumes:**  
  Customize port mappings and volume mounts if your environment requires different configurations.
  
- **HEC Settings:**  
  Ensure that the HEC endpoint is properly configured. You may need to adjust the collector’s port or token in the YAML.

> **Tip:** Open the YAML file and look for sections marked with comments like `# Customize below` to find where you might change passwords or ports.

---

## Running the Docker Compose File

To run your Splunk service:

1. **Navigate to the Project Directory:**  
   Open your terminal and navigate to the directory containing your `docker-compose.splunk.yaml` file.

2. **Run Docker Compose:**  
   Execute the following command:  
   ```
   docker-compose -f docker-compose.splunk.yaml up -d
   ```  
   This command will start the Splunk service in detached mode.

3. **Verify Splunk is Running:**  
   Open your browser and navigate to [http://localhost:8000](http://localhost:8000) (or your custom port if modified) to access the Splunk web interface.

---

## Configuring Ingestion Settings

The ingestion configuration is maintained in a separate JSON file (e.g., `ingestion.json`). Here, you can define how data should be processed. At this stage, the installation is basic, but you can update the file as your needs grow.

- **Custom Fields:**  
  Modify the JSON keys and values to reflect the fields you need. This is where you align with your internal schema requirements.

> **Example Placeholder:**  
> Inside your `ingestion.json`, you can configure parameters like index,username etc.

---

## Logs Structure and Data Flow

Splunk accepts data that follows a defined structure. For instance, our system expects logs to comply with the Elastic Common Schema. Below is an example schema:

```json
{
    "index": "<elastic_index>",
    "id": "<log_id>",
    "timestamp": "<log_timestamp>",
    "user": {
        "name": "<user_name>"
    },
    "source": {
        "geo": {
            "country_name": "<country_origin_log>",
            "location": {
                "lat": "<log_latitude>",
                "lon": "<log_longitude>"
            }
        },
        "as": {
            "organization": {
                "name": "<ISP_name>"
            }
        },
        "ip": "<log_source_ip>",
        "intelligence_category": "<intelligence_category>"
    },
    "user_agent": {
        "original": "<log_device_user_agent>"
    },
    "event": {
        "type": "start",
        "category": "authentication",
        "outcome": "success"
    }
}
```
---

### **Adding Data to Local Splunk**  

If you're running Splunk locally, you can add data using the **GUI (manual upload)** or **HEC (automated ingestion via API calls).**  

### **Method 1: Manual Upload via Splunk GUI**  
1. **Open Splunk Web Interface**  
   - Go to [http://localhost:8000](http://localhost:8000) in your browser.  
   - Log in with your credentials.

2. **Navigate to the Data Input Section**  
   - Click on **"Settings" > "Add Data"**  
   - Choose **Upload files from my computer** (if you have a local log file).  

3. **Upload Your File**  
   - Click **Browse**, select your file, and upload it.  
   - Choose a **Source Type** (or let Splunk auto-detect).  
   - Assign an **Index** (default is `main`).  

4. **Finish Setup & Start Searching**  
   - Click **Next**, review settings, and click **Submit**.  
   - Go to **Search & Reporting** to query your data.  

---

### **Method 2: Send Data Using HEC (HTTP Event Collector)**
To send data programmatically, ensure HEC is enabled on your local Splunk:

#### **1. Enable HEC in Splunk**
- Go to **Settings > Data Inputs > HTTP Event Collector**.
- Click **New Token**, configure the **source type**, and **enable it**.
- Note the generated **HEC Token**.

#### **2. Send Data via cURL**
Run the following command in your terminal:

```bash
curl -k https://localhost:8088/services/collector \
     -H "Authorization: Splunk <your_hec_token>" \
     -H "Content-Type: application/json" \
     -d '{"event": "Hello, Splunk!", "sourcetype": "manual"}'
```

**Replace `<your_hec_token>` with your actual token.**  

---


**How It Works:**

> **Note:** In this documentation, we are using a cloud-based example, but the process and concepts are the same for a local Splunk installation. The only difference is that you will need to replace the `<splunk_host>` with `localhost` if running Splunk locally.

> 
> ![Raw data](https://github.com/user-attachments/assets/e0863604-4480-4468-a7a8-26222b199106)


- **Data Pasting:**  
  When you paste data with this schema, Splunk automatically creates Table based values based on the nested structure.
  
> **Table view of Data:**  
> ![Screenshot of ingestion source table](https://github.com/user-attachments/assets/821ee11f-7e10-44d9-9baf-fd01a32826c5)


 **Processing Logic:**
  
  The `splunk_ingestion.py` connector is built around three core functions:
  
  - **process_user:** Extracts and handles the username data.
  - **process_user_login:** Collects and processes login responses.
  - **normalized_fields:** Normalizes incoming data, converting logs into the BuffaLogs format to power further operations.

This streamlined approach not only organizes your log ingestion flow but also sets the stage for additional processing.

---

## Troubleshooting and Support

If you encounter any issues:

- **Raise an Issue/Discussion:**  
  Please report your problems or discuss concerns on the [BuffaLogs Official Repository](https://github.com/buffalogs/buffalogs). This ensures you receive timely support from the community.
  
- **Official Splunk Documentation:**  
  For more detailed troubleshooting regarding Splunk’s ingestion processes, check out the [Splunk Ingestion Documentation](https://docs.splunk.com/Documentation/Splunk/latest/Data/HEC).

---

Remember, this guide is a starting point for setting up a basic Docker-based Splunk installation. As your needs evolve, you can further customize both the `docker-compose.splunk.yaml` and `ingestion.json` configurations.

If you feel stuck at any point, don't hesitate to seek help on the official repository or engage in community discussions. 

---

