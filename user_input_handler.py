def get_user_input():
    """
    Collects and validates user input for the gradient generator.

    Returns:
        dict: A dictionary containing user inputs.
    """
    print("Welcome to the Notion Background Generator!")
    
    # Get text input
    text = input("Enter the text you want to display in the middle of the gradient: ").strip()
    if not text:
        raise ValueError("Text cannot be empty!")

    # Get background mode (dark/light)
    while True:
        bg_choice = input("Choose background mode (dark/light): ").strip().lower()
        if bg_choice in ["dark", "light"]:
            dark_mode = bg_choice == "dark"
            break
        print("Invalid choice. Please type 'dark' or 'light'.")

    # Get output file name
    output_file = input("Enter the output file name (e.g., gradient_image.png): ").strip()
    if not output_file.endswith(".png"):
        print("Output file must be a .png file. Adding '.png' extension.")
        output_file += ".png"

    return {
        "text": text,
        "dark_mode": dark_mode,
        "output_file": output_file
    }