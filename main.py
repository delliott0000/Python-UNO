from __future__ import annotations

import random
import time
import json
import sys

from abc import ABC, abstractmethod


"""

A simple, console-based, object-oriented UNO game coded by Delliott using Python 3.11.

"""


# Typehints
STRINGLIST = list[str]
JSON = int | bool | STRINGLIST | dict[str, bool | STRINGLIST]

# Constants
DELAY: float = 2.0
COLOUR_LIST: STRINGLIST = ['Red', 'Yellow', 'Green', 'Blue']
BOOL_CHOICES: STRINGLIST = ['True', 'False']
BOOL_MAPPING: dict[str, bool] = {'True': True, 'False': False}


def get_input(question: str, choices: STRINGLIST) -> str:
    while True:
        print(question)
        print(f'Choices: {", ".join(choices)}')
        choice = input('Enter choice: ')
        if choice in choices:
            return choice
        elif choice == 'Exit':
            sys.exit()
        print('Invalid choice!')


def print_line() -> None:
    print('------------------------------')


class SaveData:

    FILEPATH: str = 'data.json'

    @classmethod
    def read_data(cls) -> dict[str, JSON]:
        with open(cls.FILEPATH, 'r') as file:
            return json.loads(file.read())

    @classmethod
    def write_data(cls, **kwargs: JSON) -> None:
        with open(cls.FILEPATH, 'w') as file:
            file.write(json.dumps(kwargs))


class BaseUnoCard(ABC):

    __slots__ = (
        'game',
        'colour',
    )

    def __init__(self, game: UnoGame, colour: str | None) -> None:
        self.game = game
        self.colour = colour

    def __str__(self) -> str:
        return (f'{self.colour} ' if self.colour else '') + self.__class__.__name__

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}:{self.colour}'

    def __eq__(self, other: BaseUnoCard) -> bool:
        return isinstance(other, self.__class__) and self.colour == other.colour

    @classmethod
    def from_string(cls, game: UnoGame, string: str) -> BaseUnoCard:
        components = string.split(':')
        if components[0] == 'NumberedCard':
            return NumberedCard(game, components[1], int(components[2]))
        elif components[0] == 'DrawFourCard':
            return DrawFourCard(game)
        elif components[0] == 'WildCard':
            return WildCard(game)
        else:
            return getattr(sys.modules[__name__], components[0])(game, components[1])

    @abstractmethod
    def play(self) -> None:
        ...


class NumberedCard(BaseUnoCard):

    __slots__ = (
        'number',
    )

    def __init__(self, game: UnoGame, colour: str, number: int) -> None:
        super().__init__(game, colour)
        self.number = number

    def __str__(self) -> str:
        return f'{self.colour} {self.number}'

    def __repr__(self) -> str:
        return f'{super().__repr__()}:{self.number}'

    def __eq__(self, other: BaseUnoCard | NumberedCard) -> bool:
        return super().__eq__(other) and self.number == other.number

    def play(self) -> None:
        if self.game.seven_zero is True:

            current_player = self.game.player_from_turn(self.game.turn)

            if self.number == 7:

                other_player_list = [player for player in self.game.player_list if player is not current_player]

                if current_player.human is True:
                    player_name_list = [player.name for player in other_player_list]
                    new_player_name = get_input('Select a player to switch hands with...', player_name_list)
                    new_player = [player for player in self.game.player_list if player.name == new_player_name][0]

                else:
                    new_player = random.choice(other_player_list)

                current_player_hand = [c for c in current_player.hand]
                new_player_hand = [c for c in new_player.hand]

                current_player.hand = new_player_hand
                new_player.hand = current_player_hand

                print(f'{current_player} swapped hands with {new_player}.')

            elif self.number == 0:

                player_hands = []
                for player in self.game.player_list:
                    player_hands.append([c for c in player.hand])

                if self.game.spin == 1:

                    for i in range(len(player_hands) - 1):
                        self.game.player_list[i + 1].hand = player_hands[i]

                    self.game.player_list[0].hand = player_hands[-1]

                else:

                    for i in range(len(player_hands) - 1):
                        self.game.player_list[i].hand = player_hands[i + 1]

                    self.game.player_list[-1].hand = player_hands[0]

                print(f'Each player must pass their hand to the next player...')


class SkipCard(BaseUnoCard):

    __slots__ = ()

    def play(self) -> None:
        self.game.turn = self.game.next_turn


