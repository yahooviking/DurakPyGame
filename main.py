import pygame
import socket
import threading
import queue
import http.client
from card import get_hands, Hand, Card, Playground, show_bito, show_take_card, Deck, cards_36, hod_coloda
from database import add_client

create_server_pressed = False
connect_to_server_pressed = False
connected_clients = 0
current_state = "main"

input_ip_active = False
input_ip_text = ""

message_queue = queue.Queue()

show_bito_button = False
show_take_button = False

cards = cards_36.copy()

# Создание сервера
def create_server():
    global create_server_pressed, connected_clients
    create_server_pressed = False

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5555))
    server_socket.listen(1)
    print("Ждем подключения...")

    while connected_clients < 1:
        client_socket, client_address = server_socket.accept()
        connected_clients += 1
        print(f"Подключился клиент {client_address}")
        message_queue.put('карты ХОСТА')  # сюда их уже проще запихнуть

        if connected_clients == 1:
            client_socket.sendall("Добро пожаловать, вы клиент".encode())

    ip, port = client_address
    add_client(ip, port)

    server_socket.close()


def run_window(message):
    global current_state, show_bito_button, show_take_button
    current_state = "message"
    window_size = (600, 700)
    message_screen = pygame.display.set_mode(window_size)
    font = pygame.font.Font(None, 36)
    if connected_clients == 1:
        status = "1"
        role = "host"
        pygame.display.set_caption("ХОСТ")

        host_hand, client_hand, trump = get_hands(cards)

        message: str = host_hand  # список карт хоста
        client_cards: str = client_hand  # строка карт клиента
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # направляем подключение
        host = '0.0.0.0'
        port = 5555
        server_socket.bind((host, port))  # подключаем свой адрес
        server_socket.listen(1)
        client_socket, client_address = server_socket.accept()  # принимаем подключение
        print(client_cards)
        client_socket.send(f"{client_cards}|{host_hand};{trump}".encode(
            'utf-8'))  # список отправлять нельзя, только закодированные строки
        message = message.split(';')
    else:
        status = "0"
        role = "client"
        pygame.display.set_caption("КЛИЕНТ")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # направляем подключение
        host = input_ip_text
        port = 5555
        client_socket.connect((host, port))  # подключаемся
        data = client_socket.recv(1024).decode('utf-8')  # получаем карт
        client_socket.settimeout(0.01)

        trump = data.split(";")[-1]
        message = data.split("|")[0].split(";")  # карты клиента назначаются в data
        host_cards = data.split("|")[1].split(";")[:-1]

        print(message, host_cards)

    clock = pygame.time.Clock()

    running = True
    bg = pygame.image.load("images/bg.png")

    hand = Hand([Card(*i.split(), trump) for i in message])

    hand.show()

    draggable_objects = [(card, card.img) for card in hand.get_cards()]

    playground = Playground()

    deck = Deck(cards, trump)
    if status == "0":
        lst = hand.cards + [Card(*i.split(), trump) for i in host_cards]
        for card in hand.get_cards() + lst:
            if card in deck.cards:
                deck.cards.remove(card)

    amount_of_enemy_cards = 6
    won = False
    while running:
        message_screen.blit(bg, (0, 0))
        if won:
            pobeda = font.render("Вы победили!", True, BLACK)
            screen.blit(pobeda, (110, 115))
        hod_coloda(message_screen, status == "1", len(deck.cards), trump)

        if show_bito_button:
            show_bito(message_screen)

        if show_take_button:
            show_take_card(message_screen)

        if role == "client":
            client_socket.send('NONE'.encode('utf-8')) # вместо "отправил на хост" нужная инфа
        try:
            if role == "host":
                data = client_socket.recv(1024).decode('utf-8').replace("NONE", "")  # получение инфы хостом
                if "ENEMY_CARDS" in data:
                    deck = deck.decode(data.split(";")[0], trump)
                    amount_of_enemy_cards = int(data.replace("ENEMY_CARDS:", "").split(";")[-1])
                    continue
                if len([i for i in data if i.isdigit()]) != 0:
                    amount_of_enemy_cards = int(data.replace("CHANGE_STATUS", "").replace("&CLEAR_PG", "").split(";")[-2])
            else:
                data = client_socket.recv(1024).decode('utf-8')
                if "ENEMY_CARDS" in data:
                    deck = deck.decode(data.split(";")[0], trump)
                    amount_of_enemy_cards = int(data.replace("ENEMY_CARDS:", "").split(";")[-1])
                    continue
                amount_of_enemy_cards = int(data.replace("CHANGE_STATUS", "").replace("&CLEAR_PG", "").split(";")[-2])

            if data:
                deck = deck.decode(data.split(";")[-1], trump)
                if "CHANGE_STATUS" in data or "&CLEAR_PG;" in data:
                    while len(hand.cards) < 6:
                        card = deck.get_card()
                        if not card:
                            break

                        hand.add_card(card)

                    if len(hand.cards) == 0:
                        bg = pygame.image.load("images/clearbg.png") # победа
                        won = True
                        print('e')

                    hand.show()

                    if "CHANGE_STATUS" in data:
                        data = data.replace("CHANGE_STATUS", "")

                        show_take_button = True
                        if status == "0":
                            show_take_button = False
                            status = "1"
                        else:
                            status = "0"
                            show_bito_button = False


                    if "CLEAR_PG;" in data:
                        show_take_button = False
                        show_bito_button = False

                        playground = Playground()
                        draggable_objects = [(card, card.img) for card in hand.get_cards()]

                        client_socket.send(f"{deck.encode()};ENEMY_CARDS:{len(hand.cards)}".encode("utf-8"))
                    else:
                        data = ";".join(data.split(";")[:-2])
                        try:
                            playground = Playground(data)
                        except:
                            raise ValueError(data)
                        lst = playground.convert_to_cards_and_draggable()

                        for j in lst:
                            if j[0] not in [i[0] for i in draggable_objects]:
                                draggable_objects.append(j)
                else:
                    data = ";".join(data.split(";")[:-2])
                    playground = Playground(data)
                    lst = playground.convert_to_cards_and_draggable()

                    for j in lst:
                        if j[0] not in [i[0] for i in draggable_objects]:
                            draggable_objects.append(j)

                    if playground.can_end_move():
                        if status == "1":
                            show_bito_button = True
                    else:
                        if status == "0":
                            show_take_button = True
        except TimeoutError:
            pass


        playground.show_enemy_cards(message_screen, amount_of_enemy_cards) # вместо 6 кол-во карт у противника
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break
            elif event.type == pygame.MOUSEBUTTONDOWN and 15 <= event.pos[0] <= 165 and 483 <= event.pos[1] <= 557 and show_bito_button:
                print('bito clicked')
                status = "0"

                playground = Playground()
                while len(hand.cards) < 6:
                    card = deck.get_card()
                    if not card:
                        break

                    if len(hand.cards) == 0:
                        bg = pygame.image.load("images/clearbg.png") # победа
                        won = True
                        print('e')

                    hand.add_card(card)

                hand.show()
                draggable_objects = [(card, card.img) for card in hand.get_cards()]

                show_bito_button = False
                client_socket.send(f"CHANGE_STATUS&CLEAR_PG;{len(hand.cards)};{deck.encode()}".encode("utf-8"))
            elif event.type == pygame.MOUSEBUTTONDOWN and 15 <= event.pos[0] <= 165 and 483 <= event.pos[1] <= 557 and show_take_button:
                show_take_button = False
                lst = []
                for card in [i[0] for i in playground.convert_to_cards_and_draggable()]:
                    lst.append((card, card.img))
                    hand.add_card(card)

                for i in draggable_objects:
                    if i[0] not in [j[0] for j in lst]:
                        lst.append(i)

                draggable_objects = lst.copy()
                lst.clear()

                hand.show()
                playground = Playground()
                client_socket.send(f"&CLEAR_PG;{len(hand.cards)};{deck.encode()}".encode("utf-8"))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for pare in draggable_objects:
                    card, obj = pare
                    if playground.contains(card):
                        continue
                    if obj.rect.collidepoint(event.pos):
                        obj.is_dragging = True
                        offset_x, offset_y = obj.rect.x - event.pos[0], obj.rect.y - event.pos[1]
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for pare in draggable_objects:
                    card, obj = pare
                    if playground.contains(card):
                        continue
                    cell = playground.validate_move(obj.rect.topleft, obj.rect.bottomright)
                    if cell:
                        res = cell.set_card(card, status)

                        if not res:
                            obj.rect.x = card.x
                            obj.rect.y = card.y
                        else:
                            if len(res.split("&")) == 2:
                                command = res.split("&")[-1]

                                if command == "CHANGE_STATUS":
                                    show_take_button = False
                                    status = "1"

                            hand.delete_card(card)
                            playground = Playground(res)
                            hand.show()
                            if playground.can_end_move():
                                if status == "0":
                                    show_take_button = False
                            else:
                                if status == "1":
                                    show_bito_button = False


                            client_socket.send((res + f";{len(hand.cards)};{deck.encode()}").encode("utf-8"))
                    else:
                        obj.rect.x = card.x
                        obj.rect.y = card.y
                    obj.is_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                for pare in draggable_objects:
                    card, obj = pare
                    if playground.contains(card):
                        continue
                    if obj.is_dragging:
                        obj.rect.x = event.pos[0] + offset_x
                        obj.rect.y = event.pos[1] + offset_y

        for pare in draggable_objects:
            _, obj = pare
            obj.draw(message_screen)

        pygame.display.flip()

        clock.tick(60)

