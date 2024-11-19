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
        dict: A dictionary containing user inputs.
    """
    # Print the title
    print(Fore.CYAN + Style.BRIGHT + """
 _   _       _   _             
| \ | | ___ | |_(_) ___  _ __  
|  \| |/ _ \| __| |/ _ \| '_ \ 
| |\  | (_) | |_| | (_) | | | |
|_|_\_|\___/ \__|_|\___/|_| |_|
  _____                        
 / ___|_____   _____ _ __      
| |   / _ \ \ / / _ \ '__|     
| |__| (_) \ V /  __/ |        
 \____\___/ \_/ \___|_|        
  _____                    
 / ___| ___ _ __               
| |  _ / _ \ '_ \              
| |_| |  __/ | | |             
 \____|\___|_| |_|             
    """)

    print("-" * 75)
    print("\n")

    # Get text input
    text = input(Fore.WHITE + Style.BRIGHT + "Enter page name: ").strip()
    if not text:
        raise ValueError("Text cannot be empty!")

    # Get background mode (dark/light) using arrow keys
    mode_question = [
        inquirer.List(
            "dark_mode",
            message="Choose the background mode",
            choices=["Dark Mode", "Light Mode"],
            default="Dark Mode",
        )
    ]
    answers = inquirer.prompt(mode_question)
    dark_mode = answers["dark_mode"] == "Dark Mode"

    # Get output file name
    print(Fore.GREEN + "\nAlmost done!")
    output_file = input("Enter custom output name (or leave blank for default): ").strip()

    # Set default file name
    if not output_file:
        output_file = "page-cover.png"

    if not output_file.endswith(".png"):
        print(Fore.YELLOW + "Output file must be a .png file. Adding '.png' extension.")
        output_file += ".png"

    # Set default directory for outputs
    output_dir = "backgrounds"
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

    # Generate the next available file name if the specified one exists
    output_file = os.path.join(output_dir, get_next_available_filename(output_file, output_dir))

    return {
        "text": text,
        "dark_mode": dark_mode,
        "output_file": output_file,
    }
