# from _typeshed import Self
import socket
import threading
from time import sleep, time
import struct



class Member:


    def __init__(self) -> None:
        
        self.multicast_group = ("224.0.0.1", 10000)

        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_sock.connect(('8.8.8.8', 80))
        self.my_IP = temp_sock.getsockname()[0]
        temp_sock.close()

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.my_socket.sendto(bytes([1]), ("8.8.8.8", 12000))
        self.my_socket_number = self.my_socket.getsockname()[1]
        print(self.my_socket_number)
        self.my_unique_id = (str(self.my_IP), str(self.my_socket_number))
        self.my_socket.settimeout(5)

        self.my_groups = []
        self.hashlist = []
        self.servers_address = []
        self.socket_list = []
        self.total_seq = []

        self.peer_sockets = []
        self.team_seq_num = []
        self.left_groups = []
        self.received_messages = []
        self.server_data= ""

        self.gsock = -1
        self.gsock_list = []
        self.number_of_teams = 1
        self.cv = threading.Condition()
        self.mutex = threading.Lock()



    def recmessage(self,rec_addr):
        try:
            rec_data, to_send_address = rec_addr.recvfrom(2048)
            if rec_data.decode() == '':
                return None, None

            return rec_data, to_send_address

        except Exception as ex:
            return None, None

    #Sinartisi gia na kwdikopoiisume to onoma tis omadas se arithmo
    def my_hash(self,grp_name):
        hashcode = 0
        for i in range(len(grp_name) - 1):
            hashcode += ord(grp_name[i]) ^ ord(grp_name[i + 1])

        self.hashlist.append((hashcode, grp_name))
        print(hashcode)
        return hashcode


    def my_de_hash(self,grp_name):
        for i in range(len(self.hashlist)):
            if( self.hashlist[i][1]==grp_name):
                return str(self.hashlist[i][0])

        print("de to vrike i hash")
        return -1


    def get_my_groups(self):
        return self.my_groups
   
   
    def print_my_groups(self):
        groups = self.get_my_groups()
        for i in range(len(groups)):
            for j in range(len(groups[i][1])):
                print(groups[i][1][j])
   
    #an i omada pu pame na bume einai kainurgia an oxi tote eisai idi ekei
    def new_team(self,grpname):
        for i in range(len(self.hashlist)):
            if self.hashlist[i][1] == grpname:
                return False

        return True

    #apokwdikopoiisi tu minimatos pu erxetai apo ton group service management
    def deserialization(self,list, data):
        temp = data[1:]
        temp = temp.replace("\\", "")
        temp = temp.replace("\"", "")
        splitter = temp.split("'")
        user_list = []

        i = 0
        while i < len(temp):
            if temp[i] == "#":
                i += 1
                temp_user = ""
                while temp[i] != "#":
                    temp_user += temp[i]
                    i += 1
                user_list.append(temp_user)
                # print(temp_user)
            i += 1

        list.append((splitter[1], user_list))
        return list


    #stelnw multicast gia na vrw ton server kai meta perimenw na mu anoiksei mia sindesi
    # com_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def connect_with_server(self):
        self.my_socket.sendto(bytes("D", "utf-8"), self.multicast_group)

        while True:
            self.server_data, serv_addres = self.recmessage(self.my_socket)
            if self.server_data is not None:
                self.server_data = self.server_data.decode()
                self.server_data = self.server_data.split(",")
                self.server_data[0] = self.server_data[0][2:len(self.server_data[0]) - 1]
                self.server_data[1] = self.server_data[1][:len(self.server_data[1]) - 1]
                # print((server_data[0], int(server_data[1])))
                self.server_data = (str(self.server_data[0]), int(self.server_data[1]))
                break

    
    def grp_join(self,grpname):
        # global servers_address, number_of_teams, gsock
    #elengxw an bainw prwti fora stin omada,an paw na bw defteri "ebodizw" ton eafto mu
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytes([1]), ("8.8.8.8", 12000))
        sock.settimeout(1)
        myid = (self.my_IP, sock.getsockname()[1])


        if self.new_team(grpname):
            number_of_teams = 1
        else:
            number_of_teams = 2

        if self.grp_exists(grpname, self.left_groups):
            for i in range(len(self.left_groups)):
                if self.left_groups[i] == grpname:
                    self.left_groups.pop(i)
                    break

        temp_sock = (socket.socket(socket.AF_INET, socket.SOCK_STREAM), grpname)
        temp_sock[0].connect(self.server_data)
    #stelnw se poia omada thelw na bw
        temp_sock[0].sendto(
            bytes("+", "utf-8") + bytes(str(number_of_teams), "utf-8") + bytes([len(grpname)]) + bytes(grpname,
                                                                                                    "utf-8") + bytes(
                str(myid), "utf-8"), self.server_data)

        print("sindethika me server")
        data, address = self.recmessage(temp_sock[0])
        #an mu steilei oti iparxw idi de bainw
        if str(data) == "dup":
            print("im already there")
            temp_sock[0].close()
            return -1

    # ola pigan kala bika stin omada
        if str(data.decode()[0]) == "+":
            temp = data.decode()[1:]
            splitter = temp.split("'")

            gsock = self.my_hash(splitter[1])

            self.total_seq.append((str(gsock), [], [False]))
            self.team_seq_num.append((str(gsock), []))
            self.deserialization(self.my_groups, temp)
            temp_list = []
            #pernw ta meli tis omadas apton manager
            for i in range(len(self.my_groups[len(self.my_groups) - 1][1])):
                temp_addr = self.my_groups[len(self.my_groups) - 1][1][i]
                temp_addr = temp_addr.split(",")
                temp_addr[0] = temp_addr[0][2:len(temp_addr[0]) - 1]
                temp_addr[1] = temp_addr[1][:len(temp_addr[1]) - 1]
                self.team_seq_num[len(self.team_seq_num) - 1][1].append(((temp_addr[0], int(temp_addr[1])), []))
                self.total_seq[len(self.total_seq) - 1][1].append(((temp_addr[0], int(temp_addr[1])), []))
            #an eimai prwtos eimai coordinator se periptwsi total
            if len(self.total_seq[len(self.total_seq) - 1][1]) == 1:
                print("EIMAI PRWTOS")
                self.total_seq[len(self.total_seq) - 1][2][0] = True
            # print("TOtal seq num", total_seq)

            self.received_messages.append((gsock, "s", self.my_groups[len(self.my_groups) - 1]))
            temp_sock[0].settimeout(1)
            self.socket_list.append(temp_sock)

            self.peer_sockets.append((sock,gsock,myid, [0], [0], [0]))

            return gsock

        return -1


 

    def grp_leave(self,gsock):

        self.mutex.acquire()
        for i in range(len(self.peer_sockets)):
            if str(self.peer_sockets[i][1]) == gsock:
                temp = self.peer_sockets[i]
                self.peer_sockets.pop(i)
                break

        for i in range(len(self.team_seq_num)):
            if str(self.team_seq_num[i][0]) == gsock:
                self.team_seq_num.pop(i)
                break

        for i in range(len(self.total_seq)):
            if str(self.total_seq[i][0]) == gsock:

                if self.total_seq[i][2][0] is True:
                    # for j in range(1,len(total_seq[i][1])):
                    if len(self.total_seq[i][1]) > 1:
                        temp[0].sendto(bytes("YOU", 'utf-8'), self.total_seq[i][1][1][0])
                self.total_seq.pop(i)
                break

        for i in range(len(self.hashlist)):

            if str(self.hashlist[i][0]) == gsock:

                for j in range(len(self.socket_list)):

                    if self.socket_list[j][1] == self.hashlist[i][1]:
                        try:
                            self.socket_list[j][0].connect(self.server_data)
                        except Exception as ex:
                            print()

                        self.socket_list[j][0].send(bytes("-", "utf-8") + bytes(str(self.hashlist[i][1]), "utf-8"))
                        print("esteila kai minima")
                        self.left_groups.append(self.hashlist[i][1])
                        self.hashlist.pop(i)
                        # gsock_list.pop(i)

                        self.mutex.release()
                        return 1
        self.mutex.release()
        return -1


    def find_who_left(self,list1, list2):
        for i in range(len(list1)):
            counter = 0
            for j in range(len(list2)):
                if list1[i] != list2[j]:
                    counter += 1

            if counter == len(list2):
                # print(list1[i])
                return list1[i]

    #antigrafw mia lista stin alli
    def list_duplicate(self,list1, list2):
        list1.clear()
        for i in range(len(list2)):
            list1.append(list2[i])
            return list1


    def grp_exists(self,grp_name, list1):
        for i in range(len(list1)):
            if list1[i] == grp_name:
                return True

        return False


   


    def grp_rcv(self,fd, type, block):
        if block:
            while True:
                for i in range(len(self.received_messages)):
                    if str(fd) == str(self.received_messages[i][0]):
                        if str(type) == self.received_messages[i][1]:
                            temp = self.received_messages[i][2]
                            self.received_messages.pop(i)
                            return temp

                with self.cv:
                    print("perimenw")
                    self.cv.wait()

        for i in range(len(self.received_messages)):
            if str(fd) == str(self.received_messages[i][0]):
                if str(type) == self.received_messages[i][1]:
                    temp = self.received_messages[i][2]
                    self.received_messages.pop(i)
                    return temp


    # seq_total = 0

    def grp_send(self,fd, msg, total):
        if str(total) == "0":
            for i in range(len(self.peer_sockets)):

                if str(self.peer_sockets[i][1]) == str(fd):

                    self.mutex.acquire()
                    for j in range(len(self.team_seq_num)):
                        if self.team_seq_num[j][0] == str(fd):
                            self.add_pending_message(self.team_seq_num, str(fd), self.peer_sockets[i][2], self.peer_sockets[i][3][0], False)
                            num = struct.pack("i", self.peer_sockets[i][3][0])
                            num = bytes([num[0]]) + bytes([num[1]]) + bytes([num[2]]) + bytes([num[3]])

                            for k in range(len(self.team_seq_num[j][1])):
                                self.peer_sockets[i][0].sendto(
                                    bytes([0]) + bytes([int(fd)]) + bytes([len(str(self.peer_sockets[i][2]))]) +
                                    bytes(str(self.peer_sockets[i][2]), "utf-8") + num + bytes(str(msg), "utf-8")
                                    , self.team_seq_num[j][1][k][0])

                    self.mutex.release()
                    self.peer_sockets[i][3][0] += 1
                    break
        elif str(total) == "1":

            for i in range(len(self.peer_sockets)):
                if str(self.peer_sockets[i][1]) == str(fd):

                    self.mutex.acquire()

                    for j in range(len(self.total_seq)):
                        if self.total_seq[j][0] == str(fd):
                            self.add_pending_message(self.total_seq, str(fd), self.peer_sockets[i][2], self.peer_sockets[i][5][0], True)

                            num = struct.pack("i", self.peer_sockets[i][5][0])
                            num = bytes([num[0]]) + bytes([num[1]]) + bytes([num[2]]) + bytes([num[3]])
                            # print("to stelnw to total")

                            for k in range(len(self.total_seq[j][1])):

                                self.peer_sockets[i][0].sendto(
                                    bytes([1]) + bytes([int(fd)]) + bytes([len(str(self.peer_sockets[i][2]))]) +
                                    bytes(str(self.peer_sockets[i][2]), "utf-8") + num + bytes(str(msg), "utf-8")
                                    , self.total_seq[j][1][k][0])

                    self.peer_sockets[i][5][0] += 1

                    self.mutex.release()

                    break


    received_packets = []

    #otan paw na steilw ena minima simeiwnw se poius to stelnw kai meta perimenw apadisi apo aftus gia na to paradwsw
    def add_pending_message(self,list, g_sock, address, seq, total=False):
        temp_flag = 0

        for i in range(len(list)):

            if str(list[i][0]) == str(g_sock):

                for j in range(len(list[i][1])):

                    if total is False:

                        if len(list[i][1][j][1]) > 0:
                            for k in range(len(list[i][1][j][1])):
                                if str(list[i][1][j][1][k][0]) == str(address):

                                    list[i][1][j][1][k][1].append(seq)
                                    temp_flag = 1

                            if temp_flag == 0:
                                list[i][1][j][1].append((address, [seq]))
                            temp_flag = 0

                        else:
                            list[i][1][j][1].append((address, [seq]))
                    else:
                        if len(list[i][1][j][1]) > 0:

                            for k in range(len(list[i][1][j][1])):
                                if str(list[i][1][j][1][k][0]) == str(address):
                                    list[i][1][j][1][k][1].append(seq)
                                    temp_flag = 1

                            if temp_flag == 0:
                                list[i][1][j][1].append((address, [seq]))

                            temp_flag = 0
                        else:

                            list[i][1][j][1].append((address, [seq]))

    #elegxw na ena sigkekimenos paketo iparxei sti lista twn teammates dld mu to xrwstaei
    def packet_handler(self,list, address, g_sock, seq, my_sock):
        for i in range(len(list)):
            if str(list[i][0]) == str(g_sock):
                for j in range(len(list[i][1])):
                    if list[i][1][j][0] != my_sock:
                        for k in range(len(list[i][1][j][1])):
                            if str(list[i][1][j][1][k][0]) == str(address):
                                for l in range(len(list[i][1][j][1][k][1])):
                                    if list[i][1][j][1][k][1][l] == seq:
                                        return False
        return True


    def make_first(self,g_sock, list):
        for i in range(len(list)):
            if str(list[i][0]) == str(g_sock):
                list[i][2][0] = True
                print("IM THE FIRST")

    #epanapostoli minimatos  se aftus pu mu "xrwstane"
    def resend_message(self,grpsock, list, packet_list, my_sock, my_addr, total):
        for i in range(len(list)):
            if int(list[i][0]) == grpsock:

                for j in range(len(list[i][1])):
                    # print("MY ADDR", my_addr)
                    if str(list[i][1][j][0]) != str(my_addr):
                        for k in range(len(list[i][1][j][1])):

                            for l in range(len(packet_list)):
                                if packet_list[l][1] == grpsock and packet_list[l][0] == list[i][1][j][1][k][0]:
                                    for m in range(len(list[i][1][j][1][k][1])):
                                        if packet_list[l][2][0] == list[i][1][j][1][k][1][m]:

                                            num = struct.pack("i", packet_list[l][2][0])
                                            num = bytes([num[0]]) + bytes([num[1]]) + bytes([num[2]]) + bytes([num[3]])

                                            my_sock.sendto(bytes([total]) + bytes([int(grpsock)]) + bytes(
                                                [len(list[i][1][j][1][k][0])]) + bytes(list[i][1][j][1][k][0],
                                                                                    "utf-8") + num + bytes(
                                                packet_list[l][3], "utf-8"), list[i][1][j][0])


    total_rec_packets = []


    def thread(self):
        global gsock, my_groups
        t0 = 0
        t1 = 0
        clock = 0
        message_counter = 0

        while True:
            clock += t1 - t0

            t0 = time()
            temp_list = []

            for i in range(len(self.left_groups)):
                for j in range(len(self.socket_list)):
                    if self.left_groups[i] == self.socket_list[j][1]:
                        # print("exited team", left_groups[i])
                        self.socket_list.pop(j)
                        self.my_groups.pop(j)
                        break

            if clock > 6:
                for i in range(len(self.socket_list)):
                    self.socket_list[i][0].sendto(bytes("H", "utf-8"), self.server_data)
                clock = 0
    #edw akuw to group management
            for i in range(len(self.socket_list)):

                data, address = self.recmessage(self.socket_list[i][0])

                if data is not None:
                    data = data.decode()
                    print(str(data[0]))
                    if str(data[0]) == "-" or str(data[0]) == "/":

                        if str(data[0]) == "/":
                            print("someone got an error")
                        else:
                            print("Someone left")

                        temp_list = self.deserialization(temp_list, data[1:])
                        for j in range(len(self.my_groups)):
                            if self.my_groups[j][0] == temp_list[0][0]:

                                left = self.find_who_left(self.my_groups[j][1], temp_list[0][1])

                                for k in range(len(self.hashlist)):
                                    if self.hashlist[k][1] == self.socket_list[i][1]:
                                        self.received_messages.append((self.hashlist[k][0], "s", temp_list))
                                        break

                                self.mutex.acquire()

                                self.my_groups.pop(j)
                                self.deserialization(self.my_groups, data[1:])

                                left = left.split(",")
                                left[0] = left[0][2:len(left[0]) - 1]
                                left[1] = left[1][:len(left[1]) - 1]

                                for l in range(len(self.hashlist)):
                                    if self.hashlist[l][1] == temp_list[0][0]:
                                        temp_gsock = self.hashlist[l][0]
                                        break

                                if len(self.hashlist) == 0:
                                    temp_gsock = ''

                                for k in range(len(self.team_seq_num)):

                                    if self.team_seq_num[k][0] == str(temp_gsock):
                                        for l in range(len(self.team_seq_num[k][1])):

                                            if self.team_seq_num[k][1][l][0] == (left[0], int(left[1])):
                                                print("from group",self.team_seq_num[k][0],"user ", (left[0], int(left[1])),"left")
                                                self.team_seq_num[k][1].pop(l)
                                                break

                                for k in range(len(self.total_seq)):

                                    if self.total_seq[k][0] == str(temp_gsock):
                                        for l in range(len(self.total_seq[k][1])):

                                            if self.total_seq[k][1][l][0] == (left[0], int(left[1])):
                                                # print("aftos efige ", (left[0], int(left[1])))
                                                self.total_seq[k][1].pop(l)
                                                # mutex.release()
                                                break

                                self.mutex.release()
                                break

                    if str(data[0]) == "+":

                        print("someone came")
                        temp_list = self.deserialization(temp_list, data[1:])
                        for j in range(len(self.my_groups)):

                            self.mutex.acquire()
                            if self.my_groups[j][0] == temp_list[0][0]:
                                self.my_groups.pop(j)
                                self.deserialization(self.my_groups, data[1:])

                                for l in range(len(self.hashlist)):
                                    if self.hashlist[l][1] == temp_list[0][0]:
                                        temp_gsock = self.hashlist[l][0]
                                        break

                                for k in range(len(self.team_seq_num)):

                                    if self.team_seq_num[k][0] == str(temp_gsock):
                                        temp = temp_list[0][1][len(temp_list[0][1]) - 1]
                                        temp = temp.split(",")
                                        temp[0] = temp[0][2:len(temp[0]) - 1]
                                        temp[1] = temp[1][:len(temp[1]) - 1]
                                        self.team_seq_num[k][1].append(((temp[0], int(temp[1])), []))
                                        # mutex.release()
                                        break

                                for k in range(len(self.total_seq)):

                                    if self.total_seq[k][0] == str(temp_gsock):
                                        self.total_seq[k][1].append(((temp[0], int(temp[1])), []))
                                        self.mutex.release()
                                        break

                                for k in range(len(self.hashlist)):
                                    if self.hashlist[k][1] == self.socket_list[i][1]:
                                        self.received_messages.append((self.hashlist[k][0], "s", temp_list))
                                        break

                                break
                            self.mutex.release()

    #edw akuw tus teammates
            for i in range(len(self.peer_sockets)):

                try:
                    peer_data, peer_address = self.peer_sockets[i][0].recvfrom(2048)
                except:
                    peer_data, peer_address = None, None
                if peer_data is not None:

                    # total 0
                    if int(peer_data[0]) == 0:
                        peer_gsock = int(peer_data[1])

                        temp = peer_data[3:int(peer_data[2]) + 3].decode()
                        seq = peer_data[int(peer_data[2]) + 3:int(peer_data[2]) + 7]

                        seq = struct.unpack('i', seq)[0]
                        message = peer_data[int(peer_data[2]) + 7:].decode()

                        flag = 0
                        stupid_flag = 0
                        # an su rthe prwti fora anaparage to
                        for j in range(len(self.team_seq_num)):

                            if str(self.team_seq_num[j][0]) == str(peer_gsock):
                                for k in range(len(self.team_seq_num[j][1])):
                                    if self.team_seq_num[j][1][k][0] == self.peer_sockets[i][2]:

                                        if len(self.team_seq_num[j][1][k][1]) == 0:
                                            self.add_pending_message(self.team_seq_num, peer_gsock, temp, seq, False)

                                            for n in range(len(self.team_seq_num[j][1])):
                                                self.peer_sockets[i][0].sendto(peer_data, self.team_seq_num[j][1][n][0])
                                            # print("esteila kai stus allus")
                                            continue

                                        for l in range(len(self.team_seq_num[j][1][k][1])):

                                            if str(self.team_seq_num[j][1][k][1][l][0]) == temp:
                                                flag = 1

                                                for m in range(len(self.team_seq_num[j][1][k][1][l][1])):
                                                    if self.team_seq_num[j][1][k][1][l][1][m] == seq:
                                                        # print("to xw idi")
                                                        stupid_flag = 1
                                                        break

                                                if stupid_flag == 0:
                                                    self.add_pending_message(self.team_seq_num, peer_gsock, temp, seq, False)
                                                    for n in range(len(self.team_seq_num[j][1])):
                                                        self.peer_sockets[i][0].sendto(peer_data, self.team_seq_num[j][1][n][0])
                                                    # print("esteila kai stus allus apo dw")

                                        if flag == 0:
                                            # print("se periptwsi pu de to xei prepei na to kanw add ")
                                            self.add_pending_message(self.team_seq_num, peer_gsock, temp, seq, False)
                                            for n in range(len(self.team_seq_num[j][1])):
                                                self.peer_sockets[i][0].sendto(peer_data, self.team_seq_num[j][1][n][0])
                                        flag = 0

                        # AN STO ESTEILE KAPOIOS APTUS ALLUS,VGALTO
                        if peer_address != self.peer_sockets[i][2]:
                            for j in range(len(self.team_seq_num)):
                                if self.team_seq_num[j][0] == str(peer_gsock):

                                    for k in range(len(self.team_seq_num[j][1])):
                                        if self.team_seq_num[j][1][k][0] == peer_address:

                                            for l in range(len(self.team_seq_num[j][1][k][1])):
                                                if str(self.team_seq_num[j][1][k][1][l][0]) == temp:

                                                    for m in range(len(self.team_seq_num[j][1][k][1][l][1])):
                                                        if self.team_seq_num[j][1][k][1][l][1][m] == seq:
                                                            self.team_seq_num[j][1][k][1][l][1].pop(m)
                                                            # print("EGINE I DULEIA")
                                                            break

                        #apothikefsi paketwn mono twn prototipwn
                        stupid_flag = 0
                        for j in range(len(self.received_packets)):
                            if self.received_packets[j][0] == temp and self.received_packets[j][1] == peer_gsock and \
                                    self.received_packets[j][2][0] == seq:
                                stupid_flag = 1
                                break
                        if stupid_flag == 0:
                            self.received_packets.append((temp, peer_gsock, [seq], message, [0]))

                        for j in range(len(self.received_packets)):
                            #an den su xrwstaei kaneis to paketo afto ute to proigumeno tu dwsto sto application kai ksipna to se periptwsi pu perimenei
                            if self.packet_handler(self.team_seq_num, self.received_packets[j][0], self.received_packets[j][1],
                                            self.received_packets[j][2][0], self.peer_sockets[i][2]) \
                                    and self.packet_handler(self.team_seq_num, self.received_packets[j][0], self.received_packets[j][1],
                                                    self.received_packets[j][2][0] - 1, self.peer_sockets[i][2]) \
                                    and self.received_packets[j][4][0] == 0:
                                # print("vazw afto",peer_gsock,received_packets[j][3])

                                self.received_messages.append((peer_gsock, "n", self.received_packets[j][3]))
                                self.received_packets[j][4][0] = 1
                                with self.cv:
                                    self.cv.notify()
                        #ana 5 seconds steile stus teammates gia ta xrwstumena
                        if clock >= 5:
                            for j in range(len(self.hashlist)):
                                if str(self.hashlist[j][0]) == str(self.peer_sockets[i][2]):
                                    self.resend_message(self.hashlist[j][0], self.team_seq_num, self.received_packets, self.peer_sockets[i][0],
                                                self.peer_sockets[i][2], 0)

                    #######################################TOTAL#######################################################

                    #an su pei oti eisai o prwtos gine prwtos
                    # try:
                    #     if peer_data.decode() == "YOU":
                    #         make_first(peer_sockets[i][1], total_seq)
                    # except:
                    #     print()

                    # if int(peer_data[0]) == 1:
                 
                    #     peer_gsock = int(peer_data[1])
                    #     temp = peer_data[3:int(peer_data[2]) + 3].decode()
                    #     seq = peer_data[int(peer_data[2]) + 3:int(peer_data[2]) + 7]

                    #     seq = struct.unpack('i', seq)[0]
                    #     if seq >= 0:
                    #         message = peer_data[int(peer_data[2]) + 7:].decode()
                    #     else:
                    #         message = None

                    #     flag = 0
                    #     stupid_flag = 0

                    #     for j in range(len(total_seq)):
                    #         if str(total_seq[j][0]) == str(peer_gsock):
                    #             for k in range(len(total_seq[j][1])):
                    #                 if total_seq[j][1][k][0] == peer_sockets[i][2]:

                    #                     if len(total_seq[j][1][k][1]) == 0:
                    #                         add_pending_message(total_seq, peer_gsock, temp, seq, True)
                    #                         peer_sockets[i][4][0] += 1  # an to pires prwti fora anevase to total sequence

                    #                         for n in range(len(total_seq[j][1])):
                    #                             peer_sockets[i][0].sendto(peer_data, total_seq[j][1][n][0])
                    #                             # print("esteila kai stus allus")
                    #                         continue

                    #                     for l in range(len(total_seq[j][1][k][1])):
                    #                         if str(total_seq[j][1][k][1][l][0]) == temp:
                    #                             flag = 1

                    #                             for m in range(len(total_seq[j][1][k][1][l][1])):
                    #                                 if str(total_seq[j][1][k][1][l][1][m]) == str(seq):
                    #                                     # print("to xw idi")
                    #                                     stupid_flag = 1
                    #                                     break

                    #                             if stupid_flag == 0:
                    #                                 add_pending_message(total_seq, peer_gsock, temp, seq, True)
                    #                                 peer_sockets[i][4][0] += 1

                    #                                 for n in range(len(total_seq[j][1])):
                    #                                     peer_sockets[i][0].sendto(peer_data, total_seq[j][1][n][0])
                    #                                     # print("esteila kai stus allus apo dw")

                    #                     if flag == 0:
                    #                         add_pending_message(total_seq, peer_gsock, temp, seq, True)
                    #                         peer_sockets[i][4][0] += 1
                    #                         for n in range(len(total_seq[j][1])):
                    #                             peer_sockets[i][0].sendto(peer_data, total_seq[j][1][n][0])
                    #                     flag = 0

                    #     if peer_address != peer_sockets[i][2]:
                    #         for j in range(len(total_seq)):
                    #             if total_seq[j][0] == str(peer_gsock):

                    #                 for k in range(len(total_seq[j][1])):
                    #                     if total_seq[j][1][k][0] == peer_address:

                    #                         for l in range(len(total_seq[j][1][k][1])):

                    #                             if str(total_seq[j][1][k][1][l][0]) == temp:
                    #                                 for m in range(len(total_seq[j][1][k][1][l][1])):

                    #                                     if total_seq[j][1][k][1][l][1][m] == seq:
                    #                                         total_seq[j][1][k][1][l][1].pop(m)
                    #                                         print("EGINE I DULEIA")
                    #                                         break

                    #     stupid_flag = 0
                    #     for j in range(len(total_rec_packets)):
                    #         if str(total_rec_packets[j][0]) == str(peer_gsock) and str(total_rec_packets[j][1]) == str(
                    #                 temp) and str(total_rec_packets[j][2][0]) == str(seq):
                    #             stupid_flag = 1
                    #             break

                    #     if stupid_flag == 0:
                    #         total_rec_packets.append((peer_gsock, temp, [seq], message, [0], [0]))
                    #     elif message == '':
                    #         total_rec_packets.append((peer_gsock, temp, [-0.5], message, [0], [0]))

                    #     if len(total_rec_packets) > 0:
                    #         for j in range(len(total_seq)):
                    #             #an eisai o coordinator
                    #             if total_seq[j][0] == str(peer_sockets[i][1]) and total_seq[j][2][0] is True:
                    #                 for k in range(len(total_rec_packets)):
                    #                     #den su xrwstaei kaneis to paketo kai den to xeis ksanasteilei steile diatagi na to diavasun
                    #                     if total_rec_packets[k][0] == peer_sockets[i][1] \
                    #                             and total_rec_packets[k][2][0] >= 0 \
                    #                             and total_rec_packets[k][5][0] == 0 \
                    #                             and packet_handler(total_seq, total_rec_packets[k][1],
                    #                                             total_rec_packets[k][0], total_rec_packets[k][2][0],
                    #                                             peer_sockets[i][2]):
                    #                         num = struct.pack("i", -int(total_rec_packets[k][2][0]))

                    #                         num = bytes([num[0]]) + bytes([num[1]]) + bytes([num[2]]) + bytes([num[3]])

                    #                         total_rec_packets[k][5][0] = 1
                    #                         print("stelnw DIATAGI")

                    #                         for n in range(len(total_seq[j][1])):
                    #                             peer_sockets[i][0].sendto(
                    #                                 bytes([1]) + bytes([int(total_seq[j][0])]) + bytes(
                    #                                     [len(total_rec_packets[k][1])]) + bytes(total_rec_packets[k][1],
                    #                                                                             "utf-8") + num,
                    #                                 total_seq[j][1][n][0])

                    #     for j in range(len(total_rec_packets)):
                    #         if total_rec_packets[j][2][0] > 0:
                    #             #an den su xrwstaei kaneis to paketo kai den su xrwstaei kaneis ti diatagi diavasmatos tu paketu ute tu proigumenu paketu (ti diatagi) dwsto sto app
                    #             if packet_handler(total_seq, total_rec_packets[j][1], total_rec_packets[j][0],
                    #                             total_rec_packets[j][2][0], peer_sockets[i][2]) \
                    #                     and packet_handler(total_seq, total_rec_packets[j][1], total_rec_packets[j][0],
                    #                                     -total_rec_packets[j][2][0], peer_sockets[i][2]) \
                    #                     and packet_handler(total_seq, total_rec_packets[j][1], total_rec_packets[j][0],
                    #                                     -total_rec_packets[j][2][0] + 1, peer_sockets[i][2]) \
                    #                     and total_rec_packets[j][4][0] == 0:
                    #                 received_messages.append((total_rec_packets[j][0], "n", total_rec_packets[j][3]))
                    #                 total_rec_packets[j][4][0] = 1

                    #                 with cv:
                    #                     cv.notify()

                    #         elif total_rec_packets[j][2][0] == 0:
                    #             if packet_handler(total_seq, total_rec_packets[j][1], total_rec_packets[j][0],
                    #                             total_rec_packets[j][2][0], peer_sockets[i][2]) \
                    #                     and packet_handler(total_seq, total_rec_packets[j][1], total_rec_packets[j][0],
                    #                             -0.5, peer_sockets[i][2])\
                    #                     and total_rec_packets[j][4][0] == 0:
                    #                 # print("VAZW TO 0 PAKETO")
                    #                 received_messages.append((total_rec_packets[j][0], "n", total_rec_packets[j][3]))
                    #                 total_rec_packets[j][4][0] = 1

                    #                 with cv:
                    #                     cv.notify()

            t1 = time()


    def start(self):
        self.connect_with_server()
        thread_id = threading.Thread(target=self.thread, args=(), daemon=True)
        thread_id.start()

    def stop(self):
        self.my_socket.close()
        for i in range(len(self.socket_list)):
            self.socket_list[i][0].close()

    def clear_client(self):
        temp_list = []

        for i in range(len(self.hashlist)):
            temp_list.append(self.hashlist[i][0])

        for i in range(len(temp_list)):
            print("leavarw", temp_list[i])
            print(self.grp_leave(str(temp_list[i])))


