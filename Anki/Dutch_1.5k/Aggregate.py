
import sys, os
import argparse
import re

#import file, need to know which column is term and which is value
#words are sent to lower case and words with occurance less than TBD number area discarded, then added to list as [word, occ]. Afterwards, list is sorted by term, then like terms are combined and finally freq is replaced by rank
#do this for every file
#combine lists by multiplying rank by weight, then adding like terms from every list together.
#sort by freq, then take top 1.5k


#argParser = argparse.ArgumentParser(prog="ListAggregator", description="Aggregates occurance lists, then outputs the top 1.5k words.")

#argParser.add_argument("-f", "--file", nargs=5, action='append', help="Adds a file to the list. Takes 5 arguments: <separator>, <zero indexed term column> <zero indexed occurance column> <integer weight> <path to file>")

#args = argParser.parse_args()

minOcc = 5

files = [
        {
            "path":"./FrequencyDicts/hermitdave_nl_full.txt",
            "name":"hermitdave_OpenSubs",
            "term":0,
            "val":1,
            "weight":10,
            "separator":" "
        }, {
            "path":"./FrequencyDicts/nld_news_2024_1M/nld_news_2024_1M-words.txt",
            "name":"wortschatz_news",
            "term":1,
            "val":2,
            "weight":5,
            "separator":"\t"
        }, {
            "path":"./FrequencyDicts/nld_wikipedia_2021_1M/nld_wikipedia_2021_1M-words.txt",
            "name":"wortschatz_wikipedia",
            "term":1,
            "val":2,
            "weight":3,
            "separator":"\t"
        }, {
            "path":"./FrequencyDicts/nld-nl_web-public_2019_1M/nld-nl_web-public_2019_1M-words.txt",
            "name":"wortschatz_web-public",
            "term":1,
            "val":2,
            "weight":1,
            "separator":"\t"
        }
]

fileTest = [{
        "path":"nld_news_2024_10K-words.txt",
        "name":"wortschatz_news",
        "term":1,
        "val":2,
        "weight":5,
        "separator":"\t"
    }]

def getIndex(List, word):
    #returns a boolean that is true if an exact match is found, and the index of the match
    def greater(a: str, b: str):
        short = len(a) if len(a) < len(b) else len(b)
        i = 0
        while i < short:
            if a[i] != b[i]:
                return ord(a[i]) - ord(b[i])
            i += 1

        if len(a) == len(b):
            return 0
        return len(a) - len(b)

    h = len(List)
    l = 0
    center = int(((h - l) / 2) + l)
    while l < h and List[center][0] != word:
        diff = greater(List[center][0], word)
        #print(f"diff: {diff}, low: {l}, center: {center}, High: {h}, CenterWord: {List[center][0]}, Word: {word}")
        if diff > 0:
            h = center
            center = int(((h - l) / 2) + l)
            continue
        #diff < 0, diff cannot be 0 here because the condition for the while loop precludes it.
        l = center + 1
        center = int(((h - l) / 2) + l)
    #print(f"low: {l}, center: {center}, High: {h}, CenterWord: {List[center][0] if center < len(List) else "NaN"}, Word: {word}, Len: {len(List)}")
    if center < len(List) and List[center][0] == word:
        return True, center
    return False, center

class FreqList:

    def __init__(self, path, name, weight):
        self.Path = path
        self.Name = name
        self.Weight = weight
        self.List = []
        self.Pattern = re.compile(r"^[a-zëéèêïöóüçáàäûîíôúñâÅ'\ \-]+$", re.IGNORECASE)

    def Add(self, word, occurrence):
        word = word.lower()
        if not self.Pattern.match(word):
            with open("non-matching-words.txt", "a") as f:
                f.write(word)
                f.write("\n")
            return

        match, index = getIndex(self.List, word)
        if match:
            #print(f"Adding {word} and {self.List[index][0]}")
            self.List[index][1] += occurrence
        else:
            self.List.insert(index, [word, occurrence])

    def GenerateSorted(self):
        self.SortedList = sorted(self.List, key=lambda Term: Term[1], reverse=True)

os.remove("non-matching-words.txt")

lists = []
#for lstMeta in fileTest:#Used for testing
for lstMeta in files:
    print(f"Loading {lstMeta["path"]}")
    lst = FreqList(lstMeta["path"], lstMeta["name"], lstMeta["weight"])
    with open(lstMeta["path"], "r") as f:
        sep = lstMeta["separator"]
        valK = lstMeta["val"]
        termK = lstMeta["term"]
        for line in f:
            dat = line.split(sep)
            val = int(dat[valK])
            if val < minOcc:
                continue
            lst.Add(dat[termK], val)
    print(f"\tCreating sorted list")
    lst.GenerateSorted()
    lists.append(lst)


"""
for lst in lists:
    for i in range(0, len(lst.List)):
        if i > 50:
            break
        print(f"{lst.List[i]}")



"""


#write out the top 1.5k words from each list.
for lst in lists:
    fname = lst.Name + "_1.5k.tsv"
    print(f"Writing {fname}")
    with open(fname, "w") as f:
        for i in range(0, len(lst.SortedList)):
            if i < 1500:
                f.write(f"{lst.SortedList[i][0]}\t{lst.SortedList[i][1]}\n")

print(f"Creating combined weighted list")
comb = []
combName = ""
for lst in lists:
    print(f"\tAdding {lst.Name} with weight {lst.Weight}")
    combName += f"{lst.Name}_weighted-{lst.Weight}_"
    if len(comb) == 0:
        for item in lst.List:
            comb.append([item[0], item[1] * lst.Weight])
        continue

    for item in lst.List:
        match, index = getIndex(comb, item[0])
        if match:
            comb[index][1] += item[1] * lst.Weight
            continue
        comb.insert(index, [item[0], item[1] * lst.Weight])


print(f"Writing combined list (full): {combName + "combined_alphabetical.tsv"}")
with open(combName + "combined_alphabetical.tsv", "w") as f:
    for item in comb:
        f.write(f"{item[0]}\t{item[1]}\n")

combOcc = sorted(comb, key=lambda Term: Term[1], reverse=True)

combName += "combined_occurance.tsv"
print(f"Writing combined list (full): {combName}")
with open(combName, "w") as f:
    for item in combOcc:
        f.write(f"{item[0]}\t{item[1]}\n")

combName = "1.5k_" + combName
print(f"Writing combined list (1.5k): {combName}")
with open(combName, "w") as f:
    for i in range(0, len(combOcc)):
        if i < 1500:
            f.write(f"{combOcc[i][0]}\t{combOcc[i][1]}\n")
