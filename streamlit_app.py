

"""
Name: Eleri Schutte, Raegan Rapoza, Sophia Higgins
Data: Netflix Titles
URL: https://www.kaggle.com/datasets/abdelrahman16/netflix

Description: Our program uses Netflix data to analyze a variety of elements, including top genres and actors. Our
program gives recommendations for movies and TV shows, as several visuals.

"""
import csv
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pandas.core.config_init import max_cols
import requests
from bs4 import BeautifulSoup
from PIL import Image
from wordcloud import WordCloud

# CREATE DATAFRAME FROM CSV
net_df = pd.read_csv("netflix_titles.csv")


# [DA1] CLEAN THE DATA
net_df.info()
net_df.isnull().sum()

#Replacing null values with "Unknown"
def clean_columns(df, replace="Unknown"):
    df["director"] = df["director"].fillna(replace)
    df["cast"] = df["cast"].fillna(replace)
    df["country"] = df["country"].fillna(replace)
    df["rating"] = df["rating"].fillna("Not Rated")
    return df
net_df = clean_columns(net_df)
net_df[["director", "cast", "country", "rating"]].isnull().sum()

# [DA1] CLEAN THE DATA & [DA7] CREATE NEW COLUMNS
net_df["date_added"] = pd.to_datetime(net_df["date_added"], errors="coerce")

net_df["year_added"] = net_df["date_added"].dt.year
net_df["month_added"] = net_df["date_added"].dt.month
net_df["month_name"] = net_df["date_added"].dt.month_name()

net_df["year_month"] = net_df["date_added"].dt.to_period("M").astype(str)

#the user will request a show or movie, enter a genre they are interested in, and choose the number of recommendations they want
def recommend(type, genre, number, df = net_df): # [PY1] FUNCTION WITH 4 PARAMETERS
    filtered_df = df[df["type"].str.lower() == type.lower()] # [DA4] FILTER BY TYPE
    filtered_df = filtered_df[filtered_df["listed_in"].str.contains(genre, case = False)] # [DA4] FILTER BY GENRE

    try: #[PY3]
        filtered_df = filtered_df.sample(n=number)
        return filtered_df[['title', 'duration', 'release_year']]

    except ValueError:
        st.warning("No results found for your selection. Try another genre or type.")
        return pd.DataFrame({"Warning": [f"No results found."]})


# [DA8] ITERATE THROUGH ROWS OF A DATAFRAME WITH ITERROWS()
def count(column_name, df = net_df):
    count_dict = {} #[PY5] DICTIONARY
    for index, row in df.iterrows():
        item = row[column_name]
        if column_name == "listed_in" or column_name == "country" or column_name == "cast":
            items = [c.strip() for c in str(item).split(',')]
            for c in items:
                if c in count_dict:
                    count_dict[c] += 1
                else:
                    count_dict[c] = 1
        else:
            if item in count_dict:
                count_dict[item] += 1
            else:
                count_dict[item] = 1
    return count_dict

#[PY2] FUNCTION RETURNING MULTIPLE VALUES
def genre_summary(df=net_df, top_n = 5):
    genre_counts = count("listed_in",df)
    sorted_genres = sorted(genre_counts.items(),key=lambda  x: x[1],reverse=True)
    summary_df = pd.DataFrame(sorted_genres,columns =["Genre","Count"])
    return sorted_genres[:top_n],summary_df

# WEB SCRAPING -- CREATES DATAFRAME WITH REVENUE INFO
pd.set_option("display.max_columns", None,)

url = "https://www.the-numbers.com/movies/country-breakdown/2025"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.content, "html.parser")
main_block = soup.find("table")

if main_block:
    headers_list = []
    for th in main_block.find_all("th"):
        headers_list.append(th.text.strip())
    revenue_df = pd.DataFrame(columns=headers_list)
    for tr in main_block.find_all('tr')[1:]:
        row_data = []
        for td in tr.find_all("td"):
            row_data.append(td.text.strip())
        if row_data:
            revenue_df.loc[len(revenue_df)] = row_data
    #print(revenue_df)

revenue_df.drop('NumberofMovies', axis=1, inplace=True)
#print(revenue_df)


