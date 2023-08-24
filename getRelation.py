import os
import json
import random
from pprint import pprint
from mongoHandler import MongoDBHandler as handler
import configparser
from ArticutAPI import Articut
import re

config = configparser.RawConfigParser()

# mongoDB
try:
    config.read('config.ini')
    connect_string = f"mongodb://{config['mongodb']['user']}:{config['mongodb']['password']}@{config['mongodb']['host']}:{config['mongodb']['port']}/?authMechanism=DEFAULT"
    database_name = config['mongodb']['db']
    collection_name = "test"
except:
    print("config.ini not found")
    exit()

# Articut
try:
    articut = Articut(config["droidtown"]["user"], config["droidtown"]["articut_key"])
except:
    print("ArticutAPI initialize error")
    exit()


# Global Variables
verbLIST = ["ACTION_verb", "VerbP"]


def getRelation(objectID):
    """
    0. 抓取判決書內容
    """
    db = handler(database_name, collection_name, connect_string)
    data = db.search_document_by_ID(objectID)

    # 沒有 party 欄位先不處理
    if "party" not in data:
        return {"status": False, "msg": "{} 沒有 party!".format(objectID)}
    
    # 隱藏的案件
    if data["reason"] == "" or "本件經程式判定為依法不得公開或須去識別化後公開之案件" in data["judgement"]:
        return {"status": False, "msg": data["judgement"]}        


    """
    1. 前處理: 判斷人物身分
    """
    # ld: list of dict; lld: list of list of dictionary; etc.
    party = {
        "plaintiff": [],    # ld: 原告，有可能為法人或一般民眾 
        "defendant": [],    # ld: 被告，有可能為法人或一般民眾
        "p_agent": [],      # lld: 原告法定代理人 
        "d_agent": []       # lld: 被告法定代理人 
    }

    tempKey = ""
    tempLIST = []
    for p in data["party"]:
        # 要加入的物件資料格式
        pAdd = {"title": p["title"],
                "value": p["value"]}

        # 紀錄上一個出現的類別，歸類法定代理人屬於哪方
        if len(p["group"]) > 0:
            tempKey = p["group"][0][0] + "_agent"   # "p"/"d" + "_agent"

        # 法定代理人/相對人
        if len(p["group"]) < 1:
            tempLIST.append(pAdd)
            if p["title"] == "法定代理人":
                party[tempKey].append(tempLIST)
                tempLIST = []
                tempKey = ""
            elif p["title"] == "相對人":
                # TODO: 相對人的定義
                party[tempKey].append(tempLIST)
                tempLIST = []
                tempKey = ""
        # 原告代理人
        elif len(p["group"]) > 1 and p["group"][0] == "plaintiff":
            party["p_agent"].append([pAdd])
        # 被告代理人
        elif len(p["group"]) > 1 and p["group"][0] == "defendant":
            party["d_agent"].append([pAdd])
        # 原告
        elif p["group"][0] == "plaintiff":
            # 把兩種名稱分開算
            if "即" in p["title"]:
                addLIST = p["title"].split("即")
                pAdd = {"title": addLIST[0],
                        "value": p["value"]}
                party["plaintiff"].append(pAdd)
                pAdd = {"title": addLIST[1],
                        "value": p["value"]}
            party["plaintiff"].append(pAdd)
        # 被告
        elif p["group"][0] == "defendant":
            if "即" in p["title"]:
                addLIST = p["title"].split("即")
                pAdd = {"title": addLIST[0],
                        "value": p["value"]}
                party["defendant"].append(pAdd)
                pAdd = {"title": addLIST[1],
                        "value": p["value"]}
            party["defendant"].append(pAdd)


    """
    2. 前處理: 文本
    """
    resultLIST = []
    
    # 忽略開頭判決書資訊
    lastParty = data["party"][-1]["value"]
    if isinstance(data["judgement"], list):
        for d, dLine in enumerate(data["judgement"]):
            if d.endswith(lastParty):
                tempSTR = "\r\n".join(data["judgement"][dLine+1:])
    elif isinstance(data["judgement"], str):
        dPos = re.search(lastParty, data["judgement"]).end()
        tempSTR = data["judgement"][dPos+1:]
    else:
        print(type(tempSTR))
        tempSTR = data["judgement"]

    # 將沒用的字取代
    replaceLIST = ["\r\n", " ", "\u3000"]   # \u3000: 全形空白
    for i in replaceLIST:
        tempSTR = tempSTR.replace(i, "")
     # 斷句
    jugLIST = tempSTR.split("。")


    """
    3. 序列化關係
    """
    # TODO: 根據特定案件類別特化結果
    # 案件類別
    # jugType = data["no"].split(",")[2]


    # 有被告跟原告
    if len(party["plaintiff"]) * len(party["defendant"][0]) > 0:
        # 找到同時出現原告跟被告的句子
        pSTR = party["plaintiff"][0]["title"]
        dSTR = party["defendant"][0]["title"]

        for jugSTR in jugLIST:
            if pSTR in jugSTR and dSTR in jugSTR:
                response = articut.parse(jugSTR, level="lv2")
                if response["status"]:
                    #pprint(response)
                    returnLIST = []
                    for objLIST in response["result_obj"]:
                        relation = ""
                        lastIsVerb = False
                        for obj in objLIST:
                            # 如果遇到「事件」則強制停止
                            if obj["text"] == "事件":
                                break
                            # 「等」會被當成動詞，跳過
                            elif obj["pos"] in verbLIST and obj["text"] == "等":                        
                                pass
                            # 連續出現的動詞關係
                            elif obj["pos"] in verbLIST and obj["text"] not in relation:
                                if lastIsVerb:                     
                                    relation += obj["text"]
                                else:
                                    relation = obj["text"]
                        returnLIST.append(relation)

        resultLIST.append({"pSTR": pSTR, "dSTR": dSTR, "return": returnLIST, "party": party})

    return {"status": True, "msg": resultLIST}


from bson.objectid import ObjectId  
if __name__ == "__main__":
    #testID = ObjectId("64d73d6bfba698f6bb2a925b")
    testID = ObjectId("64db9d1865296c25d879ce29")
    
    result = getRelation(testID)
    pprint(result["msg"])
    