class DrawTwoCard(BaseUnoCard):

    __slots__ = ()

    def activate(self, player: Player) -> None:
        count = 1

        if self.game.stacking is True:
            for card in reversed(self.game.pile[:-1]):
                if isinstance(card, DrawTwoCard):
                    count += 1
                else:
                    break

        print(f'{player} must draw {2 * count} cards from the deck.')
        for _ in range(2):
            self.game.deal_card(player)
        self.game.turn = self.game.next_turn

    def play(self) -> None:
        next_player = self.game.player_from_turn(self.game.next_turn)

        if self.game.stacking is False:
            self.activate(next_player)

        else:
            for card in next_player.hand:
                if isinstance(card, DrawTwoCard):
                    break
            else:
                self.activate(next_player)


class ReverseCard(BaseUnoCard):

    __slots__ = ()

    def play(self) -> None:
        self.game.spin *= -1


class DrawFourCard(BaseUnoCard):

    __slots__ = ()

    def __init__(self, game: UnoGame):
        super().__init__(game, None)

    def activate(self, player: Player) -> None:
        count = 1

        if self.game.stacking is True:
            for card in reversed(self.game.pile[:-1]):
                if isinstance(card, DrawFourCard):
                    count += 1
                else:
                    break

        print(f'{player} must draw {4 * count} cards from the deck.')
        for _ in range(4 * count):
            self.game.deal_card(player)
        self.game.turn = self.game.next_turn

    def play(self) -> None:
        current_player = self.game.player_from_turn(self.game.turn)
        if current_player.human is True:
            self.colour = get_input('Choose a colour...', COLOUR_LIST)
        else:
            self.colour = random.choice(COLOUR_LIST)
        print(f'{current_player} chose {self.colour} as the new colour.')

        next_player = self.game.player_from_turn(self.game.next_turn)

        if self.game.stacking is False:
            self.activate(next_player)

        else:
            for card in next_player.hand:
                if isinstance(card, DrawFourCard):
                    break
            else:
                self.activate(next_player)


class WildCard(BaseUnoCard):

    __slots__ = ()

    def __init__(self, game: UnoGame):
        super().__init__(game, None)

    def play(self) -> None:
        current_player = self.game.player_from_turn(self.game.turn)
        if current_player.human is True:
            self.colour = get_input('Choose a colour...', COLOUR_LIST)
        else:
            self.colour = random.choice(COLOUR_LIST)
        print(f'{current_player} chose {self.colour} as the new colour.')


class Player:

    __slots__ = (
        'game',
        'name',
        'human',
        'hand',
    )

    def __init__(self, game: UnoGame, name: str, human: bool, hand: list[BaseUnoCard] = None) -> None:
        self.game = game
        self.name = name
        self.human = human
        self.hand: list[BaseUnoCard] = hand or []

    def __str__(self) -> str:
        return self.name

    def playable_cards(self) -> list[BaseUnoCard]:
        current = self.game.top_pile_card
        playable_cards = []

        for card in self.hand:

            if isinstance(card, WildCard):
                playable_cards.append(card)

            if isinstance(card, DrawFourCard) and isinstance(current, DrawFourCard) and self.game.stacking is True:
                playable_cards.append(card)

            elif isinstance(card, NumberedCard) and isinstance(current, NumberedCard) and card.number == current.number:
                playable_cards.append(card)

            elif card.colour == current.colour and not isinstance(card, (WildCard, DrawFourCard)):
                playable_cards.append(card)

            else:
                for cls in [SkipCard, ReverseCard, DrawTwoCard]:
                    if isinstance(card, cls) and isinstance(current, cls):
                        playable_cards.append(card)

        for card in self.hand:
            if not playable_cards and isinstance(card, DrawFourCard):
                playable_cards.append(card)

        return playable_cards

    def display_cards(self) -> None:
        hand_string = ''
        for i, card in enumerate(self.hand):
            hand_string += f'({i + 1}) {card}, '
        print(hand_string[:-2])

    def get_played_card(self) -> BaseUnoCard:
        if self.human is True:
            self.display_cards()
            while True:
                index_range = [str(i + 1) for i in range(len(self.hand))]
                index = int(get_input('Choose the index of the card to play...', index_range))
                chosen_card = self.hand[index - 1]
                if chosen_card in self.playable_cards():
                    return chosen_card
                print('Invalid choice! Try again!')
        else:
            return random.choice(self.playable_cards())


