from random import choice, shuffle
import pygame

cards_36 = [(6, "hearts"), (7, "hearts"), (8, "hearts"), (9, "hearts"), (10, "hearts"), (11, "hearts"), (12, "hearts"),
            (13, "hearts"), (14, "hearts"), (6, "diamonds"), (7, "diamonds"), (8, "diamonds"), (9, "diamonds"),
            (10, "diamonds"), (11, "diamonds"), (12, "diamonds"), (13, "diamonds"), (14, "diamonds"), (6, "spades"),
            (7, "spades"), (8, "spades"), (9, "spades"), (10, "spades"), (11, "spades"), (12, "spades"), (13, "spades"),
            (14, "spades"), (6, "clubs"), (7, "clubs"), (8, "clubs"), (9, "clubs"), (10, "clubs"), (11, "clubs"),
            (12, "clubs"), (13, "clubs"), (14, "clubs")]

back = pygame.image.load("images/cards/back.png")


def get_hands(deck):
    first_hand = ""
    second_hand = ""
    for _ in range(6):
        card_1_data = choice(deck)
        first_hand += " ".join(tuple(map(str, card_1_data))) + ";"
        deck.remove(card_1_data)

        card_2_data = choice(deck)
        second_hand += " ".join(tuple(map(str, card_2_data))) + ";"
        deck.remove(card_2_data)

    trump = deck[-1][-1]

    return first_hand[:-1], second_hand[:-1], trump


class Deck:
    def __init__(self, cards, trump):
        self.cards = []
        for i in cards:
            self.cards.append(Card(*i, trump))

        shuffle(self.cards)

    def encode(self):
        res = ""
        for card in self.cards:
            res += f"{card}*"

        return res

    def decode(self, string, trump):
        cards = []
        data = string.split("*")[:-1]
        for i in data:
            cards.append(i.split())

        return Deck(cards, trump)

    def get_card(self):
        if len(self.cards) == 0:
            return

        card = self.cards[0]
        self.cards.remove(card)

        return card


class DraggableImage:
    def __init__(self, x, y, image_path):
        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_dragging = False

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)


class Card:
    def __init__(self, value: int, suit: str, trump: str):
        self.img = None
        # Является козырем или нет
        if suit == trump:
            self.is_trump = True
        else:
            self.is_trump = False

        self.value = int(value)
        self.suit = suit
        self.trump = trump

    # Вызывается при событии побития карты у карты, которой бьётся игрок
    def can_beat(self, other) -> bool:
        """Проверяет, можно ли побить другую карту данной"""

        if self.is_trump and not other.is_trump:
            return True

        if not self.is_trump and other.is_trump:
            return False

        return self.suit == other.suit and self.value > other.value

    def __eq__(self, other):
        if not isinstance(other, Card):
            return
        return self.suit == other.suit and self.value == other.value

    def __repr__(self):
        return f"{self.value} {self.suit}"


    def show(self, x, y):
        self.x, self.y = x, y

        self.img = DraggableImage(x, y, self.get_image_path())
        # self.img.draw(screen)

    def get_image_path(self):
        return f"images/cards/{self.value} {self.suit}.png"

    def __hash__(self):
        return hash(f"{self.value} {self.suit}")


class Hand:
    order = ["hearts", "spades", "diamonds", "clubs"]

    def __init__(self, cards: list):
        self.trump = cards[0].trump
        self.cards = cards

    def get_cards(self):
        """Возвращает отсортированную руку слева направо в порядке возрастания"""

        list_with_cards = []
        order = self.order.copy()
        order.remove(self.trump)

        for suit in order:
            list_with_cards.extend(sorted([card for card in self.cards if card.suit == suit],
                                          key=lambda card: card.value))

        list_with_cards.extend(
            sorted([card for card in self.cards if card.suit == self.trump], key=lambda card: card.value))

        return list_with_cards

    def show(self):
        cards = self.get_cards()
        for i, card in enumerate(cards):
            step = 550 / (len(cards) + 1)
            card.show(40 + step * i, 570)

    def add_card(self, card):
        self.cards.append(card)

    def delete_card(self, other_card):
        for card in self.cards:
            if card.value == other_card.value and card.suit == other_card.suit:
                self.cards.remove(card)
                return



class Cell:
    def __init__(self, upper_left: tuple, lower_right: tuple, playground):
        self.upper_left = upper_left
        self.lower_right = lower_right
        self.playground = playground

        self.first_card = None
        self.second_card = None

    def set_card(self, card, status=None):
        if not card:
            return

        if status == "1":
            if self.first_card:
                return
            else:
                if not self.playground.can_throw(card):
                    return

                card.img.rect.topleft = self.upper_left
                card.img.rect.bottomright = self.lower_right

                self.first_card = card

                return self.playground.encode()

        elif status == "0":
            if self.playground.is_empty():
                return

            if self.first_card:
                if card.can_beat(self.first_card):
                    print("CAN")
                    x1, y1 = self.upper_left
                    card.img.rect.topleft = (x1 + 15, y1 - 15)

                    x2, y2 = self.lower_right
                    card.img.rect.bottomright = (x2 + 15, y2 - 15)

                    self.second_card = card

                    return self.playground.encode()

            else:
                if not self.playground.can_reverse_move(card):
                    return

                card.img.rect.topleft = self.upper_left
                card.img.rect.bottomright = self.lower_right

                self.first_card = card

                return f"{self.playground.encode()}&CHANGE_STATUS"

        else:
            if not self.first_card:
                self.first_card = card
            else:
                self.second_card = card

    def is_empty(self):
        return self.first_card is None and self.second_card is None


