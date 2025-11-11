import asyncio
import websockets
import random
from enum import Enum
import os

PORT = int(os.environ.get("PORT", 41670))  # Railway assigns the port

clients = set()
used_colors = set()

class Client:
    def __init__(self, websocket, color):
        self.websocket = websocket
        self.color = color
        
    def __eq__(self, other):
        return isinstance(other, Client) and self.websocket.remote_address == other.websocket.remote_address

    def __hash__(self):
        return hash(self.websocket.remote_address)

class SEND_CODES(Enum):
    ADD = "ADDP" # code to tell client to add a player
    JOIN = "ADDM" # tells the client to add a a player that is an owner, that is itself
    CHANGE_TRANSFORM = "CTR" # sends updated transform of player
    CHANGE_ANIMATOR_VALUE = "CAV" # code to say your changing a value in the animator
    CHANGE_NETWORK_FLOAT = "CNF" # changes network float
    PLAY_AUDIO_SOURCE = "PAS"
    STOP_AUDIO_SOURCE = "SAS"
    
    """
    FORMAT:
    
    AAAA <- Send Code
    B <- Color
    """
    
class COLORS(Enum):
    RED = "0"
    ORANGE = "1"
    YELLOW = "2"
    GREEN = "3"
    BLUE = "4"
    PURPLE = "5"
    

async def handle_client(websocket):
    
    # creates a random color for clients - should be unique unless there's to many clients.
    if used_colors == set(COLORS):
        used_colors.clear()
    col = random.choice(list(set(COLORS) - used_colors)) # color is a random one that hasn't been used yet
    me = Client(websocket, col)
    used_colors.add(col)
    
    clients.add(me)
    print(f"New client connected, color:{me.color}")
    
    try:
        for client in clients:
            if client != me:
                # tells the new player about all the clients it missed and says to add it
                await me.websocket.send(f"{SEND_CODES.ADD.value}{client.color.value}")
                
                # tells all the other players to add this new guy
                await client.websocket.send(f"{SEND_CODES.ADD.value}{me.color.value}")


        # tells the new player to add itself
        await me.websocket.send(f"{SEND_CODES.JOIN.value}{me.color.value}")
        await me.websocket.send("Welcome player, " + str(len(clients)))
        
        async for message in me.websocket:
            for client in clients:
                if client != me:
                    await client.websocket.send(message)
    except websockets.ConnectionClosed:
        print("Client disconnected.")
    finally:
        print(f"Client Left {me.websocket.remote_address}")
        clients.remove(me)

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 41670):
        print("WebSocket server running on port 41670")
        await asyncio.Future()
        
asyncio.run(main())
