import yaml
import datetime
import math

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

# --- Display Functions ---

def display_core_mindset(workflow_data):
    """Displays the core mindset."""
    print("\n=== Core Daily Mindset ===")
    mindset = workflow_data.get('core_mindset')
    if mindset:
        print(mindset)
    else:
        print("Core mindset not defined in workflow.")

def display_daily_blocks(workflow_data, current_day_of_week, current_day_numeric, current_week_of_month):
    """Displays the daily blocks based on the current day/week."""
    print("\n=== Today's Workflow Blocks ===")
    daily_blocks = workflow_data.get('daily_blocks', {})

    # Block 1: Vision & Pitch Refinement
    block1_data = daily_blocks.get('block1')
    if block1_data:
        print(f"\n--- {block1_data.get('title', 'Block 1')} ({block1_data.get('duration', 'N/A')}) ---")
        daily_focus = block1_data.get('daily_focus', {}).get(current_day_numeric)
        if daily_focus and 'theme' in daily_focus:
            print(f"Focus: {daily_focus['theme']}")
        else:
            print(f"Focus: No specific theme for {current_day_numeric}.")
        print(f"Win Condition: {block1_data.get('win_condition', 'N/A')}")

    # Block 2: Problem & Vision Validation
    block2_data = daily_blocks.get('block2')
    if block2_data:
        print(f"\n--- {block2_data.get('title', 'Block 2')} ({block2_data.get('duration', 'N/A')}) ---")
        if current_day_of_week in ["saturday", "sunday"]:
            print("Activity: No specific activity scheduled for today (weekend).")
        else:
            weekly_activity = block2_data.get('weekly_rotation', {}).get(current_day_of_week)
            if weekly_activity:
                print(f"Activity: {weekly_activity.get('activity', 'N/A')}")
                print(f"Details:\n{weekly_activity.get('details', 'N/A')}")
            else:
                print(f"Activity: No specific activity for {current_day_of_week}.")
        print(f"Win Condition: {block2_data.get('win_condition', 'N/A')}")

    # Block 3: Talent & Advisor Attraction
    block3_data = daily_blocks.get('block3')
    if block3_data:
        print(f"\n--- {block3_data.get('title', 'Block 3')} ({block3_data.get('duration', 'N/A')}) ---")
        if current_day_of_week in ["saturday", "sunday"]:
            print("Activity: No specific activity scheduled for today (weekend).")
        else:
            weekly_activity = block3_data.get('weekly_rotation', {}).get(current_day_of_week)
            if weekly_activity:
                print(f"Activity: {weekly_activity.get('activity', 'N/A')}")
                print(f"Details:\n{weekly_activity.get('details', 'N/A')}")
            else:
                print(f"Activity: No specific activity for {current_day_of_week}.")
        print(f"Win Condition: {block3_data.get('win_condition', 'N/A')}")

    # Block 4: Community Building & Demand Generation
    block4_data = daily_blocks.get('block4')
    if block4_data:
        print(f"\n--- {block4_data.get('title', 'Block 4')} ({block4_data.get('duration', 'N/A')}) ---")
        activities = block4_data.get('activities', {})

        daily_activity = activities.get('daily')
        if daily_activity:
            print(f"\nDaily Task: {daily_activity.get('description', 'N/A')}")
            print(f"Details:\n{daily_activity.get('details', 'N/A')}")

        weekly_show_dont_tell = activities.get('weekly_show_dont_tell')
        if weekly_show_dont_tell:
            print(f"\nWeekly Reminder: {weekly_show_dont_tell.get('description', 'N/A')}")
            options = weekly_show_dont_tell.get('options')
            if options and isinstance(options, list):
                print("Options (choose one or work on one per week):")
                for option in options:
                    print(f"  - {option}")
            else:
                print("  No options listed.")

        ongoing_promotion = activities.get('ongoing_promotion')
        if ongoing_promotion:
            print(f"\nOngoing: {ongoing_promotion.get('description', 'N/A')}")
            print(f"Details: {ongoing_promotion.get('details', 'N/A')}")

        print(f"\nWin Condition: {block4_data.get('win_condition', 'N/A')}")

    # Block 5: Funding Preparation & Strategic Thinking
    block5_data = daily_blocks.get('block5')
    if block5_data:
        print(f"\n--- {block5_data.get('title', 'Block 5')} ({block5_data.get('duration', 'N/A')}) ---")
        # If current_week_of_month is "week5", default to "week4" as per YAML structure or handle as "no specific task"
        effective_week = current_week_of_month
        if effective_week == "week5" and "week5" not in block5_data.get('monthly_rotation', {}):
            # Option 1: Default to week4
            # effective_week = "week4"
            # print(f"Focus: (No specific task for Week 5, showing Week 4 or general reminder if available)")
            # Option 2: State no specific task beyond week 4
            print(f"Focus: No specific activity defined for {effective_week} beyond week 4 in the current plan.")
            monthly_activity = None # Ensure it doesn't try to fetch
        else:
            monthly_activity = block5_data.get('monthly_rotation', {}).get(effective_week)

        if monthly_activity: # Check if monthly_activity was found/set
            print(f"Focus: {monthly_activity.get('activity', 'N/A')}")
            print(f"Details:\n{monthly_activity.get('details', 'N/A')}")
        elif effective_week != "week5": # Avoid double "no activity" message if it was already week5
             print(f"Focus: No specific activity for {effective_week}.")
        print(f"Win Condition: {block5_data.get('win_condition', 'N/A')}")


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
    workflow = load_workflow()
    if not workflow:
        print("Exiting: Failed to load workflow.")
        # Consider exiting the script if workflow loading fails
        # import sys
        # sys.exit(1)
    else:
        current_day_str = get_current_day_of_week()
        current_day_num_str = get_current_day_numeric()
        current_week_str = get_current_week_of_month()

        # print(f"Debug: Day of week: {current_day_str}, Numeric day: {current_day_num_str}, Week of month: {current_week_str}")

        display_core_mindset(workflow)
        display_daily_blocks(workflow, current_day_str, current_day_num_str, current_week_str)
        display_end_of_day_review(workflow)
        display_key_mindset_reminders(workflow)
