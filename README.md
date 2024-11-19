**Notion Background Generator**

**✨ Overview**

The **Notion Background Generator** is a Python-based tool designed to create stunning, customizable mesh gradient backgrounds with text overlays. It offers a vibrant design experience, allowing you to adjust colors, gradient intensity, and text, making it perfect for page covers, banners, and more.

**🚀 Features**

• **Dynamic Gradients**: Generates colorful mesh-like gradients.

• **Dark & Light Modes**: Choose between sleek dark or elegant light styles.

• **Custom Text**: Add text to the center of your gradient or leave it blank for a minimalistic look.

• **Vibrant Colors**: Colors dynamically pulled from colors.json for easy customization.

• **File Auto-Naming**: Automatically generates file names to avoid overwrites.

• **Grain Effect**: Adds subtle noise for a polished, modern design.

• **Configurable Output**: Customize image dimensions and design parameters.

**🛠️ Requirements**

• **Python 3.8+**

• Required Libraries:

• Pillow

• numpy

• colorama

• inquirer

Install dependencies using:

pip install -r requirements.txt

**📂 Project Structure**

notion-bg-gen/

├── main.py \# Entry point of the program

├── gradient_generator.py \# Gradient and image generation logic

├── user_input_handler.py \# Handles user input

├── assets/

│ ├── colors.json \# Configurable color palettes

│ ├── Inter-Bold.ttf \# Font used for text

├── backgrounds/ \# Directory for generated images

└── README.md \# Project documentation

**🎨 Usage**

1. **Clone the Repository**:

git clone https://github.com/your-username/notion-bg-gen.git

cd notion-bg-gen

2. **Run the Script**:

python3 main.py

3. **Follow On-Screen Prompts**:

• Specify the number of covers to generate.

• Choose dark or light mode.

• Enter custom text for each cover (or leave it blank for no text).

• Decide whether to customize output file names.

4. **Output**:

• Generated images are saved in the backgrounds/ directory.

**📦 Configuration**

**assets/colors.json**

Customize the color palettes for dark and light modes and base colors:

{

"dark_mode_colors": \["#FF4500", "#FF6347", "#FF8C00", "#FFA500", "#6A5ACD"\],

"light_mode_colors": \["#FFFACD", "#FAD02E", "#F5B041", "#FF5733", "#DAF7A6"\],

"base_colors": {

"dark_background": "#09090b",

"light_background": "#fafafa",

"dark_text": "#fafafa",

"light_text": "#09090b"

}

}

**🌟 Example Output**

1. **Dark Mode Gradient with Text**:

2. **Light Mode Gradient**:

**📖 License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

**❤️ Contributing**

Feel free to fork this repository, submit issues, or create pull requests. Contributions are always welcome!

**📧 Contact**

For questions, feedback, or ideas:

• **Email**: your-email@example.com

• **GitHub**: [your-username](https://github.com/your-username)

Happy Gradient Making! 😊
