from mongoHandler import MongoDBHandler
import re
import configparser
import json
from bson.objectid import ObjectId
class SearchHandler:
    def __init__(self, database_name, collection_name, connect_string):
        self.handler = MongoDBHandler(database_name, collection_name, connect_string)
    def search_documents_by_keyword(self, search_string:str, limit=10) -> dict():
        search_documents_list = self.handler.search_documents_by_keyword(search_string)
        result = []
        if search_documents_list:
            try:
                for doc in search_documents_list:
                    row = {}
                    row["id"] = str(doc.get("_id"))
                    row["title"] = f"{doc.get('date').split('T')[0]} {doc.get('court')} {doc.get('no')}"
                    result.append(row)
                    if len(result) >= limit:
                        break
            except:
                pass
        result = json.dumps(result)
        return result
    def search_document_by_ID(self, search_ID:str) -> dict():
        search_ID = ObjectId(search_ID)
        search_document = self.handler.search_document_by_ID(search_ID)
        return search_document
    def analysis_related_issues(self, search_ID:str, limit:int=10) -> dict():
        search_ID = ObjectId(search_ID)
        search_document = self.handler.search_document_by_ID(search_ID)
        relation_table = {}
        for issue in search_document.get("relatedIssues"):
            match_docs = self.handler.search_documents_by_related(issue)
            for doc in match_docs:
                if doc.get("_id") != search_ID:
                    if doc.get("_id") not in relation_table:
                        relation_table[doc.get("_id")] = {
                            "related": doc.get("relatedIssues"),
                            "title": f"{doc.get('date').split('T')[0]} {doc.get('court')} {doc.get('no')}",
                            "accuracy": 0
                        }
        # calculate accuracy
        set_origin = {(d['lawName'], d['issueRef']) for d in search_document.get("relatedIssues")}
        for key in relation_table.keys():
            set_compare = {(d['lawName'], d['issueRef']) for d in relation_table[key]["related"]}
            # intersection
            intersection = list(set_origin.intersection(set_compare))
            # union
            union = list(set_origin.union(set_compare))
            # accuracy
            relation_table[key]["accuracy"] = len(intersection) / len(union)

        # sort
        relation_table = sorted(relation_table.items(), key=lambda x: x[1]["accuracy"], reverse=True)

        # return
        result = []
        for key, value in relation_table:
            row = {}
            row["id"] = str(key)
            row["title"] = value["title"]
            result.append(row)

        if(limit > len(result)):
            limit = len(result)
        return result[0:limit]

class CMD(SearchHandler): 
    def __init__(self, config_path="config.ini"):
        config = configparser.ConfigParser()
        try:
            config.read(config_path)
            connect_string = f"mongodb://{config['mongodb']['user']}:{config['mongodb']['password']}@{config['mongodb']['host']}:{config['mongodb']['port']}/?authMechanism=DEFAULT"
            database_name = config['mongodb']['db']
            collection_name = "test"
        except:
            print("config.ini not found")
            return None
        super().__init__(database_name, collection_name, connect_string)
        self.handler = MongoDBHandler(database_name, collection_name, connect_string)
    
def main():
    handler = CMD()
    if handler is None:
        return
    # 輸入要尋找的相符字串
    search_string = input("請輸入要尋找的相符字串：")
    search_documents_list = handler.search_documents_by_keyword(search_string)
    print("查詢結果：")
    print(search_documents_list.encode('utf-8').decode('unicode_escape'))
    

    # 輸出查閱結果
    search_documents_ID = input("請輸入要查閱的文件ID：")
    search_documents = handler.search_document_by_ID(search_documents_ID)
    print(f"ID:{search_documents.get('_id')} {search_documents.get('judgement')}")

    # 輸出相似文件
    print("相似文件:")
    relation_table = handler.analysis_related_issues(search_documents_ID)
    print(relation_table)
    

if __name__ == "__main__":
    main()