# notes

Keep short notes from the terminal.

## Usage

    python3 src/app.py init          # create notes.json here
    python3 src/app.py add "text"    # add a note
    python3 src/app.py list          # print every note
    python3 src/app.py list --limit 2  # at most 2 notes, oldest first; 0 or less exits 2

When something goes wrong, the error should tell the user which command fixes it.
