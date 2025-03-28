import random
import config
from agents.agent_setup import create_agents

rooms = {
    "Cafeteria": ["Weapons", "Navigation", "Storage", "Admin", "MedBay", "Upper Engine"],
    "Weapons": ["Cafeteria", "O2"],
    "Navigation": ["O2", "Shields"],
    "O2": ["Weapons", "Navigation", "Cafeteria"],
    "Shields": ["Navigation", "Communications", "Storage"],
    "Communications": ["Shields"],
    "Admin": ["Cafeteria", "Storage"],
    "Storage": ["Admin", "Shields", "Electrical", "Lower Engine", "Cafeteria"],
    "Electrical": ["Storage", "Lower Engine"],
    "Lower Engine": ["Storage", "Electrical", "Security", "Reactor"],
    "Security": ["Lower Engine", "Upper Engine", "Reactor"],
    "Reactor": ["Security", "Upper Engine", "Lower Engine"],
    "Upper Engine": ["Reactor", "Security", "MedBay", "Cafeteria"],
    "MedBay": ["Upper Engine", "Cafeteria"]
}

def show_ship_map(state):
    mapping = {room: [] for room in rooms}
    for agent, info in state.items():
        if not info.get("killed", False):
            mapping[info["room"]].append(agent)

    def fmt(room):
        agents = " ".join(mapping.get(room, []))
        return f"[{room}]" if not agents else f"[{room}: {agents}]"

    print("\n--- Ship Map ---\n")
    print(f"{fmt('Upper Engine')}               {fmt('Cafeteria')}              {fmt('Weapons')}")
    print("")
    print(f"{fmt('Reactor')}        {fmt('Security')}       {fmt('MedBay')}        {fmt('O2')}      {fmt('Navigation')}")
    print("")
    print(f"{fmt('Lower Engine')}   {fmt('Electrical')}     {fmt('Storage')}       {fmt('Admin')}   {fmt('Shields')}")
    print("")
    print(f"{' ' * 55}{fmt('Communications')}")

    print("\nPlayer Locations:")
    for room, occupants in mapping.items():
        if occupants:
            print(f"{room}: {' '.join(occupants)}")

def movement_phase(state, agents):
    for agent in agents:
        current = state[agent.name]["room"]
        adj = rooms[current]
        dest = agent.choose_room(current, adj, state)

        if dest.startswith("Kill "):
            target_name = dest.split(" ")[1]
            if target_name in state and state[target_name]["room"] == current:
                state[target_name]["killed"] = True
                print(f"{target_name} has been killed by {agent.name} in {current}.")
                continue
        else:
            state[agent.name]["room"] = dest
            print(f"{agent.name} moved from {current} to {dest}")

def run_map_demo():
    agents, _ = create_agents()
    all_rooms = list(rooms.keys())
    state = {agent.name: {"room": random.choice(all_rooms), "killed": False} for agent in agents}

    print("Room Movement Demo\n")
    rounds = 3
    for _ in range(rounds):
        show_ship_map(state)
        movement_phase(state, agents)

if __name__ == "__main__":
    run_map_demo()
