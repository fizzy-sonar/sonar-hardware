class MockTransport:
    def __init__(self, chunks):
        self.chunks = iter(chunks)

    def read(self, n):
        return next(self.chunks, b"")


class FT232HTransport:
    def __init__(self, url):
        from pyftdi.ftdi import Ftdi

        self.dev = Ftdi()
        self.dev.open_from_url(url)
        self.dev.set_bitmode(0, 0x40)

    def read(self, n):
        return self.dev.read_data_bytes(n, 4)
