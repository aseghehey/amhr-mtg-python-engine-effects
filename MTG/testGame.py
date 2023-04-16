import sys
import os
from MTG import game
from MTG import player
from MTG import play
from MTG import zone
from MTG import cards
from MTG import gamesteps
from MTG import cardtype
from MTG import combat
from MTG import triggers
from MTG.exceptions import *

def getCardName(card):
    return card.characteristics.name

def getInstants(hand):
    instants = []
    for card in hand:
        if card.is_instant:
            instants.append(card)
    return instants

def getCardText(card):
    return card.characteristics.text

def printCardCharacteristics(cardList):
   for card in cardList:
        cardCharacteristics = card.characteristics
        print(f"{cardCharacteristics.name}: \033[91m{cardCharacteristics.text}\033[0m")

if __name__ == "__main__":
    decks = game.parseDecks()
    gamePlayed = game.Game(decks)
    gamePlayed.setup_game()
    gamePlayed.step = gamesteps.Step.BEGINNING_OF_COMBAT

    cardsPlayed = set()

    players = gamePlayed.players_list

    #TODO: automate it for both players
    handPlayer0 = players[0].hand 
    instants = getInstants(handPlayer0)
    # printCardCharacteristics(instants)

    # AIMING TO test "Lightning Blast" for now, will change later
    for instant in instants:
        cardName = getCardName(instant)
        if cardName in cardsPlayed:
            # ignore cards we've already tested
            continue

        #TODO: instant.targets() needs user to type target like "opponent"
        # may have to change it from getting user input to taking it as param
        canTarget = instant.targets() 
        try:
            observeEffect = None
            #TODO: make it interpret text and know what to call 
            if 'player' in getCardText(instant): # will change, did this for a test
                observeEffect = players[1].life

            inPlay = play.Play(apply_func=instant.play_func,
                               card=instant)
            inPlay.apply()

            print(players[1].life, players[1].life != observeEffect)            
            cardsPlayed.add(cardName)
        except:
            raise Exception(f"Could not play {instant.characteristics.name}")
        
 