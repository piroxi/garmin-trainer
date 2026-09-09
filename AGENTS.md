# AGENTS

## Garmin MFA

When running `trainer.py` (or anything that logs into Garmin Connect), Garmin may prompt for an MFA code. Do not let the process die on `EOFError`. Instead, keep the shell/process open, ask the user for the code, and feed it into the running process. The user will type the code.

To keep a shell open across MFA prompts, run the command so it stays interactive (e.g. use a pseudo-tty / read the code from the user and pipe it in). If a one-shot `bash` call would hit EOF, ask the user for the code first and pass it on stdin.
