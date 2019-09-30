from NLIMED import NLIMED

nlimed = NLIMED(repo='bm', parser='stanford', pl=3, alpha=4, beta=0.7, gamma=0.5, delta=0.8)
result = nlimed.getSparql(query='sodium',format='json')
print(result)
