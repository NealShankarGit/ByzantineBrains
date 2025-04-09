from core.simulation import run_simulation, get_results

if __name__ == "__main__":
    agents_state = run_simulation()
    trust_scores, memory_streams = get_results(agents_state)

    print("\n--- Final Trust Scores ---")
    for name, scores in trust_scores.items():
        print(f"{name}: {scores}")

    print("\n--- Memory Streams ---")
    for name, stream in memory_streams.items():
        print(f"\n{name}:")
        for entry in stream:
            print(f"  Round {entry['round']} - Room: {entry['perception'].get('room')} - Msg: {entry['message']}")
