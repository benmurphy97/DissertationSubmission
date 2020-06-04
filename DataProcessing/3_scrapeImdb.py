import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import re
import time
from pymongo import MongoClient


###### Read in data and change imdb links to mathc imdb website
movieDF = pd.read_csv('MovieLensFilteredData/moviesFiltered.csv')
movieDF['imdbId_string'] = movieDF['imdbId'].astype('str')

def addZeroToFiveLetters(idString):
    output = ""
    if len(idString) == 5:
        output = "00" + idString
    elif len(idString) == 6:
        output = "0" + idString
    else:
        output = idString
    return output

movieDF['imdbID_padded'] = movieDF["imdbId_string"].apply(lambda row: addZeroToFiveLetters(row))

# this mvie doesnt have an imdb page
movieDF = movieDF.loc[~movieDF['imdbID_padded'].isin(['0118114'])]


# data from df
imdb_link_ids = movieDF.imdbID_padded.tolist()
titles = movieDF.title.tolist()
movie_ids = movieDF.movieId.tolist()
print(len(imdb_link_ids))


# links must be in this format:
# https://www.imdb.com/title/tt0114709/

client = MongoClient('mongodb://localhost:27017/')
db = client.nebflix


# list to create df
movieDataList = []


print("************SCRAPING************")

for ind, link in enumerate(imdb_link_ids):
    st = time.time()

    page_link = "https://www.imdb.com/title/tt"+link

    movie_page  = requests.get(page_link)
    movie_page = movie_page.text
    # movie_soup = BeautifulSoup(movie_page, "html.parser")
    movie_soup = BeautifulSoup(movie_page, "lxml")

    #     get title
    #     title_step = movie_soup.find("div", class_ = 'title_wrapper')
    #     title = title_step.find_next("h1").text

    # we have title in df
    title = titles[ind]
    
    year = title[-5:-1]
    title = title[:-7]
    print(title)
   
    poster = movie_soup.find("div", class_ = 'poster').find_next("img")['src']

    # movieId from df
    movieId = movie_ids[ind]

    # get storyline
    storyline = movie_soup.find("div", id = 'titleStoryLine')
    storyline = storyline.find_next("span").find_next("span").text
    # storyline = movie_soup.findChild("div", class_ = "inline canwrap").find_next("span").text

    # get director
    director = movie_soup.find("div", class_ = 'credit_summary_item').find_next("a").text

    # get actors
    actors = []
    actor_photos = movie_soup.find_all("td", class_ = 'primary_photo')
    
    for i in actor_photos:
        actor = i.find_next("td").text.strip()
        actors.append(actor)

    # get genres
    genres = []
    title_wrapper = movie_soup.find("div", class_ = 'title_wrapper').find_next("div")
    genre_elements = title_wrapper.find_all("a")

    for g in genre_elements:
        genres.append(g.text)

    genres = genres[:-1]

    
    # get rating
    titleStoryLine = movie_soup.find("div", id = 'titleStoryLine')
    # print(titleStoryLine.text)

    # create dict object to insert into mongo
    movie_dict = {
        "movieId": movieId,
        "title": title,
        "year": year,
        "storyline": storyline,
        "director": director,
        "actors": actors,
        "genres": genres,
        "imdbId": link,
        "image_link": poster
    }    

    
    db.movies.insert_one(movie_dict)


    movieDataList.append(movie_dict)

#     print(time.time()-st, "\n")
    
#     insert movie data

#     myquery = { "movieId": movieId }
#     newvalues = { "$set": { "image_link": poster } }
#     db.movies.update_one(myquery, newvalues)


dataDf = pd.DataFrame(movieDataList)

dataDf.to_csv('MovieLensFilteredData/ScrapedMoviedData.csv')