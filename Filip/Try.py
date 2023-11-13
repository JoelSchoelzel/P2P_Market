niu = {}
for i in range(3):
    niu[i] = {}
    niu[i]['Price'] = i
    niu[i]['Quantity'] = i*2
print(niu)

mei = []
la = {}
for m in range(3):
        la['price'] = niu[m]['Price']
        la['quantity'] = niu[m]['Quantity']
        mei.append(la.copy())
print(la)
print(mei)