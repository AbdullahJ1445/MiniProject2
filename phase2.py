import pymongo
import json
import re

port_num = input("Enter a port number: ")
mango_ad =str("mongodb://localhost:"+port_num+"/")

myclient = pymongo.MongoClient(mango_ad)
mydb = myclient["291db"]
dblp = mydb["dblp"]

#Search for articles The user should be able to provide one or more keywords, and the system should retrieve all articles that match all those keywords (AND semantics). A keyword matches if it appears in any of title, authors, abstract, venue and year fields (the matches should be case-insensitive). For each matching article, display the id, the title, the year and the venue fields. The user should be able to select an article to see all fields including the abstract and the authors in addition to the fields shown before. If the article is referenced by other articles, the id, the title, and the year of those references should be also listed.

def search_articles():
    #user can input one or more keywords
    keyword = input("Enter a keyword: ")
    #split the keywords into a list
    keyword_list = keyword.split()
    
    #search for articles, title, authors, abstract, venue, year
    articles = dblp.aggregate([
        {"$match": {"$and": [{"$or": [{"title": {"$regex": keyword, "$options": "i"}}, 
        {"authors": {"$regex": keyword, "$options": "i"}}, 
        {"abstract": {"$regex": keyword, "$options": "i"}}, 
        {"venue": {"$regex": keyword, "$options": "i"}}, 
        {"year": {"$regex": keyword, "$options": "i"}}]} for keyword in keyword_list]}},
        {"$project": {"_id": 1, "title": 1, "year": 1, "venue": 1}}
    ])

    #print numbers of matches
    # list1 = list(articles)
    # num_matches = len(list1)
    # print("Number of matches: ", num_matches)

    # #print the articles
    article_num = 1
    for article in articles:
        print("Article number: ", article_num)
        print("ID: ", article["_id"])
        print("Title: ", article["title"])
        print("Year: ", article["year"])
        print("Venue: ", article["venue"])
        print("")
        article_num += 1

    #user can select an article number to see all fields including the abstract and the authors in addition to the fields shown before
    article_num = int(input("Enter an article number: "))
    #cross reference the article number with the id
    article_id = dblp.aggregate([
        {"$match": {"$and": [{"$or": [{"title": {"$regex": keyword, "$options": "i"}},
        {"authors": {"$regex": keyword, "$options": "i"}},
        {"abstract": {"$regex": keyword, "$options": "i"}},
        {"venue": {"$regex": keyword, "$options": "i"}},
        {"year": {"$regex": keyword, "$options": "i"}}]} for keyword in keyword_list]}},
        {"$project": {"_id": 1, "title": 1, "year": 1, "venue": 1}},
        {"$skip": article_num - 1},
        {"$limit": 1}
    ])

    #get the id
    for article in article_id:
        id = article["_id"]
    #search for the article with the id
    article = dblp.find_one({"_id": id})
    #print the article
    print("ID: ", article["_id"])
    print("Title: ", article["title"])
    print("Year: ", article["year"])
    print("Venue: ", article["venue"])
    #get the abstract from its index
    abstract = dblp.find_one({"_id": id}, {"abstract": 1})
    #if no abstract, print "No abstract"
    if abstract == None:
        print("Abstract: No abstract")
    else:
        #ignore KeyError
        try:
            print("Abstract: ", abstract["abstract"])
        except KeyError:
            print("Abstract: No abstract")
    #get the authors from its index
    authors = dblp.find_one({"_id": id}, {"authors": 1})
    print("Authors: ", authors["authors"])

    # if the article is referenced by other articles, the id, the title, and the year of those references should be also listed
    # get the references from its index
    referencess = dblp.find_one({"_id": id}, {"references": 1})
    #if there is no references, print no references
    if referencess== []:
        print("No references")
    #if there are references, print the references
    else:
        print("References: ")
        try:
            referencess = article["references"]
            #search for the references
            reference_articles = dblp.aggregate([
                {"$match": {"_id": {"$in": referencess}}}, 
                {"$project": {"_id": 1, "title": 1, "year": 1}}
            ])
            #print the references
            for reference in reference_articles:
                print("ID: ", reference["_id"])
                print("Title: ", reference["title"])
                print("Year: ", reference["year"])
                print("")
        except KeyError:
            print("No references")
    

