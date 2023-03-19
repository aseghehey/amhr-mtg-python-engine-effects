from enum import Enum
import random, pdb

from MTG import gameobject
from MTG import cards
from MTG import card
from MTG import permanent
from MTG import triggers


class ZoneType(Enum):
    LIBRARY = 0
    HAND = 1
    BATTLEFIELD = 2
    GRAVEYARD = 3
    STACK = 4
    EXILE = 5
    # COMMAND = 6

# Returns the technical format of a zone given that zone's name
def str_to_zone_type(z):
    return {
        'library': ZoneType.LIBRARY,
        'hand': ZoneType.HAND,
        'battlefield': ZoneType.BATTLEFIELD,
        'graveyard': ZoneType.GRAVEYARD,
        'stack': ZoneType.STACK,
        'exile': ZoneType.EXILE
    }[z.lower()]

# Class for all basic zone features and functions
class Zone():

    # Attributes:
    # - is_library: bool, whether or not the zone is a library.
    # - is_battlefield: bool, whether or not the zone is a battlefield.
    # - is_public: bool, whether or not the zone is public.
    # - elements: list, a list of objects in the zone.
    # - controller: object, the controller of the zone.
    # - game: object, the game the zone belongs to.
    
    is_library = False
    is_battlefield = False
    is_public = False

    # Creates an empty zone with no elements, assigns it to the controller, and assigns it to the game
    def __init__(self, controller=None, elements: list=None):
        if elements is None:
            self.elements = []
        else:
            self.elements = elements
            for ele in elements:
                ele.controller = controller
        self.controller = controller
        if controller is not None:
            self.game = self.controller.game

    # Prints basic zone information: name, controller, and elements
    def __repr__(self):
        return 'zone.Zone %r controlled by %r len=%s\n%r' % (self.__class__.__name__,
                                                             self.controller, len(self), self.elements)

    # Lists all elements in the zone controlled by the player
    def __str__(self):
        return '%s\'s %s (%s cards)\n%s' % (self.controller, 
                                            self.__class__.__name__,
                                            len(self), 
                                            [ele.name for ele in self.elements])

    # Returns a list of elements in the zone. This usually means cards
    def __len__(self):
        return len(self.elements)

    def __bool__(self):
        return bool(self.elements)

    # Returns an element from the zone. Example use case would be searching the library for a card
    def __getitem__(self, pos):
        return self.elements[pos]

    # Determines if the zone is empty
    @property
    def isEmpty(self):
        return len(self) == 0

    # Adds objects to a zone
    def add(self, obj):

        # convert string (card's name) to a Card object
        if type(obj) is str:
            obj = cards.card_from_name(obj)

        # If a the object is a list then add each element to the zone list
        if type(obj) is list:
            for o in obj:
                o.zone = self
                if not isinstance(self, Stack):
                    assert isinstance(o, gameobject.GameObject)
                o.controller = self.controller
            self.elements.extend(obj)
            return obj

        # Assign control of the object if it is not a stack object
        if not isinstance(self, Stack):
            assert isinstance(obj, gameobject.GameObject)
            obj.controller = self.controller

        # Assigns the objects to the appropriate zone and returns them
        obj.zone = self
        self.elements.append(obj)
        return obj

    # Removes a specfic object or list of objects in a zone
    def remove(self, obj):
        if type(obj) is list:
            return all([self.remove(o) for o in obj])

        try:
            self.elements.remove(obj)
            obj.zone = None
            return True
        except ValueError:
            return False

    # Applies a filter to the objects in a zone and returns a set of those objects
    def filter(self, characteristics=None, filter_func=None):
        found = set()

        if filter_func:
            for ele in self:
                if filter_func(ele):
                    found.add(ele)
        else:
            assert (characteristics is None
                    or isinstance(characteristics, gameobject.Characteristics))

            for ele in self:
                if ele.characteristics.satisfy(characteristics):
                    found.add(ele)

        return found

    # Returns a count of objects in the zone
    def count(self, characteristics=None, filter_func=None):
        return len(self.filter(characteristics, filter_func))

    # Determines if a card object exists in the zone
    def get_card_by_name(self, name):
        cards = self.filter(gameobject.Characteristics(name=name))
        if cards:
            return list(cards)[0]
        else:
            return None

    # Returns the last element in the list. Used for drawing cards, the library is stored in reverse order.
    def pop(self, pos=-1):
        return self.elements.pop(pos)

    # Removes all elements in the zone
    def clear(self):
        # bypass triggers
        self.elements = []

# ******************************
# Declare all zone classes below
# ******************************

class Battlefield(Zone):
    zone_type = 'BATTLEFIELD'
    is_battlefield = True
    is_public = True

    def add(self, obj, status_mod=None, modi_func=None):

        # convert string (card's name) to a Card object
        if type(obj) is str:
            obj = cards.card_from_name(obj)
        obj.controller = self.controller

        # convert card to Permanent
        if isinstance(obj, card.Card):
            # this will call Battlefield.add(...) again
            obj = permanent.make_permanent(obj, status_mod, modi_func)
        else:
            assert isinstance(obj, permanent.Permanent)
            obj.zone = self
            self.elements.append(obj)

            # reset status upon entering battlefield
            obj.status.reset()
            if status_mod:
                if 'tapped' in status_mod:
                    status.tapped = True
            
            # apply "enter the battlefield with ..." effects: e.g. tapped
            if modi_func:
                modi_func(self)

            # Performs all triggers
            obj.trigger('onEtB', obj)
            obj.controller.trigger('onControllerPermanentEtB', obj)
            obj.game.trigger('onPermanentEtB', obj)

            if obj.is_creature:
                obj.controller.trigger('onControllerCreatureEtB', obj)
                obj.game.trigger('onCreatureEtB', obj)

class Stack(Zone):
    zone_type = 'STACK'
    is_public = True

    #TODO: move stack printing here (from game.py)
    pass

class Hand(Zone):
    zone_type = 'HAND'
    is_public = False
    pass

class Graveyard(Zone):
    zone_type = 'GRAVEYARD'
    is_public = True
    pass

class Exile(Zone):
    zone_type = 'EXILE'
    is_public = True
    pass

class Library(Zone):
    zone_type = 'LIBRARY'
    is_library = True
    is_public = False

    # Must be declared above __init__ as shuffle is used there
    def shuffle(self):
        random.shuffle(self.elements)

    # Adds all cards in library to the library zone and shuffles the zone
    def __init__(self, controller=None, elements: list=None):
        super(Library, self).__init__(controller, elements)
        for ele in self.elements:
            ele.zone = self
        self.shuffle()

    # Adds a new card to the library
    def add(self, obj, from_top=0, shuffle=True):
        """ Note: the library is reversed; i.e. self.elements[0] is the last card

        When you draw, you draw from self.pop(), or self.elements[-1]
        """
        if type(obj) is str:
            obj = cards.card_from_name(obj)
        assert isinstance(obj, gameobject.GameObject)
        obj.controller = self.controller
        obj.zone = self

        if from_top == 0:
            self.elements.append(obj)
        elif from_top == -1:  # put on bottom
            self.elements = [obj] + self.elements
        else:
            self.elements = self.elements[:-from_top] + [obj] + self.elements[-from_top:]

        if shuffle:
            self.shuffle()

        return obj

    # Removes a card from the library
    def remove(self, obj, shuffle=False):
        if shuffle:
            self.shuffle()

        return super(Library, self).remove(obj)