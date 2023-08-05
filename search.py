from mongoHandler import MongoDBHandler
import re
import configparser

def main():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        connect_string = f"mongodb://{config['mongodb']['user']}:{config['mongodb']['password']}@{config['mongodb']['host']}:{config['mongodb']['port']}/?authMechanism=DEFAULT"
        database_name = config['mongodb']['db']
        collection_name = "test"
    except:
        print("config.ini not found")
        return
    
    handler = MongoDBHandler(database_name, collection_name, connect_string)

    # 輸入要尋找的相符字串
    search_string = input("請輸入要尋找的相符字串：")

    # 執行搜尋
    search_documents_list = handler.search_documents_by_keyword(search_string)

    # 輸出結果
    search_documents_ID_list = []
    if search_documents_list:
        print("相符資料：")
        index = 0
        for doc in search_documents_list:
            print(f"[{index}] {doc.get('date').split('T')[0]} {re.findall(r'([0-9]+年度.*號)',doc.get('judgement'))[0]}")
            index += 1
            search_documents_ID_list.append(doc.get("_id"))
            if index > 9:
                break
    else:
        print("未找到相符資料")
        return
    
    # 輸入要查閱的文件
    search_index = input("請輸入要查閱的文件：")
    search_index = int(search_index)
    if search_index > index or search_index < 0:
        print("查閱文件超出範圍")
        return
    
    # 輸出查閱結果
    print("查閱結果：")
    search_documents_ID = search_documents_ID_list[search_index]
    search_documents = handler.search_document_by_ID(search_documents_ID)
    print(f"ID:{search_documents.get('_id')}")
    # print(search_documents.get("relatedIssues"))

    relation_table = {}
    # relation table
    # {
    #   "5f9b3a1b9c9d6e0b9c9d6e0b":
    #   {       
    #       "related": [],
    #       "accuracy": 0
    #   }
    # ]

    for issue in search_documents.get("relatedIssues"):
        match_docs = handler.search_documents_by_related(issue)
        # issue
        # {"lawName": "","issueRef": ""}
        for doc in match_docs:
            if doc.get("_id") != search_documents_ID:
                if doc.get("_id") not in relation_table:
                    relation_table[doc.get("_id")] = {
                        "related": doc.get("relatedIssues"),
                        "accuracy": 0
                    }

    # calculate accuracy
    set_origin = {(d['lawName'], d['issueRef']) for d in search_documents.get("relatedIssues")}
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

    for index in range(len(relation_table)):
        print(f"[{index}] {relation_table[index][0]} {relation_table[index][1]['accuracy']}")
        if index > 9:
            break
    
    
    

    





if __name__ == "__main__":
    main()