'''N階階梯 走完 兩種方式 方式一 一次一步  一次兩部  總共幾種方式把階梯走完'''

''' x + 2y = n '''
''' x = n , n-2, n-4 '''

# def floor(num):
#     sum = 1
#     for i in range(1,num + 1):
#         sum *= i
#     return sum
# n = 9
# x = [x for x in range(0,n+1,2)] #
# y = [(n-i) // 2 for i in x]
# print(x, y)
# for c in range(len(y)):
'''假設10層，前面9層最後一階用1去上有M總方法  前面8層有N總方法最後一階用2去上，
大於3的情況一次走一步或者兩部，看接下來情況如何，當能走的步數小於3(1or2)即為其中一走走法'''
def step(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 2
    else:
        return step(n - 1) + step(n - 2)

print(step(0))
