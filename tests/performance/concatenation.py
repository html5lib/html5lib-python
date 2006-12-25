from time import time

x = "TEST"
y = "TEST"
z = "TEST"

t = time()
for i in xrange(1000000):
    x += y + z
    x = "TEST"
print 'duration:', time()-t

x = "TEST"
t = time()
for i in xrange(1000000):
    x = x + y + z
    x = "TEST"
print 'duration:', time()-t

x = "TEST"
t = time()
for i in xrange(1000000):
    x = "".join((x, y, z))
    x = "TEST"
print 'duration:', time()-t

x = "TEST"
t = time()
for i in xrange(1000000):
    x = "%s%s%s" % (x, y, z)
    x = "TEST"
print 'duration:', time()-t
