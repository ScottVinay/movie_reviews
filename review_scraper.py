### --- In this file, we scrape the rotten tomatoes website for user reviews --- ###
### --- Importing modules --- ###
import json
import random
import re
import time
from collections import defaultdict

import numpy as np
import pandas as pd
import requests

from api_call import search_for_movie
from movie_scraper import get_next_movie


### --- get_movie_info function provides the movie id and movie name --- ###
def get_movie_info(url_id):
    # Requesting the HTML documentation
    response = requests.get(f'https://www.rottentomatoes.com/{url_id}/reviews?type=user')

    # Searching the HTML doc to extract the movie_id
    html_data  = json.loads(re.search('movieReview\s=\s(.*);', response.text).group(1))
    movie_id   = html_data['movieId']
    # Extracting movie_name for file saving
    movie_name = html_data['title']
    movie_name = movie_name.lower().replace(' ','_')

    # Returning movie_id and movie_name
    return movie_name, movie_id


### --- get_reviews function flicks through the review pages --- ###
def get_review_page(endCursor, movie_id):
    r = requests.get(f'https://www.rottentomatoes.com/napi/movie/{movie_id}/reviews/user',
    params = {
        "direction": "next",
        "endCursor": endCursor,
        "startCursor": ""
    })
    return r.json()


### --- get_all_reviews function uses get_review_page to loop through thousands of review pages for our chosen movie --- ###
def get_all_reviews(movie_id):
    reviews = []
    result  = {}
    
    i = 0
    while True:
        try:
            # Random no. generator created to pause code and prevent overloading servers
            r = np.abs(np.random.randn()/3 + 1)
            time.sleep(r) #[s]

            # Gathering all movie review information into list: reviews
            result = get_review_page(result['pageInfo']['endCursor'] if i != 0  else '', movie_id)
            reviews.extend([t for t in result['reviews']])

            # Stopping loop at final page or after 5,000 pages
            if result['pageInfo']['hasNextPage']==False or i > 4999:
                break
            elif i > 5000:
                break
            if len(reviews)>140:
                return reviews #XX
            # Pausing for a minute after 10,000 reviews (100 pages)
            i += 1
            if i%1000==0:
                time.sleep(60)
        
        except requests.exceptions.RequestException:
            print('Wifi out, waiting...')
            time.sleep(30)
    
    return reviews


### --- Parsing function that obtains relevant data and puts it into a dataframe --- ###
def parse_reviews(save_name, movie_id, movie_year, meter_score):
    reviews = get_all_reviews(movie_id)
    N = len(reviews)

    # data = defaultdict(list)
    data = {}

    # Movie name
    data['movie_name'] = [save_name]*N
    # Movie year
    data['movie_year'] = [movie_year]*N
    # Meter score
    data['meter_score'] = [meter_score]*N

    # User id
    users_all = [reviews[i]['user']['userId'] for i in range(N)]
    users     = [reviews[i]['user']['userId'] 
                if len(users_all[i]) == 9 
                else np.nan 
                for i in range(N)]
    data['user'] = users

    # Finding reviewers who have user id's 
    users = [
        reviews[i]['user']['userId']
        if len(reviews[i]['user']['userId'])==6
        else np.nan
        for i in range(len(reviews))
        ]
    N =2;meter_score = 2

    data = {}
    data['movie_name']  = [save_name]*N
    data['movie_year']  = [movie_year]*N
    data['meter_score'] = [meter_score]*N

    # Get various columns
    data['user'].extend(users)
    data['super_reviewer'].extend([int(rev['isSuperReviewer']) for rev in reviews])
    data['profanity'].extend([int(rev['hasProfanity']) for rev in reviews])
    data['review'].extend([rev['review'] for rev in reviews])
    
    star_rating = [rev['rating'] for rev in reviews]
    star_rating = [float(x.replace('STAR_','').replace('_','.')) for x in star_rating]
    data['rating'].extend(star_rating)

    # Creating dataframe of reviews
    df = pd.DataFrame(data)
    df.to_pickle(f'./review_dfs/{save_name}.pkl')
    return df


### --- Run Code --- ###
if __name__ == '__main__':
    start = time.time()
    for i in range(4):
        # Calling functions
        search_name, movie_year         = get_next_movie()
        movie_name, url_id, meter_score = search_for_movie(search_name, movie_year)
        save_name, movie_id             = get_movie_info(url_id)
        parse_reviews(save_name, movie_id, movie_year, meter_score)

    end = time.time()
    print(f'Time to run:{(start-end)/3600:.2f} hrs')



# When to use a default dict
# Counting how many of each letter we have:
string = 'aababcaccbbabababbacccabababcaa'
counts = defaultdict(int)
for s in string:
    counts[s] += 1