# Подключение к серверу
def connect_to_server():
    global connect_to_server_pressed, input_ip_text

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = (input_ip_text, 5555)

    client_socket.connect(server_address)
    print("Подключение к серверу установлено")

    message = client_socket.recv(1024).decode()
    print(message)

    message_queue.put('карты КЛИЕНТА')

    ip, port = server_address
    add_client(ip, port)

    client_socket.close()


pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

window_size = (600, 700)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Durak Online")

running = True
once = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if create_server_button.collidepoint(event.pos) and not create_server_pressed:
                create_server_pressed = True
                conn = http.client.HTTPConnection("ifconfig.me")
                conn.request("GET", "/ip")
                ip = str(conn.getresponse().read())[2:-1]
                text_your_ip = font.render(f"Ждём подключения...", True, BLACK)
                threading.Thread(target=create_server).start()

            if connect_to_server_button.collidepoint(event.pos) and not connect_to_server_pressed and len(
                    input_ip_text):
                connect_to_server_pressed = True
                threading.Thread(target=connect_to_server).start()

            if input_ip_rect.collidepoint(event.pos):
                input_ip_active = True
            else:
                input_ip_active = False

        if event.type == pygame.MOUSEBUTTONUP:
            create_server_pressed = False
            connect_to_server_pressed = False

        if event.type == pygame.KEYDOWN:
            if input_ip_active:
                if event.key == pygame.K_RETURN:
                    input_ip_active = False
                    threading.Thread(target=connect_to_server).start()
                elif event.key == pygame.K_BACKSPACE and len(input_ip_text) > 0:
                    input_ip_text = input_ip_text[:-1]
                elif event.unicode.isnumeric() or event.unicode == '.':
                    input_ip_text += event.unicode

    current_bg = pygame.image.load('images/start_bg.png')
    screen.blit(current_bg, (0, 0))
    font = pygame.font.Font(None, 36)

    if once:
        create_server_button = pygame.draw.rect(screen, (0, 255, 0), (175, 241, 250, 50))
        connect_to_server_button = pygame.draw.rect(screen, (0, 0, 255), (175, 430, 250, 50))
        text_your_ip = font.render('', True, BLACK)
        once = False
    input_ip_rect = pygame.draw.rect(screen, BLACK, (150, 483, 300, 30), 2)

    text_input_ip = font.render(input_ip_text, True, BLACK)

    screen.blit(text_input_ip, (152, 485))
    screen.blit(text_your_ip, (177, 293))

    pygame.display.flip()

    while not message_queue.empty():
        message = message_queue.get()
        run_window(message)

pygame.quit()
