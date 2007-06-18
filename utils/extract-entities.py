import urllib2
entitiesPage = "http://www.whatwg.org/specs/web-apps/current-work/multipage/section-entities.html"
output = ""
for line in urllib2.urlopen(entitiesPage).readlines():
    entityNameSig = "     <td> <code title=\"\">"
    entityValueSig = "     </td><td> "
    if line.startswith(entityNameSig):
        x = len(entityNameSig)
        output += "    \"" + line[x:-8] + "\": "
    elif line.startswith(entityValueSig):
        x = len(entityValueSig)
        output += "u\"" + line[x:-1].replace("U+", "\\u") + "\",\n"
print output
