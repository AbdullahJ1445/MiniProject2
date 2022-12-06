import pymongo	# in terminal: pip freeze | grep pymongo
import json
from pymongo import TEXT

"""For this part, you will write a program, named load-json with a proper extension 
(e.g. load-json.py if using Python), which will take a json file in the current 
directory and constructs a MongoDB collection. Your program will take as input a 
json file name and a port number under which the MongoDB server is running, will 
connect to the server and will create a database named 291db (if it does not exist). 
Your program then will create a collection named dblp. 

If the collection exists, your 
program should drop it and create a new collection. Your program for this phase ends 
after building the collection.

Important Note: The input file is expected to be too large to fit in memory and you 
are expected to process it as one-row-at-a time, and not to fully load the file into 
memory. You may find Mongoimport helpful, and you may change the default batch size 
(if needed) to allow loading large files on lab machines."""

port_num = input ("Enter the port number: ")
json_name = input ("Enter the json file name (including the .json): ")

mango_ad =str("mongodb://localhost:"+port_num+"/")

myclient = pymongo.MongoClient(mango_ad)
mydb = None
dblp = None

database_names = myclient.list_database_names()
if "291db" not in database_names:
    mydb = myclient["291db"]
else:
    myclient.drop_database("291db")
    mydb = myclient["291db"]

collection_names = mydb.list_collection_names()
if "dblp" not in collection_names:
    dblp = mydb["dblp"]
else:
    mydb.drop_collection("dblp")
    dblp = mydb["dblp"]

# {"authors": ["Jovan Dj. Golic", "Guglielmo Morgari"], 
# "n_citation": 2, 
# "title": "Vectorial fast correlation attacks.", 
# "venue": "", 
# "year": 2004, 
# "id": "00638a94-23bf-4fa6-b5ce-40d799c65da7"}

counter = 0
list_temp = []

with open(json_name) as f:
    for line in f:

        counter += 1
        data = json.loads(line)
        list_temp.append(data)

        if counter >= 10000:
            dblp.insert_many(list_temp)
            list_temp = []
            counter = 0

    if len(list_temp) > 0:
        dblp.insert_many(list_temp)


#create text index for authors, and abstract and set default language to none
dblp.create_index([("authors", TEXT), ("abstract", TEXT)], default_language="none")

#create an ordered index for references
dblp.create_index([("references", pymongo.ASCENDING)])

#create an ordered index for id
dblp.create_index([("id", pymongo.ASCENDING)]) 
