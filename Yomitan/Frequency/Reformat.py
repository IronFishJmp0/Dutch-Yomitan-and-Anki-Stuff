
import json
import argparse
import zipfile
import os
import sys

class FrequencyDict:

    class Word:
        def __init__(self, Term: str, Rank=-1, Occurrence=-1):
            self.Term = Term
            self.Rank = Rank
            self.Occurrence = Occurrence

    def __init__(self, isRank: bool, Title: str, Revision="1", Author="", Description=""):
        self.isRank = isRank
        self.Author = Author
        self.Description = Description
        self.Title = Title
        self.Revision = Revision
        self.Terms = []

    def Add(self, Term: str, Val: int):
        if self.isRank:
            self.Terms.append(self.Word(Term, Rank=Val))
        else:
            self.Terms.append(self.Word(Term, Occurrence=Val))

    def GetOccurance(self):
        if self.isRank:
            print("Error: Unable to export occurance based dictionary. Source is ranked based, so occurance values do not exist.")
            return

        Terms = sorted(self.Terms, key=lambda Term: Term.Occurrence)
        print(f"GetRank:: Terms contains {len(Terms)} elements.")

        TermBank = []
        for i in range(len(Terms) - 1, -1, -1):
            freq = {}
            freq["reading"] = Terms[i].Term
            freq["frequency"] = Terms[i].Occurrence
            TermBank.append([Terms[i].Term, "freq", freq])

        return TermBank

    def GetRank(self):
        Terms = []
        if not self.isRank:
            Terms = sorted(self.Terms, key=lambda Term: Term.Occurrence)
        else:
            Terms = sorted(self.Terms, key=lambda Term: Term.Rank)
        print(f"GetRank:: Terms contains {len(Terms)} elements.")

        TermBank = []
        rank = 0
        lastOcc = 0
        sameCount = 1
        for i in range(len(Terms) - 1, -1, -1):
            freq = {}
            freq["reading"] = Terms[i].Term
            if Terms[i].Rank == lastOcc:
                freq["frequency"] = rank
                sameCount += 1
            else:
                rank += sameCount
                sameCount = 1
                lastOcc = Terms[i].Occurrence
                freq["frequency"] = rank

            TermBank.append([Terms[i].Term, "freq", freq])

        return TermBank

    def Export(self, ExportRank=True):
        print(f"Exporting dictionaray with {len(self.Terms)} terms.")

        print("Compiling info.json")
        info = {
            "title": self.Title,
            "format": 3,
            "revision": self.Revision,
            "description": self.Description,
            "author": self.Author
        }

        print("Sorting terms")
        bank = []
        if ExportRank:
            bank = self.GetRank()
            info["frequencyMode"] = "rank-based"
        else:
            bank = self.GetOccurance()
            info["frequencyMode"] = "occurrence-based"
        print(f"Recieved a term bank with {len(bank)} terms.")

        print("Writing index and term bank json files.")
        with open("index.json", "w") as f:
            json.dump(info, f, indent=4)

        with open("term_meta_bank_1.json", "w") as f:
            json.dump(bank, f, check_circular=False)

        zipName = self.Title + "_" + ("rank" if ExportRank else "occurance") + ".zip"
        print("Zipping index.json and term_meta_bank_1.json into " + zipName + ".")
        with zipfile.ZipFile(zipName, "w") as zf:
            zf.write("index.json")
            zf.write("term_meta_bank_1.json")

        print("Cleaning up .json files.")
        os.remove("index.json")
        os.remove("term_meta_bank_1.json")




argParser = argparse.ArgumentParser(prog="FrequencyListReformatter", description="Reformats a csv or tsv frequency list into a yomitan frequency dictionary.")

argParser.add_argument("-t", "--title", nargs=1, type=str, required=True, help="The title of the dictionary. This is what shows up in the Yomitan window when you look up a word.")
argParser.add_argument("-r", "--revision", nargs=1, default="1", required=False, help="The revision of this dictionary. When updating a dictionary, increase this parameter.")
argParser.add_argument("-d", "--description", nargs=1, required=False, help="The description for this dictionary. Appears only in the settings page under the 'configure dictionaries' dialog.")
argParser.add_argument("-a", "--author", nargs=1, required=False, help="The Author of the dictionary, in otherwords who created it.")
argParser.add_argument("-R", "--rank", action="store_true", help="Tells the program that the supplied frequency dictionary is rank based. Either --rank or --occurance must be supplied.")
argParser.add_argument("-O", "--occurance", action="store_true", help="Tells the program that the supplied frequency dictionary is occurance based. Either --rank or --occurance must be supplied.")
argParser.add_argument("-e", "--export_type", choices=["rank", "occurance", "both"], default="rank", help="Sets the type of dictionary that will be exported. Default is rank.")
#argParser.add_argument("-i", "--index", nargs=1, help="Specifies a info.json file from which to pull information from. Revision field will be increased by one if it contains an integer.")
argParser.add_argument("-s", "--separator", nargs=1, default="\t", help="Sets the seperator for the provided frequency dictionary. Set to \",\" if using a csv. Default is a single tab.")
argParser.add_argument("--term_col", nargs=1, type=int, default=0, help="The zero indexed column in the provided file(s) that contains the term or word. Default is 0 (the first column).")
argParser.add_argument("--val_col", nargs=1, type=int, default=1, help="The zero indexed column in the provided file(s) that contains the rank or occurance of the term. Default is 1 (the second column).")
argParser.add_argument("-m", "--minimum_occurance", nargs=1, default=5, help="Specifies the minimum number of occurances a term must have in order to be added to the final dictionary. Used as a cleaning measure. Default of 5.")
#argParser.add_argument("--charset", nargs=1, help="A whitelist of characters. If the word contains any characters outside of those provided, the word will be discarded.")
#argParser.add_argument("--regex", nargs=1, help="A regular expression that acts as a whitelist for terms in the dictionary. If a term does not match the regular expression, it is excluded from the final dictionary. You can find more info on how to create a regular expression here: https://docs.python.org/3/howto/regex.html")

argParser.add_argument("files", nargs='+', help="The file(s) to be included in the dictionary. Caution: Like terms will not be combined. This means that if a word appears in multiple files, it will have multiple entries in the final dictionary which may cause issues in Yomitan.")


args = argParser.parse_args()

if not args.rank and not args.occurance:
    print("Error: either --rank or --occurance must be supplied.")
    sys.exit(1)
if args.rank and args.occurance:
    print("Error: --rank and --occurance cannot both be supplied.")
    sys.exit(1)




freqDict = FrequencyDict(isRank=args.rank, Title=args.title[0])
if args.revision:
    if type(args.revision) == str:
        freqDict.Revision = args.revision
    else:
        freqDict.Revision = args.revision[0]
if args.description:
    if type(args.description) == str:
        freqDict.Description = args.description
    else:
        freqDict.Description = args.description[0]
if args.author:
    if type(args.description) == str:
        freqDict.Author = args.author
    else:
        freqDict.Author = args.author[0]

termCol = args.term_col[0]
valCol = args.val_col[0]
minOcc = args.minimum_occurance
sep = args.separator[0]


for fileName in args.files:
    print(f"Importing {fileName}.")
    try:
        with open(fileName, "r", encoding="utf-8") as f:
            for line in f:
                l = line.split(sep)
                val = int(l[valCol])
                if val >= minOcc:
                    freqDict.Add(l[termCol], val)
    except OSError as e:
        print(e)
        sys.exit(2)

if args.export_type == "both" or args.export_type == "rank":
    freqDict.Export()
if args.export_type == "both" or args.export_type == "occurance":
    freqDict.Export(ExportRank=False)







