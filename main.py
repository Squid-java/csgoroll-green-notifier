import asyncio
import websockets
import json
import requests

# Discord webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# CSGORoll WebSocket URL (can change over time; check CSGORoll dev tools for updates)
CSGOROLL_WS = "wss://api.csgoroll.com/graphql"

# GraphQL subscription message to listen to roulette results
SUBSCRIPTION_MSG = {
    "id": "1",
    "type": "start",
    "payload": {
        "variables": {},
        "extensions": {},
        "operationName": None,
        "query": """
            subscription {
                rouletteSpin {
                    id
                    status
                    result
                    color
                }
            }
        """
    }
}

# Track green streaks
green_streak = 0

async def send_discord_message(message):
    data = {"content": message}
    requests.post(WEBHOOK_URL, json=data)

async def listen_to_roulette():
    global green_streak

    async with websockets.connect(CSGOROLL_WS, extra_headers={"Sec-WebSocket-Protocol": "graphql-ws"}) as ws:
        # Initialize the GraphQL connection
        await ws.send(json.dumps({"type": "connection_init"}))
        await ws.recv()  # Acknowledge

        # Subscribe to roulette spins
        await ws.send(json.dumps(SUBSCRIPTION_MSG))

        while True:
            try:
                response = await ws.recv()
                data = json.loads(response)
                if data.get("type") == "data":
                    spin_data = data["payload"]["data"]["rouletteSpin"]
                    color = spin_data["color"]

                    if color == "green":
                        green_streak += 1
                        print(f"Green streak: {green_streak}")
                        if green_streak == 2:
                            await send_discord_message("🟢🟢 DOUBLE GREEN HIT ON CSGOROLL!")
                    else:
                        green_streak = 0
            except Exception as e:
                print(f"Error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)
                break  # reconnect

async def main():
    while True:
        await listen_to_roulette()

if __name__ == "__main__":
    asyncio.run(main())
