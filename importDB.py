import pymongo
import json
import configparser
import os

config = configparser.ConfigParser()
try:
    config.read('config.ini')
    connect_string = f"mongodb://{config['mongodb']['user']}:{config['mongodb']['password']}@{config['mongodb']['host']}:{config['mongodb']['port']}/?authMechanism=DEFAULT"
    database_name = config['mongodb']['db']
    collection_name = "test"
except:
    print("config.ini not found")
    exit()

myclient = pymongo.MongoClient(connect_string)
mydb = myclient[database_name]
mycol = mydb[collection_name]

dataPATH = "./福建連江地方法院_民事"

if __name__ == "__main__":
    fileLIST = os.listdir(dataPATH)
    for fname in fileLIST:
        with open(f"{dataPATH}/{fname}", "r", encoding="utf-8") as f:
            data = json.load(f)
            mycol.insert_one(data)



"""
mydict = { "name": "John", "address": "Highway 37" }
x = mycol.insert_one(mydict)

db.createUser({
    user: "root",
    pwd: "4E27860D9377A4493C485AEEFE423FDC",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})

"""
