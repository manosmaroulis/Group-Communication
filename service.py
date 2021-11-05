import signal
import socket
import struct
import threading



class Server:
    
    def __init__(self) -> None:
        self.group_list= []
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket.settimeout(1)



        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.connect(("8.8.8.8", 80))

        self.my_IP= my_socket.getsockname()[0]
        print(self.my_IP)

        my_socket.close()

        self.send_socket.bind((str(self.my_IP),0))
        self.send_socket.listen(1)

        self.my_socket_number = self.send_socket.getsockname()[1]
        self.my_unique_id = (str(self.my_IP), str(self.my_socket_number))



        signal.signal(signal.SIGINT, self.handler)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)

        self.multicast_group = "224.0.0.1"  # "224.3.29.71"
        self.server_address = ('', 10000)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.server_address)
        self.group = socket.inet_aton(self.multicast_group)
        self.mreq = struct.pack('4sL', self.group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)



        self.cl_sockets = []
        self.cl_adresses = []
        self.my_tcp_sockets = []
        self.delay = []


    def recmessage(self,rec_addr):
        if rec_addr is None:
            return None,None

        try:
            rec_data, to_send_address = rec_addr.recvfrom(1024)
            if rec_data.decode() == '':
                return None,None
            return rec_data,to_send_address

        except Exception as ex:
            if ex.__class__ is socket.timeout:
                return None,None


    def handler(self,signum, frame):
        self.sock.close()
        self.send_socket.close()
        print("closing")

        exit()





    def member_finder(self,list, member, mem_addr, group, new_team):

        for i in range(len(list)):

            if list[i][0] == group:
                for j in range(len(list[i][1])):
                    if list[i][1][j][0] == member or list[i][1][j][1] == mem_addr or (new_team == 2 and list[i][1][j][1][0] == mem_addr[0]):
                        return True

        return False


    def group_name_finder(self,list,name):

        for i in range(len(list)):
            if list[i][0] == name:
                return True

        return False


    def add_member(self,list,group,member):
        for i in range(len(list)):
            if list[i][0]== group:
                list[i][1].append(member)
                return True

        return False

