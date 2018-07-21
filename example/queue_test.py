import queue


if __name__ == "__main__":
    q = queue.Queue(10)

    data = ['0088657', 'A005690', '보통가', '1', '19,400', '1', '0', '0', '1']



    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)
    q.put(data)

    print(q.qsize())
    test_list = list(q.queue)
    print(q.qsize())

    #print(test_list)

    print(test_list[0][1])


    #q.put(data)
    #q.put('banana')
    #q.put(10)
    #print(q.qsize())
    #print(q.get())
    #a = q.get()
    #print(a)
    #print(q.qsize())

    #print(q.get())
    #print(q.qsize())

