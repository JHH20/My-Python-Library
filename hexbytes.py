from .class_decorators import immutify_methods, inherit_methods

__exclude__ = list(globals())


@immutify_methods({'join'})
@inherit_methods
class hexbytes(bytearray):
    """
    Mutable list containing byte data
    Extended `bytearray` class for easier use
    - Add support for interacting via ASCII string
    - Altered to only mutate on explicit setters
    """

    @classmethod
    def ishexbyte(cls, hex_str):
        """
        Check if given string is a valid hex representation of a byte
        - ignore whitespace
        - has exactly 2 valid hex characters
        """

        hex_chars = hex_str.upper().split()
        valid_chars = "0123456789ABCDEF"
        return len(hex_chars) == 2 \
            and hex_chars[0] in valid_chars \
            and hex_chars[1] in valid_chars

    @classmethod
    def enforcehexbyte(cls, hex_str):
        """
        Assert that given input is a valid hex representation of a byte
        and raise appropriate errors if otherwise
        """
        if not isinstance(hex_str, str):
            raise TypeError(f"Invalid hex string: {hex_str}")
        if not cls.ishexbyte(hex_str):
            raise ValueError(f"Invalid hex string: '{hex_str}'")


    def __str__(self):
        """
        List-like string representation with "0x" prefix

        ex) 0x [a0, b1, c2]
        """
        return f"0x [{self.hex('/')}]".replace('/', ", ")


    @classmethod
    def fromtext(cls, text):
        """
        Create `hexbytes` instance for given ASCII string
        ex) "ABCD" -> [41, 42, 43, 44]
        """
        if not text.isascii():
            raise ValueError(f"Cannot convert non-ASCII text: '{text}'")

        return cls(ord(c) for c in text)


    def set(self, index, hex_str):
        """
        Set byte value from hexbyte string
        Use [] operator for accessing as integer
        """
        self.enforcehexbyte(hex_str)

        self[index] = int(hex_str, 16)


    def get(self, index):
        """
        Get byte value as hexbyte string
        Use [] operator for accessing as integer
        """

        return format(self[index], '02x')


    def __padhex(self, width, fill_hex, *, pad_left, sign_ext):
        """
        Private method for padding left or right using hexbyte string
        """

        # If sign_extend == True, ignore fill_hex
        if sign_ext:
            fill_hex = "00" if self[0] < 128 else "ff"
        else:
            # Ensure fill_hex is valid hex string
            self.enforcehexbyte(fill_hex)

        if pad_left:
            return self.rjust(width, self.fromhex(fill_hex))
        else:
            return self.ljust(width, self.fromhex(fill_hex))


    def lpad(self, width, fill_hex=None, *, sign_ext=False):
        """
        Extend by repeating fill_hex to the left until new length == width
        If sign_extend == True, fill_hex is ignored and can be omitted
        Else fill_hex must be provided
        """
        if fill_hex is None and not sign_ext:
            raise ValueError("Must provide fill_hex if sign_ext=False")

        return self.__padhex(width, fill_hex, pad_left=True, sign_ext=sign_ext)


    def rpad(self, width, fill_hex):
        """
        Extend by repeating fill_hex to the right until new length == width
        """

        return self.__padhex(width, fill_hex, pad_left=False, sign_ext=False)


__all__ = [x for x in globals() if x not in __exclude__ and not x.startswith('_')]
