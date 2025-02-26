from django.test import TestCase
from impossible_travel.modules.ingestion_handler import Ingestion


class IngestionTestCase(TestCase):

    # Tests for the ingestion source: Elasticsearch
    def test_load_ingestion_sources__elasticsearch(self):
        ingestion_source_received = Ingestion.load_ingestion_sources()
        self.assertEqual(type(ingestion_source_received), list)
        "impossible_travel.modules.ingestion_handler.ElasticsearchIngestion"

    def test_process_user__elasticsearch(self):
        pass
        # testing the process_user function for the Elasticsearch ingestion source
        # @patch("impossible_travel.tasks.check_fields")
        # @patch.object(tasks.Search, "execute")
        # def test_process_user(self, mock_execute, mock_check_fields):
        #     data_elastic_sorted_dot_not = []
        #     imp_travel = impossible_travel.Impossible_Travel()
        #     data_elastic = load_test_data("test_data_process_user")
        #     data_elastic_sorted = sorted(data_elastic, key=lambda d: d["@timestamp"])
        #     for data in data_elastic_sorted:
        #         data_elastic_sorted_dot_not.append(DictStruct(kwargs=data))
        #     data_results = load_test_data("test_data_process_user_result")
        #     mock_execute.return_value = data_elastic_sorted_dot_not
        #     start_date = timezone.datetime(2023, 3, 8, 0, 0, 0)
        #     end_date = timezone.datetime(2023, 3, 8, 23, 59, 59)
        #     iso_start_date = imp_travel.validate_timestamp(start_date)
        #     iso_end_date = imp_travel.validate_timestamp(end_date)
        #     db_user = User.objects.get(username="Lorena Goldoni")
        #     tasks.process_user(db_user, iso_start_date, iso_end_date)
        #     mock_check_fields.assert_called_once_with(db_user, data_results)