#BUILDING STREAMLIT
tab1, tab2, tab3, tab4 = st.tabs(['Home','Get Recommendations','World View','Learn More'])

with st.sidebar: #[ST4] CUSTOMIZED SIDEBAR
    st.title(":red[Netflix] Explorer")
    st.markdown(
        "Use the tabs above to:\n"
        "- Get custom :red[Netflix] recommendations\n"
        "- Explore :red[Netflix] by country and revenue insights\n"
        "- Learn about release years, genres, and actors")

# WELCOME PAGE
with tab1:
    st.title("Welcome!", "center")
    st.header("Click around to learn more about the thousands of titles featured on :red[Netflix]!", "center")
    st.markdown("Here on the welcome page, you can learn about some of our features \n\n"
                "Click on the get recommendations tab to custom generate :red[Netflix] recommendations based on your preferences!\n\n"
                "Use the World View tab to see where the thousands of :red[Netflix] titles come from\n\n"
                "Finally, check out the Learn More tab to find out more about the kinds of Movies and shows :red[Netflix] has to offer!")
    # shows netflix logo
    image = Image.open('netflix_logo.jpg')
    st.image(image, width=400)

    # citation: https://docs.streamlit.io/develop/api-reference/media/st.image

# RECOMMENDATION PAGE
with tab2:
    st.header("Custom Recommendations!")
    user_type = st.selectbox("Select a title type:", ['TV Show', "Movie"]) #[ST1] FIRST WIDGET - SELECTBOX
    user_genre = st.text_input("Enter a genre:", value = '') #[ST2] SECOND WIDGET - TEXT
    user_num = st.slider('How many recommendations would you like', min_value=1, max_value=20, step = 1) #[ST3] THIRD WIDGET - SLIDER

    if st.button("Get Recommendations"):
        results = recommend(user_type, user_genre, user_num)

        if "Warning" in results.columns:
            pass
        else:
            st.success(f"Found {len(results)} recommendations!")
            st.dataframe(results)

# WORLD VIEW PAGE
with tab3:
    #https://www.mapsofworld.com/lat_long/usa-lat-long.html#google_vignette
    #[VIZ4] MAP
    map_df = pd.DataFrame([
        {"country": "United States", "lat": 38.00, "lon": -97.00},
        {"country": "India", "lat": 22.00, "lon": 77.00},
        {"country": "United Kingdom", "lat": 54.00, "lon": -2.00}
    ])
    st.subheader("Map of Top :red[Netflix]-Producing Countries")
    st.map(map_df)

    # HOW MANY MOVIES EACH COUNTRY PRODUCES (SORTED)
    st.header("World View")
    movies_produced = count("country")
    sorted_movies_produced = dict(sorted(movies_produced.items(), key=lambda item: item[1], reverse=True)) #[DA2] SORT DATA

    top_ten = dict(list(sorted_movies_produced.items())[0:10])
    netflix_series = pd.Series(top_ten)

    #[VIZ1] BAR CHART
    fig, ax = plt.subplots(figsize=(10,5))
    ax.bar(netflix_series.index, netflix_series.values, color = "pink")
    ax.set_title("Countries Producing the Most Movies")
    ax.set_ylabel("Count",fontsize = 12)
    ax.set_xticklabels(netflix_series.index, rotation=45, ha="right")
    st.pyplot(fig)

    data_with_revenue = {} #[PY5] DICTIONARY
    for key, value in top_ten.items():
        if key == "United States" or key == "India" or key == "United Kingdom":
            data_with_revenue[key] = {'Number Movies': value}

    for i in range(len(revenue_df)):
        if revenue_df["Country"][i] == "United States":
            data_with_revenue['United States']['Average Production Budget'] = revenue_df["AverageProductionBudget"][i]
            data_with_revenue['United States']['Total Worldwide Box Office'] = revenue_df["TotalWorldwideBox Office"][i]
        elif revenue_df["Country"][i] == "India":
            data_with_revenue['India']['Average Production Budget'] = revenue_df["AverageProductionBudget"][i]
            data_with_revenue['India']['Total Worldwide Box Office'] = revenue_df["TotalWorldwideBox Office"][i]
        elif revenue_df["Country"][i] == "United Kingdom":
            data_with_revenue['United Kingdom']['Average Production Budget'] = revenue_df["AverageProductionBudget"][i]
            data_with_revenue['United Kingdom']['Total Worldwide Box Office'] = revenue_df["TotalWorldwideBox Office"][
                i]

    data_with_revenue_df = pd.DataFrame(data_with_revenue)
    st.subheader("Revenue Insights")
    st.write(data_with_revenue_df)

