import textwrap

def wrap_text(text, width=15):
    newtext = textwrap.fill(text, width)
    # replace the new line character with a <br>
    newtext = newtext.replace('\n', '<br>')
    return newtext


def rgb2hex(color):
                return "#{:02x}{:02x}{:02x}".format(int(color[0]*255),int(color[1]*255),int(color[2]*255))