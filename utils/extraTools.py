import textwrap

def wrap_text(text, width=15):
    newtext = textwrap.fill(text, width)
    # replace the new line character with a <br>
    newtext = newtext.replace('\n', '<br>')
    return newtext
