from bs4 import BeautifulSoup
import requests
from datetime import date
import calendar
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.sentiment import SentimentIntensityAnalyzer
import json

nltk.download(
    "names",
    "stopwords",
    "twitter_samples",
    "movie_reviews",
    "averaged_perceptron_tagger",
    "vader_lexicon",
    "punkt"
)

# News sources (URLs for requests)

GUARDIAN_URL = "https://www.theguardian.com/theguardian/mainsection/topstories"
MAIL_URL = "https://www.dailymail.co.uk/home/latest/index.html#news"
METRO_URL = "https://metro.co.uk/news/uk/"

# Setting up some variables we need

datetime = date.today()
month = calendar.month_abbr[datetime.month].lower()
day = str(datetime.day)
if len(day) == 1:
    day = "0" + day
date_string = month + "/" + day
excluded_words = ["guardian", "said"]

# Setting up some data structures
# to store scraped data

guardian_data = []
mail_data = []
metro_data = []

# Stand alone function to write date to a JSON file

def write_data_to_json_file(data):
    with open("scraped_data.json", 'w') as f:
        json.dump(data, f, indent=4)

# Creates a news scraper class to create the soup object
# that can be inherited by the individual objects
# which also provides functionality which is shared
# between the classes

class NewsScraper:
    def __init__(self, url):
        self.url = url

    def get_soup(self):

        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

    def split_title_by_key_words(self, article_title):

        delimiters = [";", ",", ":", "|"]
        for character in article_title:
            if character in delimiters:
                return article_title.split(character)[0]

        return article_title

    def get_summary_of_title(self, article_title):
        summary_title = self.split_title_by_key_words(article_title).strip()
        return summary_title

    def get_sentiment_scores(self, article):

        sia = SentimentIntensityAnalyzer()
        scores = sia.polarity_scores(article)

        return scores

    def get_sentiment(self, scores):

        scores.pop("compound")
        highest_value = max(scores.values())

        transform_results_to_full = {
            "neu": "Neutral",
            "pos": "Positive",
            "neg": "Negative"
        }

        sentiment = [transform_results_to_full[key] for key, value in scores.items() if value == highest_value][0]

        return sentiment

    def tokenize_article_text(self, article):

        tokenized_text = RegexpTokenizer(r'\w+').tokenize(article)
        stopwords = nltk.corpus.stopwords.words("english")
        words = [w for w in tokenized_text if (w.lower() not in stopwords and w.lower() not in excluded_words)]
        return words

    def get_top_nine_most_common_words(self, words):

            distribution = nltk.FreqDist(words)
            most_common_words = distribution.most_common(9)
            return most_common_words

    def get_salient_sentences(self, words, article_text):

        find_four = nltk.collocations.QuadgramCollocationFinder.from_words(words)
        sentences = article_text.split(".")

        most_common_four_words_together = find_four.ngram_fd.most_common(1)[0][0]
        unpack_words = [word for word in most_common_four_words_together]

        salient_sentences = []

        for sentence in sentences:
            if all(x in sentence for x in unpack_words):
                salient_sentences.append(sentence)

        return salient_sentences

# Guardian class to transform and store
# scraped data

class Guardian(NewsScraper):

    def __init__(self, guardian_url):
        self.url = guardian_url
        self.data = []
        self.links_with_todays_date = []

    def get_links_with_todays_date(self, date_string):

        main_link = NewsScraper(GUARDIAN_URL).get_soup().section.a.get("href")
        a_tags = NewsScraper(main_link).get_soup().find_all("a")
        all_links = [link.get("href") for link in a_tags]
        todays_links = (list(set([link for link in all_links if date_string in str(link)][1:])))[:3]

        self.links_with_todays_date = todays_links

    def scrape_and_save_data(self):

        for article_link in self.links_with_todays_date:

            soup = NewsScraper(article_link).get_soup()
            article_data = [data.text for data in (soup.find("div", {"id": "maincontent"}).find_all("p"))]
            article_title = soup.title.text
            article_text = "".join(article_data)

            summary_title = NewsScraper(article_link).get_summary_of_title(article_title)
            scores = NewsScraper(article_link).get_sentiment_scores(article_title)
            sentiment = NewsScraper(article_link).get_sentiment(scores)
            scores = str(scores).replace("{", "").replace("}", "")
            words = NewsScraper(article_link).tokenize_article_text(article_text)
            salient_sentences = NewsScraper(article_link).get_salient_sentences(words, article_text)
            salient_sentences_no_duplicate = []

            for sentence in salient_sentences:
                if sentence not in salient_sentences_no_duplicate:
                    salient_sentences_no_duplicate.append(sentence)

            salient_sentences = ". ".join(salient_sentences_no_duplicate)
            sentiment_analysis_article = NewsScraper(article_link).get_sentiment_scores(article_text)
            article_sentiment_overall = NewsScraper(article_link).get_sentiment(sentiment_analysis_article)
            sentiment_analysis_article = str(sentiment_analysis_article).replace("}", "").replace("{", "")

            article_data = {
                "newspaper": "guardian",
                "article_title": article_title,
                "article_text": article_text,
                "summary_title": summary_title,
                "sentiment_title_scores": scores,
                "sentiment_title": sentiment,
                "salient_sentences": salient_sentences,
                "sentiment_analysis_article": sentiment_analysis_article,
                "article_sentiment_overall": article_sentiment_overall

            }
            self.data.append(article_data)

