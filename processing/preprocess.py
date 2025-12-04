import string
import pickle
import pandas as pd
import ast
import requests
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# Object for porterStemmer
ps = PorterStemmer()

# Ensure stopwords are available once; avoid repeated downloads on every rerun
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")


def get_genres(obj):
    lista = ast.literal_eval(obj)
    l1 = []
    for i in lista:
        l1.append(i['name'])
    return l1


def get_cast(obj):
    a = ast.literal_eval(obj)
    l_ = []
    len_ = len(a)
    for i in range(0, 10):
        if i < len_:
            l_.append(a[i]['name'])
    return l_


def get_crew(obj):
    l1 = []
    for i in ast.literal_eval(obj):
        if i['job'] == 'Director':
            l1.append(i['name'])
            break
    return l1


def read_csv_to_df():
    #  Reading both the csv files
    credit_ = pd.read_csv(r'Files/tmdb_5000_credits.csv')
    movies = pd.read_csv(r'Files/tmdb_5000_movies.csv')

    # Merging the dataframes
    movies = movies.merge(credit_, on='title')

    movies2 = movies
    movies2.drop(['homepage', 'tagline'], axis=1, inplace=True)
    movies2 = movies2[['movie_id', 'title', 'budget', 'overview', 'popularity', 'release_date', 'revenue', 'runtime',
                       'spoken_languages', 'status', 'vote_average', 'vote_count']]

    #  Extracting important and relevant features
    movies = movies[
        ['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'production_companies', 'release_date']]
    movies.dropna(inplace=True)

    # df[df['column_name'] == some_condition]['target_column'] = new_value
    # df.loc[df['column_name'] == some_condition, 'target_column'] = new_value

    #  Applying functions to convert from list to only items.
    movies['genres'] = movies['genres'].apply(get_genres)
    movies['keywords'] = movies['keywords'].apply(get_genres)
    movies['top_cast'] = movies['cast'].apply(get_cast)
    movies['director'] = movies['crew'].apply(get_crew)
    movies['prduction_comp'] = movies['production_companies'].apply(get_genres)

    #  Removing spaces from between the lines
    movies['overview'] = movies['overview'].apply(lambda x: x.split())
    movies['genres'] = movies['genres'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['keywords'] = movies['keywords'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['tcast'] = movies['top_cast'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['tcrew'] = movies['director'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['tprduction_comp'] = movies['prduction_comp'].apply(lambda x: [i.replace(" ", "") for i in x])

    # Creating a tags where we have all the words together for analysis
    movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['tcast'] + movies['tcrew']

    #  Creating new dataframe for the analysis part only.
    new_df = movies[['movie_id', 'title', 'tags', 'genres', 'keywords', 'tcast', 'tcrew', 'tprduction_comp']]

    # new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))
    new_df['genres'] = new_df['genres'].apply(lambda x: " ".join(x))
    # new_df['keywords'] = new_df['keywords'].apply(lambda x: " ".join(x))
    new_df['tcast'] = new_df['tcast'].apply(lambda x: " ".join(x))
    new_df['tprduction_comp'] = new_df['tprduction_comp'].apply(lambda x: " ".join(x))

    new_df['tcast'] = new_df['tcast'].apply(lambda x: x.lower())
    new_df['genres'] = new_df['genres'].apply(lambda x: x.lower())
    new_df['tprduction_comp'] = new_df['tprduction_comp'].apply(lambda x: x.lower())

    #  Applying stemming on tags and tags and keywords
    new_df['tags'] = new_df['tags'].apply(stemming_stopwords)
    new_df['keywords'] = new_df['keywords'].apply(stemming_stopwords)

    return movies, new_df, movies2


def stemming_stopwords(li):
    ans = []

    # ps = PorterStemmer()

    for i in li:
        ans.append(ps.stem(i))

    # Removing Stopwords
    stop_words = set(stopwords.words('english'))
    filtered_sentence = []
    for w in ans:
        w = w.lower()
        if w not in stop_words:
            filtered_sentence.append(w)

    str_ = ''
    for i in filtered_sentence:
        if len(i) > 2:
            str_ = str_ + i + ' '

    # Removing Punctuations
    punc = string.punctuation
    str_.translate(str_.maketrans('', '', punc))
    return str_


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_posters(movie_id):
    """
    Fetch poster URL from TMDB API using movie ID.
    Returns None if poster is not available.
    Cached for 1 hour to improve performance.
    """
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=6177b4297dff132d300422e0343471fb',
            timeout=3
        )
        data = response.json()
        
        if 'poster_path' in data and data['poster_path']:
            return f"https://image.tmdb.org/t/p/w300{data['poster_path']}"
        return None
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_posters_batch(movie_ids):
    """
    Fetch multiple posters at once using concurrent requests for better performance.
    Returns a dictionary mapping movie_id to poster URL.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    posters = {}
    
    def fetch_single(movie_id):
        try:
            response = requests.get(
                f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=6177b4297dff132d300422e0343471fb',
                timeout=3
            )
            data = response.json()
            if 'poster_path' in data and data['poster_path']:
                return movie_id, f"https://image.tmdb.org/t/p/w300{data['poster_path']}"
        except Exception:
            pass
        return movie_id, None
    
    # Fetch up to 10 posters concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_single, mid): mid for mid in movie_ids}
        for future in as_completed(futures):
            movie_id, poster = future.result()
            if poster:
                posters[movie_id] = poster
    
    return posters


@st.cache_resource(show_spinner=False)
def _load_similarity(pickle_file_path):
    with open(pickle_file_path, 'rb') as pickle_file:
        similarity_tags = pickle.load(pickle_file)
    return similarity_tags


def recommend(new_df, movie, pickle_file_path):
    similarity_tags = _load_similarity(pickle_file_path)

    movie_idx = new_df[new_df['title'] == movie].index[0]

    # Getting the top 25 movies from the list which are most similar
    movie_list = sorted(list(enumerate(similarity_tags[movie_idx])), reverse=True, key=lambda x: x[1])[1:26]

    rec_movie_list = []
    rec_movie_ids = []

    for i in movie_list:
        rec_movie_list.append(new_df.iloc[i[0]]['title'])
        rec_movie_ids.append(new_df.iloc[i[0]]['movie_id'])

    return rec_movie_list, rec_movie_ids


def vectorise(new_df, col_name):
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vec_tags = cv.fit_transform(new_df[col_name]).toarray()
    sim_bt = cosine_similarity(vec_tags)
    return sim_bt


@st.cache_data(show_spinner=False)
def fetch_person_details(id_):
    import time
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            data = requests.get(
                'https://api.themoviedb.org/3/person/{}?api_key=6177b4297dff132d300422e0343471fb'.format(id_),
                timeout=10
            ).json()

            try:
                url = 'https://image.tmdb.org/t/p/w220_and_h330_face' + data['profile_path']

                if data['biography']:
                    biography = data['biography']
                else:
                    biography = " "

            except:
                url = "https://media.istockphoto.com/vectors/error-icon-vector-illustration-vector-id922024224?k=6&m" \
                      "=922024224&s=612x612&w=0&h=LXl8Ul7bria6auAXKIjlvb6hRHkAodTqyqBeA6K7R54="
                biography = ""

            return url, biography
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                # Return placeholder if all retries fail
                url = "https://media.istockphoto.com/vectors/error-icon-vector-illustration-vector-id922024224?k=6&m" \
                      "=922024224&s=612x612&w=0&h=LXl8Ul7bria6auAXKIjlvb6hRHkAodTqyqBeA6K7R54="
                biography = ""
                return url, biography
        except Exception as e:
            url = "https://media.istockphoto.com/vectors/error-icon-vector-illustration-vector-id922024224?k=6&m" \
                  "=922024224&s=612x612&w=0&h=LXl8Ul7bria6auAXKIjlvb6hRHkAodTqyqBeA6K7R54="
            biography = ""
            return url, biography


@st.cache_resource(show_spinner=False)
def _load_movie_frames():
    # Loading both the dataframes for fast reading
    pickle_file_path = r'Files/movies_dict.pkl'
    with open(pickle_file_path, 'rb') as pickle_file:
        loaded_dict = pickle.load(pickle_file)

    movies = pd.DataFrame.from_dict(loaded_dict)

    pickle_file_path = r'Files/movies2_dict.pkl'
    with open(pickle_file_path, 'rb') as pickle_file:
        loaded_dict_2 = pickle.load(pickle_file)

    movies2 = pd.DataFrame.from_dict(loaded_dict_2)

    return movies, movies2


def get_details(selected_movie_name):
    movies, movies2 = _load_movie_frames()

    # Extracting series of data to be displayed
    a = pd.DataFrame(movies2[movies2['title'] == selected_movie_name])
    b = pd.DataFrame(movies[movies['title'] == selected_movie_name])

    # Extracting necessary details
    budget = a.iloc[0, 2]
    overview = a.iloc[0, 3]
    release_date = a.iloc[:, 5].iloc[0]
    revenue = a.iloc[:, 6].iloc[0]
    runtime = a.iloc[:, 7].iloc[0]
    available_lang = ast.literal_eval(a.iloc[0, 8])
    vote_rating = a.iloc[:, 10].iloc[0]
    vote_count = a.iloc[:, 11].iloc[0]
    movie_id = a.iloc[:, 0].iloc[0]
    cast = b.iloc[:, 9].iloc[0]
    director = b.iloc[:, 10].iloc[0]
    genres = b.iloc[:, 3].iloc[0]
    this_poster = fetch_posters(movie_id)
    cast_per = b.iloc[:, 5].iloc[0]
    a = ast.literal_eval(cast_per)
    cast_id = []
    for i in a:
        cast_id.append(i['id'])
    lang = []
    for i in available_lang:
        lang.append(i['name'])

    # Adding to a list for easy export
    info = [this_poster, budget, genres, overview, release_date, revenue, runtime, available_lang, vote_rating,
            vote_count, movie_id, cast, director, lang, cast_id]

    return info
