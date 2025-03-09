from flask import Flask, render_template, request
import random
import string

app = Flask(__name__)

# Function to generate random variable names
def generate_random_name(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Simple Python code obfuscation function
def obfuscate_code(code):
    obfuscated_code = code
    var_names = {}
    lines = code.split('\n')

    for line in lines:
        # Only obfuscate simple variable assignments and functions
        if '=' in line:
            parts = line.split('=')
            var_name = parts[0].strip()
            if var_name not in var_names:
                new_var_name = generate_random_name()
                var_names[var_name] = new_var_name
            obfuscated_code = obfuscated_code.replace(var_name, var_names[var_name])

    return obfuscated_code

@app.route('/', methods=['GET', 'POST'])
def index():
    obfuscated_code = None
    if request.method == 'POST':
        code = request.form['code']
        obfuscated_code = obfuscate_code(code)
    return render_template('index.html', obfuscated_code=obfuscated_code)

if __name__ == '__main__':
    app.run(debug=True)
