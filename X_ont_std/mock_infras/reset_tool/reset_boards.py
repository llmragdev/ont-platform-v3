import os
import sqlite3
import argparse
from datetime import datetime

RESET_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_INFRAS_DIR = os.path.dirname(RESET_TOOL_DIR)
S1_DB_PATH = os.path.join(MOCK_INFRAS_DIR, "s1_customer_board", "s1_customer_board.db")
S2_DB_PATH = os.path.join(MOCK_INFRAS_DIR, "s2_factory_board", "s2_factory_board.db")

def reset_scenario_1(post_id="q-001", reset_all=False):
    """Resets comments in the Customer Board (Scenario 1) database.
    Note: The primary posts themselves are NEVER deleted.
    Only comments are cleared, and the initial seed comment by '시스템봇' is preserved for reference.
    """
    if not os.path.exists(S1_DB_PATH):
        print(f"[-] Customer Board database not found at: {S1_DB_PATH}")
        return

    try:
        conn = sqlite3.connect(S1_DB_PATH)
        cursor = conn.cursor()
        
        if reset_all:
            # Delete all comments except the initial seed comment by '시스템봇'
            cursor.execute("DELETE FROM comments WHERE author != '시스템봇'")
            deleted = cursor.rowcount
            print(f"[+] Deleted {deleted} workflow comments from Customer Board (Preserved seed comments).")
        else:
            # Delete comments for a specific post_id except seed comments
            cursor.execute("DELETE FROM comments WHERE post_id = ? AND author != '시스템봇'", (post_id,))
            deleted = cursor.rowcount
            print(f"[+] Deleted {deleted} workflow comments for post '{post_id}' (Preserved seed comments).")
            
        conn.commit()
        conn.close()
        print("[+] Scenario 1 reset successful!")
    except Exception as e:
        print(f"[-] Error resetting Scenario 1: {e}")

def reset_scenario_2(event_id="fe-001", reset_all=False):
    """Resets comments, maintenance tasks, and event statuses in the Factory Board (Scenario 2) database.
    Note: The primary factory events themselves are NEVER deleted.
    Only generated responses (excluding the seed response 'fr-seed') and maintenance tasks are cleared.
    """
    if not os.path.exists(S2_DB_PATH):
        print(f"[-] Factory Board database not found at: {S2_DB_PATH}")
        return

    try:
        conn = sqlite3.connect(S2_DB_PATH)
        cursor = conn.cursor()
        
        if reset_all:
            # Delete all responses except the initial seed 'fr-seed'
            cursor.execute("DELETE FROM factory_responses WHERE id != 'fr-seed'")
            res_deleted = cursor.rowcount
            cursor.execute("DELETE FROM maintenance_tasks")
            task_deleted = cursor.rowcount
            
            # Reset all events to 'open'
            cursor.execute("UPDATE factory_events SET status = 'open'")
            updated = cursor.rowcount
            
            print(f"[+] Deleted all {res_deleted} responses (preserved 'fr-seed') and {task_deleted} maintenance tasks.")
            print(f"[+] Reset status to 'open' for all {updated} events.")
        else:
            # Delete responses (excluding seed) and tasks for a specific event
            cursor.execute("DELETE FROM factory_responses WHERE event_id = ? AND id != 'fr-seed'", (event_id,))
            res_deleted = cursor.rowcount
            cursor.execute("DELETE FROM maintenance_tasks WHERE factory_event_id = ?", (event_id,))
            task_deleted = cursor.rowcount
            
            # Reset status of this specific event to 'open'
            cursor.execute("UPDATE factory_events SET status = 'open' WHERE id = ?", (event_id,))
            updated = cursor.rowcount
            
            print(f"[+] Deleted {res_deleted} responses and {task_deleted} tasks for event '{event_id}'.")
            if updated > 0:
                print(f"[+] Reset status of event '{event_id}' back to 'open'.")
            else:
                print(f"[-] Event '{event_id}' not found or already open.")
                
        conn.commit()
        conn.close()
        print("[+] Scenario 2 reset successful!")
    except Exception as e:
        print(f"[-] Error resetting Scenario 2: {e}")

def interactive_menu():
    print("=" * 60)
    print("        Ontology Platform Mock Boards Reset Utility")
    print("=" * 60)
    print("1. Scenario 1 (Customer Auto-reply) Reset")
    print("   - Clear workflow replies for post 'q-001' (Preserves post & '시스템봇' seed comment)")
    print("2. Scenario 1 (Customer Auto-reply) Complete Reset")
    print("   - Clear all workflow replies (Preserves posts & '시스템봇' seed comments)")
    print("3. Scenario 2 (Factory Repeated Fault) Reset")
    print("   - Clear replies/tasks & set status back to 'open' for event 'fe-001' (Preserves event & 'fr-seed' comment)")
    print("4. Scenario 2 (Factory Repeated Fault) Complete Reset")
    print("   - Clear all workflow replies/tasks & set all event statuses to 'open' (Preserves events & 'fr-seed' comment)")
    print("5. Reset Both Scenarios (Default seed data 'q-001' & 'fe-001')")
    print("6. Reset Both Scenarios Completely (All data - Preserves seed comments/posts)")
    print("q. Exit")
    print("-" * 60)
    
    choice = input("Select an option (1-6, q): ").strip().lower()
    
    if choice == "1":
        reset_scenario_1(post_id="q-001")
    elif choice == "2":
        reset_scenario_1(reset_all=True)
    elif choice == "3":
        reset_scenario_2(event_id="fe-001")
    elif choice == "4":
        reset_scenario_2(reset_all=True)
    elif choice == "5":
        reset_scenario_1(post_id="q-001")
        reset_scenario_2(event_id="fe-001")
    elif choice == "6":
        reset_scenario_1(reset_all=True)
        reset_scenario_2(reset_all=True)
    elif choice == "q":
        print("Exiting reset utility.")
    else:
        print("Invalid option. Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset Mock Board databases for Scenario 1 and 2 testing.")
    parser.add_argument("--s1", action="store_true", help="Reset Scenario 1 default post ('q-001')")
    parser.add_argument("--s1-all", action="store_true", help="Reset all Scenario 1 comments")
    parser.add_argument("--s1-id", type=str, default="q-001", help="Specify post ID to reset in Scenario 1")
    
    parser.add_argument("--s2", action="store_true", help="Reset Scenario 2 default event ('fe-001')")
    parser.add_argument("--s2-all", action="store_true", help="Reset all Scenario 2 responses and tasks")
    parser.add_argument("--s2-id", type=str, default="fe-001", help="Specify event ID to reset in Scenario 2")
    
    parser.add_argument("--all", action="store_true", help="Reset all data in both boards")
    
    args = parser.parse_args()
    
    # If no arguments are provided, open interactive menu
    if not (args.s1 or args.s1_all or args.s2 or args.s2_all or args.all):
        interactive_menu()
    else:
        if args.all:
            reset_scenario_1(reset_all=True)
            reset_scenario_2(reset_all=True)
        else:
            if args.s1_all:
                reset_scenario_1(reset_all=True)
            elif args.s1:
                reset_scenario_1(post_id=args.s1_id)
                
            if args.s2_all:
                reset_scenario_2(reset_all=True)
            elif args.s2:
                reset_scenario_2(event_id=args.s2_id)