# Metro class to transform and store
# scraped data

class Metro(NewsScraper):

    def __init__(self, metro_url):

        self.url = metro_url
        self.data = []

    def scrape_and_save_data(self):

        metro_soup = NewsScraper(self.url).get_soup()
        mix_to_search = metro_soup.find_all(attrs={"class": "trending-module-item"})

        titles_and_links = [{elem.h2.text: elem.a["href"]} for elem in mix_to_search][:3]

        for data in titles_and_links:
            for title, link in data.items():
                article_soup = NewsScraper(link).get_soup()

                paras = article_soup.find_all("div", attrs={"class": "article-body"})[0].find_all("p")

                relevant_paras = []

                for para in paras:
                    if "zopo-title" not in str(para):
                        relevant_paras.append(para.text)

                article_text = ". ".join(relevant_paras).split("Get in touch with our news team")[0]

                summary_title = NewsScraper(link).get_summary_of_title(title)
                scores = NewsScraper(link).get_sentiment_scores(title)
                sentiment = NewsScraper(link).get_sentiment(scores)
                scores = str(scores).replace("{", "").replace("}", "")
                words = NewsScraper(link).tokenize_article_text(article_text)
                salient_sentences = NewsScraper(link).get_salient_sentences(words, article_text)

                salient_sentences_no_duplicate = []

                for sentence in salient_sentences:
                    if sentence not in salient_sentences_no_duplicate:
                        salient_sentences_no_duplicate.append(sentence)

                salient_sentences = ". ".join(salient_sentences_no_duplicate)
                sentiment_analysis_article = NewsScraper(link).get_sentiment_scores(article_text)
                article_sentiment_overall = NewsScraper(link).get_sentiment(sentiment_analysis_article)
                sentiment_analysis_article = str(sentiment_analysis_article).replace("}", "").replace("{", "")

                article_data = {
                    "newspaper": "metro",
                    "article_title": title,
                    "article_text": article_text,
                    "summary_title": summary_title,
                    "sentiment_title_scores": scores,
                    "sentiment_title": sentiment,
                    "salient_sentences": salient_sentences,
                    "sentiment_analysis_article": sentiment_analysis_article,
                    "article_sentiment_overall": article_sentiment_overall
                }

                self.data.append(article_data)

# Mail class to transform and store
# scraped data

class Mail(NewsScraper):

    def __init__(self, mail_url):
        self.url = mail_url
        self.data = []

    def get_article_text_from_article(self, article_url):

        soup = NewsScraper(article_url).get_soup()
        article_text = soup.find_all("div", {"itemprop": "articleBody"})[0].text
        return article_text

    def save_mail_data(self):

        soup = NewsScraper(self.url).get_soup()
        mix_to_search = soup.find_all(attrs={"class": "mol-fe-latest-headlines--article"})[:3]

        link_title = [(x.a["href"], x.a.span.text) for x in mix_to_search]

        for data in link_title:

            link, title = data
            full_link_to_article = "https://www.dailymail.co.uk" + link
            article_text = self.get_article_text_from_article(full_link_to_article)

            summary_title = NewsScraper(link).get_summary_of_title(title)
            scores = NewsScraper(link).get_sentiment_scores(title)
            sentiment = NewsScraper(link).get_sentiment(scores)
            scores = str(scores).replace("{", "").replace("}", "")
            words = NewsScraper(link).tokenize_article_text(article_text)
            salient_sentences = NewsScraper(link).get_salient_sentences(words, article_text)
            salient_sentences_no_duplicate = []

            for sentence in salient_sentences:
                if sentence not in salient_sentences_no_duplicate:
                    salient_sentences_no_duplicate.append(sentence)

            salient_sentences = ". ".join(salient_sentences_no_duplicate)
            sentiment_analysis_article = NewsScraper(link).get_sentiment_scores(article_text)
            article_sentiment_overall = NewsScraper(link).get_sentiment(sentiment_analysis_article)
            sentiment_analysis_article = str(sentiment_analysis_article).replace("}", "").replace("{", "")


            article_data = {
                "newspaper": "mail",
                "article_title": title,
                "article_text": article_text,
                "summary_title": summary_title,
                "sentiment_title_scores": scores,
                "sentiment_title": sentiment,
                "salient_sentences": salient_sentences,
                "sentiment_analysis_article": sentiment_analysis_article,
                "article_sentiment_overall": article_sentiment_overall
            }
            self.data.append(article_data)

#GUARDIAN

guardian = Guardian(GUARDIAN_URL)
guardian.get_links_with_todays_date(date_string)

if not guardian.links_with_todays_date:
    guardian.get_links_with_todays_date(month + "/" + str(int(day)-1))

guardian.scrape_and_save_data()

#METRO

metro = Metro(METRO_URL)
metro.scrape_and_save_data()

#MAIL

mail = Mail(MAIL_URL)
mail.save_mail_data()

#WRITE THE DATA TO A JSON FILE

write_data_to_json_file(guardian.data + mail.data + metro.data)

