import json
import os
import subprocess
import random

def parseJson(filename_json) -> list:
    """ Given json file, returns list containing card names """
    with open(filename_json) as json_file:
        cards = json.load(json_file)
        card_list = []
        for _set in cards.values():
            card_list.extend(_set['cards'])
    cards = set()
    for card in card_list:
        cards.add(card["name"])
    return cards

def countCards():
    """Count number of cards automated"""
    with open("totalcards.txt", "r") as file:
        i = 0
        for card in file:
            card = card.rstrip()
            if not card:
                continue
            if card[0] in {'#','\t', ' '}:
                continue
            i += 1
    return i

def addCardsToFile(file_to_write, card) -> None: 
    """given a filename, adds card to that file"""
    file_to_write.write("#"*30 + "\n")
    for info in card:
        file_to_write.write(info)
        file_to_write.write("\n")
    file_to_write.write("\n\n" + "#"*30)

def runMTGTests(command) -> bool: # returns true if all tests passed
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = p.stdout.readlines()[-1].strip()
    return 'OK' in res

def runFileAddition() -> None:
    m15 = open("../../data/m15_cards.txt", "a")
    cc = open("../../data/cube_cards.txt", "a")
    
    M15_SET = parseJson("../../parser/data/M15.json")
    appended_cards = []
    with open("totalcards.txt", "r") as automation_file:
        lines = []  # buffer

        for line in automation_file:
            line = line.rstrip()
            if not line:
                continue

            if line[:3] == '###':  # end of a card
                if not lines: 
                    continue
                if lines[0] in M15_SET: 
                    addCardsToFile(m15, lines)
                else:
                    addCardsToFile(cc, lines)
                appended_cards.append(lines[0])
                lines = []
            else:  # wait to parse cards until we've read in all information about a card
                lines.append(line)
    m15.close()
    cc.close()
    return appended_cards

''' 
#WIP
def createDecks(deck_quantity, cards, size): 
    decks = []
    for i in range(deck_quantity): # create decks
        decks.append(open(f"/mtg-python-engine-effects/data/decks/deck{i + 1}.txt", 'w'))
    
    # add random number, add random card from cards
    for i in range(size):
        pass

    for file in decks: # close files
        file.close()
''' 

def createDecks(deck_num, size, cards) -> set:
    files = [open(f'../../data/decks/deck{i + 1}.txt', 'w') for i in range(deck_num)]
    cards_in_decks = set()
    for file in files:
        for i in range(size):
            card = random.choice(cards)
            file.write(f'{random.randint(1,10)} {card}')
            if i + 1 == size: continue
            file.write("\n")
            cards_in_decks.add(card)
        file.close()
    return cards_in_decks

if __name__ == "__main__":
    # print(countCards())
    
    cards = runFileAddition()
    createDecks(4, 10, cards)
    # res_runTest = runMTGTests("cd ~/Development/mtg-python-engine-effects/; ./test.sh") # call ./test.sh for the game to parse it

    # if res_runTest:
    # createDecks(2, cards)
    