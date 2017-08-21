import sys
import pickle

from MTG.parsedcards import *
from MTG import abilities
from MTG import zone
from MTG import triggers
from MTG.exceptions import *

SETPREFIX = ['M15', 'test_set']
name_to_id_dict = {}
id_to_name_dict = {}

# compile all the dictionaries from different parsed sets
for pre in SETPREFIX:
    try:
        with open('data/%s_name_to_id_dict.pkl' % pre, 'rb') as f:
            name_to_id_dict.update(pickle.load(f))
    except:
        print("%s name_to_id_dict not found\n" % pre)

    try:
        with open('data/%s_id_to_name_dict.pkl' % pre, 'rb') as f:
            id_to_name_dict.update(pickle.load(f))
    except:
        print("%s id_to_name_dict not found\n" % pre)


def id_to_name(ID):
    return id_to_name_dict.get(ID, None)


def name_to_id(name):
    return name_to_id_dict.get(name, None)


def str_to_class(str):
    return getattr(sys.modules[__name__], str)


def card_from_name(name, get_instance=True):
    ID = name_to_id(name)
    if ID is not None:
        if get_instance:  # gets instance of class
            # default card class generated by parse_cards.py
            return str_to_class(ID)()
        else:
            return str_to_class(ID)
    else:
        return None


def read_deck(filename):
    """File format:
    NUM CARDNAME

    e.g.
    10 Plains
    10 Oreskos Swiftclaw

    """
    with open(filename, 'r') as f:
        file = f.read().split("\n")
        deck = []
        for line in file:
            try:
                i = line.index(" ")
                num = int(line[:i])
                for j in range(num):  # add NUM copies of CARDNAME
                    card = card_from_name(line[i + 1:])
                    if card:
                        deck.append(card)
                        # print(deck[-1].name())
                    else:
                        pass
                        # print("card {} does not exist\n".format(line[i+1:]))
            except:
                raise DecklistFormatError()

    return deck


def add_activated_ability(cardname, cost, effect, is_mana_ability=False):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    _costs = cost.split(', ')
    costs = ""
    costs_validation = "True"
    if 'T' in _costs:
        costs += "self.tap();"
        costs_validation += " and not self.status.tapped"
    # elif MANA

    card.activated_abilities.append((costs, effect, is_mana_ability))

    card._activated_abilities_costs.append(lambda self: exec(costs))
    card._activated_abilities_costs_validation.append(
        lambda self: eval(costs_validation))
    card._activated_abilities_effects.append(lambda self: exec(effect))


def add_targets(cardname, criterias=[lambda p: True], prompts=["Choose a target\n"]):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    card.target_criterias = criterias
    card.target_prompts = prompts


def make_play_func_single_target(cardname, outcome=lambda self, t: True):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    def play_func(self):
        if self.targets_chosen and self.target_criterias[0](self.targets_chosen[0]):
            outcome(self, self.targets_chosen[0])
        self.controller.graveyard.add(self)

    card.play_func = play_func


def make_play_func_no_target(cardname, outcome=lambda self: True):
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    card.play_func = outcome


def make_trigger(cardname, condition, effect):
    """
    Each effect is a function of the form
        lambda self: do_something

    It will be passed into the stack as
        play.Play(lambda: effect(self))

    where self is the source of the trigger (the permanent)
    """
    if not name_to_id(cardname):
        return
    card = card_from_name(cardname, get_instance=False)

    # make it a variable specific to card rather than a card.Card class var
    # normally, trigger_listeners is defined in card.Card,
    # and our parsed card classes just inherit that
    if card.trigger_listeners == {}:
        card.trigger_listeners = {}

    if condition not in card.trigger_listeners:
        card.trigger_listeners[condition] = []

    # each element in the dict is a list of triggers, since there could be multiple abilities
    # that trigger from the same effect, e.g. tap AND draw a card on etb
    # each of them will go into a separate play.Play object and be put onto the stack
    card.trigger_listeners[condition].append(effect)


def set_up_cards():
    add_activated_ability(
        "Plains", 'T', 'self.controller.mana.add(mana.Mana.WHITE, 1)', True)
    add_activated_ability(
        "Island", 'T', 'self.controller.mana.add(mana.Mana.BLUE, 1)', True)
    add_activated_ability(
        "Swamp", 'T', 'self.controller.mana.add(mana.Mana.BLACK, 1)', True)
    add_activated_ability(
        "Mountain", 'T', 'self.controller.mana.add(mana.Mana.RED, 1)', True)
    add_activated_ability(
        "Forest", 'T', 'self.controller.mana.add(mana.Mana.GREEN, 1)', True)
    # add_activated_ability(
    #    "Wastes", 'T', 'self.controller.mana.add(mana.Mana.COLORLESS, 1)', True)

    add_targets("Lightning Bolt", [lambda p: p.__class__.__name__ == 'Player'
                                   or p.is_creature and p.zone == zone.ZoneType.BATTLEFIELD])
    make_play_func_single_target("Lightning Bolt",
                                 lambda self, t: t.take_damage(self, 3))

    add_targets("Lightning Strike", [lambda p: p.__class__.__name__ == 'Player'
                                     or p.is_creature and p.zone == zone.ZoneType.BATTLEFIELD])
    make_play_func_single_target("Lightning Strike",
                                 lambda self, t: t.take_damage(self, 3))

    add_targets("Congregate", [lambda p: p.__class__.__name__ == 'Player'])
    make_play_func_single_target("Congregate",
                                 lambda self, t: t.gain_life(
                                    2 * len([p for plyr in self.controller.game.players_list
                                               for p in plyr.battlefield
                                               if p.is_creature])))

    make_play_func_no_target("Mass Calcify", lambda self:
                             self.controller.game.apply_to_battlefield(
                                 lambda p: p.dies(),
                                 lambda p: p.is_creature and not p.has_color('W')))

    make_trigger("Ajani's Pridemate", triggers.triggerConditions.onControllerLifeGain,
                 lambda self: self.add_counter("+1/+1")
                 if self.controller.make_choice(
                     "Would you like to put a +1/+1 counter on %r?" % self)
                 else None)
