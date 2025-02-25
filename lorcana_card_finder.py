# -*- coding: utf-8 -*-
"""
@author: Ervan Renault
"""
import json
import logging
import re
import requests
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
import socketserver
import threading
import http.server
import webbrowser

import time
import os


PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))  # Serve files from the script's folder



# Logging configuration
logging.basicConfig(
    filename='logs.log', 
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



def start_server():
    """Starts an HTTP server in a separate thread."""
    os.chdir(DIRECTORY)  # Change directory to serve index.html properly
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()  # Keep server running

# Start the server in a background thread
threading.Thread(target=start_server, daemon=True).start()

# Allow some time for the server to start
time.sleep(1)

# 🔹 Open the `index.html` file in the default web browser
webbrowser.open(f"http://localhost:{PORT}/index.html")

# Now, continue with your main script (modify index.html, etc.)
print("Server is running. You can now fetch files via http://localhost:8000/index.html")


def update_css_class(file_path, class_name, new_styles):
    try:
        with open(file_path, 'r') as file:
            css_content = file.read()
    except FileNotFoundError:
        css_content = ""

    class_pattern = re.compile(rf'\.{re.escape(class_name)}\s*\{{[^}}]*\}}', re.DOTALL)
    new_class_definition = f".{class_name} {{\n" + "\n".join(f"    {style}: {value};" for style, value in new_styles.items()) + "\n}\n"

    if class_pattern.search(css_content):
        css_content = class_pattern.sub(new_class_definition, css_content)
    else:
        css_content += "\n" + new_class_definition

    with open(file_path, 'w') as file:
        file.write(css_content)

    trigger_browser_refresh()

def write_css_file(url, player_number):
    logging.debug(f'Writing CSS for player {player_number} with URL: {url}')
    class_name = f"player{player_number}"
    new_styles = {
        "background-image": f'url("{url}")',
        "background-repeat": "no-repeat",
        "background-size": "contain",
        "background-position": "center",
        "width": "100%",
        "height": "100%"
    }
    update_css_class("background.css", class_name, new_styles)




# def find_card_image(set_number, card_number, player_number):
#     try:
#         currentCard = None
#         filePath = f"./cardSets/{set_number}.json"
#         with open(filePath, 'r') as file:
#             currentSet = json.load(file)['cards']

#         for card in currentSet:
#             #logging.debug(f'GetNumber:' + card['number'])
#             if str(card.get('number')) == str(card_number):
#              currentCard = card
#              break

#         ##response = requests.get(f"{currentCard.images.full}")
#         ##response.raise_for_status()
#         ##image_large = response.json()["image_uris"]["digital"]["large"]
#         #logging.debug(f'CurrentCard:' + currentCard)
    
#         write_css_file(currentCard.get('images').get('full'), player_number)
        
#     except requests.RequestException as e:
#         logging.debug(f'Failed to fetch card image: {e}')
#         write_css_file("https://api.lorcast.com/v0/cards/1/207", player_number)


def update_html_image(file_path, player_number, image_url):
    try:
        with open(file_path, 'r+') as file:
            html_content = file.read()
    except FileNotFoundError:
        html_content = "<html><body><img id='player1' src='' /><img id='player2' src='' /></body></html>"
    
    # Replace the existing image URL for the specific player
    new_html = re.sub(
        rf'(<img id="player{player_number}" src=")(.*?)(")',  # Capture the src URL for player{player_number}
        rf'\1{image_url}\3',  # Replace it with the new URL
        html_content
    )
    
    print(f"✅ Updated {file_path} with new image for player {player_number}")

    with open(file_path, 'w') as file:
        file.write(new_html)


    # 🔹 Trigger a browser refresh
    trigger_browser_refresh()

    # # Ensure that the modification timestamp is updated after writing to the file
    # os.utime(file_path, None)  # This updates the file's access and modification times
    # print(f"File {file_path} has been updated.")  # Log the file update



# 🔹 Function to Refresh Browser
def trigger_browser_refresh():
    """Creates a dummy file change to force browser refresh."""
    refresh_file = os.path.join(DIRECTORY, "index.html")
    with open(refresh_file, "a") as file:
        file.write(" ")  # Update file with current timestamp
    print("🔄 Triggered browser refresh!")



def find_card_image(set_number, card_number, player_number):
    try:
        with open(f"./cardSets/{set_number}.json", 'r') as file:
            cards = json.load(file)['cards']
            card = next((c for c in cards if str(c.get('number')) == str(card_number)), None)

        if card:
            image_url = card.get('images', {}).get('full', '')
        else:
            raise ValueError("Card not found.")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        logging.debug(f'Error fetching card image: {e}')
        image_url = "https://api.lorcast.com/v0/cards/1/207"  # Default placeholder image

    update_html_image("index.html", player_number, image_url)
    # write_css_file(image_url, player_number)

def find_card_image_by_name(card_name, player_number):
    if not card_name:
        #write_css_file("", player_number)
        return

    try:
        response = requests.get(f"https://api.lorcana-api.com/cards/fetch?search=name={card_name}")
        response.raise_for_status()
        parsed = response.json()
        card_number = str(parsed[0]["Card_Num"])
        set_number = str(parsed[0]["Set_Num"])
        find_card_image(set_number, card_number, player_number)
    except (requests.RequestException, IndexError, KeyError) as e:
        logging.debug(f'Failed to fetch card by name: {e}')
       # write_css_file("https://api.lorcast.com/v0/cards/1/207", player_number)

# Helper function to create labels and entry widgets
def create_label_and_entry(frame, text, x, y):
    label = tk.Label(frame, text=text, fg="#FFD700", bg="#1C3664", font=("Arial", 12, "bold"))
    label.place(x=x, y=y)
    entry = tk.Entry(frame, font=("Arial", 12), width=25)
    entry.place(x=x + 150, y=y)
    return entry

# Function to change button color when mouse enters
def on_enter(e, hover_color):
    e.widget['background'] = hover_color  # Change to golden color on hover

# Function to revert button color when mouse leaves
def on_leave(e, leave_color):
    e.widget['background'] = leave_color # Revert back to the original color

# Updated setup_gui function
def setup_gui():
    window = tk.Tk()
    window.title("Lorcana Card Finder")
    window.iconbitmap('icon.ico')
    window.geometry("1280x800")
    window.configure(bg="#1C3664")

    # Player Frames
    def create_player_frame(parent, player_num):
        frame = tk.Frame(parent, bg="#1C3664", bd=5)
        frame.place(relx=0.01 if player_num == 1 else 0.50, rely=0.02, relwidth=0.48, relheight=0.95)

        # Title labels
        title = tk.Label(frame, text=f"Joueur {player_num}", fg="#FFD700", bg="#1C3664", font=("Comic Sans MS", 16, "bold"))
        title.place(relx=0.4, rely=0.02)

        return frame

    frame_player1 = create_player_frame(window, 1)
    frame_player2 = create_player_frame(window, 2)

    # Create input fields for players
    entry_set1 = create_label_and_entry(frame_player1, "Chapitre", 25, 50)
    entry_card_number1 = create_label_and_entry(frame_player1, "Numéro de carte", 25, 80)
    entry_set2 = create_label_and_entry(frame_player2, "Chapitre", 25, 50)
    entry_card_number2 = create_label_and_entry(frame_player2, "Numéro de carte", 25, 80)

    # Create frames for card decks with scrollbars
    def create_deck_frame(frame):
        deck_frame = tk.Frame(frame, bg="#ffffff")
        deck_frame.place(x=1, y=200, relwidth=1, relheight=0.75)

        canvas = tk.Canvas(deck_frame, bg="#ffffff")
        scrollbar = ttk.Scrollbar(deck_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame

    deck_frame1 = create_deck_frame(frame_player1)
    deck_frame2 = create_deck_frame(frame_player2)

    # Global variables to hold dynamic buttons
    list_of_buttons_player1 = []
    list_of_buttons_player2 = []

    # Callbacks for searching cards and loading deck
    def callback_player1():
        find_card_image(entry_set1.get(), entry_card_number1.get(), 1)

    def callback_player2():
        find_card_image(entry_set2.get(), entry_card_number2.get(), 2)

    def open_card_deck_file(player_number):
        if player_number == 1:
            for button in list_of_buttons_player1:
                button.destroy()
            list_of_buttons_player1.clear()
            parent_frame = deck_frame1
        else:
            for button in list_of_buttons_player2:
                button.destroy()
            list_of_buttons_player2.clear()
            parent_frame = deck_frame2

        card_deck_file = filedialog.askopenfilename(
            title="Select A File", filetypes=(("txt files", ".txt"), ("all files", ".*"))
        )
        if not card_deck_file:
            return

        list_of_cards = np.genfromtxt(card_deck_file, delimiter=";", dtype=str, unpack=True)
        list_of_cards = [re.search(r"\d+\s(.+)", card).group(1) for card in list_of_cards if re.search(r"\d+\s(.+)", card)]

        row_index, col_index = 0, 0
        for card in list_of_cards:
            button = tk.Button(parent_frame, text=card, anchor="w", bd=0,
                               command=lambda x=card, pn=player_number: find_card_image_by_name(x, pn),
                               height=2, width=25, borderwidth=1, bg="#4682B4", font=("Arial", 10))
            button.bind("<Enter>", lambda e: on_enter(e, "#F0E68C"))
            button.bind("<Leave>", lambda e: on_leave(e, "#4682B4"))
            button.grid(row=row_index, column=col_index, sticky="w", padx=2, pady=5)
            if player_number == 1:
                list_of_buttons_player1.append(button)
            else:
                list_of_buttons_player2.append(button)

            col_index += 1
            if col_index == 2:
                row_index += 1
                col_index = 0

    # Buttons for searching and loading deck files
    buttonSearch1 = tk.Button(frame_player1, text="Rechercher carte", command=callback_player1, bg="#4682B4", fg="#ffffff", font=("Arial", 12))
    buttonSearch1.place(x=25, y=110)
    buttonSearch1.bind("<Enter>", lambda e: on_enter(e, "#F0E68C"))
    buttonSearch1.bind("<Leave>", lambda e: on_leave(e, "#4682B4"))
    
    buttonSearch2 = tk.Button(frame_player2, text="Rechercher carte", command=callback_player2, bg="#4682B4", fg="#ffffff", font=("Arial", 12))
    buttonSearch2.place(x=25, y=110)
    buttonSearch2.bind("<Enter>", lambda e: on_enter(e, "#F0E68C"))
    buttonSearch2.bind("<Leave>", lambda e: on_leave(e, "#4682B4"))


    buttonLoad1 = tk.Button(frame_player1, text="Charger un deck", command=lambda: open_card_deck_file(1), bg="#2E0854", fg="#ffffff", font=("Arial", 12))
    buttonLoad1.place(x=25, y=150)
    buttonLoad1.bind("<Enter>", lambda e: on_enter(e, "#F0E68C"))
    buttonLoad1.bind("<Leave>", lambda e: on_leave(e, "#2E0854"))


    buttonLoad2 = tk.Button(frame_player2, text="Charger un deck", command=lambda: open_card_deck_file(2), bg="#2E0854", fg="#ffffff", font=("Arial", 12))
    buttonLoad2.place(x=25, y=150)
    buttonLoad2.bind("<Enter>", lambda e: on_enter(e, "#F0E68C"))
    buttonLoad2.bind("<Leave>", lambda e: on_leave(e, "#2E0854"))

    return window

if __name__ == "__main__":
    list_of_buttons_player1 = []
    list_of_buttons_player2 = []
    window = setup_gui()
    window.mainloop()