#LEARN MORE TAB
with tab4:
    info_type = st.selectbox("Select a topic to learn about", ['Release Year','Genre','Featured Actors'])
    if info_type == "Release Year":
        sorted_years = sorted(count('release_year').items()) #[DA2] SORT DATA
        xval = [year[0] for year in sorted_years] #[PY4] LIST COMPREHENSION
        yval = [year[1] for year in sorted_years] #[PY4] LIST COMPREHENSION
        ticks = range(min(xval),max(xval)+1,15)

        # [VIZ2] LINE CHART
        # create axis
        fig, ax = plt.subplots()
        ax.plot(xval, yval, marker='o',color = 'red')

        #plot design:
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.tick_params(colors = 'white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')

        # plot labels
        ax.set_xticks(ticks)
        ax.set_xlabel('Year')
        ax.set_ylabel('Number of Movies')
        ax.set_title('Movies Released per Year')

        # call plot to streamlit
        st.pyplot(fig)
    elif info_type == "Genre":
        st.subheader("Most Featured Genres on :red[Netflix]")
        top_list, genre_df = genre_summary(net_df,top_n = 10)
        top_genres = genre_df.head(10) #[DA3] TOP GENRES
        st.subheader("Top 10 Genres on :red[Netflix]")
        st.dataframe(top_genres)

        # [VIZ3] BAR CHART
        top5_genres = top_genres[:5] #[DA3] TOP 5 GENRES
        fig, ax = plt.subplots()
        ax.bar(top5_genres["Genre"],top5_genres["Count"],color="pink")
        ax.set_title("Top 5 Netflix Genres")
        ax.set_ylabel("Number of Titles")
        plt.xticks(rotation=45, ha='right') # rotate labels
        plt.tight_layout() # better spacing
        st.pyplot(fig)

        top_genre_name, top_genre_count = top_list[0]
        #st.text(f"The most popular genre is: {top_genre_name} ({top_genre_count} titles)")

        count_genre = count("listed_in")

        def plot_wordcloud(freq):
            top_50 = dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[
                              :50])  # turns into tuple and sorts by value, not key- descending. turns back to dict at end

            # creates just the wordcloud object, not the actual plot:
            wc = WordCloud(width=1000,
                           height=1000,
                           background_color='black',
                           colormap='Reds').generate_from_frequencies(top_50)

            # creates the axis:
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.patch.set_facecolor('black')

            # places wc inside of creates axis:
            ax.imshow(wc, interpolation='bilinear')

            # neatens by removing tickmarks etc
            ax.axis('off')
            return fig


        # creates genre wc
        fig = plot_wordcloud(count_genre)
        # places in streamlit
        st.pyplot(fig)

    elif info_type == "Featured Actors":
        st.subheader("Most Featured Actors on :red[Netflix]")
        actors_count = count("cast",net_df)
        if "Unknown" in actors_count:
            del actors_count["Unknown"]
        sorted_actors = sorted(actors_count.items(),key=lambda x: x[1],reverse= True) #[DA2] SORTING ACTORS

        top10_actors = sorted_actors[:10] #[DA3] TOP ACTORS
        actor_df = pd.DataFrame(top10_actors, columns=["Actor","Appearances"])
        st.subheader("Top 10 Most Featured Actors on :red[Netflix]")
        st.dataframe(actor_df)

        #[VIZ EXTRA] PIE CHART
        top5_actors = sorted_actors[:5] #[DA3] TOP ACTORS
        pie_df = pd.DataFrame(top5_actors, columns = ["Actor","Appearances"])
        fig, ax = plt.subplots()
        ax.pie(pie_df["Appearances"], labels=pie_df["Actor"], autopct="%1.1f%%", startangle=90)
        ax.set_title("Top 5 Featured Actors on Netflix")
        st.pyplot(fig)
