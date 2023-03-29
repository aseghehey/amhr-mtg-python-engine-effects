import json
import subprocess
import random

def ParseJson(filename_json) -> list:
    """ Given json file, returns list containing card names
        Useful because it will let us know what function a card must go to (cube_cards or m15)    
    """
    with open(filename_json) as json_file:
        cards = json.load(json_file)
        card_list = []
        for _set in cards.values():
            card_list.extend(_set['cards'])
    cards = set()
    for card in card_list:
        cards.add(card["name"])
    return cards

def CountCards():
    """Counts number of cards automated to keep track of progress. All cards must be stored in totalcards.txt"""
    with open("totalcards.txt", "r") as file:
        count = 0
        for card in file:
            card = card.rstrip()
            if not card: # ignore empty lines
                continue
            if card[0] in {'#','\t', ' '}: # ignore hashtags
                continue
            count += 1
    return count

# helper function for CardAddition
def AddCardsToFileWithFormat(file_to_write, card) -> None: 
    """ Given a filename, adds card to that file
        Current files: data/cube_cards.txt and data/m15_cards.txt
    """
    file_to_write.write("#"*30 + "\n")
    for info in card:
        file_to_write.write(info)
        file_to_write.write("\n")
    file_to_write.write("\n\n" + "#"*30)

def CardAddition() -> None:
    """ Goes through cards in totalcards.txt and adds them to the appropriate files (m15_cards.txt or cube_cards.txt))"""

    # opening files that the program writes to
    m15_file = open("../../data/m15_cards.txt", "a")
    cube_cards_file = open("../../data/cube_cards.txt", "a")
    # to group cards. check m15, everything outside m15 is cube_cards
    M15_SET = ParseJson("../../parser/data/M15.json")

    ''' 
    the following arrays are important because the parser reads from a pre-made list and we need to add
    the cards to that list or else they will never get loaded and recognized inside the game
    especially when they do not exist in the list already
    '''
    cube_cards_added = []
    m15_cards_added = [] # stores card names of added cards
    with open("totalcards.txt", "r") as automation_file:
        lines = []  # buffer

        for line in automation_file:
            line = line.rstrip()
            if not line:
                continue

            if line[:3] == '###':  # end of a card
                if not lines: 
                    continue
                if lines[0] in M15_SET: # add to m15
                    AddCardsToFileWithFormat(m15_file, lines)
                    m15_cards_added.append(line[0])
                else: # add to cube_cards
                    AddCardsToFileWithFormat(cube_cards_file, lines)
                    cube_cards_added.append(lines[0])
                lines = []
            else:  # wait to parse cards until we've read in all information about a card
                lines.append(line)
    m15_file.close()
    cube_cards_file.close()
    return cube_cards_added, m15_cards_added

def CreateDecks(deck_num, size, cards) -> set:
    """ Out of all the cards we added, will create decks in data/decks
        deck_num: number of decks to create
        size: how many cards a deck must have
        cards: a list of cards to randomly pick from
    """
    #TODO: Keep track of cards added to decks so we know which ones are being tested. 
    # Maybe also try to make it so a card does not appear in more than 1 deck
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

def RunParser() -> bool:
    """ Run everytime we add cards, so we can actually use them in the game """
    proc = subprocess.Popen("cd ../..; python3 -m parser.parse_mtgjson", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if not proc.stderr: # if nothing goes wrong, return True
        return True
    return False

def RunMTGTests(command='') -> bool:
    """ Runs the game's unit tests - checks for errors as well """
    if not command: command = "cd ../..; ./test.sh" # make sure we're in the actual directory and run the unit tests
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        if "FAILED" in str(line): # in case something fails the test, will require human intervention
            print(line)
            return False
    return True

def AddCardsToParsedList(cards, path=''):
    """ In order for the cards to actually be in game, they have to be added to the parser's list and so they need to go through this function"""
    # currently the default path because this is the only existent list in the program
    if not path: 
        path = "../../parser/cube_card_list.txt"
    with open(path, "a") as file:
        for card in cards:
            file.write(f"{card}\n")
    
if __name__ == "__main__":
    cc, m15 = CardAddition()
    AddCardsToParsedList(cc) # right now only works with cc
    if not RunParser():
        print("Parser failed to run")
        exit(1)
    print("Parser ran successfully")
    # Add cards to cube_card_list
    if RunMTGTests():
        print("All tests passed")
        CreateDecks(2, 6, cc)