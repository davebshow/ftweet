import csv
import json
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer


def parse_tweets(infiles, tweetfile, tagfile, userfile, edgefile, kwrd_set):
    tweetfile = open(tweetfile, "w")
    tweet_writer = csv.writer(tweetfile, delimiter='\t')
    edgefile = open(edgefile, "w")
    edge_writer = csv.writer(edgefile, delimiter='\t')
    tagfile = open(tagfile, "w")
    tag_writer = csv.writer(tagfile, delimiter='\t')
    userfile = open(userfile, "w")
    user_writer = csv.writer(userfile, delimiter='\t')
    ht_dict = {}
    ht_id_counter = 1
    user_dict = {}
    tweet_dict = {}
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
                    text = tweet["text"].replace('"', "'").replace("\\", "")
                except KeyError:
                    continue
                # Hmmm this is a hack for the art tweets...
                text_tokens = set(w.lstrip("#") for w in text.lower().split(' '))
                if not kwrd_set & text_tokens:
                    continue
                tid = str(tweet["id"])
                user_id = str(tweet["user"]["id"])
                screen_name = tweet["user"]["screen_name"]
                user_dict[user_id] = screen_name
                rt_id = ""
                country_code = ""
                country = ""
                full_name = ""
                name = ""
                coordinates = ""
                replies_to = tweet["in_reply_to_status_id"]
                created_at = tweet["created_at"]
                hashtags = tweet["entities"]["hashtags"]
                user_mentions = tweet["entities"]["user_mentions"]
                lang = tweet["lang"]
                place = tweet["place"]
                rt_status = tweet.get("retweeted_status", "")
                if rt_status:
                    rt_id = str(rt_status["id"])

                    rt_user_id = str(rt_status["user"]["id"])
                    rt_user_screen_name = rt_status["user"]["screen_name"]
                    rt_text = rt_status["text"].replace('"', "'").replace("\\", "")
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
                        if place:
                            print(place["full_name"], rt_place["full_name"])
                        rt_country_code = rt_place["country_code"]
                        rt_country = rt_place["country"]
                        rt_full_name = rt_place["full_name"]
                        rt_name = rt_place["name"]
                        rt_coordinates = rt_place["bounding_box"]["coordinates"]
                        rt_coordinates = json.dumps(rt_coordinates)
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
                    if rt_id not in tweet_dict:
                        tweet_dict[rt_id] = rt_row
                        edge_writer.writerow([rt_user_id, rt_id, "TWEETS"])
                    elif tweet_dict[rt_id][11] == "":
                        tweet_dict[rt_id] = rt_row
                    user_dict[rt_user_id] = rt_user_screen_name
                if place:
                    country_code = place["country_code"]
                    country = place["country"]
                    full_name = place["full_name"]
                    name = place["name"]
                    coordinates = place["bounding_box"]["coordinates"]
                    coordinates = json.dumps(coordinates)
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
                if tid not in tweet_dict:
                    tweet_dict[tid] = row
                    edge_writer.writerow([user_id, tid, "TWEETS"])
                elif tweet_dict[tid][11] == "":
                    tweet_dict[tid] = row

                # write out edges
                if rt_id:
                    edge_writer.writerow([rt_id, tid, "RETWEETS"])
                if replies_to:
                    replies_to = str(replies_to)
                    edge_writer.writerow([tid, replies_to, "REPLIES_TO"])
                    if replies_to not in tweet_dict:
                        tweet_dict[replies_to] = [replies_to, "", "", "", "", "",
                                                  "", "", "", "", "", "", "tweet"]
                for hashtag in hashtags:
                    hashtag = hashtag["text"].lower()
                    if hashtag not in ht_dict:
                        ht_id = "h{}".format(ht_id_counter)
                        ht_dict[hashtag] = ht_id
                        ht_id_counter += 1
                    else:
                        ht_id = ht_dict[hashtag]
                    edge_writer.writerow([tid, ht_id, "USES"])
                for user_mention in user_mentions:
                    uid = str(user_mention["id"])
                    mention_screen_name = user_mention["screen_name"]
                    user_dict[uid] = mention_screen_name
                    edge_writer.writerow([tid, uid, "MENTIONS"])

    for k, v in ht_dict.items():
        tag_writer.writerow([v, k, "hashtag"])

    for k, v in user_dict.items():
        user_writer.writerow([k, v, "user"])

    for v in tweet_dict.values():
        tweet_writer.writerow(v)

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
