alist = ['yo', 'mama', 'hobag']
blist = ['popa', 'sick', 'bastard']

for count, (itema, itemb) in enumerate(zip(alist, blist)):
    print([count, itema, itemb])
