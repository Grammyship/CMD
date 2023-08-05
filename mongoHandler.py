import pymongo
class MongoDBHandler:
    def __init__(self, database_name, collection_name, connect_string):
        self.client = pymongo.MongoClient(connect_string)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def search_documents_by_keyword(self, search_string):
        query = { "judgement": { "$regex": search_string} }
        result = self.collection.find(query)
        return result
    
    def search_document_by_ID(self, search_ID):
        query = { "_id": search_ID }
        result = self.collection.find(query)
        return [doc for doc in result][0]
    
    def search_documents_by_related(self, related_string):
        query = { "relatedIssues": related_string}
        result = self.collection.find(query)
        return result