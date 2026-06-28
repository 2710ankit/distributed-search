import os

from elasticsearch import Elasticsearch

ES_HOST = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

es = Elasticsearch(ES_HOST)
