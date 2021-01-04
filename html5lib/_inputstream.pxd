# cython: language_level=3
cimport cython
from cpython cimport array

ctypedef void (*rCEf)(HTMLUnicodeInputStream, unicode) except *

cdef dict charsUntilCache

cdef class BufferedStream(object):
    cdef object stream
    cdef object buffer
    cdef object position
    cpdef object tell(self)
    cpdef object seek(self, object pos)
    cpdef object read(self, object bytes)
    cdef object _bufferedBytes(self)
    cdef object _readStream(self, object bytes)
    cdef object _readFromBuffer(self, object bytes)

#def HTMLInputStream(source, object **kwargs)

cdef class HTMLUnicodeInputStream(object):
    cdef rCEf reportCharacterErrors
    cdef object newLines
    cdef readonly object charEncoding
    cdef object dataStream
    cdef unicode chunk
    cdef Py_ssize_t chunkSize
    cdef Py_ssize_t chunkOffset
    cdef readonly list errors

    # number of (complete) lines in previous chunks
    cdef Py_ssize_t prevNumLines
    # number of columns in the last line of the previous chunk
    cdef Py_ssize_t prevNumCols

    # Deal with CR LF and surrogates split over chunk boundaries
    cdef unicode _bufferedCharacter

    cdef object reset(self)
    cdef object openStream(self, object source)
    
    @cython.locals(nLines=Py_ssize_t, lastLinePos=Py_ssize_t)
    cdef tuple _position(self, Py_ssize_t offset)
    cpdef tuple position(self)
    
    @cython.locals(chunkOffset=Py_ssize_t, char=unicode)
    cpdef unicode char(self)

    @cython.locals(data=unicode)
    cdef bint readChunk(self, Py_ssize_t chunkSize=?) except? -1

    @cython.locals(c=ulong)
    cdef void characterErrorsUCS4(self, unicode data) except *
    cdef void characterErrorsUCS2(self, unicode data) except *
    
    cpdef object charsUntil(self, object characters, bint opposite=?)
    cpdef object unget(self, object char)

cdef class HTMLBinaryInputStream(HTMLUnicodeInputStream):
    cdef object rawStream
    cdef readonly object numBytesMeta
    cdef readonly object numBytesChardet
    cdef object override_encoding
    cdef object transport_encoding
    cdef object same_origin_parent_encoding
    cdef object likely_encoding
    cdef object default_encoding
    cdef object reset(self)
    cdef object openStream(self, object source)
    cdef object determineEncoding(self, object chardet=?)
    cpdef object changeEncoding(self, object newEncoding)
    @cython.locals(string=bytes)
    cdef object detectBOM(self)
    cdef object detectEncodingMeta(self)

# cdef class EncodingBytes(bytes):
#     cdef object previous(self)
#     cdef object setPosition(self, object position)
#     cdef object getPosition(self)
#     cdef object getCurrentByte(self)
#     cdef object skip(self, object chars=?)
#     cdef object skipUntil(self, object chars)
#     cdef object matchBytes(self, object bytes)
#     cdef object jumpTo(self, object bytes)

ctypedef bint (*encstate)(EncodingParser) except? -1

cdef class EncodingParser(object):
    cdef object data
    cdef object encoding

    @cython.locals(func=encstate, keepParsing=bint)
    cdef object getEncoding(self)
    cdef bint handleComment(self) except? -1
    @cython.locals(hasPragma=bint, name=bytes, value=bytes, tentativeEncoding=bytes)
    cdef bint handleMeta(self) except? -1
    cdef bint handlePossibleStartTag(self) except? -1
    cdef bint handlePossibleEndTag(self) except? -1
    cdef bint handlePossibleTag(self, bint endTag) except? -1
    cdef bint handleOther(self) except? -1
    @cython.locals(c=bytes)
    cdef tuple getAttribute(self)

cdef class ContentAttrParser(object):
    cdef object data
    cpdef object parse(self)  # this needs to be cpdef for tests

cdef object lookupEncoding(object encoding)
