import yaml
import datetime
import math
import json
import os # Though try-except is used for file opening

PROGRESS_FILE = "progress.json"

def load_workflow(filepath="workflow.yaml"):
    """
    Opens, reads, and parses the YAML workflow file.
    Returns the parsed workflow data (Python dictionary).
    """
    try:
        with open(filepath, 'r') as file:
            workflow_data = yaml.safe_load(file)
        return workflow_data
    except FileNotFoundError:
        print(f"Error: Workflow file '{filepath}' not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{filepath}': {e}")
        return None

def get_current_day_of_week():
    """
    Gets the current day of the week as a lowercase string.
    (e.g., "monday", "tuesday")
    """
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return days[datetime.datetime.now().weekday()]

def get_current_day_numeric():
    """
    Gets the current day as a numeric string for Block 1.
    (e.g., "day1", "day2", ..., "day7")
    """
    return f"day{datetime.datetime.now().isoweekday()}"

def get_current_week_of_month():
    """
    Calculates the current week of the month.
    Returns a string like "week1", "week2", etc., capped at "week4".
    """
    day_of_month = datetime.datetime.now().day
    week_number = math.ceil(day_of_month / 7)
    # Cap at week4 as per current YAML structure
    return f"week{min(int(week_number), 4)}" # Ensure week_number is int before min()

# --- Progress Functions ---

def load_progress():
    """
    Loads progress from PROGRESS_FILE.
    Returns a dictionary of progress data or an empty dictionary if file not found or error.
    """
    try:
        with open(PROGRESS_FILE, 'r') as f:
            progress_data = json.load(f)
        return progress_data
    except FileNotFoundError:
        return {} # No progress file found, start fresh
    except json.JSONDecodeError:
        print(f"Error: Could not decode {PROGRESS_FILE}. Starting with a fresh session.")
        return {}
    except Exception as e:
        print(f"Error loading progress from {PROGRESS_FILE}: {e}")
        return {}

def save_progress(progress_data):
    """
    Saves progress_data to PROGRESS_FILE.
    """
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress_data, f, indent=4)
    except Exception as e:
        print(f"Error: Could not save progress to {PROGRESS_FILE}: {e}")

# --- Display Functions ---

def display_core_mindset(workflow_data):
    """Displays the core mindset."""
    print("\n=== Core Daily Mindset ===")
    mindset = workflow_data.get('core_mindset')
    if mindset:
        print(mindset)
    else:
        print("Core mindset not defined in workflow.")

