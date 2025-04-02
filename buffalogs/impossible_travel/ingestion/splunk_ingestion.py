import logging
from datetime import datetime

import splunklib.client as client
import splunklib.results as results
from impossible_travel.ingestion.base_ingestion import BaseIngestion


class SplunkIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for Splunk ingestion source
    """

    def __init__(self, ingestion_config: dict):
        """
        Constructor for the Splunk Ingestion object
        """
        super().__init__()
        self.splunk_config = ingestion_config
        try:
            # Create Splunk connection
            self.service = client.connect(
                host=self.splunk_config.get("host", "localhost"),
                port=self.splunk_config.get("port", 8089),
                username=self.splunk_config.get("username", "admin"),
                password=self.splunk_config.get("password", "changeme"),
                scheme=self.splunk_config.get("scheme", "https")
            )
        except ConnectionError as e:
            logging.error("Failed to establish a connection: %s", e)
            self.service = None
            
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        """
        Concrete implementation of the BaseIngestion.process_users abstract method

        :param start_date: the initial datetime from which the users are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the users are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: list of users strings that logged in Splunk
        :rtype: list
        """
        self.logger.info(f"Starting at: {start_date} Finishing at: {end_date}")
        users_list = []
        
        # Format dates for Splunk query
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Build Splunk query to get unique users with successful authentication
        query = f"""
            search index={self.splunk_config["indexes"]} 
            earliest="{start_date_str}" latest="{end_date_str}"
            event.category="authentication" event.outcome="success" event.type="start"
            | stats count by user.name
            | where isnotnull(user.name) AND user.name!=""
        """
        
        try:
            # Execute the search
            search_kwargs = {
                "earliest_time": start_date_str,
                "latest_time": end_date_str,
                "exec_mode": "normal",
                "count": self.splunk_config.get("bucket_size", 10000)
            }
            
            search_job = self.service.jobs.create(query, **search_kwargs)
            
            # Wait for the job to complete
            while not search_job.is_done():
                search_job.refresh()
            
            # Get the results
            results_reader = results.ResultsReader(search_job.results())
            for result in results_reader:
                if isinstance(result, dict) and "user.name" in result:
                    users_list.append(result["user.name"])
                    
            self.logger.info(f"Successfully got {len(users_list)} users")
            
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {self.splunk_config.get('host')}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {self.splunk_config.get('host')}")
        except Exception as e:
            self.logger.error(f"Exception while querying Splunk: {e}")
        print("process user: ",users_list)    
        return users_list

    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        """
        Concrete implementation of the BaseIngestion.process_user_logins abstract method

        :param username: username of the user that logged in Splunk
        :type username: str
        :param start_date: the initial datetime from which the logins of the user are considered
        :type start_date: datetime (with tzinfo=datetime.timezone.utc)
        :param end_date: the final datetime within which the logins of the user are considered
        :type end_date: datetime (with tzinfo=datetime.timezone.utc)

        :return: Splunk response of logins of that username
        :rtype: list
        """
        response = []
        
        # Format dates for Splunk query
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Build Splunk query to get login events for specific user
        query = f"""
            search index={self.splunk_config["indexes"]} 
            earliest="{start_date_str}" latest="{end_date_str}"
            user.name="{username}" event.category="authentication" event.outcome="success" event.type="start"
            | where isnotnull(source.ip)
            | fields user.name, _time AS "@timestamp", source.geo.location.lat, source.geo.location.lon, 
              source.geo.country_name, source.as.organization.name, user_agent.original, index, source.ip, _id,
              source.intelligence_category
            | sort 0 @timestamp
        """
        print(query)  
        try:
            # Execute the search
            search_kwargs = {
                "earliest_time": start_date_str,
                "latest_time": end_date_str,
                "exec_mode": "normal",
                "count": self.splunk_config.get("bucket_size", 10000)
            }
            
            search_job = self.service.jobs.create(query, **search_kwargs)
            
            # Wait for the job to complete
            while not search_job.is_done():
                search_job.refresh()
            
            # Get the results
            results_reader = results.ResultsReader(search_job.results())
            for result in results_reader:
                if isinstance(result, dict):
                    response.append(result)
                    
            self.logger.info(f"Got {len(response)} logins for the user {username} to be normalized")
            
        except ConnectionError:
            self.logger.error(f"Failed to establish a connection with host: {self.splunk_config.get('host')}")
        except TimeoutError:
            self.logger.error(f"Timeout reached for the host: {self.splunk_config.get('host')}")
        except Exception as e:
            self.logger.error(f"Exception while querying Splunk: {e}")
        print("processs login: ",{"hits": {"hits": response}, "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0}})    
        return {"hits": {"hits": response}, "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0}}

    def normalize_fields(self, logins_response):
        """
        Concrete implementation of the BaseIngestion.normalize_fields abstract method

        :param logins_response: user related logins returned by the Splunk query
        :type logins_response: dict

        :return: list of normalized logins
        :rtype: list
        """
        fields = []
        
        # Extract hits from the response
        hits = logins_response.get("hits", {}).get("hits", [])
        
        for hit in hits:
            # In Splunk results, each hit is already a dict (not a nested _source)
            if "source.ip" in hit:
                tmp = {
                    "timestamp": hit.get("@timestamp", ""),
                    "id": hit.get("_id", ""),
                    "index": "fw-proxy" if hit.get("index", "").startswith("fw-") else hit.get("index", "").split("-")[0],
                    "ip": hit.get("source.ip", ""),
                    "agent": hit.get("user_agent.original", ""),
                    "organization": hit.get("source.as.organization.name", ""),
                }
                
                # Geolocation fields
                if (hit.get("source.geo.location.lat") and 
                    hit.get("source.geo.location.lon") and 
                    hit.get("source.geo.country_name")):
                    
                    tmp.update({
                        "lat": hit["source.geo.location.lat"],
                        "lon": hit["source.geo.location.lon"],
                        "country": hit["source.geo.country_name"],
                    })
                    
                    fields.append(tmp)
        print("Normalized: ",fields)            
        return fields