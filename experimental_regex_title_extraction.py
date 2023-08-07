import re

# https://regex101.com/r/eZ1gT7/5

s = "Some text here start matching string end some more text."


greedy = r"(?<=This is)(.*)(?=sentence)"
lazy = r"(?<=This is)(.*?)(?=sentence)"
plus_questionmark = r"(?<=start).+?(?=end)"
raw_start_end = r"AAA(.+?)ZZZ"

match = re.search(plus_questionmark, s)
if match:
    print(match.group(0))  # prints ' matching string '

# --------------
import re

s = "asdf=5;iwantthis123jasd"
result = re.search("asdf=5;(.*)123jasd", s)
print(result.group(1))
# ----------


s = "123123STRINGabcabc"


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def find_between_r(s, first, last):
    try:
        start = s.rindex(first) + len(first)
        end = s.rindex(last, start)
        return s[start:end]
    except ValueError:
        return ""


# print find_between( s, "123", "abc" )
# print find_between_r( s, "123", "abc" )