def display_daily_blocks(workflow_data, progress_data, current_day_of_week, current_day_numeric, current_week_of_month):
    """
    Displays the daily blocks based on the current day/week,
    marks tasks as complete or pending, and returns a map of displayed tasks.
    """
    print("\n=== Today's Workflow Blocks ===")
    daily_blocks_data = workflow_data.get('daily_blocks', {})

    displayed_tasks_map = []
    task_counter = 1

    # Helper function to add task to map and print
    def process_task(task_id, task_text, details_text=""):
        nonlocal task_counter
        is_complete = progress_data.get(task_id, False)
        prefix = "[x]" if is_complete else "[ ]"
        print(f"{prefix} {task_counter}. {task_text}")
        if details_text:
            # Indent details for readability
            for line in details_text.strip().split('\n'):
                print(f"     {line.strip()}")
        displayed_tasks_map.append({'number': task_counter, 'id': task_id, 'text': task_text})
        task_counter += 1

    # Block 1: Vision & Pitch Refinement
    block1_data = daily_blocks_data.get('block1')
    if block1_data:
        print(f"\n--- {block1_data.get('title', 'Block 1')} ({block1_data.get('duration', 'N/A')}) ---")
        print(f"Win Condition: {block1_data.get('win_condition', 'N/A')}")
        daily_focus_data = block1_data.get('daily_focus', {}).get(current_day_numeric)
        if daily_focus_data and 'id' in daily_focus_data and 'theme' in daily_focus_data:
            process_task(daily_focus_data['id'], daily_focus_data['theme'])
        else:
            print(f"     No specific theme for {current_day_numeric}.")
        print("-" * 40) # Separator after block

    # Block 2: Problem & Vision Validation
    block2_data = daily_blocks_data.get('block2')
    if block2_data:
        print(f"\n--- {block2_data.get('title', 'Block 2')} ({block2_data.get('duration', 'N/A')}) ---")
        print(f"Win Condition: {block2_data.get('win_condition', 'N/A')}")
        if current_day_of_week in ["saturday", "sunday"]:
            print("     No specific activity scheduled for today (weekend).")
        else:
            weekly_activity_data = block2_data.get('weekly_rotation', {}).get(current_day_of_week)
            if weekly_activity_data and 'id' in weekly_activity_data and 'activity' in weekly_activity_data:
                process_task(weekly_activity_data['id'], weekly_activity_data['activity'], weekly_activity_data.get('details', ''))
            else:
                print(f"     No specific activity for {current_day_of_week}.")
        print("-" * 40)

    # Block 3: Talent & Advisor Attraction
    block3_data = daily_blocks_data.get('block3')
    if block3_data:
        print(f"\n--- {block3_data.get('title', 'Block 3')} ({block3_data.get('duration', 'N/A')}) ---")
        print(f"Win Condition: {block3_data.get('win_condition', 'N/A')}")
        if current_day_of_week in ["saturday", "sunday"]:
            print("     No specific activity scheduled for today (weekend).")
        else:
            weekly_activity_data = block3_data.get('weekly_rotation', {}).get(current_day_of_week)
            if weekly_activity_data and 'id' in weekly_activity_data and 'activity' in weekly_activity_data:
                process_task(weekly_activity_data['id'], weekly_activity_data['activity'], weekly_activity_data.get('details', ''))
            else:
                print(f"     No specific activity for {current_day_of_week}.")
        print("-" * 40)

    # Block 4: Community Building & Demand Generation
    block4_data = daily_blocks_data.get('block4')
    if block4_data:
        print(f"\n--- {block4_data.get('title', 'Block 4')} ({block4_data.get('duration', 'N/A')}) ---")
        print(f"Win Condition: {block4_data.get('win_condition', 'N/A')}")
        activities = block4_data.get('activities', {})

        daily_activity_data = activities.get('daily')
        if daily_activity_data and 'id' in daily_activity_data and 'description' in daily_activity_data:
            print("\n  Daily Task:")
            process_task(daily_activity_data['id'], daily_activity_data['description'], daily_activity_data.get('details', ''))

        weekly_show_dont_tell = activities.get('weekly_show_dont_tell')
        if weekly_show_dont_tell:
            print(f"\n  Weekly Reminder: {weekly_show_dont_tell.get('description', 'N/A')}")
            options = weekly_show_dont_tell.get('options')
            if options and isinstance(options, list):
                # print("  Options (choose one or work on one per week):")
                for option_item in options:
                    if isinstance(option_item, dict) and 'id' in option_item and 'text' in option_item:
                        process_task(option_item['id'], option_item['text'])
                    else:
                        print(f"     - Malformed option: {option_item}")
            else:
                print("     No options listed.")

        ongoing_promotion_data = activities.get('ongoing_promotion')
        if ongoing_promotion_data and 'id' in ongoing_promotion_data and 'description' in ongoing_promotion_data:
            print("\n  Ongoing Promotion:")
            process_task(ongoing_promotion_data['id'], ongoing_promotion_data['description'], ongoing_promotion_data.get('details', ''))
        print("-" * 40)

    # Block 5: Funding Preparation & Strategic Thinking
    block5_data = daily_blocks_data.get('block5')
    if block5_data:
        print(f"\n--- {block5_data.get('title', 'Block 5')} ({block5_data.get('duration', 'N/A')}) ---")
        print(f"Win Condition: {block5_data.get('win_condition', 'N/A')}")
        effective_week = current_week_of_month
        monthly_activity_data = None
        if effective_week == "week5" and "week5" not in block5_data.get('monthly_rotation', {}):
            print(f"     No specific activity defined for {effective_week} beyond week 4 in the current plan.")
        else:
            monthly_activity_data = block5_data.get('monthly_rotation', {}).get(effective_week)

        if monthly_activity_data and 'id' in monthly_activity_data and 'activity' in monthly_activity_data:
            process_task(monthly_activity_data['id'], monthly_activity_data['activity'], monthly_activity_data.get('details', ''))
        elif not (effective_week == "week5" and "week5" not in block5_data.get('monthly_rotation', {})): # Avoid double message
             print(f"     No specific activity for {effective_week}.")
        print("-" * 40)

    return displayed_tasks_map

def display_end_of_day_review(workflow_data):
    """Displays the end-of-day review questions."""
    print("\n=== End of Day Review ===")
    review_data = workflow_data.get('end_of_day_review')
    if review_data and 'questions' in review_data:
        for i, question in enumerate(review_data['questions'], 1):
            print(f"{i}. {question}")
    else:
        print("No end-of-day review questions defined.")

