import random
import config
from agents.agent_setup import create_agents
import json
from datetime import datetime
import os

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

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = os.path.join(log_dir, f"simulation_log_{timestamp}.json")
log_data = {
    "start_time": timestamp,
    "events": []
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
            if dest == current:
                print(f"{agent.name} stayed in {current}")
            else:
                print(f"{agent.name} moved from {current} to {dest}")

        seen = [a for a in state if state[a]["room"] == dest and a != agent.name and not state[a]["killed"]]
        state[agent.name]["perception"].append({"room": dest, "agents_seen": seen})

def run_map_demo():
    agents, _ = create_agents()
    all_rooms = list(rooms.keys())
    state = {
        agent.name: {
            "room": random.choice(all_rooms),
            "killed": False,
            "perception": []
        } for agent in agents
    }

    print("Room Movement Demo\n")
    rounds = 3
    for step in range(rounds):
        show_ship_map(state)
        movement_phase(state, agents)

        log_data["events"].append({
            "step": step,
            "state": {name: {
                "room": data["room"],
                "killed": data["killed"],
                "perception": data["perception"].copy()
            } for name, data in state.items()}
        })

    with open(log_file_path, "w") as f:
        json.dump(log_data, f, indent=2)
    print(f"Simulation results saved to {log_file_path}")

if __name__ == "__main__":
    run_map_demo()

def run_game_round(step, state, agents):
    show_ship_map(state)
    movement_phase(state, agents)

    log_data["events"].append({
        "step": step,
        "state": {name: {
            "room": data["room"],
            "killed": data["killed"],
            "perception": data["perception"].copy()
        } for name, data in state.items()}
    })

def finalize_log():
    with open(log_file_path, "w") as f:
        json.dump(log_data, f, indent=2)
    print(f"Simulation results saved to {log_file_path}")
