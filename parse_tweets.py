import csv
import json
from itertools import chain
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer


def parse_tweets(infiles, tweetfile, tagfile, userfile, edgefile):
    tweetfile = open(tweetfile, "w")
    tweet_writer = csv.writer(tweetfile)
    edgefile = open(edgefile, "w")
    edge_writer = csv.writer(edgefile)
    tagfile = open(tagfile, "w")
    tag_writer = csv.writer(tagfile)
    userfile = open(userfile, "w")
    user_writer = csv.writer(userfile)
    ht_dict = {}
    ht_id_counter = 1
    user_dict = {}
    rt_ids = set()
    tweet_header = ["tid:ID", "lang", "name", "text", "clean_text", "polarity:float",
                    "subjectivity:float", "created_at", "full_name",
                    "country", "country_code", "coordinates", ":LABEL"]
    tweet_writer.writerow(tweet_header)
    edge_header = [":START_ID", ":END_ID", ":TYPE"]
    edge_writer.writerow(edge_header)
    tag_header = ["tagid:ID", "hashtag", ":LABEL"]
    tag_writer.writerow(tag_header)
    user_header = ["uid:ID", "screen_name", ":LABEL"]
    user_writer.writerow(user_header)
    for infile in infiles:
        with open(infile, "r") as f:
            # parse the tweet
            for line in f:
                tweet = json.loads(line)
                try:
                    text = tweet["text"].replace('"', "")
                except KeyError:
                    continue
                if "paris" not in text.lower():
                    continue
                user_id = str(tweet["user"]["id"])
                screen_name = tweet["user"]["screen_name"]
                user_dict[screen_name] = user_id
                rt_id = ""
                country_code = ""
                country = ""
                full_name = ""
                name = ""
                coordinates = ""
                tid = str(tweet["id"])
                replies_to = tweet["in_reply_to_status_id"]
                created_at = tweet["created_at"]
                hashtags = tweet["entities"]["hashtags"]
                user_mentions = tweet["entities"]["user_mentions"]
                lang = tweet["lang"]
                rt_status = tweet.get("retweeted_status", "")
                if rt_status:
                    rt_id = str(rt_status["id"])
                    if rt_id not in rt_ids:
                        rt_ids.add(rt_id)
                        rt_user_id = rt_status["user"]["id"]
                        rt_user_screen_name = rt_status["user"]["screen_name"]
                        rt_text = rt_status["text"].replace('"', "")
                        rt_created_at = rt_status["created_at"]
                        rt_place = rt_status["place"]
                        rt_lang = rt_status["lang"]
                        rt_clean_text, rt_polarity, rt_subjectivity = get_sent(
                            rt_text, rt_lang)
                        rt_country_code = ""
                        rt_country = ""
                        rt_full_name = ""
                        rt_name = ""
                        rt_coordinates = ""
                        if rt_place:
                            rt_country_code = rt_place["country_code"]
                            rt_country = rt_place["country"]
                            rt_full_name = rt_place["full_name"]
                            rt_name = rt_place["name"]
                            rt_coordinates = rt_place["bounding_box"]["coordinates"]
                            rt_coordinates = ",".join(
                                str(x) for x in chain.from_iterable(coordinates))
                        rt_row = [
                            rt_id,
                            rt_lang,
                            rt_name,
                            rt_text,
                            rt_clean_text,
                            rt_polarity,
                            rt_subjectivity,
                            rt_created_at,
                            rt_full_name,
                            rt_country,
                            rt_country_code,
                            rt_coordinates,
                            "tweet"]
                        tweet_writer.writerow(rt_row)
                    edge_writer.writerow([rt_user_id, rt_id, "tweets"])
                    user_dict[rt_user_screen_name] = rt_user_id
                place = tweet["place"]
                if place:
                    country_code = place["country_code"]
                    country = place["country"]
                    full_name = place["full_name"]
                    name = place["name"]
                    coordinates = place["bounding_box"]["coordinates"]
                    coordinates = ",".join(
                        str(x) for x in chain.from_iterable(coordinates))
                clean_text, polarity, subjectivity = get_sent(text, lang)

                # write out the nodes
                row = [
                    tid,
                    lang,
                    name,
                    text,
                    clean_text,
                    polarity,
                    subjectivity,
                    created_at,
                    full_name,
                    country,
                    country_code,
                    coordinates,
                    "tweet"]
                tweet_writer.writerow(row)

                # write out edges
                edge_writer.writerow([user_id, tid, "tweets"])
                if rt_id:
                    edge_writer.writerow([rt_id, tid, "retweets"])
                if replies_to:
                    edge_writer.writerow([tid, replies_to, "replies_to"])
                for hashtag in hashtags:
                    hashtag = hashtag["text"]
                    if hashtag not in ht_dict:
                        ht_id = "h{}".format(ht_id_counter)
                        ht_dict[hashtag] = ht_id
                        ht_id_counter += 1
                    else:
                        ht_id = ht_dict[hashtag]
                    edge_writer.writerow([tid, ht_id, "uses"])
                for user_mention in user_mentions:
                    uid = user_mention["id"]
                    mention_screen_name = user_mention["screen_name"]
                    user_dict[mention_screen_name] = uid
                    edge_writer.writerow([tid, uid, "mentions"])

    for k, v in ht_dict.items():
        tag_writer.writerow([v, k, "hashtag"])
    for k, v in user_dict.items():
        user_writer.writerow([v, k, "user"])
    tweetfile.close()
    edgefile.close()
    tagfile.close()
    userfile.close()


def get_sent(text, lang):
    clean_text = ' '.join(filter(
        lambda x: (x[0] != "@" and x[0] != "#" and x != "RT"
                   and not x.startswith("http")), text.split()))
    if lang == "en":
        blob = TextBlob(clean_text)
        sent = blob.sentiment
    elif lang == "fr":
        blob = TextBlob(
            clean_text, pos_tagger=PatternTagger(),
            analyzer=PatternAnalyzer())
        sent = blob.sentiment
    else:
        sent = ("", "")
    return clean_text, sent[0], sent[1]
