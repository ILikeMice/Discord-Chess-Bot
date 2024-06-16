from PIL import Image
import discord 
import json
from discord.ext import commands 
import os
from discord import app_commands 
import time
from stockfish import Stockfish 

BOT_TOKEN = "your_bot_token"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
stockfish = Stockfish(path="stockfish executeable path here")

def readdata():
    with open("data.json", "r") as infile:
        data = json.load(infile)
    return data

def writedata(data):
    with open("data.json", "w") as outfile:
        json.dump(data, outfile, indent=3)


def FEN_to_board(board, FEN):
    currentpos = 0
    currentrow = 0
    for i in FEN:
        if i.isnumeric():
            currentpos += int(i)
            continue
        elif i != "/" and i != " ":
            board[currentrow][currentpos] = i
        currentpos += 1
        if i == "/":
            currentrow += 1
            currentpos = 0
        if i == " ":
            break


def board_to_image(board, uid):
    boardimg = Image.open("./images/board.png").copy()
    for i in range(8):
        for b in range(8):
            if board[i][b] and board[i][b].islower():
                piece = Image.open(f"./images/b{board[i][b]}.png")
                piece.resize((515//8, 515//8))
                boardimg.paste(piece, (((515//8)*b), (515//8)*i), piece)
            elif board[i][b] and board[i][b].isupper():
                piece = Image.open(f"./images/w{board[i][b].lower()}.png")
                piece.resize((515//8, 515//8))
                boardimg.paste(piece, (((515//8)*b), (515//8)*i), piece)
    boardimg.save(f"/home/ilikemice/Documents/Coding/Python/Discord-chess-bot/outputs/{uid}.png",)




@bot.tree.command(name="newgame", description="Start a new game against the bot")
@app_commands.describe(move="Your starting move, e.g e2e3")
async def newgame(interaction: discord.Interaction, move: str):
    uid = str(interaction.user.id)
    data = readdata()
    board = [
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0]
    ]
    FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w"
    if not uid in data["Users"]:
        data["Users"][uid] = {"currentpos": []}
    
    data["Users"][uid]["currentpos"] = FEN
    writedata(data)

    stockfish.set_fen_position(FEN)
    
    if stockfish.is_move_correct(move):
        stockfish.make_moves_from_current_position([move])
        bestmove = stockfish.get_best_move()
        stockfish.make_moves_from_current_position([bestmove])
    else:
        await interaction.response.send_message(f"{move} is an invalid move!")
        return
    
    FEN = stockfish.get_fen_position()

    data["Users"][uid]["currentpos"] = FEN
    writedata(data)

    FEN_to_board(board,FEN)
    board_to_image(board, uid)
    
    while not os.path.exists(f"./outputs/{uid}.png"):
        time.sleep(1)

    if os.path.isfile(f"./outputs/{uid}.png"):
        file = discord.File(f"./outputs/{uid}.png", f"{uid}.png")
        embed = discord.Embed(title=f"***I play {bestmove} Your turn!***")
        embed.set_image(url=f"attachment://{uid}.png")

        await interaction.response.send_message(file=file, embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("Error! Please try again!")


@bot.tree.command(name="move")
async def move(interaction: discord.Interaction, move: str):
    uid = str(interaction.user.id)
    data = readdata()
    if uid in data["Users"]:
        FEN = data["Users"][uid]["currentpos"]
    else:
        await interaction.response.send_message(f"You need to start a game with /newgame first!", ephemeral=True)
        return

    stockfish.set_fen_position(FEN)
    
    if stockfish.is_move_correct(move):
        stockfish.make_moves_from_current_position([move])
        bestmove = stockfish.get_best_move()
        if bestmove == None:
            won = True
        stockfish.make_moves_from_current_position([bestmove])
        FEN = stockfish.get_fen_position()
        
        board = [
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0]
        ]
        
        data["Users"][uid]["currentpos"] = FEN
        writedata(data)

        FEN_to_board(board,FEN)
        board_to_image(board, uid)

        while not os.path.exists(f"./outputs/{uid}.png"):
            time.sleep(1)

        if os.path.isfile(f"./outputs/{uid}.png"):
            file = discord.File(f"./outputs/{uid}.png", f"{uid}.png")
            embed = discord.Embed(title=f"***I play {bestmove} Your turn!***")
            embed.set_image(url=f"attachment://{uid}.png")
            if won:
                embed.title = "You Won! Good Game!"
            if stockfish.get_best_move() == None:
                embed.title = "I Won! Good game!"
                print(stockfish.get_evaluation())
            await interaction.response.send_message(file=file, embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Error! Please try again!")        
    else:
        await interaction.response.send_message(f"{move} is an invalid move!")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

bot.run(BOT_TOKEN)
