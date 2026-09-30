"""Small GIF89a encoder for Qt viewport frames; no optional Python packages.

Qt supplies a per-frame indexed palette. A bounded LZW dictionary keeps codes
at nine bits and resets before growth, trading some compression for simplicity.
"""
import struct


def lzw_pixels(pixels):
    clear, end = 256, 257
    table = {bytes((i,)): i for i in range(256)}
    next_code = 258
    output = bytearray()
    bits = accumulator = 0

    def emit(code):
        nonlocal bits, accumulator
        accumulator |= code << bits
        bits += 9
        while bits >= 8:
            output.append(accumulator & 255)
            accumulator >>= 8
            bits -= 8

    emit(clear)
    word = b''
    for pixel in pixels:
        char = bytes((pixel,))
        joined = word + char
        if joined in table:
            word = joined
            continue
        emit(table[word])
        table[joined] = next_code
        next_code += 1
        word = char
        if next_code >= 510:
            emit(clear)
            table = {bytes((i,)): i for i in range(256)}
            next_code = 258
    if word:
        emit(table[word])
    emit(end)
    if bits:
        output.append(accumulator & 255)
    return bytes(output)


class GifWriter:
    def __init__(self, path, width, height, fps=12):
        self.file = open(path, 'xb')
        self.width, self.height = width, height
        self.delay = max(1, round(100 / fps))
        self.file.write(b'GIF89a' + struct.pack('<HHBBB', width, height, 0x70, 0, 0))
        self.file.write(b'!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')

    def frame(self, pixels, palette):
        if len(pixels) != self.width*self.height:
            raise ValueError('GIF frame dimensions differ.')
        if len(palette) != 768:
            raise ValueError('GIF palette must contain 256 RGB entries.')
        self.file.write(b'!\xf9\x04\x04' + struct.pack('<H',self.delay) + b'\x00\x00')
        self.file.write(b',' + struct.pack('<HHHHB',0,0,self.width,self.height,0x87))
        self.file.write(palette+b'\x08')
        compressed=lzw_pixels(pixels)
        for i in range(0,len(compressed),255):
            block=compressed[i:i+255];self.file.write(bytes((len(block),))+block)
        self.file.write(b'\x00')

    def close(self):
        if not self.file.closed:
            self.file.write(b';');self.file.close()


def from_pngs(paths, destination, fps=12):
    from PySide6 import QtGui
    import numpy as np
    # Use one union crop for the whole motion; per-frame crops would make it jump.
    bounds=None
    for path in paths:
        image=QtGui.QImage(str(path)).convertToFormat(QtGui.QImage.Format_RGBA8888)
        if image.isNull():raise RuntimeError('Unreadable frame: '+str(path))
        rgba=np.frombuffer(image.constBits(),dtype=np.uint8).reshape(image.height(),image.bytesPerLine())[:,:image.width()*4].reshape(image.height(),image.width(),4)
        ys,xs=np.where(rgba[:,:,:3].max(axis=2)>35)
        if len(xs):
            box=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
            bounds=box if bounds is None else (min(bounds[0],box[0]),min(bounds[1],box[1]),max(bounds[2],box[2]),max(bounds[3],box[3]))
    if bounds:
        left=max(0,bounds[0]-50);top=max(0,bounds[1]-50)
        bounds=(left,top,min(image.width(),bounds[2]+50)-left,min(image.height(),bounds[3]+50)-top)
    writer=None
    try:
        for path in paths:
            image=QtGui.QImage(str(path))
            if image.isNull():raise RuntimeError('Unreadable frame: '+str(path))
            if bounds:image=image.copy(*bounds)
            indexed=image.convertToFormat(QtGui.QImage.Format_Indexed8)
            if writer is None:writer=GifWriter(destination,image.width(),image.height(),fps)
            rows=np.frombuffer(indexed.constBits(),dtype=np.uint8).reshape(indexed.height(),indexed.bytesPerLine())
            palette=bytearray()
            colors=indexed.colorTable()
            for i in range(256):
                color=colors[i] if i<len(colors) else 0
                palette.extend(((color>>16)&255,(color>>8)&255,color&255))
            writer.frame(rows[:,:indexed.width()].tobytes(),bytes(palette))
    finally:
        if writer:writer.close()
    return destination
