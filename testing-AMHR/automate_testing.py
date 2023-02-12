import json
import os

def parseJson(filename_json) -> list:
    with open(filename_json) as json_file:
        cards = json.load(json_file)
        card_list = []
        for _set in cards.values():
            card_list.extend(_set['cards'])
    cards = set()
    for card in card_list:
        cards.add(card["name"])
    return cards

def addCardsToFile(file_w, card) -> None: # given a filename, adds card to that file
    file_w.write("#"*30 + "\n")
    for c in card:
        file_w.write(c)
        file_w.write("\n")
    file_w.write("\n\n" + "#"*30)

def runTest() -> bool: # returns true if all tests passed
    # run ./test.sh
    pass

def runFileAddition():
    m15 = open("m15_cards.txt", "a")
    cc = open("cube_cards.txt", "a")

    c = parseJson("/Users/emanuelaseghehey/Development/mtg-python-engine-effects/parser/data/M15.json")
    with open("automation.txt", "r") as automation_file:
        lines = []  # buffer

        for line in automation_file:
            line = line.rstrip()
            if not line:
                continue

            if line[:3] == '###':  # end of a card
                if not lines: 
                    continue

                if lines[0] in c: 
                    addCardsToFile(m15, lines)
                else:
                    # has to be AllSets so goes to cube_cards_automation
                    addCardsToFile(cc, lines)
                lines = []
            else:  # wait to parse cards until we've read in all information about a card
                lines.append(line)
    

if __name__ == "__main__":
    try:
        pass
        # runFileAddition()
        # os.system("bash test.sh")  # running tests
    except Exception as err:
        print(err)
