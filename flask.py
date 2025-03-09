from flask import Flask, render_template, request
import pyarmor

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    obfuscated_code = ""
    if request.method == "POST":
        original_code = request.form["code"]
        
        # Write the original code to a temporary Python file
        with open("temp_code.py", "w") as f:
            f.write(original_code)
        
        # Obfuscate the code using pyarmor
        pyarmor.cli(['obfuscate', 'temp_code.py'])
        
        # Read the obfuscated code from the generated file
        with open("dist/temp_code.py", "r") as f:
            obfuscated_code = f.read()

    return render_template("index.html", obfuscated_code=obfuscated_code)

if __name__ == "__main__":
    app.run(debug=True)
