# Maintenacne utilities

## Snippets

For recursively finding files "poluted" with Windows carriage returns, use

    grep --exclude-dir=build --exclude-dir=dist --exclude-dir=__pycache__ --exclude-dir=data --exclude-dir=.git -l -r $'\r' .

and for removing all carriage returns, pipe to

    grep --exclude-dir=build --exclude-dir=dist --exclude-dir=__pycache__ --exclude-dir=data --exclude-dir=.git -l -r $'\r' . | xargs -n 1 -I{} sed -i -e 's/\r//g' {}




