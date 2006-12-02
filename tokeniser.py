contentModelFlags = {"PCDATA":0, "RCDATA":1, "CDATA":2, "PLAINTEXT":3}

#Data representing the end of the input stream
EOF = object()

class Token(object):
    """Abstract base class from which all tokens derive"""
    def __init__(self):
	raise NotImplementedError

class DoctypeToken(Token):
    """Token representing a DOCTYPE
    Attributes - name:  The name of the doctype
                 error: The Error status of the doctype (True, False, or 
                        None for undefined)"""
    def __init__(self):
	self.name = None
	self.error = None

class StartTag(Token):
    """Token representing a start tag
    Attributes - name:   The tag name
                 attributes: A list of (attribute-name,value) tuples"""
    def __init__(self, name=None):
	self.name = name
	self.attributes = []

class EndTag(Token):
    """Token representing an end tag
    Attributes - name:   The tag name
                 attributes: A list of (attribute-name,value) tuples"""
    def __init__(self, name):
	self.name = name
	self.attributes = []

class CommentToken(Token):
    """Token representing a comment
    Attributes - data:   The comment data"""
    def __init__(self):
	self.data = None

class CharacterToken(Token):
    """Token representing a comment
    Attributes - data:   The character data"""
    def __init__(self):
	self.data = None
    def __eq__(self, other):
        return self.data == other.data

class EOFToken(Token):
    """Token representing the end of the file"""
    def __init__(self):
	pass

class Tokeniser(object):
    def __init__(self, dataStream):
	#For simplicity we assume here that the input to the tokeniser is
	#already decoded to unicode
	self.dataStrem = dataStream

        self.states = {
            "data":self.dataState,
            "entityData":self.entityDataState,
            "tagOpen":self.tagOpenState,
            "closeTagOpen":self.closeTagOpenState,
            "tagName":self.tagNameState,
            "beforeAttributeName":self.beforeAttributeNameState,
            "attributeName":self.attributeNameState,
            "afterAttributeName":self.afterAttributeNameState,
            "beforeAttributeValue":self.beforeAttributeValueState,
            "attributeValueDoubleQuote":self.attributeValueDoubleQuoteState,
            "attributeValueSingleQuote":self.attributeValueSingleQuoteState,
            "entityInAttributeValue":self.entityInAttributeValueState,
            "bogusComment":self.bogusCommentState,
            "markupDeclerationOpen":self.markupDeclerationOpenState,
            "comment":self.commentState,
            "commentDash":self.commentDashState,
            "commentEnd":self.commentEndState,
            "doctype":self.doctypeState,
            "beforeDoctypeName":self.beforeDoctypeNameState,
            "doctypeName":self.doctypeNameState,
            "afterDoctypeName":self.afterDoctypeNameState,
            "bogusDoctype":self.bogusDoctypeState,
            }


	#Setup the initial tokeniser state
	self.contentModelFlag = contentModelFlags['PCDATA']
	self.state = self.states['data'](self)

	#The current token being processed
	self.token = None
	
	self.characterQueue = []
	self.tokenQueue = []

    def getToken(self):	
	#Continue reading data until we have a token to return
	while not (self.tokenQueue):
	    self.state()
	return self.tokenQueue.pop()
	
    def consumeNext(self):
        """Get the next character to be consumed"""
        #If the characterQueue has chacracters they must be processed 
        #efore any character is added to the stream. 
        #This is to allow e.g. lookahead
	if self.characterQueue:
	    return self.characterQueue.pop(0)
	else: 
	    return self.dataStream.read(1)
    
    def dataState(self):
	data = self.consumeNext()
	if (data == u"&" and 
	    (tokenizer.contentModelFlag in 
	     (contentModelFlags['PCDATA'] or contentModelFlags['RCDATA']))):
	    self.state = self.states['entity']
	elif (data == u"<" and 
	      self.contentModelFlag != contentModelFlags['PLAINTEXT']):
	    self.state = self.states['tagOpen']
	elif data == EOF:
	    self.tokenQueue.append(EOFToken())
	else:
	    self.tokenQueue.append(CharacterToken(data))
    
    def entityDataState(self):
	assert self.content_model_flag != contentModelFlags['PCDATA']
	raise NotImplementedError
    
    def tagOpenState(self):
	data = self.consumeNext()
	if (tokenizer.contentModelFlag in 
	    (contentModelFlags['RCDATA'] or contentModelFlags['CDATA'])):
	    if data == u"/":
		self.state=self.states['closeTagOpen']
	    else:
		self.characterQueue.append(data)
		self.state = self.states['DATA_STATE']
	elif tokenizer.contentModelFlag == contentModelFlags['PCDATA']:
	    if data == u"!":
                self.state = self.states["markupDeclerationOpen"]
	else:
	    assert False
          
    def closeTagOpenState(self):
        raise NotImplementedError

    def tagNameState(self):
        raise NotImplementedError

    def beforeAttributeNameState(self):
        raise NotImplementedError

    def attributeNameState(self):
        raise NotImplementedError

    def afterAttributeNameState(self):
        raise NotImplementedError

    def beforeAttributeValueState(self):
        raise NotImplementedError

    def attributeValueDoubleQuoteState(self):
        raise NotImplementedError

    def attributeValueSingleQuoteState(self):
        raise NotImplementedError

    def entityInAttributeValueState(self):
        raise NotImplementedError

    def bogusCommentState(self):
        raise NotImplementedError

    def markupDeclerationOpenState(self):
        raise NotImplementedError

    def commentState(self):
        raise NotImplementedError

    def commentDashState(self):
        raise NotImplementedError
    
    def commentEndState(self):
        raise NotImplementedError
    
    def doctypeState(self):
        raise NotImplementedError

    def beforeDoctypeNameState(self):
        raise NotImplementedError

    def doctypeNameState(self):
        raise NotImplementedError

    def afterDoctypeNameState(self):
        raise NotImplementedError

    def bogusDoctypeState(self):
        raise NotImplementedError

class ParseError(Exception):
    """Error in parsed document"""
    pass
