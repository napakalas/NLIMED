import NLIMED

nlimed = NLIMED.NLIMED(repo='pmr', parser='stanford', pl=2, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
# query = 'concentration of potassium in the portion of tissue fluid'
query = 'mitochondrial calcium ion transmembrane transport  '
result = nlimed.getModels(query=query,format='json')
print(result)
