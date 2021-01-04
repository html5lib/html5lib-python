# cython: language_level=3
cimport cython

from cpython cimport version

from . cimport _inputstream

ctypedef bint (*tokstate)(HTMLTokenizer) except? -1

cdef frozenset spaceCharacters
cdef dict entities
cdef frozenset asciiLetters
cdef dict asciiUpper2Lower
cdef frozenset digits
cdef frozenset hexDigits
cdef EOF = None
cdef dict tokenTypes
cdef frozenset tagTokenTypes
cdef dict replacementCharacters

cdef class HTMLTokenizer(object):
    cdef readonly _inputstream.HTMLUnicodeInputStream stream
    cdef object parser
    cdef tokstate _state
    cdef unicode temporaryBuffer
    cdef public dict currentToken
    cdef unicode currentAttribute
    cdef object tokenQueue

    @cython.locals(charAsInt=uint, char=unicode)
    cdef unicode consumeNumberEntity(self, bint isHex)
    cdef void consumeEntity(self, unicode allowedChar=?, bint fromAttribute=?) except *
    cdef void processEntityInAttribute(self, unicode allowedChar) except *

    cdef void emitCurrentToken(self) except *

    cdef bint dataState(self) except? -1
    cdef bint entityDataState(self) except? -1
    cdef bint rcdataState(self) except? -1
    cdef bint characterReferenceInRcdata(self) except? -1
    cdef bint rawtextState(self) except? -1
    cdef bint scriptDataState(self) except? -1
    cdef bint plaintextState(self) except? -1
    cdef bint tagOpenState(self) except? -1
    cdef bint closeTagOpenState(self) except? -1
    cdef bint tagNameState(self) except? -1
    cdef bint rcdataLessThanSignState(self) except? -1
    cdef bint rcdataEndTagOpenState(self) except? -1
    cdef bint rcdataEndTagNameState(self) except? -1
    cdef bint rawtextLessThanSignState(self) except? -1
    cdef bint rawtextEndTagOpenState(self) except? -1
    cdef bint rawtextEndTagNameState(self) except? -1
    cdef bint scriptDataLessThanSignState(self) except? -1
    cdef bint scriptDataEndTagOpenState(self) except? -1
    cdef bint scriptDataEndTagNameState(self) except? -1
    cdef bint scriptDataEscapeStartState(self) except? -1
    cdef bint scriptDataEscapeStartDashState(self) except? -1
    cdef bint scriptDataEscapedState(self) except? -1
    cdef bint scriptDataEscapedDashState(self) except? -1
    cdef bint scriptDataEscapedDashDashState(self) except? -1
    cdef bint scriptDataEscapedLessThanSignState(self) except? -1
    cdef bint scriptDataEscapedEndTagOpenState(self) except? -1
    cdef bint scriptDataEscapedEndTagNameState(self) except? -1
    cdef bint scriptDataDoubleEscapeStartState(self) except? -1
    cdef bint scriptDataDoubleEscapedState(self) except? -1
    cdef bint scriptDataDoubleEscapedDashState(self) except? -1
    cdef bint scriptDataDoubleEscapedDashDashState(self) except? -1
    cdef bint scriptDataDoubleEscapedLessThanSignState(self) except? -1
    cdef bint scriptDataDoubleEscapeEndState(self) except? -1
    cdef bint beforeAttributeNameState(self) except? -1
    cdef bint attributeNameState(self) except? -1
    cdef bint afterAttributeNameState(self) except? -1
    cdef bint beforeAttributeValueState(self) except? -1
    cdef bint attributeValueDoubleQuotedState(self) except? -1
    cdef bint attributeValueSingleQuotedState(self) except? -1
    cdef bint attributeValueUnQuotedState(self) except? -1
    cdef bint afterAttributeValueState(self) except? -1
    cdef bint selfClosingStartTagState(self) except? -1
    cdef bint bogusCommentState(self) except? -1
    cdef bint markupDeclarationOpenState(self) except? -1
    cdef bint commentStartState(self) except? -1
    cdef bint commentStartDashState(self) except? -1
    cdef bint commentState(self) except? -1
    cdef bint commentEndDashState(self) except? -1
    cdef bint commentEndState(self) except? -1
    cdef bint commentEndBangState(self) except? -1
    cdef bint doctypeState(self) except? -1
    cdef bint beforeDoctypeNameState(self) except? -1
    cdef bint doctypeNameState(self) except? -1
    cdef bint afterDoctypeNameState(self) except? -1
    cdef bint afterDoctypePublicKeywordState(self) except? -1
    cdef bint beforeDoctypePublicIdentifierState(self) except? -1
    cdef bint doctypePublicIdentifierDoubleQuotedState(self) except? -1
    cdef bint doctypePublicIdentifierSingleQuotedState(self) except? -1
    cdef bint afterDoctypePublicIdentifierState(self) except? -1
    cdef bint betweenDoctypePublicAndSystemIdentifiersState(self) except? -1
    cdef bint afterDoctypeSystemKeywordState(self) except? -1
    cdef bint beforeDoctypeSystemIdentifierState(self) except? -1
    cdef bint doctypeSystemIdentifierDoubleQuotedState(self) except? -1
    cdef bint doctypeSystemIdentifierSingleQuotedState(self) except? -1
    cdef bint afterDoctypeSystemIdentifierState(self) except? -1
    cdef bint bogusDoctypeState(self) except? -1
    @cython.locals(nullCount=Py_ssize_t)
    cdef bint cdataSectionState(self) except? -1
