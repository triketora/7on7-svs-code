"""Produced for the 7th edition of Rhizome's 7on7: sevenonseven.rhizome.org
Copyright 2016, Tracy Chou and Claire Evans.
"""

import argparse
import random
import re
import subprocess
import sys

# Only uncomment if you have the pyfiglet dependency installed. It's fun for big
# ASCII printing but not necessary, so commenting out by default.
# from pyfiglet import figlet_format


MALE_VOICES = [
    "Alex",
    "Daniel",
    "Fred",
    "Junior",
    # "Lee",  
    # "Oliver",  
    "Ralph"
]


FEMALE_VOICES = [
    "Agnes",
    "Fiona",
    # "Karen",  
    "Kathy",
    "Princess",
    "Tessa",
    "Vicki",
    "Victoria"
]


def mic_check():
    for voice in MALE_VOICES + FEMALE_VOICES:
        print "Next up: {voice}".format(voice=voice)

        say_cmd = "say -v {voice} {dialog}".format(voice=voice, dialog="Test test 1 2 3")
        subprocess.call(say_cmd.split())


class Gender:
    MALE = 1
    FEMALE = 2


class Character(object):
    def __init__(self, number, gender=None, voice=None, is_ai=None, color=None):
        self.placeholder = "X{number}".format(number=number)
        self.color = color
        self.gender = gender
        self.voice = voice
        self.is_ai = is_ai

    def set_gender(self, gender):
        self.gender = gender

    def set_voice(self, voice):
        self.voice = voice

    def set_is_ai(self, is_ai):
        self.is_ai = is_ai

    def set_color(self, color):
        self.color = color

    @property
    def name(self):
        return self.voice

    def say(self, dialog):
        # Default speed is 200 wpm for humans, 250 pm for AIs. Override to a
        # slow speed of 130pm if there"s a directive in the script as such.
        wpm = 250 if self.is_ai else 200
        if should_read_slowly(dialog):
            wpm = 130

        dialog = replace_pauses(dialog)
        dialog = remove_parentheticals(dialog)

        say_cmd = "say -v {voice} -r {wpm} {dialog}".format(
            voice=self.voice, wpm=wpm, dialog=dialog)
        subprocess.call(say_cmd.split())


class Colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[37m"
    WHITE = "\033[38m"

    @classmethod
    def all(cls):
        return [
            cls.RED,
            cls.GREEN,
            cls.YELLOW,
            cls.BLUE,
            cls.MAGENTA,
            cls.CYAN,
            cls.GRAY,
            cls.WHITE
        ]


class Formatting:
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def batch_set_voices(characters, gender):
    if gender == Gender.MALE:
        voices = MALE_VOICES
    else:
        voices = FEMALE_VOICES

    random.shuffle(voices)
    for character, voice in zip(characters, voices[:len(characters)]):
        character.set_voice(voice)


def construct_characters(genders, is_ais, colors):
    assert len(genders) == len(is_ais) == len(colors)

    num_characters = len(genders)
    characters = [Character(i) for i in range(1, num_characters+1)]

    male_characters = []
    female_characters = []

    for character, gender, is_ai, color in zip(characters, genders, is_ais, colors):
        character.set_gender(gender)
        character.set_is_ai(is_ai)
        character.set_color(color)

        if gender == Gender.MALE:
            male_characters.append(character)
        else:
            female_characters.append(character)

    # Batch set the voices by gender so we don't randomly select the same voice
    # for multiple characters.
    batch_set_voices(male_characters, Gender.MALE)
    batch_set_voices(female_characters, Gender.FEMALE)

    return dict((character.placeholder, character) for character in characters)


class Acts:
    I = "ACT I"
    II = "ACT II"
    III = "ACT III"

    @classmethod
    def all(cls):
        return [cls.I, cls.II, cls.III]


CHARACTER_PROG = re.compile("(?P<placeholder>X[1-4])[^:]*:(?P<dialog>.*)")


def get_character_placeholder_and_dialog(line):
    match = CHARACTER_PROG.match(line)
    if match:
        return match.group("placeholder"), match.group("dialog")
    else:
        return None, None


HE_SHE_PROG = re.compile("\((?P<placeholder>X[1-4]) (?P<pronoun>he/she)\)", flags=re.IGNORECASE)
HIS_HER_PROG = re.compile("\((?P<placeholder>X[1-4]) (?P<pronoun>his/her)\)", flags=re.IGNORECASE)
HIM_HER_PROG = re.compile("\((?P<placeholder>X[1-4]) (?P<pronoun>him/her)\)", flags=re.IGNORECASE)


def replace_gender_pronoun(prog, line, characters, female_pronoun, male_pronoun):
    for match in re.finditer(prog, line):
        placeholder = match.group("placeholder")
        character = characters.get(placeholder)
        pronoun_capitalized = match.group("pronoun")[0].isupper()
        if character.gender == Gender.MALE:
            pronoun = male_pronoun
        else:
            pronoun = female_pronoun
        if pronoun_capitalized:
            pronoun = pronoun.capitalize()

        line = re.sub(prog, pronoun, line)
    return line


def replace_gender_pronouns(line, characters):
    line = replace_gender_pronoun(HE_SHE_PROG, line, characters, "she", "he")
    line = replace_gender_pronoun(HIS_HER_PROG, line, characters, "her", "his")
    line = replace_gender_pronoun(HIM_HER_PROG, line, characters, "her", "him")
    return line


CHARACTER_PLACEHOLDER_PROG = re.compile("(?P<placeholder>X[1-4])", flags=re.IGNORECASE)


def replace_placeholder_names(line, characters):
    prog = CHARACTER_PLACEHOLDER_PROG

    for match in re.finditer(prog, line):
        placeholder = match.group("placeholder")
        character = characters.get(placeholder)
        name = character.name
        line = re.sub(prog, name, line, count=1)

    return line


SLOW_SPEED_DIRECTIVE_PROG = re.compile("\(Slowly.*\) ")


def should_read_slowly(line):
    match = SLOW_SPEED_DIRECTIVE_PROG.search(line)
    return bool(match)


BEAT_PROG = re.compile("\(Beat.\) ")


MILLISECOND_WAIT_PROG = re.compile("\(After a (?P<ms>\d+) millisecond pause\.\)")


def replace_pauses(line):
    line = re.sub(BEAT_PROG, "[[slnc 500]]", line)
    match = MILLISECOND_WAIT_PROG.search(line)
    if match:
        ms = match.group("ms")
        line = re.sub(MILLISECOND_WAIT_PROG, "[[slnc {ms}]]".format(ms=ms), line)

    return line


PARENTHETICAL_PROG = re.compile("\([^\)]*\)")


def remove_parentheticals(dialog):
    return re.sub(PARENTHETICAL_PROG, "", dialog)


def print_line_in_color(line, color, bold=False, remove_trailing_newline=False):
    bold_formatting = Formatting.BOLD if bold else ""
    if remove_trailing_newline:
        print "%s%s%s%s" % (bold_formatting, color, line, Formatting.END),
    else:
        print "%s%s%s%s" % (bold_formatting, color, line, Formatting.END)


def clear_screen():
    sys.stderr.write("\x1b[2J\x1b[H")


def read_script(filename, characters, start, end):
    with open(filename) as f:
        started = False
        ended = False

        for line in f:
            line = line.strip()

            if not started and line == "<{start}>".format(start=start):
                started = True
            elif started and line == "</{end}>".format(end=end):
                ended = True

            if not started:
                continue

            if any(line == "<{act}>".format(act=act) for act in Acts.all()) or \
                any(line == "</{act}>".format(act=act) for act in Acts.all()):
                # Either the beginning or end of an act, so clear the screen.
                clear_screen()

                # Switch the commenting of the two following lines if you have
                # pyfiglet installed and want big ASCII lettering for the
                # beginning and end of each act.
                # print_line_in_color(figlet_format(line, font="starwars"), Colors.YELLOW)
                print_line_in_color(line, Colors.YELLOW, bold=True)

                # Press [Enter] to continue.
                raw_input()
                clear_screen()
                continue

            # Figure out if this is a line of dialog.
            placeholder, dialog = get_character_placeholder_and_dialog(line)

            # Do name and pronoun replacements for line to be printed on screen.
            line = replace_gender_pronouns(line, characters)
            line = replace_placeholder_names(line, characters)

            if not line:
                print
            elif line and not dialog:
                # Stage direction. Press [Enter] to continue.
                print_line_in_color(line, Colors.YELLOW, bold=True, remove_trailing_newline=True)
                raw_input()
            else:
                # Dialog!
                character = characters.get(placeholder)
                print_line_in_color(line, character.color)

                # Do name and pronoun replacements for the dialog to be spoken.
                dialog = replace_gender_pronouns(dialog, characters)
                dialog = replace_placeholder_names(dialog, characters)

                character.say(dialog)

            if ended:
                break


def main(genders=None, start=None, end=None):
    clear_screen()

    num_characters = 4
    if not genders:
        genders = [Gender.MALE if random.random() < 0.5 else Gender.FEMALE
                   for i in range(num_characters)]
    colors = [Colors.CYAN, Colors.GREEN, Colors.WHITE, Colors.BLUE]
    is_ais = [False, False, True, False]
    characters = construct_characters(genders=genders, is_ais=is_ais, colors=colors)

    print_line_in_color("Reading script with characters:", Colors.YELLOW)
    for placeholder in sorted(characters.keys()):
        character = characters.get(placeholder)
        if character.gender == Gender.FEMALE:
            gender_for_print = "f"
        else:
            gender_for_print = "m"
        print_line_in_color("  {placeholder} in the voice of {name} ({gender})".format(
            placeholder=placeholder, name=character.name, gender=gender_for_print),
            Colors.YELLOW)
    raw_input()

    if not start:
        start = Acts.I
    if not end:
        end = Acts.III
    assert start <= end

    filename = "svs.txt"
    read_script(filename, characters, start, end)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--genders", type=str, help="""
        a four-letter string of f's and m's to indicate the genders of the four
        characters, in order; e.g., FMFF""", required=False)
    parser.add_argument("--start", type=str, help="""
        the act to start reading; e.g., ACT I""", required=False)
    parser.add_argument("--end", type=str, help="""the act to stop reading;
        e.g., ACT II""", required=False)

    args = parser.parse_args()
    genders = args.genders
    if genders:
        assert len(genders) == 4
        genders = [gender.lower() == "f" and Gender.FEMALE or
                   gender.lower() == "m" and Gender.MALE
                   for gender in list(genders)]
    start = args.start
    end = args.end

    # mic_check()
    main(genders=genders, start=start, end=end)
