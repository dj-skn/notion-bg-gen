import os
import colorama
from colorama import Fore, Style
import inquirer

colorama.init(autoreset=True)  # Automatically reset colors after each print


def get_next_available_filename(base_name, directory):
    """
    Generate the next available file name if the base name exists.

    Args:
        base_name (str): The base file name.
        directory (str): The directory to check for existing files.

    Returns:
        str: The next available file name with an incremented number.
    """
    if not os.path.exists(os.path.join(directory, base_name)):
        return base_name

    name, ext = os.path.splitext(base_name)
    counter = 2

    while os.path.exists(os.path.join(directory, f"{name}-{counter}{ext}")):
        counter += 1

    return f"{name}-{counter}{ext}"


def get_user_input():
    """
    Collects and validates user input for the gradient generator.

    Returns:
        list[dict]: A list of dictionaries containing user inputs for each cover.
    """
    # Print the title
    print(Fore.CYAN + Style.BRIGHT + """
 _   _       _   _             
| \ | | ___ | |_(_) ___  _ __  
|  \| |/ _ \| __| |/ _ \| '_ \ 
| |\  | (_) | |_| | (_) | | | |
|_|_\_|\___/ \__|_|\___/|_| |_|
    """)

    print("-" * 75)
    print("\n")

    # Get the number of covers to create
    while True:
        try:
            num_covers = int(input(Fore.YELLOW + "How many covers do you want to create? ").strip())
            if num_covers > 0:
                break
            else:
                print(Fore.RED + "Please enter a positive number.")
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a number.")

    # Get background mode (dark/light) using arrow keys
    mode_question = [
        inquirer.List(
            "dark_mode",
            message="Background mode:",
            choices=["Dark", "Light"],
            default="Dark",
        )
    ]
    answers = inquirer.prompt(mode_question)
    dark_mode = answers["dark_mode"] == "Dark"

    # Ask if the user wants to provide a custom file name
    custom_name_question = [
        inquirer.Confirm(
            "custom_name",
            message="Custom file names?",
            default=False,
        )
    ]
    custom_name_answer = inquirer.prompt(custom_name_question)["custom_name"]

    # Collect inputs for each cover
    user_inputs = []
    for i in range(1, num_covers + 1):
        print(Fore.CYAN + f"\n--- Page {i} ---")
        
        # Get page text
        text = input(Fore.WHITE + Style.BRIGHT + f"Enter text for page {i} (leave blank for no text): ").strip()
        if not text:
            print(Fore.YELLOW + f"Page {i} text empty. Using a clear version.")
            text = " "  # Set text to a single space to ensure no visible text

        # Handle file name input
        if custom_name_answer:
            output_file = input(Fore.GREEN + f"File name for page {i}: ").strip()
            if not output_file:
                output_file = f"page-{i}-cover.png"
        else:
            output_file = f"page-{i}-cover.png"

        if not output_file.endswith(".png"):
            print(Fore.YELLOW + "Adding '.png' extension.")
            output_file += ".png"

        # Set default directory for outputs
        output_dir = "backgrounds"
        os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

        # Generate the next available file name if the specified one exists
        output_file = os.path.join(output_dir, get_next_available_filename(output_file, output_dir))

        # Store inputs for this cover
        user_inputs.append({
            "text": text,
            "dark_mode": dark_mode,
            "output_file": output_file,
        })

    return user_inputs
