import random
import config
from agents.agent_setup import create_agents
import json
from datetime import datetime
import os
import platform
def clear_terminal():
    os.system("cls" if platform.system() == "Windows" else "clear")

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

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = os.path.join(log_dir, f"simulation_log_{timestamp}.json")
log_data = {
    "start_time": timestamp,
    "events": []
}

def show_ship_map(state, agents):
    clear_terminal()
    mapping = {room: [] for room in rooms}
    bodies = {room: [] for room in rooms}
    for agent, info in state.items():
        if not info.get("killed", False):
            agent_obj = next((a for a in agents if a.name == agent), None)
            mapping[info["room"]].append(f"{agent_obj.color}{agent}" if agent_obj else agent)
        elif info.get("room_body"):
            agent_obj = next((a for a in agents if a.name == agent), None)
            color = agent_obj.color if agent_obj else ""
            bodies[info["room_body"]].append(f"💀{color}{agent}")

    def fmt(room):
        entries = mapping.get(room, []) + bodies.get(room, [])
        return f"[{room}]" if not entries else f"[{room}: {' '.join(entries)}]"

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

def movement_phase(state, agents, agents_state):
    for agent in agents:
        if state[agent.name]["killed"]:
            continue
        current = state[agent.name]["room"]
        adj = rooms[current]
        dest = agent.choose_room(current, adj, state)

        if dest.startswith("Kill "):
            target_name = dest.split(" ")[1]
            if target_name in state and state[target_name]["room"] == current and not state[target_name]["killed"]:
                state[target_name]["killed"] = True
                state[target_name]["room_body"] = current
                print(f"{agent.name} killed {target_name} in {current}")
            # Allow the agent to still choose to move after a kill
            move_dest = agent.choose_room(current, rooms[current], state)
            if move_dest in rooms[current]:
                state[agent.name]["room"] = move_dest
                print(f"{agent.name} moved from {current} to {move_dest}")
            else:
                print(f"{agent.name} stayed in {current}")
        else:
            state[agent.name]["room"] = dest
            if dest == current:
                print(f"{agent.name} stayed in {current}")
            else:
                print(f"{agent.name} moved from {current} to {dest}")

        seen = [a for a in state if state[a]["room"] == dest and a != agent.name and not state[a]["killed"]]
        room = state[agent.name]["room"]  # current location after moving

        seen_bodies = [
            a for a in state
            if state[a].get("killed") and state[a].get("room_body") == room
        ]

        state[agent.name]["perception"].append({
            "room": room,
            "agents_seen": seen,
            "bodies_seen": seen_bodies
        })

        if seen_bodies and not state[agent.name]["killed"]:
            if agent.__class__.__name__ == "HonestAgent":
                agent_msg = f"I just found the body of {seen_bodies[0]} in {room}! Reporting it now!"
                print(f"{agent.name} reports: {agent_msg}")
                agents_state[agent.name]["messages"].append(agent_msg)

        if agent.__class__.__name__ == "HonestAgent":
            if not state[agent.name]["task_done"]:
                if state[agent.name]["room"] == state[agent.name]["task_room"]:
                    if state[agent.name]["doing_task"]:
                        state[agent.name]["task_done"] = True
                        print(f"{agent.name} completed their task in {state[agent.name]['room']}.")
                    else:
                        state[agent.name]["doing_task"] = True
                        print(f"{agent.name} started task in {state[agent.name]['room']}.")
                else:
                    state[agent.name]["doing_task"] = False

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
        show_ship_map(state, agents)
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

def run_game_round(step, state, agents, agents_state):
    movement_phase(state, agents, agents_state)
    show_ship_map(state, agents)

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