# descriptors = []


def app():
    descriptors = []
    member = Member()
    member.start()
    wait = ''
    while True:
        choice = input("(1)join\n(2)leave\n(3)exit\n(4)my groups\n(5)send\n: ")
        
        # print(member.hashlist)
        if choice == "1":
            # s_name = input("name-->")
            s_group = input("group to join -->")

            print("GROUP TO JOIN ", s_group)
          
            descriptors.append(member.grp_join(s_group))
            if descriptors[len(descriptors) - 1] == -1:
                print("couldn't enter team")
                # sock.close()
                descriptors.pop(len(descriptors) - 1)
                continue

        if choice == "2":
            s_name = input("group to leave -->")
            # print(member.hashlist)
            group_hash = member.my_de_hash(s_name)
            # print(group_hash)
            if member.grp_leave(group_hash) == 1:
                print("left group",s_name)
            else:
                print("could not leave team")

        if choice == "3":
            member.clear_client()
            member.stop()
            break
        # print(my_groups)
        if choice == "4":
            print(member.get_my_groups())
            # member.print_my_groups()

           

        if choice == "5":
            grp_name = input("group name: ")
            msg = input("MESSAGE -> ")
            # total = input("TOTAL? ->")
            # if total == 'y':
                # print(team_seq_num)
                # pass
                # member.grp_send(fd, msg, 1)
            # else:
            group_hash = member.my_de_hash(grp_name)
            # print(group_hash)
            member.grp_send(group_hash, msg, 0)

        wait= input("Wait for incoming messages?")
        for i in range(len(descriptors)):
            message = member.grp_rcv(descriptors[i], "s", False)

            if wait == 'y':
                message2=member.grp_rcv(descriptors[i], "n", True)
            else:
                message2 = member.grp_rcv(descriptors[i], "n", False)

            if message is not None:
                print("From Group Management Service:",descriptors[i],"message -->", message)
            if message2 is not None:
                print("From Group:", descriptors[i], "message -->",message2)



if __name__ == '__main__':
    app()


