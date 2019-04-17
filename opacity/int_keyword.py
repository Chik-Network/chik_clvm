# compiler

import binascii

from .SExp import SExp


class Token(str):
    def __new__(self, s, offset):
        self = str.__new__(self, s)
        self._offset = offset
        return self


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


def parse_as_int(s, offset):
    try:
        v = int(s)
        return SExp(v)
    except (ValueError, TypeError):
        pass


def parse_as_hex(s, offset):
    if s[:2].upper() == "0X":
        try:
            return SExp(bytes_as_hex(binascii.unhexlify(s[2:])))
        except Exception:
            raise SyntaxError("invalid hex at %d: %s" % (offset, s))


def parse_as_var(s, offset):
    if s[:1].upper() == "X":
        try:
            return SExp.from_var_index(int(s[1:]))
        except Exception:
            raise SyntaxError("invalid variable at %d: %s" % (offset, s))


def compile_atom(token, keyword_to_int):
    s = token.as_bytes().decode("utf8")
    c = s[0]
    if c in "\'\"":
        assert c == s[-1] and len(s) >= 2
        return SExp(token.as_bytes()[1:-1])

    if c == '#':
        keyword = s[1:].lower()
        keyword_id = keyword_to_int.get(keyword)
        if keyword_id is None:
            raise SyntaxError("unknown keyword: %s" % keyword)
        return SExp(keyword_id)

    for f in [parse_as_int, parse_as_var, parse_as_hex]:
        v = f(s, token._offset)
        if v is not None:
            return v
    raise SyntaxError("can't parse %s at %d" % (s, token._offset))


def compile_list(tokens, keyword_to_int):
    if len(tokens) == 0:
        return SExp.null

    r = []
    if not tokens[0].is_list():
        keyword = keyword_to_int.get(tokens[0].as_bytes().decode("utf8").lower())
        if keyword:
            r.append(SExp(keyword))
            tokens = tokens[1:]

    for token in tokens:
        r.append(from_int_keyword_tokens(token, keyword_to_int))

    return SExp(r)


def from_int_keyword_tokens(token, keyword_to_int):
    if token.is_list():
        return compile_list(token, keyword_to_int)
    return compile_atom(token, keyword_to_int)


def to_int_keyword_tokens(form, keywords=[], is_first_element=False):
    if form.is_list():
        return SExp([to_int_keyword_tokens(f, keywords, _ == 0) for _, f in enumerate(form)])

    if form.is_var():
        return SExp(("x%d" % form.var_index()).encode("utf8"))

    if is_first_element and 0 <= form.as_int() < len(keywords):
        v = keywords[form.as_int()]
        if v != '.':
            return v.encode("utf8")

    if len(form.as_bytes()) > 4:
        return SExp(("0x%s" % binascii.hexlify(form.as_bytes()).decode("utf8")).encode("utf8"))

    return SExp(("%d" % form.as_int()).encode("utf8"))