class Playground:
    cell_coordinates = [
        # [(левый верх, правый низ)]
        [(152, 232), (224, 332)], [(263, 232), (335, 332)], [(374, 232), (446, 332)],
        [(152, 368), (224, 468)], [(263, 368), (335, 468)], [(374, 368), (446, 468)]
    ]

    def __init__(self, message: str = None):
        self.cells = []

        for i in range(6):
            cell = Cell(*self.cell_coordinates[i], self)
            self.cells.append(cell)

        if message:
            trump = message.split(";")[-1]

            for i in message.split(";")[:-1]:
                index, cards_data = i.split(":")
                cell = Cell(*self.cell_coordinates[int(index)], self)

                cards_data = cards_data.split("|")
                for k, c in enumerate(cards_data, start=1):
                    if not c:
                        continue
                    value, suit = c.split()
                    card = Card(int(value), suit, trump)

                    x, y = self.cell_coordinates[int(index)][0]

                    if k == 2:
                        x += 15
                        y -= 15

                    card.img = DraggableImage(x, y, card.get_image_path())

                    cell.set_card(card)

                self.cells[int(index)] = cell



    def validate_move(self, upper_left, lower_right):
        x1, y1 = upper_left
        x2, y2 = lower_right

        for cell in self.cells:
            cell_x1, cell_y1 = cell.upper_left
            cell_x2, cell_y2 = cell.lower_right

            if abs(x1 - cell_x1) <= 30 and abs(y1 - cell_y1) <= 30 and abs(x2 - cell_x2) <= 30 and abs(y2 - cell_y2) <= 30:
                return cell

    def encode(self) -> str:
        res = ""

        for i, cell in enumerate(self.cells):
            first_card, second_card = cell.first_card, cell.second_card
            if any([first_card, second_card]):
                res += f"{i}:"
                for card in (first_card, second_card):
                    if card:
                        trump = card.trump
                        res += f"{str(card.value)} {card.suit}|"

                res += ";"


        try:
            if trump:
                return res + trump
        except UnboundLocalError:
            return res


    def is_empty(self):
        if not self.encode():
            return True

    def convert_to_cards_and_draggable(self):
        cards_and_draggable = []
        for cell in self.cells:
            first_card, second_card = cell.first_card, cell.second_card

            for card in (first_card, second_card):
                if card:
                    cards_and_draggable.append((card, card.img))

        return cards_and_draggable

    def contains(self, other_card):
        if not isinstance(other_card, Card):
            return

        for cell in self.cells:
            first_card, second_card = cell.first_card, cell.second_card

            for card in (first_card, second_card):
                if card == other_card:
                    return True

    def can_throw(self, other_card):
        values = []

        for cell in self.cells:
            first_card, second_card = cell.first_card, cell.second_card

            for card in (first_card, second_card):
                if card:
                    values.append(card.value)

        return other_card.value in values or len(values) == 0

    def can_reverse_move(self, other_card):
        values = []

        for cell in self.cells:
            first_card, second_card = cell.first_card, cell.second_card
            if second_card:
                return

            if first_card:
                values.append(first_card.value)

        return other_card.value in values

    def can_end_move(self):
        if all([cell.is_empty() for cell in self.cells]):
            return

        for cell in self.cells:
            if cell.first_card and not cell.second_card:
                return

        return True

    def show_enemy_cards(self, screen, amount_of_enemy_cards: int):
        for i in range(amount_of_enemy_cards):
            step = 550 / (amount_of_enemy_cards + 1)
            screen.blit(back, (40 + step * i, 50))



def show_bito(screen):
    bito = pygame.image.load("images/buttons/bito.png")
    screen.blit(bito, (15, 483))


def show_take_card(screen):
    take = pygame.image.load("images/buttons/take.png")
    screen.blit(take, (15, 483))


def hod_coloda(screen, youmove: bool, cardctr: int, trump):
    RED = (191, 20, 20)
    font = pygame.font.Font('fonts/TeleSys.ttf', 30)
    font2 = pygame.font.Font(None, 30)
    if youmove:
        text_move = font2.render('Ваш ход', True, RED)
        screen.blit(text_move, (11, 341))
    trumpimg = pygame.image.load(f'images/cards/{trump}.png')
    trumpimg.blit(trumpimg, (532, 418))
    if cardctr:
        back = pygame.image.load('images/cards/back.png')
        screen.blit(back, (507, 300))
        cards_num = font.render(str(cardctr), True, RED)
        screen.blit(cards_num, (528, 259))

