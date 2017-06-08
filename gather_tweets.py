
import json
import time
from TwitterAPI import TwitterAPI
from TwitterAPI import TwitterConnectionError

# Daves
consumer_key = "S2kVYYW3ihDtPgOZg5Q"
consumer_secret = "ERKZS7zBKQk36GjdNVpe9oMBCpRn0quho5K7tA0"
access_token_key = "120258418-sFgDZ8K0V0hSSLfdRDlINXh2Ix5f7BkWJ3H3aXGU"
access_token_secret = "SBXH3oNOv6J665naQbxQNPOpSDuiPjI9XwzioW3WE7Jb5"


#consumer_key = "JyxWqhkAOrJMcmaYgLQrCl7Nk"
#consumer_secret = "bZW1WDqmZIwNqmlpgbhPV8cGp1D7eK9VngGbFrqJQOKGYErIIr"
#access_token_key = "178393959-CLHT5AEVrG74wDTqQ5NL5syj7yMnuFhWkSaqw4ZO"
#access_token_secret = "Zd7BWn9u1LrbYxORi1sXA3STarcLcYI8cZPmSpl2opqDt"


# This is the object that we will use to send the request to Twitter
# A request is a HTTP request, just like your browser does when it goes to a website!
api = TwitterAPI(consumer_key, consumer_secret, access_token_key,
                 access_token_secret)


# UNTESTED!!!
def get_tweets(base_outfile, kwrd):
    file_num = 1
    num_lines = 0
    num_retries = 0
    # This asks twitter to open up a stream of data
    # The stream sends tweets that come from the specified location.
    while True:
        try:
            outfile = "{0}{1}.json".format(base_outfile, file_num)
            f = open(outfile, "w")
            r = api.request('statuses/filter', {'track': kwrd})
            num_retries = 0
            for tweet in r:
                try:
                    data = json.dumps(tweet)
                    print(tweet["text"])
                    f.write("{0}\n".format(data))
                except:
                    pass
                else:
                    num_lines += 1
                    if not num_lines % 1000000:
                        file_num += 1
                        f.close()
                        outfile = "{0}{1}.json".format(base_outfile, file_num)
                        f = open(outfile, "w")
        except TwitterConnectionError:
            num_retries += 1
            time.sleep(num_retries)
            file_num += 1