class UnoGame:

    def __init__(self, new_game: bool = False, **kwargs: int | bool) -> None:
        self.player_list: list[Player] = []

        self.deck: list[BaseUnoCard]
        self.pile: list[BaseUnoCard]

        self.turn: int
        self.spin: int

        self.jump_in: bool
        self.stacking: bool
        self.seven_zero: bool

        if new_game is True:
            total_players: int = kwargs.get('player_count', 4)
            human_players: int = kwargs.get('human_count', 1)
            robot_players: int = total_players - human_players

            count: int = 0
            for _ in range(human_players):
                count += 1
                self.player_list.append(Player(self, f'Player {count}', True))
            for __ in range(robot_players):
                count += 1
                self.player_list.append(Player(self, f'Player {count}', False))

            self.deck, self.pile, self.turn, self.spin = [], [], 1, 1

            self.jump_in = kwargs.get('jump_in', False)
            self.stacking = kwargs.get('stacking', False)
            self.seven_zero = kwargs.get('seven_zero', False)

            self.init_cards()

        else:
            all_data = SaveData.read_data()

            for entry in all_data:
                if 'Player' in entry:
                    data = all_data[entry]

                    human: bool = data.get('human', True)
                    cards: STRINGLIST = data.get('cards', [])
                    cards: list[BaseUnoCard] = [BaseUnoCard.from_string(self, card) for card in cards]

                    player = Player(self, entry, human, hand=cards)
                    self.player_list.append(player)

            self.deck = [BaseUnoCard.from_string(self, card) for card in all_data.get('deck', [])]
            self.pile = [BaseUnoCard.from_string(self, card) for card in all_data.get('pile', [])]

            self.turn = all_data.get('turn', 1)
            self.spin = all_data.get('spin', 1)

            self.jump_in = all_data.get('jump_in', False)
            self.stacking = all_data.get('stacking', False)
            self.seven_zero = all_data.get('seven_zero', False)

    @property
    def top_pile_card(self) -> BaseUnoCard:
        try:
            return self.pile[-1]
        except IndexError:
            while True:
                card = random.choice(self.deck)
                if isinstance(card, NumberedCard):
                    self.deck.remove(card)
                    self.pile.append(card)
                    break
            return self.pile[-1]

    @property
    def next_turn(self) -> int:
        next_turn_int = self.turn + self.spin
        if next_turn_int > len(self.player_list):
            return 1
        elif next_turn_int == 0:
            return len(self.player_list)
        return next_turn_int

    def save_game(self) -> None:
        print('\nSaving game...')
        game_data = {
            'deck': [repr(card) for card in self.deck],
            'pile': [repr(card) for card in self.pile],
            'turn': self.turn,
            'spin': self.spin,
            'jump_in': self.jump_in,
            'stacking': self.stacking,
            'seven_zero': self.seven_zero
        }
        for player in self.player_list:
            player_data = {'human': player.human, 'cards': [repr(card) for card in player.hand]}
            game_data[player.name] = player_data
        SaveData.write_data(**game_data)
        print('Done!')

    def init_cards(self) -> None:
        for colour in COLOUR_LIST:
            self.deck.append(WildCard(self))
            self.deck.append(DrawFourCard(self))

            for _ in range(2):

                for i in range(1, 10):
                    self.deck.append(NumberedCard(self, colour, i))

                self.deck.append(SkipCard(self, colour))
                self.deck.append(DrawTwoCard(self, colour))
                self.deck.append(ReverseCard(self, colour))

            self.deck.append(NumberedCard(self, colour, 0))

        for _ in range(7):
            for player in self.player_list:
                self.deal_card(player)

    def deal_card(self, player: Player) -> BaseUnoCard:
        card: BaseUnoCard = random.choice(self.deck)

        self.deck.remove(card)
        player.hand.append(card)

        if not self.deck:
            for _ in range(len(self.pile) - 1):
                _card = self.pile[0]
                self.pile.remove(_card)
                self.deck.append(_card)

        return card

    def player_from_turn(self, turn: int) -> Player:
        for player in self.player_list:
            if str(turn) in player.name:
                return player

    def play_jump_in(self, card: BaseUnoCard) -> None:
        for player in self.player_list:

            if player is self.player_from_turn(self.next_turn) and isinstance(card, SkipCard):
                continue

            for player_card in player.hand:

                if isinstance(card, (WildCard, DrawFourCard)):
                    continue

                if player_card == card:

                    if player.human is True:
                        jump_in = BOOL_MAPPING[get_input(f'{player}, jump in?', BOOL_CHOICES)]
                    else:
                        jump_in = random.choice([True, False])

                    if jump_in is True:
                        print_line()
                        print(f'{player} is jumping in with {player_card}!')
                        self.turn = int(player.name[-1])
                        self.play_card(player, player_card)
                        break

        else:
            card.play()

    def play_card(self, player: Player, card: BaseUnoCard) -> None:
        print(f'{player} played {card}.')

        player.hand.remove(card)
        self.pile.append(card)

        if len(player.hand) == 0:
            print(f'{player} has won the game!')
            sys.exit()
        elif len(player.hand) == 1:
            print(f'{player} has 1 card left!')

        if self.jump_in is True:
            self.play_jump_in(card)
        else:
            card.play()

    def run_game(self) -> None:

        print_line()
        rule_mapping = {True: 'Enabled', False: 'Disabled'}
        print(f'Stacking: {rule_mapping[self.stacking]}')
        print(f'Jump-In: {rule_mapping[self.jump_in]}')
        print(f'7-0: {rule_mapping[self.seven_zero]}')
        print_line()

        if not self.top_pile_card.colour:
            self.top_pile_card.colour = random.choice(COLOUR_LIST)
        print(f'Starting card: {self.top_pile_card}')

        while True:
            time.sleep(DELAY)
            print_line()

            current_player = self.player_from_turn(self.turn)

            for card in current_player.hand:
                if isinstance(card, (WildCard, DrawFourCard)):
                    card.colour = None

            print(f'{current_player}\'s turn:')

            playable_cards = current_player.playable_cards()

            if not playable_cards:

                if current_player.human is True:
                    current_player.display_cards()

                print(f'{current_player} has no playable cards and must draw from the deck.')
                new_card = self.deal_card(current_player)

                if current_player.human is True:
                    print(f'{current_player} drew a {new_card} from the deck.')

                if playable_cards:
                    self.play_card(current_player, playable_cards[0])

            else:
                card = current_player.get_played_card()
                self.play_card(current_player, card)

            self.turn = self.next_turn

            print_line()
            print(f'Top card: {self.top_pile_card}')


