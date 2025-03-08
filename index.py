from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
        <form action="/command" method="GET">
            Command: <input type="text" name="cmd" />
            <input type="submit" value="Execute" />
        </form>
    '''

@app.route('/command', methods=['GET'])
def command():
    cmd = request.args.get('cmd', '')
    if cmd:
        try:
            # Vulnerable to command injection
            output = os.popen(cmd).read()
            return f"<pre>{output}</pre>"
        except Exception as e:
            return f"Error executing command: {e}"
    return "No command provided"

if __name__ == "__main__":
    app.run(debug=True)
