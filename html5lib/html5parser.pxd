cimport cython

from . cimport _tokenizer

# # def parse(doc, treebuilder="etree", namespaceHTMLElements=True, **kwargs)

# # def parseFragment(doc, container="div", treebuilder="etree", namespaceHTMLElements=True, **kwargs)

cdef class HTMLParser(object):
    cdef bint strict
    cdef bint debug
    cdef readonly object tree
    cdef readonly list errors
    cdef readonly dict phases
    cdef bint innerHTMLMode
    cdef unicode container
    cdef readonly bint scripting
    cdef readonly _tokenizer.HTMLTokenizer tokenizer
    cdef public bint firstStartTag
    cdef readonly list log
    cdef public unicode compatMode
    cdef readonly unicode innerHTML
    cdef public object phase
    cdef public bint framesetOK
    cdef public object originalPhase

    
    #def _parse(self, stream, innerHTML=False, container="div", scripting=False, **kwargs)
    cdef reset(self)
    #cdef documentEncoding(self)
    cpdef bint isHTMLIntegrationPoint(self, object element) except? -1
    cpdef bint isMathMLTextIntegrationPoint(self, object element) except? -1
    @cython.locals(
        CharactersToken=int,
        SpaceCharactersToken=int,
        StartTagToken=int,
        EndTagToken=int,
        CommentToken=int,
        DoctypeToken=int,
        ParseErrorToken=int,
        defaultNamespace=unicode,
        token=dict,
        prev_token=dict,
        new_token=dict,
        openElements=list,
        type=int
    )
    cdef mainLoop(self)
    #def parse(self, stream, *args, **kwargs)
    #def parseFragment(self, stream, *args, **kwargs)
    cpdef void parseError(self, errorcode=?, datavars=?) except *
    cpdef void adjustMathMLAttributes(self, dict token) except *
    cpdef void adjustSVGAttributes(self, dict token) except *
    cpdef void adjustForeignAttributes(self, dict token) except *
    cdef void reparseTokenNormal(self, dict token) except *
    cpdef void resetInsertionMode(self) except *
    cpdef void parseRCDataRawtext(self, dict token, unicode contentType) except *

# cdef class  Phase(object):
#     cdef readonly object parser
#     cdef readonly object tree
#     cdef dict __startTagCache
#     cdef dict __endTagCache

#     cpdef processEOF(self)
#     cpdef processComment(self, dict token)
#     cpdef processDoctype(self, dict token)
#     cpdef processCharacters(self, dict token)
#     cpdef processSpaceCharacters(self, dict token)
#     cpdef processStartTag(self, dict token)
#     cpdef startTagHtml(self, dict token)
#     cpdef processEndTag(self, dict token)

# # cdef class  InitialPhase(Phase):
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processComment(self, dict token)
# #     cdef processDoctype(self, dict token)
# #     cdef anythingElse(self)
# #     cdef processCharacters(self, dict token)
# #     cdef processStartTag(self, dict token)
# #     cdef processEndTag(self, dict token)
# #     cdef processEOF(self)

# # cdef class  BeforeHtmlPhase(Phase):
# #     cdef insertHtmlElement(self)
# #     cdef processEOF(self)
# #     cdef processComment(self, dict token)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef processStartTag(self, dict token)
# #     cdef processEndTag(self, dict token)

# # cdef class  BeforeHeadPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagHead(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagImplyHead(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InHeadPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagHead(self, dict token)
# #     cdef startTagBaseLinkCommand(self, dict token)
# #     cdef startTagMeta(self, dict token)
# #     cdef startTagTitle(self, dict token)
# #     cdef startTagNoFramesStyle(self, dict token)
# #     cdef startTagNoscript(self, dict token)
# #     cdef startTagScript(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagHead(self, dict token)
# #     cdef endTagHtmlBodyBr(self, dict token)
# #     cdef endTagOther(self, dict token)
# #     cdef anythingElse(self)

# # cdef class  InHeadNoscriptPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processComment(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagBaseLinkCommand(self, dict token)
# #     cdef startTagHeadNoscript(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagNoscript(self, dict token)
# #     cdef endTagBr(self, dict token)
# #     cdef endTagOther(self, dict token)
# #     cdef anythingElse(self)

# # cdef class  AfterHeadPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagBody(self, dict token)
# #     cdef startTagFrameset(self, dict token)
# #     cdef startTagFromHead(self, dict token)
# #     cdef startTagHead(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagHtmlBodyBr(self, dict token)
# #     cdef endTagOther(self, dict token)
# #     cdef anythingElse(self)