def main() -> None:
    print('Type "Exit" at any point to exit the program.')

    game_data = SaveData.read_data()

    if not game_data:
        new_game_bool = True
    else:
        for entry in game_data:
            if 'Player' in entry and not game_data[entry].get('cards', []):
                new_game_bool = True
                break
        else:
            new_game_string = get_input('Do you wish to start a new game?', BOOL_CHOICES)
            new_game_bool = BOOL_MAPPING[new_game_string]

    if new_game_bool is True:
        new_game_settings = {}
        total_player_count = int(get_input('How many total players do you want?', [str(i) for i in range(2, 11)]))
        human_player_count = int(get_input('How many human players do you want?',
                                           [str(i) for i in range(1, total_player_count + 1)]))
        new_game_settings['player_count'] = total_player_count
        new_game_settings['human_count'] = human_player_count

        configure_rules = BOOL_MAPPING[get_input('Configure rules?', BOOL_CHOICES)]

        if configure_rules is True:
            stacking = BOOL_MAPPING[get_input('Enable Stacking?', BOOL_CHOICES)]
            seven_zero = BOOL_MAPPING[get_input('Enable 7-0?', BOOL_CHOICES)]
            jump_in = BOOL_MAPPING[get_input('Enable Jump-In?', BOOL_CHOICES)]
        else:
            stacking = game_data.get('stacking', False)
            seven_zero = game_data.get('seven_zero', False)
            jump_in = game_data.get('jump_in', False)

        new_game_settings['stacking'] = stacking
        new_game_settings['seven_zero'] = seven_zero
        new_game_settings['jump_in'] = jump_in

        uno_game = UnoGame(new_game=True, **new_game_settings)

    else:
        uno_game = UnoGame(new_game=False)

    try:
        uno_game.run_game()
    except BaseException as error:
        uno_game.save_game()
        raise error


try:
    main()
except (KeyboardInterrupt, SystemExit):
    print('Goodbye!')
