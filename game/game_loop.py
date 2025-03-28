import random

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

def movement_phase(state):
    for agent in state:
        current = state[agent]["room"]
        adj = rooms[current]
        print(f"\n{agent} is in {current}. Adjacent rooms: {', '.join(adj)}")
        dest = input(f"Enter destination for {agent} (or type 'skip'): ").strip()
        if dest in adj:
            state[agent]["room"] = dest
        elif dest.lower() == "skip":
            continue
        else:
            print("Invalid choice. Staying in current room.")

def run_map_demo():
    state = {
        "Agent_1": {"room": "MedBay"},
        "Agent_2": {"room": "MedBay"},
        "Agent_3": {"room": "Admin"},
        "Agent_4": {"room": "Storage"},
        "Agent_5": {"room": "Weapons"}
    }
    print("Room Movement Demo\n")
    rounds = 2
    for _ in range(rounds):
        show_ship_map(state)
        movement_phase(state)

if __name__ == "__main__":
    run_map_demo()
