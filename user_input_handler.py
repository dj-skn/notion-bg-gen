import os
import inquirer
import colorama
from colorama import Fore, Style
from inquirer.themes import GreenPassion

colorama.init(autoreset=True)

def get_next_available_filename(base_name, directory):
    """
    Generate the next available file name if the base name exists.
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
    """
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

    # Ask for the number of covers
    num_covers_question = [
        inquirer.Text(
            "num_covers",
            message=Style.BRIGHT + "How many covers?",
            validate=lambda _, x: x.isdigit() and int(x) > 0,
        )
    ]
    num_covers = int(inquirer.prompt(num_covers_question, theme=GreenPassion())["num_covers"])

    # Ask for background mode (dark/light)
    mode_question = [
        inquirer.List(
            "dark_mode",
            message="Background mode:",
            choices=["Dark", "Light"],
            default="Dark",
        )
    ]
    dark_mode = inquirer.prompt(mode_question, theme=GreenPassion())["dark_mode"] == "Dark"

    # Collect inputs for each cover
    user_inputs_list = []
    for i in range(1, num_covers + 1):
        print(Fore.YELLOW + f"\nCover {i}/{num_covers}:")
        text = input(Fore.WHITE + Style.BRIGHT + "Enter cover text " + Style.NORMAL + Style.DIM + "(empty for none)" + Style.RESET_ALL  + ": " ).strip() or " "

        # Get output file name
        output_file = input(Fore.YELLOW + "Output name (leave blank for default): ").strip()
        if not output_file:
            output_file = f"page-cover-{i}.png"

        if not output_file.endswith(".png"):
            output_file += ".png"

        # Ensure the directory exists and generate a unique file name
        output_dir = "backgrounds"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, get_next_available_filename(output_file, output_dir))

        user_inputs_list.append({
            "text": text,
            "dark_mode": dark_mode,
            "output_file": output_file,
        })

    return user_inputs_list
