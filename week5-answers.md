# Week 5 activity

## Q1: Ignore private and generated files

The project’s .gitignore contains `.env`, `__pycache__/`, `.vscode/`, and `.venv/`. The first protects the local key file from normal Git staging. The others exclude generated Python files, editor settings, and the local Python environment. The assignment source is being backed up to the project’s configured GitHub repository, mashcodes10/es-3890.

## Q2: Local API key

The existing local .env file contains a GROQ_API_KEY variable. A live Groq request succeeded with this key. Show the instructor the file locally in class. Do not screenshot the file or include it in your submission.

## Q3: Why .env and .gitignore matter

A .env file separates the API key from source code. app.py loads it into the process environment, allowing the program to read GROQ_API_KEY without hardcoding it in a file shared on GitHub.

.gitignore tells Git to skip matching untracked files during normal staging. The .env entry prevents ordinary `git add .` from adding the private file. It does not remove a file that Git already tracks, erase earlier commits, or prevent someone from force-adding it.

This protection applies to Git’s staging workflow, whether commands run in a terminal or a GUI that uses Git. It does not protect against manually uploading .env through the GitHub website, copying the key into another tracked file, or sharing it in a screenshot. Saying it is limited only to terminal actions is too narrow.

## Q4: Flask installation

Flask 3.1.3 is installed for python3. Verify or install with:

```
python3 -m pip install -r requirements.txt
python3 -m pip list
```

The pip list check confirmed Flask 3.1.3. The assignment specifically requests a VS Code terminal screenshot. That screenshot remains to be captured because UI automation could not control the open VS Code window.

## Q5: Hello world

hello.py creates a Flask application, registers the `/` route, and returns a Hello, World! heading. Run `python3 hello.py` and open http://127.0.0.1:5001. The server listens on the local computer’s loopback interface. If macOS asks for local network access, choose Don’t Allow as the assignment directs.

## Q6: Localhost

Localhost is a hostname that refers to the computer you are using. It normally resolves to a loopback address such as 127.0.0.1 or ::1. A development server running on your computer receives requests from your browser at a URL such as http://localhost:5002. The port identifies the particular server. Developers use localhost to run and test websites before deploying them. This project binds to 127.0.0.1 so its Flask server accepts local connections.

## Q7: Templates folder

The project contains a lowercase templates folder with index.html for the assignment form. The existing chat template is preserved in chat.html. Flask finds HTML templates in this folder by default.

## Q8: Capture text

Run `python3 app.py` and open http://127.0.0.1:5002/echo. The HTML form sends a POST request when you click Go. app.py reads request.form into the Python variable text and renders it outside the textarea under Captured text. The `/echo` route preserves this demonstration alongside Q9.

## Q9: Groq integration

Open http://127.0.0.1:5002/assignment. Clicking Go passes the captured prompt to ask_groq in backend.py. app.py loads the local .env file at startup. backend.py reads that key and calls last week’s groq_chat.ask function to send the prompt to Groq’s chat completions endpoint. It returns the model response, which app.py passes to index.html. A live request asking for a two-sentence explanation of localhost succeeded, and its screenshot is in evidence/week5/q9-groq.jpg.

## Q10: Information path

1. The browser requests a page from app.py’s Flask server.
2. app.py calls render_template to render templates/index.html for the assignment routes. The original chat route uses chat.html.
3. The user enters text and clicks Go. The browser submits the form to Flask with a POST request.
4. app.py reads the form field into text. On /echo it displays that text directly.
5. On / it calls backend.ask_groq(text).
6. backend.py reads GROQ_API_KEY loaded from .env and calls groq_chat.ask, which sends an authenticated HTTPS request to Groq.
7. Groq returns JSON containing the model’s message. groq_chat.py extracts the response text, and backend.py returns it to app.py.
8. app.py renders index.html with that response, and the browser displays it under Model response. Jinja escapes the text for HTML output.

## Q11: GitHub backup and secret validation

The exact local API key was absent from the assignment source and the pre-existing reachable commit history. The .env file was absent from that history. Before committing, Git’s ignore and tracked-file checks confirmed the local .env remained excluded. The backup results are recorded in evidence/week5/git-backup.txt.

These checks verify this repository’s reachable history and committed assignment files for the current key. They do not prove that other copies, deleted remote history, or older keys were never exposed.

## References

- Flask quickstart: https://flask.palletsprojects.com/en/stable/quickstart/
- Git ignore documentation: https://git-scm.com/docs/gitignore
- Groq documentation: https://console.groq.com/docs/overview