#Search for authors The user should be able to provide a keyword  and see all authors whose names contain the keyword (the matches should be case-insensitive). For each author, list the author name and the number of publications. The user should be able to select an author and see the title, year and venue of all articles by that author. The result should be sorted based on year with more recent articles shown first.

def search_authors():
    keyword = input("Enter a keyword: ")
    #if input more than one word, error
    if len(keyword.split()) > 1:
        print("Error: Please enter only one keyword")
        return
    
    authors = dblp.aggregate([
        {"$match": {"$text": {"$search": keyword}}},
        {"$project": {"authors": 1, "n_citation": 1, "score": {"$meta": "textScore"}}},
        {"$sort": {"score": -1}},
        {"$unwind": "$authors"},
        {"$match": {"authors": {"$regex": keyword, "$options": "i"}}},
        {"$group": {"_id": "$authors", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])

    # #print number of authors
    # list1 = list(authors)
    # num_authors = len(list1)
    # print("Number of authors: ", num_authors)

    #list the author name and the number of publications
    for author in authors:
        print("Author: ", author["_id"])
        print("Number of publications: ", author["count"])
        print("")

    author_name = input("Enter an author name: ")
    author_papers = dblp.aggregate([
        {"$match": {"authors": author_name}},
        {"$sort": {"year": -1}}
    ])
    for paper in author_papers:
        print("Title: ", paper["title"])
        print("Year: ", paper["year"])
        print("Venue: ", paper["venue"])


def list_venues():
    #user enters a number n
    n = int(input("Enter a number: "))

    # For each venue, list the venue, the number of articles in that venue, and the number of articles that reference a paper in that venue. Sort the result based on the number of papers that reference the venue with the top most cited venues shown first.
    venues = dblp.aggregate([
        {"$match": {"venue": {"$ne": ""}}},
        {"$group": {"_id": "$venue", "count": {"$sum": 1}}},
        #project these two fields and add a new field called "cited" that is the number of papers that reference a paper in that venue
        {"$project": {"_id": 1, "count": 1, "cited": {"$size": {"$ifNull": ["$references", []]}}}}, 
          
        {"$sort": {"count": -1}},
        {"$limit": n},
        #number of articles that reference a paper in the venue that we are looking at
        {"$lookup": {"from": "dblp", "localField": "_id", "foreignField": "venue", "as": "cited"}},
        {"$unwind": "$cited"},
        {"$group": {"_id": "$_id", "count": {"$first": "$count"}, "cited": {"$sum": {"$size": {"$ifNull": ["$cited.references", []]}}}}},
        {"$sort": {"cited": -1}}
    ])


    #print the venues
    for venue in venues:
        print("Venue: ", venue["_id"])
        print("Number of articles in that venue: ", venue["count"])
        print("Number of articles that reference a paper in that venue: ", venue["cited"])
        print("")


#Add an article The user should be able to add an article to the collection by providing a unique id, a title, a list of authors, and a year. The fields abstract and venue should be set to null, references should be set to an empty array and n_citations should be set to zero. 
def add_article():
    #user enters a unique id, a title, a list of authors, and a year
    id = input("Enter a unique id: ")
    title = input("Enter a title: ")
    authors = input("Enter a list of authors: ")
    year = input("Enter a year: ")

    #if the id already exists, error
    if dblp.find_one({"_id": id}) != None:
        print("Error: The id already exists")
        return

    #if the year is not a number, error
    if not year.isdigit():
        print("Error: The year is not a number")
        return

    #if the title is empty, error
    if title == "":
        print("Error: The title is empty")
        return

    #if the authors is empty, error
    if authors == "":
        print("Error: The authors is empty")
        return

    #add the article to the collection
    dblp.insert_one({"_id": id, "title": title, "authors": authors.split(","), "year": int(year), "abstract": None, "venue": None, "references": [], "n_citation": 0})

    print("The article has been added")


def main():
    #After each action, the control is returned to the main menu for further operations
  #The user can exit the program if they wishes
    while True:
        print("1. Search for articles")
        print("2. Search for authors")
        print("3. List venues")
        print("4. Add an article")
        print("5. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            search_articles()
        elif choice == "2":
            search_authors()
        elif choice == "3":
            list_venues()
        elif choice == "4":
            add_article()
        elif choice == "5":
            break
        else:
            print("Error: Invalid choice")

if __name__ == "__main__":
    main()