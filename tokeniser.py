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
        self.states = {
            "DATA":self.dataState,
            "ENTITY_DATA":self.entityDataState,
            "TAG_OPEN",
            "CLOSE_TAG_OPEN",
            "TAG_NAME",
            "BEFORE_ATTRIBUTE_NAME",
            "ATTRIBUTE_NAME",
            "AFTER_ATTRIBUTE_NAME",
            "BEFORE_ATTRIBUTE_VALUE",
            "ATTRIBUTE_VALUE_DOUBLE_QUOTE",
            "ATTRIBUTE_VALUE_SINGLE_QUOTE",
            "ENTITY_IN_ATTRIBUTE_VALUE",
            "BOGUS_COMMENT",
            "MARKUP_DECLERATION_OPEN",
            "COMMENT",
            "COMMENT_DASH",
            "COMMENT_END",
            "DOCTYPE"
            "BEFORE_DOCTYPE_NAME",
            "DOCTYPE_NAME"
            "AFTER_DOCTYPE_NAME",
            "BOGUS_DOCTYPE"
            }

	#For simplicity we assume here that the input to the tokeniser is
	#already decoded to unicode
	self.dataStrem = dataStream

	#Setup the initial tokeniser state
	self.contentModelFlag = contentModelFlags['PCDATA']
	self.state = self.states['DATA'](self)

	#The current token being processed
	self.token = None
	
	self.characterStack = []
	self.tokenQueue = []

    def getToken(self):	
	#Continue reading data until we have a token to return
	while not (self.tokenQueue):
	    self.state():
	return self.tokenQueue.pop()

    def consumeNext(self):
	if self.characterStack:
	    return self.characterStack.pop()
	else: 
	    return self.dataStream.read(1)
    
    def dataState(self):
	data = self.consumeNext()
	if (data == u"&" and 
	    (tokenizer.contentModelFlag in 
	     (contentModelFlags['PCDATA'] or contentModelFlags['RCDATA']))):
	    self.state = self.states['ENTITY']
	elif (data == u"<" and 
	      self.contentModelFlag != contentModelFlags['PLAINTEXT']):
	    self.state = self.states['TAG_OPEN']
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
		self.state=self.states['CLOSE_TAG_OPEN']
	    else:
		self.characterStack.append(data)
		self.state = self.states['DATA_STATE']
	elif tokenizer.contentModelFlag == contentModelFlags['PCDATA']:
	    
	else:
	    assert False

class ParseError(Exception):
    """Error in parsed document"""
    pass