def display_key_mindset_reminders(workflow_data):
    """Displays key mindset reminders."""
    reminders_data = workflow_data.get('key_mindset_reminders')
    if reminders_data:
        print(f"\n=== {reminders_data.get('title', 'Key Mindset Reminders')} ===")
        if 'reminders' in reminders_data and isinstance(reminders_data['reminders'], list):
            for reminder in reminders_data['reminders']:
                print(f"- {reminder}")
        else:
            print("No reminders listed.")
    else:
        print("\nKey mindset reminders not defined.")


if __name__ == "__main__":
    workflow_data = load_workflow()
    if not workflow_data:
        print("Exiting: Failed to load workflow.")
        # import sys
        # sys.exit(1)
    else:
        progress_data = load_progress()

        # --- Test code from previous step - REMOVE/COMMENT OUT for this subtask's final test ---
        # print(f"--- Test: Attempting to clean up {PROGRESS_FILE} if it exists ---")
        # try:
        #     os.remove(PROGRESS_FILE)
        #     print(f"--- Test: Removed existing {PROGRESS_FILE} ---")
        # except FileNotFoundError:
        #     print(f"--- Test: {PROGRESS_FILE} did not exist, no removal needed ---")
        # except Exception as e:
        #     print(f"--- Test: Error removing {PROGRESS_FILE}: {e} ---")
        # print(f"--- Test: Loading progress (should be empty or error if removal failed) ---")
        # progress_data_test = load_progress() # Use a different var to not clobber main one
        # print(f"Loaded progress (initial for test): {progress_data_test}")
        # print(f"--- Test: Modifying progress and saving ---")
        # progress_data_test["test_task_id"] = True
        # progress_data_test["block1_day1_theme"] = True # Example of a real task ID
        # save_progress(progress_data_test)
        # print(f"--- Test: Called save_progress with test data ---")
        # print(f"--- Test: Reloading progress immediately after saving for test ---")
        # progress_reloaded_test = load_progress()
        # print(f"Loaded progress (after save & reload for test): {progress_reloaded_test}")
        # # Ensure progress_data for the actual display is the one loaded at the start or reloaded here
        # progress_data = load_progress() # Reload to ensure we use potentially updated file
        # --- End of previous test code ---

        # Initial display
        print(f"Initial progress loaded: {progress_data}")

        current_day_str = get_current_day_of_week()
        current_day_num_str = get_current_day_numeric()
        current_week_str = get_current_week_of_month()

        display_core_mindset(workflow_data)
        displayed_tasks_map = display_daily_blocks(workflow_data, progress_data, current_day_str, current_day_num_str, current_week_str)
        display_end_of_day_review(workflow_data)
        display_key_mindset_reminders(workflow_data)

        # Main interaction loop
        while True:
            print("\n" + "="*50)
            print("Enter task number to toggle completion status.")
            print("Enter 'r' to refresh display (e.g., if you manually edit progress.json).")
            print("Enter 'q' to quit.")
            user_input = input("Your choice: ").strip()

            if user_input.lower() == 'q':
                print("Exiting planner. Your progress has been saved.")
                # Progress is already saved after each toggle, so just break
                break

            if user_input.lower() == 'r':
                progress_data = load_progress() # Reload progress
                print("\n" + "="*50 + "\n")
                print("Refreshing display with latest progress...")
                display_core_mindset(workflow_data)
                displayed_tasks_map = display_daily_blocks(workflow_data, progress_data, current_day_str, current_day_num_str, current_week_str)
                display_end_of_day_review(workflow_data)
                display_key_mindset_reminders(workflow_data)
                continue

            if not user_input.isdigit():
                print("Invalid input. Please enter a number, 'r', or 'q'.")
                continue

            task_number = int(user_input)
            selected_task = next((task for task in displayed_tasks_map if task['number'] == task_number), None)

            if not selected_task:
                print(f"Invalid task number: {task_number}. Please choose from the list above.")
                continue

            # Toggle Task Status
            task_id = selected_task['id']
            current_status = progress_data.get(task_id, False)
            progress_data[task_id] = not current_status
            save_progress(progress_data)
            print(f"Task '{selected_task['text'][:50]}...' marked as {'DONE' if not current_status else 'PENDING'}.")

            # Re-display (or at least the blocks part)
            # For simplicity, re-displaying blocks, review, and reminders. Core mindset is less critical for re-display.
            print("\n" + "="*50 + "\n")
            print("Updating display...")
            # display_core_mindset(workflow_data) # Optional: re-display core mindset
            displayed_tasks_map = display_daily_blocks(workflow_data, progress_data, current_day_str, current_day_num_str, current_week_str)
            display_end_of_day_review(workflow_data) # Good to see this with updated tasks
            display_key_mindset_reminders(workflow_data) # Also good to keep visible
