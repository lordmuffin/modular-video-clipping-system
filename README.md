# modular-video-clipping-system
MVCS

## Development/Installation

Install mvcs and its dependencies:

    $ poetry install

Run tests and code analysis:

    $ poetry run pytest --mypy --pylint

## TODO
### Short Term
[X] Create Repo and start collab.

[ ] user preferences via a yaml config (e.g. ~/.config/mvcs/config.yaml)

[ ] smart detection of existing clips, if you happen to run a playbook twice, it shouldn't overwrite (or prompt you to overwrite) your existing clip, it should skip it

[ ] Add "controller" to handle generating YAML for clipping in real time.

### Long Term
[ ] Analyze clips with something like OpenCV to determine matches.
