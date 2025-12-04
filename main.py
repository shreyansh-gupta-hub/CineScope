import streamlit as st
import streamlit_option_menu
from streamlit_extras.stoggle import stoggle
from processing import preprocess
from processing.display import Main

# Setting the wide mode as default
st.set_page_config(
    page_title="CineScope | Movie Discovery",
    page_icon=None,
    layout="wide"
)

displayed = []
RECOMMENDER_CONFIG = [
    ("Overall similarity", r'Files/similarity_tags_tags.pkl'),
    ("Genre overlap", r'Files/similarity_tags_genres.pkl'),
    ("Shared production", r'Files/similarity_tags_tprduction_comp.pkl'),
    ("Keyword resonance", r'Files/similarity_tags_keywords.pkl'),
    ("Cast proximity", r'Files/similarity_tags_tcast.pkl')
]

if 'movie_number' not in st.session_state:
    st.session_state['movie_number'] = 0

if 'selected_movie_name' not in st.session_state:
    st.session_state['selected_movie_name'] = ""

if 'user_menu' not in st.session_state:
    st.session_state['user_menu'] = ""

if 'recommendations_cache' not in st.session_state:
    st.session_state['recommendations_cache'] = {}


def inject_custom_styles():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;600&display=swap');
            .stApp {
                background: radial-gradient(circle at top left, rgba(34,105,127,0.45), rgba(4,16,36,0.95)),
                            repeating-linear-gradient(135deg,
                                rgba(18,93,115,0.35) 0px,
                                rgba(18,93,115,0.35) 40px,
                                rgba(6,18,40,0.65) 40px,
                                rgba(6,18,40,0.65) 80px);
                color: #f5f5f5;
                font-family: 'Inter', sans-serif;
            }
            h1, h2, h3, h4 {
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                letter-spacing: 0.02em;
            }
            .main-block {
                padding: 2rem 2.5rem;
            }
            .movie-chip {
                padding: 0.35rem 0.75rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.08);
                font-size: 0.85rem;
                display: inline-block;
                margin-bottom: 0.35rem;
            }
            .section-title {
                font-size: 1.1rem;
                text-transform: uppercase;
                letter-spacing: 0.2rem;
                color: #7dd3fc;
                margin-bottom: 0.5rem;
            }
            .card {
                background: rgba(255,255,255,0.04);
                padding: 0.75rem 1rem;
                border-radius: 1rem;
                border: 1px solid rgba(255,255,255,0.08);
                min-height: 100%;
                transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
            }
            .card:hover {
                transform: translateY(-2px);
                border-color: rgba(125, 211, 252, 0.55);
                box-shadow: 0 10px 25px rgba(0,0,0,0.35);
            }
            .recommend-card img {
                border-radius: 0.75rem;
                border: 1px solid rgba(255,255,255,0.1);
            }
            .recommend-card h4 {
                font-size: 1rem;
                margin-top: 0.15rem;
                margin-bottom: 0.15rem;
                color: #f8fafc;
                line-height: 1.3;
            }
            .recommend-card span {
                font-size: 0.85rem;
                color: #cdd5f7;
            }
            .search-section .stSelectbox label {
                font-size: 0.95rem;
                color: #cbd5f5;
            }
            .stButton button {
                background: linear-gradient(90deg, #f43f5e, #fb923c);
                border: none;
                color: #fff;
                padding: 0.55rem 1.75rem;
                border-radius: 999px;
                font-weight: 600;
            }
            .stButton button:hover {
                box-shadow: 0 8px 20px rgba(244,63,94,0.35);
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.35rem;
                border-bottom: 1px solid rgba(255,255,255,0.08);
            }
            .stTabs [data-baseweb="tab"] {
                background: rgba(255,255,255,0.04);
                border-radius: 999px 999px 0 0;
                padding: 0.4rem 1.25rem;
                font-weight: 500;
                color: #e2e8f0;
            }
            .stTabs [aria-selected="true"] {
                background: rgba(125,211,252,0.15) !important;
                color: #7dd3fc !important;
            }
            .stMetric {
                background: rgba(255,255,255,0.04);
                border-radius: 0.75rem;
                padding: 0.75rem 1rem;
                border: 1px solid rgba(255,255,255,0.06);
            }
            .stSlider > div > div {
                background: rgba(255,255,255,0.08);
                border-radius: 999px;
            }
            .stSlider [role="slider"] {
                background: #38bdf8;
                border: 3px solid rgba(255,255,255,0.4);
            }
            .stToggle label {
                font-weight: 600;
            }
            /* Hide default Streamlit image icons */
            [data-testid="stImage"] img[src*="data:image"] {
                display: none;
            }
            /* Hide broken image placeholders */
            img[alt=""] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    inject_custom_styles()

    def hero_header():
        with st.container():
            left, right = st.columns([3, 2], gap="large")
            with left:
                st.markdown('<div class="section-title">CineScope</div>', unsafe_allow_html=True)
                st.title("Find your next movie night favourite")
                st.markdown(
                    "Dive into curated recommendations, rich movie insights, and a "
                    "visual catalog powered by TMDB. Pick your vibe and let CineScope handle the rest."
                )
                st.caption("Tip: Start with similarity-based picks, then inspect cast & details.")
            with right:
                st.metric("Movies indexed", f"{len(movies):,}")
                st.metric("Similarity features", "Genres | Keywords | Studios | Cast")
                st.metric("Catalogue pages", f"{len(movies) // 10:,}")

    def initial_options():
        hero_header()

        # To display menu
        st.session_state.user_menu = streamlit_option_menu.option_menu(
            menu_title='What are you looking for?',
            options=['Recommend me a similar movie', 'Check all Movies'],
            icons=['film', 'film'],
            menu_icon='list',
            orientation="horizontal",
        )

        if st.session_state.user_menu == 'Recommend me a similar movie':
            recommend_display()

        elif st.session_state.user_menu == 'Check all Movies':
            paging_movies()

    def gather_recommendations(selected_movie_name):
        global displayed
        displayed.clear()
        collected = {}
        
        # Collect all movie IDs first
        all_movie_ids = []
        temp_recs = {}
        
        for descriptor, path in RECOMMENDER_CONFIG:
            movies_list, movie_ids_list = preprocess.recommend(new_df, selected_movie_name, path)
            recs = []
            cnt = 0
            for title, movie_id in zip(movies_list, movie_ids_list):
                if cnt == 3:
                    break
                if title not in displayed:
                    recs.append({"title": title, "poster": None, "movie_id": movie_id})
                    all_movie_ids.append(movie_id)
                    displayed.append(title)
                    cnt += 1
            if recs:
                temp_recs[descriptor] = recs
        
        # Batch fetch all posters at once using concurrent requests
        poster_map = preprocess.fetch_posters_batch(all_movie_ids)
        
        # Update recommendations with fetched posters
        for descriptor, recs in temp_recs.items():
            for rec in recs:
                if rec['movie_id'] in poster_map:
                    rec['poster'] = poster_map[rec['movie_id']]
            collected[descriptor] = recs
        
        return collected

    def fetch_unique_recommendations(dataset, selected_movie_name, pickle_file_path):
        movies, posters = preprocess.recommend(dataset, selected_movie_name, pickle_file_path)
        recs = []
        cnt = 0
        for title, poster in zip(movies, posters):
            if cnt == 3:  # Reduced from 5 to 3 for faster loading
                break
            if title not in displayed:
                recs.append({"title": title, "poster": poster})
                displayed.append(title)
                cnt += 1
        return recs

    def render_recommendation_cards(label, recommendations):
        if not recommendations:
            st.info("No fresh picks for this strategy, try another tab.")
            return
        st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)
        
        cols = st.columns(len(recommendations))
        for idx, col in enumerate(cols):
            movie = recommendations[idx]
            with col:
                # Only show image if it's a valid TMDB poster
                poster = movie['poster']
                if poster and 'image.tmdb.org' in poster and 'istockphoto.com' not in poster:
                    st.image(poster, use_container_width=True)
                st.markdown(f"<h4>{movie['title']}</h4>", unsafe_allow_html=True)
                st.caption("Open Describe tab for complete profile.")

    def recommend_display():

        st.subheader('Smart movie picks tailored to your choice')

        with st.container():
            st.markdown('<div class="main-block search-section">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_movie_name = st.selectbox(
                    'Select a movie to get curated recommendations',
                    new_df['title'].values,
                    key="movie_select"
                )
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                rec_button = st.button('Recommend', use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if rec_button:
            st.session_state.selected_movie_name = selected_movie_name
            with st.spinner('🎬 Fetching movie recommendations...'):
                st.session_state.recommendations_cache = gather_recommendations(selected_movie_name)

        if st.session_state.recommendations_cache:
            st.markdown("### Explore recommendation strategies")
            tab_labels = list(st.session_state.recommendations_cache.keys())
            tabs = st.tabs(tab_labels)
            for tab, label in zip(tabs, tab_labels):
                with tab:
                    render_recommendation_cards(label, st.session_state.recommendations_cache[label])
        else:
            st.info("Pick a movie and hit Recommend to unlock tailored suggestions.")

    def display_movie_details():

        selected_movie_name = st.session_state.selected_movie_name
        if not selected_movie_name:
            st.info("Select a movie from the Recommend tab to see rich details here.")
            return
        # movie_id = movies[movies['title'] == selected_movie_name]['movie_id']
        info = preprocess.get_details(selected_movie_name)

        with st.container():
            st.text('\n')
            st.title(selected_movie_name)
            st.text('\n')
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Rating", info[8])
            with metric_col2:
                st.metric("Votes", info[9])
            with metric_col3:
                st.metric("Runtime", info[6])

            st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
            st.write(info[3])

            stat1, stat2, stat3 = st.columns(3)
            with stat1:
                st.caption("Release Date")
                st.write(info[4])
            with stat2:
                st.caption("Budget")
                st.write(info[1])
            with stat3:
                st.caption("Revenue")
                st.write(info[5])

            info_col1, info_col2, info_col3 = st.columns(3)
            with info_col1:
                genres = " · ".join(info[2])
                st.caption("Genres")
                st.write(genres)

            with info_col2:
                avail = " · ".join(info[13])
                st.caption("Available in")
                st.write(avail)
            with info_col3:
                st.caption("Directed by")
                st.write(info[12][0])

        # Displaying information of casts.
        st.header('Cast')
        cnt = 0
        urls = []
        bio = []
        cast_names = []
        for i in info[14]:
            if cnt == 5:
                break
            url, biography= preprocess.fetch_person_details(i)
            urls.append(url)
            bio.append(biography)
            cast_names.append(i)
            cnt += 1

        if not urls:
            st.info("Cast information is unavailable for this title.")
            return

        cols = st.columns(len(urls))
        for idx, col in enumerate(cols):
            with col:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"<h4 style='text-align:center;'>{cast_names[idx]}</h4>", unsafe_allow_html=True)
                stoggle(
                    "Show More",
                    bio[idx],
                )
                st.markdown('</div>', unsafe_allow_html=True)

    def paging_movies():
        # To create pages functionality using session state.
        max_pages = movies.shape[0] / 10
        max_pages = int(max_pages) - 1

        st.markdown('<div class="main-block">', unsafe_allow_html=True)
        st.subheader("Browse the entire catalogue")
        col1, col2, col3 = st.columns([1, 9, 1])

        with col1:
            st.text("Previous page")
            prev_btn = st.button("Prev")
            if prev_btn:
                if st.session_state['movie_number'] >= 10:
                    st.session_state['movie_number'] -= 10

        with col2:
            new_page_number = st.slider("Jump to page number", 0, max_pages, st.session_state['movie_number'] // 10)
            st.session_state['movie_number'] = new_page_number * 10

        with col3:
            st.text("Next page")
            next_btn = st.button("Next")
            if next_btn:
                if st.session_state['movie_number'] + 10 < len(movies):
                    st.session_state['movie_number'] += 10

        display_all_movies(st.session_state['movie_number'])
        st.markdown('</div>', unsafe_allow_html=True)

    def display_all_movies(start):
        # Fetch posters for current page in batch
        end = min(start + 10, len(movies))
        movie_ids = [movies['movie_id'][i] for i in range(start, end)]
        poster_map = preprocess.fetch_posters_batch(movie_ids)
        
        i = start
        for _ in range(2):  # two rows of five cards
            cols = st.columns(5)
            for col in cols:
                if i >= len(movies) or i >= end:
                    break
                with col:
                    title = movies['title'][i]
                    movie_id = movies['movie_id'][i]
                    poster = poster_map.get(movie_id)
                    # Only show image if it's a valid TMDB poster
                    if poster and 'image.tmdb.org' in poster:
                        st.image(poster, use_container_width=True)
                    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
                    i += 1
            if i >= len(movies) or i >= end:
                break

        st.session_state['page_number'] = i

    with Main() as bot:
        bot.main_()
        new_df, movies, movies2 = bot.getter()
        initial_options()


if __name__ == '__main__':
    main()