# # cdef class  InBodyPhase(Phase):
# #     cdef bint dropNewline
# #     cdef isMatchingFormattingElement(self, node1, node2)
# #     cdef addFormattingElement(self, dict token)
# #     cdef processEOF(self)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processSpaceCharactersDropNewline(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef processSpaceCharactersNonPre(self, dict token)
# #     cdef startTagProcessInHead(self, dict token)
# #     cdef startTagBody(self, dict token)
# #     cdef startTagFrameset(self, dict token)
# #     cdef startTagCloseP(self, dict token)
# #     cdef startTagPreListing(self, dict token)
# #     cdef startTagForm(self, dict token)
# #     cdef startTagListItem(self, dict token)
# #     cdef startTagPlaintext(self, dict token)
# #     cdef startTagHeading(self, dict token)
# #     cdef startTagA(self, dict token)
# #     cdef startTagFormatting(self, dict token)
# #     cdef startTagNobr(self, dict token)
# #     cdef startTagButton(self, dict token)
# #     cdef startTagAppletMarqueeObject(self, dict token)
# #     cdef startTagXmp(self, dict token)
# #     cdef startTagTable(self, dict token)
# #     cdef startTagVoidFormatting(self, dict token)
# #     cdef startTagInput(self, dict token)
# #     cdef startTagParamSource(self, dict token)
# #     cdef startTagHr(self, dict token)
# #     cdef startTagImage(self, dict token)
# #     cdef startTagIsIndex(self, dict token)
# #     cdef startTagTextarea(self, dict token)
# #     cdef startTagIFrame(self, dict token)
# #     cdef startTagNoscript(self, dict token)
# #     cdef startTagRawtext(self, dict token)
# #     cdef startTagOpt(self, dict token)
# #     cdef startTagSelect(self, dict token)
# #     cdef startTagRpRt(self, dict token)
# #     cdef startTagMath(self, dict token)
# #     cdef startTagSvg(self, dict token)
# #     cdef startTagMisplaced(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagP(self, dict token)
# #     cdef endTagBody(self, dict token)
# #     cdef endTagHtml(self, dict token)
# #     cdef endTagBlock(self, dict token)
# #     cdef endTagForm(self, dict token)
# #     cdef endTagListItem(self, dict token)
# #     cdef endTagHeading(self, dict token)
# #     cdef endTagFormatting(self, dict token)
# #     cdef endTagAppletMarqueeObject(self, dict token)
# #     cdef endTagBr(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  TextPhase(Phase):
# #     cdef processCharacters(self, dict token)
# #     cdef processEOF(self)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagScript(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InTablePhase(Phase):
# #     cdef object originalPhase
# #     cdef object characterTokens

# #     cdef clearStackToTableContext(self)
# #     cdef processEOF(self)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef insertText(self, dict token)
# #     cdef startTagCaption(self, dict token)
# #     cdef startTagColgroup(self, dict token)
# #     cdef startTagCol(self, dict token)
# #     cdef startTagRowGroup(self, dict token)
# #     cdef startTagImplyTbody(self, dict token)
# #     cdef startTagTable(self, dict token)
# #     cdef startTagStyleScript(self, dict token)
# #     cdef startTagInput(self, dict token)
# #     cdef startTagForm(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagTable(self, dict token)
# #     cdef endTagIgnore(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InTableTextPhase(Phase):
# #     cdef flushCharacters(self)
# #     cdef processComment(self, dict token)
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processStartTag(self, dict token)
# #     cdef processEndTag(self, dict token)

# # cdef class  InCaptionPhase(Phase):
# #     cdef ignoreEndTagCaption(self)
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagTableElement(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagCaption(self, dict token)
# #     cdef endTagTable(self, dict token)
# #     cdef endTagIgnore(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InColumnGroupPhase(Phase):
# #     cdef ignoreEndTagColgroup(self)
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagCol(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagColgroup(self, dict token)
# #     cdef endTagCol(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InTableBodyPhase(Phase):
# #     cdef clearStackToTableBodyContext(self)
# #     cdef processEOF(self)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagTr(self, dict token)
# #     cdef startTagTableCell(self, dict token)
# #     cdef startTagTableOther(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagTableRowGroup(self, dict token)
# #     cdef endTagTable(self, dict token)
# #     cdef endTagIgnore(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InRowPhase(Phase):
# #     cdef clearStackToTableRowContext(self)
# #     cdef ignoreEndTagTr(self)
# #     cdef processEOF(self)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagTableCell(self, dict token)
# #     cdef startTagTableOther(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagTr(self, dict token)
# #     cdef endTagTable(self, dict token)
# #     cdef endTagTableRowGroup(self, dict token)
# #     cdef endTagIgnore(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InCellPhase(Phase):
# #     cdef closeCell(self)
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagTableOther(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagTableCell(self, dict token)
# #     cdef endTagIgnore(self, dict token)
# #     cdef endTagImply(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InSelectPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagOption(self, dict token)
# #     cdef startTagOptgroup(self, dict token)
# #     cdef startTagSelect(self, dict token)
# #     cdef startTagInput(self, dict token)
# #     cdef startTagScript(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagOption(self, dict token)
# #     cdef endTagOptgroup(self, dict token)
# #     cdef endTagSelect(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InSelectInTablePhase(Phase):
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagTable(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagTable(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  InForeignContentPhase(Phase):
# #     cdef adjustSVGTagNames(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef processStartTag(self, dict token)
# #     cdef processEndTag(self, dict token)

# # cdef class  AfterBodyPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processComment(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagHtml(self, name)
# #     cdef endTagOther(self, dict token)

# # cdef class  InFramesetPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagFrameset(self, dict token)
# #     cdef startTagFrame(self, dict token)
# #     cdef startTagNoframes(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagFrameset(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  AfterFramesetPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagNoframes(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef endTagHtml(self, dict token)
# #     cdef endTagOther(self, dict token)

# # cdef class  AfterAfterBodyPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processComment(self, dict token)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef processEndTag(self, dict token)

# # cdef class  AfterAfterFramesetPhase(Phase):
# #     cdef processEOF(self)
# #     cdef processComment(self, dict token)
# #     cdef processSpaceCharacters(self, dict token)
# #     cdef processCharacters(self, dict token)
# #     cdef startTagHtml(self, dict token)
# #     cdef startTagNoFrames(self, dict token)
# #     cdef startTagOther(self, dict token)
# #     cdef processEndTag(self, dict token)

cdef inline void adjust_attributes(dict token, dict replacements) except *
cdef inline dict impliedTagToken(unicode name, unicode type=?, dict attributes=?, bint selfClosing=?)

# cdef class  ParseError(Exception):
#     pass
