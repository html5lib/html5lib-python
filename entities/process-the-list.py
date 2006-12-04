entities = file("the-list","r")
for line in entities.readlines():
    l = line[:-1].split(" \t")
    print "    \"" + l[0] + "\": \"\\u" + l[1][2:] + "\","
entities.close()