#serialization gia na steilw to paketo
    def group_to_tuple(self,grp_name, group):

        temp = "#"+str(group[0][0])+"#"
        for i in range(1,len(group)):
            temp = temp + "#"+str(group[i][0])+"#"

        temp= (grp_name,temp)
        # print("i group to tuple ekane afto",temp)
        return temp


    def address_to_tcp_match(self,addr,addr_list):

        for i in range(len(addr_list)):
            if addr_list[i] == addr:
                return i

        return None


    def send_to_team(self,list,group,message,client_sock):
        for i in range(len(list)):
            if list[i][0] == group:
                temp = self.group_to_tuple(group,list[i][1])
                for j in range(len(list[i][1])):
                # print(list[i][1][j][1])
                #  print("afto stelnw",temp)
                    counter=self.address_to_tcp_match(list[i][1][j][1],self.cl_adresses)

                    #print("to stelnw safton",list[i][1][j][1],"arithmos",counter)
                    self.cl_sockets[counter].send(bytes(str(message), "utf-8")+bytes(str(temp), "utf-8"))

                break


    def delete_member(self,mem_address,group_name,list):
        for i in range(len(list)):
            if list[i][0] == group_name:
                for j in range(len(list[i][1])):
                    if list[i][1][j][1] == mem_address:
                        list[i][1].pop(j)
                        ##an einai o teleftaios diagrafw kai to team
                        if len(list[i][1])<1:
                            print("team destroyed")
                            list.pop(i)

                        return True

        return False



    def run(self):
        while True:

            data, address = self.recmessage(self.sock)
            if data is not None:


                print("TCP SOCKET",self.my_socket_number, self.my_IP)
                # cl_sockets[len(cl_sockets) - 1].listen(1)

                self.sock.sendto(bytes(str((self.my_IP, self.my_socket_number)), 'utf-8'), address)

                #my_data, my_address = recmessage(cl_sockets[i])

            try:
                connection, addr = self.send_socket.accept()
                connection.settimeout(5)
                self.cl_sockets.append(connection)
                self.cl_adresses.append(addr)
                self.delay.append(0)
            except Exception as ex:
                connection=None

            #edw perimenw kainurgius pelates
            try:
                my_data, my_addr = self.recmessage(connection)

            except Exception as ex:
                print("den irthe tpt apo kainurgio",ex)

            if my_data is not None:

                take_number = my_data
                my_data = my_data.decode()
                print(my_data)


                if str(my_data[0]) == "+":
                    num = int(take_number[1])
                    new_name = my_data[int(take_number[2]) + 3:]
                    group_name = my_data[3:int(take_number[2]) + 3]

                    if self.group_name_finder(self.group_list, group_name) is False:
                        temp_list = []
                        temp = (group_name, temp_list)
                        self.group_list.append(temp)

                    if self.member_finder(self.group_list, new_name,addr, group_name, num) is False:

                        temp = (new_name,addr)

                        self.add_member(self.group_list, group_name, temp)
                        # print(group_list)

                        ###eidopoiw tus ipoloipus kai teleftaio ton kainurgio gt egine append
                        self.send_to_team(self.group_list, group_name, "+",None)
                        ###
                    else:
                        print("name  already exists ")
                        connection.send(bytes("dup", "utf-8"))
                        self.cl_sockets.pop(len(self.cl_sockets)-1)
                        self.cl_adresses.pop(len(self.cl_adresses)-1)
                        self.delay.pop(len(self.delay)-1)

                # if str(my_data[0])=="-":
                #     print("error probably")

        #edw eksipiretw tus idi iparxodes pleates
            for i in range(len(self.cl_sockets)):

                try:
                    self.cl_sockets[i].settimeout(1)
                    my_data, my_addr = self.recmessage(self.cl_sockets[i])

                except Exception as ex:
                    print("den irthe tpt apo kainurgio", ex)

                if my_data is not None:
                    print(my_data)
                    my_data = my_data.decode()

                    if len(my_data)>1:
                        my_data=my_data.replace('H','')

                    if my_data !='' and str(my_data[0]) == "-":
                        # print("to steile")
                        if self.delete_member(self.cl_adresses[i], str(my_data[1:]), self.group_list):

                            self.cl_adresses.pop(i)
                            self.cl_sockets[i].close()
                            self.cl_sockets.pop(i)
                            print("client deleted")
                            print(self.group_list)
                            connection=None
                            self.send_to_team(self.group_list,str(my_data[1:]),"-",None)
                            self.delay.pop(i)
                            break

                    if str(my_data) == "H" and len(my_data) == 1:
                        print("hartbit")
                        self.delay[i] = 0
                        continue

                else:
                    self.delay[i] += 1
                    if self.delay[i] > 5:
                        print("client drinking coffee closing him")

                        temp_grp = ''
                        temp_name= ''
                        stupid_flag=0
                        for k in range(len(self.group_list)):
                            for n in range(len(self.group_list[k][1])):

                                if self.group_list[k][1][n][1] == self.cl_adresses[i]:
                                    temp_grp = self.group_list[k][0]
                                    temp_name=self.group_list[k][1][n][0]
                                    stupid_flag=1
                                    break

                            if stupid_flag == 1:
                                stupid_flag=0
                                break

                        if self.delete_member(self.cl_adresses[i],temp_grp,self.group_list):
                            self.send_to_team(self.group_list,temp_grp,"/",None)
                            print("diagraftike apo to team", temp_grp, "o user", temp_name)
                        self.cl_sockets[i].close()
                        self.cl_sockets.pop(i)
                        self.cl_adresses.pop(i)
                        self.delay.pop(i)
                        break





if __name__ == '__main__':
    my_server = Server()
    my_server.run()